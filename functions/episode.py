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

    exists_user = get_user(user_id)
    if is_empty(exists_user):
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            f'User does not exists. userId: {user_id}',
        )

    # 格言IDにエピソード登録
    body = {
        'adageId': adage_id,
        'key': 'episode#' + user_id,
        'userId': user_id,
        'userName': exists_user['userName'],
        'episode': episode,
    }
    table_adage.put_item(Item=body)

    # ユーザIDにエピソード登録
    post_episode_list = [] \
        if is_empty(exists_user.get('postEpisodeList')) \
        else exists_user['postEpisodeList']

    post_episode_list.append(
        {
            'adageId': adage_id,
            'title': exists_adage['title'],
        },
    )
    table_user.update_item(
        Key={
            'userId': user_id,
            'key': 'userId',
        },
        UpdateExpression='set postEpisodeList=:e',
        ExpressionAttributeValues={
            ':e': post_episode_list,
        },
    )

    return PostResponse(body)


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


def get_user(user_id: str) -> dict:
    """ユーザ取得

    Args:
        user_id (str): ユーザID

    Returns:
        dict: ユーザ情報
    """
    item = table_user.get_item(
        Key={
            'userId': user_id,
            'key': 'userId',
        },
        ProjectionExpression='userName,postEpisodeList',
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
