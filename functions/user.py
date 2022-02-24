from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from http import HTTPStatus
import json

from common.decorator import handler
from common.exception import ApplicationException
from common.resource import Cognito
from common.response import PostResponse, Response
from common.resource import Table
from common.util import is_empty


table_user = Table.USER


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

    return PostResponse(
        {
            'idToken': response['AuthenticationResult']['IdToken'],
            'accessToken': response['AuthenticationResult']['AccessToken'],
            'refreshToken': response['AuthenticationResult']['RefreshToken'],
            'userName': get_user_name(login_id),
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
    sub = event['requestContext']['authorizer']['claims']['sub']
    body = json.loads(event['body'])

    user = table_user.get_item(
        Key={
            'userId': sub,
            'key': 'userId',
        },
    )

    if is_empty(user.get('Item')):
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            'User does not exists',
        )

    login_id = body.get('loginId')
    if not user['Item']['loginId'] == login_id:
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            f'Mail address is different. address: {login_id}'
        )

    # DynamoDBユーザ削除
    table_user.delete_item(
        Key={
            'userId': user['Item']['userId'],
            'key': 'userId',
        },
    )

    # Cognitoユーザ削除
    cognito = Cognito()
    cognito.delete_user(
        AccessToken=body.get('accessToken'),
    )

    return Response({})


def get_user_name(login_id: str) -> str:
    """ユーザ名取得

    Args:
        login_id (str): ログインID

    Returns:
        str: ユーザ名
    """
    item = table_user.query(
        IndexName='loginId-Index',
        KeyConditionExpression=Key('loginId').eq(login_id),
        ProjectionExpression='userName',
    )

    return '' \
        if is_empty(item.get('Items', [{}])[0].get('userName')) \
        else item['Items'][0]['userName']
