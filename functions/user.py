import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from http import HTTPStatus
import json

from common.const import LAMBDA_STAGE
from common.decorator import handler
from common.exception import ApplicationException
from common.resource import Cognito
from common.response import PostResponse, Response
from common.resource import Table
from common.util import is_empty


table_user = Table.USER
table_adage = Table.ADAGE


@handler
def post(event, context):
    """ユーザ登録

    Args:
        event (dict): イベント
        context (dict): コンテキスト

    Raises:
        ApplicationException: 既に存在するログインIDの場合

    Returns:
        PostResponse: レスポンス
    """
    body = json.loads(event['body'])
    login_id = body['loginId']
    password = body['password']

    # 既に存在するログインIDの場合
    user = table_user.query(
        IndexName='loginId-Index',
        KeyConditionExpression=Key('loginId').eq(login_id),
        ProjectionExpression='loginId',
    )
    if not is_empty(user['Items']):
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            f'This loginId already exists. loginId: {login_id}'
        )

    # ユーザ登録(cognito)
    cognito = Cognito()
    response = cognito.sing_up(
        Username=login_id,
        Password=password,
    )

    # ユーザ登録(dynamoDB)
    item = {
        'userId': response['UserSub'],
        'key': 'userId',
        'loginId': login_id,
        'userName': 'No name',
    }
    table_user.put_item(Item=item)

    return PostResponse(item)


@handler
def get(event, context):
    """ユーザ参照

    Returns:
        Response: レスポンス
    """
    user_id = event['requestContext']['authorizer']['claims']['sub']
    user = get_user_all(user_id)

    return Response(user)


@handler
def put(event, context):
    """ユーザ更新

    Raises:
        ApplicationException: ユーザが存在しない場合
        ApplicationException: 変更する値が空の場合

    Returns:
        Response: レスポンス
    """
    user_id = event['requestContext']['authorizer']['claims']['sub']
    body = json.loads(event['body'])
    new_user_name = body.get('userName')

    # 変更する値が空の場合
    if is_empty(new_user_name):
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            'Parameter is empty.',
        )

    # ユーザ名が20文字より大きい場合
    if len(new_user_name) > 20:
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            'The number of characters is over.',
        )

    # ユーザが存在しない場合
    if is_empty(user_id):
        raise ApplicationException(
            HTTPStatus.NOT_FOUND,
            f'User does not exists. userId: {user_id}',
        )

    else:
        table_user.update_item(
            Key={
                'userId': user_id,
                'key': 'userId',
            },
            UpdateExpression='set userName=:userName',
            ExpressionAttributeValues={
                ':userName': new_user_name,
            },
        )

        adages = get_adages_by_user_id(user_id)
        print(adages)
        for adage in adages:
            table_adage.update_item(
                Key={
                    'adageId': adage['adageId'],
                    'key': f'episode#{user_id}',
                },
                UpdateExpression='set userName=:userName',
                ExpressionAttributeValues={
                    ':userName': new_user_name,
                },
            )

    return Response(
        {'userName': new_user_name},
    )



@handler
def confirm(event, context):
    body = json.loads(event['body'])
    cognito = Cognito()

    # 認証
    try:
        response = cognito.confirm_sign_up(
            Username=body['loginId'],
            ConfirmationCode=body['code'],
        )

    except ClientError as e:

        # コード有効切れの場合、コード再送信
        if e.response['Error']['Code'] == 'ExpiredCodeException':
            response = cognito.resend_confirmation_code(
                Username=body['loginId'],
            )
            return PostResponse(response)

        else:
            raise e

    return PostResponse(
        {'loginId': body['loginId']},
    )


@handler
def login(event, context):
    """ユーザ認証、IDトークン発行

    Raises:
        ApplicationException: メールアドレスが違う場合、パスワードが違う場合

    Returns:
        PostResponse: IDトークン, アクセストークン
    """
    body = json.loads(event['body'])
    login_id = body.get('loginId')
    password = body.get('password')

    if is_empty(login_id or password):
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            'Mail address and Password is required',
        )

    # ログイン
    cognito = Cognito()

    try:
        response = cognito.initiate_auth(
            AuthParameters={
                'USERNAME': login_id,
                'PASSWORD': password,
            },
        )
    except ClientError as e:
        print(e.response)
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            e.response['Error']['Message'],
        )

    user = get_user_by_login_id(
        login_id,
        ['userId', 'userName'],
    )

    return PostResponse(
        {
            'idToken': response['AuthenticationResult']['IdToken'],
            'accessToken': response['AuthenticationResult']['AccessToken'],
            'refreshToken': response['AuthenticationResult']['RefreshToken'],
            'userId': user['userId'],
            'userName': user['userName'],
        },
    )


