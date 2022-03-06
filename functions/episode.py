from http import HTTPStatus
import json
from common.decorator import handler
from common.resource import Table
from common.response import Response
from common.util import is_empty
from common.exception import ApplicationException
from common.response import PostResponse


table_adage = Table.ADAGE
table_user = Table.USER


@handler
def post(event, context):
    """エピソード登録

    Args:
        event (dict): イベント
        context (dict): コンテキスト

    Raises:
        ApplicationException: 必須項目不足の場合
        ApplicationException: 既存格言が存在しない場合
        ApplicationException: 既存ユーザが存在しない場合

    Returns:
        Response: レスポンス
    """
    body = json.loads(event['body'])

    # 必須項目チェック
    adage_id = body.get('adageId')
    episode = body.get('episode')
    if is_empty(adage_id or episode):
        raise ApplicationException(
            HTTPStatus.FORBIDDEN,
            'adageId and episode is required.',
        )

    # 既存格言チェック
    exists_adage = get_adage(adage_id, 'title')
    if is_empty(exists_adage):
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            f'Adage does not exists. adageId: {adage_id}',
        )

    # 既存ユーザチェック
    user_id = body.get('userId')
    if is_empty(user_id):
        user_id = event['requestContext']['authorizer']['claims']['sub']

    exists_user = get_user(user_id, ['userName'])
    if is_empty(exists_user):
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            f'User does not exists. userId: {user_id}',
        )

    # 格言IDにエピソード登録
    table_adage.put_item(
        Item={
            'adageId': adage_id,
            'key': '#'.join(['episode', user_id]),
            'userId': user_id,
            'userName': exists_user['userName'],
            'title': exists_adage['title'],
            'episode': episode,
        },
    )

    # ユーザIDにエピソード登録
    table_user.put_item(
        Item={
            'userId': user_id,
            'key': '#'.join(['episode', adage_id]),
            'adageId': adage_id,
            'title': exists_adage['title'],
            'episode': episode,
        },
    )

    return PostResponse(body)


@handler
def get_by_id(event, context):
    """格言IDに投稿したユーザのエピソードを取得

    Returns:
        Response: レスポンス
    """
    adage_id = event['pathParameters']['adageId']
    user_id = event['pathParameters']['userId']

    episode = get_episode_by_id(adage_id, user_id)

    return Response(
        {'episode': episode.get('episode', '')},
    )


@handler
def delete(event, context):
    """格言IDに投稿したユーザのエピソード削除

    Raises:
        ApplicationException: 必須項目不足の場合

    Returns:
        Response: レスポンス
    """
    body = json.loads(event['body'])
    adage_id = body.get('adageId')
    user_id = body.get('userId')

    # 必須項目不足の場合
    if is_empty(adage_id):
        ApplicationException(
            HTTPStatus.BAD_REQUEST,
            f'adageId is required',
        )

    if is_empty(user_id):
        ApplicationException(
            HTTPStatus.BAD_REQUEST,
            f'userId is required',
        )

    # 格言IDのエピソード削除
    table_adage.delete_item(
        Key={
            'adageId': adage_id,
            'key': '#'.join(['episode', user_id]),
        },
    )

    # ユーザIDのエピソード削除
    table_user.delete_item(
        Key={
            'userId': user_id,
            'key': '#'.join(['episode', adage_id]),
        },
    )

    return Response({})


def get_adage(adage_id: str, key: str) -> dict:
    """格言取得

    Args:
        adage_id (str): 格言ID
        key (str): ソートキー

    Returns:
        dict: 格言情報
    """
    item = table_adage.get_item(
        Key={
            'adageId': adage_id,
            'key': key,
        },
        ProjectionExpression='title',
    )

    return {} if is_empty(item.get('Item')) else item['Item']


def get_user(user_id: str, projection_list: list) -> dict:
    """ユーザ取得

    Args:
        user_id (str): ユーザID
        projection_list (list): 取得属性リスト

    Returns:
        dict: ユーザ情報
    """
    item = table_user.get_item(
        Key={
            'userId': user_id,
            'key': 'userId',
        },
        ProjectionExpression=','.join(projection_list),
    )

    return {} if is_empty(item.get('Item')) else item['Item']


def get_user_name(user_id: str) -> str:
    """ユーザ名を取得

    Args:
        user_id (str): ユーザID

    Returns:
        str: ユーザ名
    """
    item = table_user.get_item(
        Key={
            'userId': user_id,
            'key': 'userId',
        },
        ProjectionExpression='userName',
    )

    user_info = {} if is_empty(item.get('Item')) else item['Item']

    return {} if is_empty(user_info.get('userName')) else user_info['userName']


def get_episode_by_id(adage_id: str, user_id: str):
    item = table_adage.get_item(
        Key={
            'adageId': adage_id,
            'key': '#'.join(
                ['episode', user_id],
            ),
        },
        ProjectionExpression='episode',
    )

    return {} if is_empty(item.get('Item')) else item['Item']