@handler
def send_reset_password_code(event, context):
    body = json.loads(event['body'])
    login_id = body.get('loginId')

    # ユーザ確認
    user = table_user.query(
        TableName='usersTable',
        IndexName="loginId-Index",
        KeyConditionExpression=Key('loginId').eq(login_id),
    )

    # ユーザが存在しない場合
    if is_empty(user['Items']):
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST.value,
            f'User does not exists. loginId: {login_id}'
        )

    # 再設定コード送信
    cognito = Cognito()
    cognito.admin_reset_user_password(
        Username=login_id,
    )

    return Response({})


@handler
def reset_password(event, context):
    body = json.loads(event['body'])
    login_id = body.get('loginId')
    code = body.get('code')
    password = body.get('password')

    cognito = Cognito()
    cognito.confirm_forgot_password(
        Username=login_id,
        ConfirmationCode=code,
        Password=password,
    )

    return Response({})


@handler
def delete(event, context):
    """ユーザ削除

    Raises:
        ApplicationException: ユーザが存在しない場合
        ApplicationException: メールアドレスが違う場合

    Returns:
        Response: レスポンス
    """
    body = json.loads(event['body'])
    user_id = event['requestContext']['authorizer']['claims']['sub']
    login_id = body.get('loginId')

    user = get_user_all(user_id)

    # ユーザが存在しない場合
    if is_empty(user):
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            f'User does not exists. userId: {user_id}',
        )

    # メールアドレス確認
    if not user.get('loginId') == login_id:
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            f'Mail address is different. address: {login_id}'
        )

    # エピソード削除
    for episode in user.get('episodeList'):
        invoke_lambda_episode_delete(episode.get('adageId'), user_id)

    # ユーザテーブル: ユーザ削除
    table_user.delete_item(
        Key={
            'userId': user['userId'],
            'key': 'userId',
        },
    )

    # Cognitoユーザ削除
    cognito = Cognito()
    cognito.delete_user(
        AccessToken=body.get('accessToken'),
    )

    return Response({})


def get_user_by_login_id(login_id: str, projection_list: list) -> dict:
    """ログインIDからユーザ取得

    Args:
        login_id (str): ログインID
        projection_list (list): 取得属性リスト

    Returns:
        dict: ユーザ
    """
    item = table_user.query(
        IndexName='loginId-Index',
        KeyConditionExpression=Key('loginId').eq(login_id),
        ProjectionExpression=','.join(projection_list),
    )

    return {} if is_empty(item.get('Items')) else item['Items'][0]


def get_user(user_id: str, projection_list: list) -> dict:
    """ユーザ取得

    Args:
        user_id (str): ユーザID
        projection_list (list): 取得属性リスト

    Returns:
        dict: ユーザ
    """
    item = table_user.get_item(
        Key={
            'userId': user_id,
            'key': 'userId',
        },
        ProjectionExpression=','.join(projection_list),
    )

    return {} if is_empty(item.get('Item')) else item['Item']


def get_user_all(user_id: str) -> dict:
    """ユーザ情報取得

    Args:
        user_id (str): ユーザID

    Returns:
        dict: ユーザ情報
    """
    user_item = table_user.get_item(
        Key={
            'userId': user_id,
            'key': 'userId',
        },
        ProjectionExpression='userId,userName,loginId',
    )

    user_episode = table_user.query(
        KeyConditionExpression=Key('userId').eq(user_id) &
            Key('key').begins_with('episode'),
        ProjectionExpression='adageId,title,episode',
    )

    user_item['Item']['episodeList'] = user_episode['Items']

    return user_item['Item']


def get_adages_by_user_id(user_id: str) -> list:
    """ユーザIDから格言リスト取得

    Args:
        user_id (str): ユーザID

    Returns:
        list: 格言リスト
    """
    items = table_adage.query(
        IndexName="userId-Index",
        KeyConditionExpression=Key('userId').eq(user_id),
        ProjectionExpression='adageId',
    )

    return [] if is_empty(items.get('Items')) else items['Items']


def invoke_lambda_episode_delete(adage_id: str, user_id: str):
    """エピソード削除関数呼び出し

    Args:
        adage_id (str): 格言ID
        user_id (str): ユーザID
    """
    client = boto3.client('lambda')

    client.invoke(
        FunctionName=f'share-adage-service-{LAMBDA_STAGE}-episodeDelete',
        Payload=json.dumps(
            {
                'body': json.dumps(
                    {
                        'adageId': adage_id,
                        'userId': user_id,
                    },
                ),
            },
        ),
    )
