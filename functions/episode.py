from http import HTTPStatus
import json
from common.decorator import handler
from common.resource import Table
from common.response import Response
from common.util import is_empty
from common.exception import ApplicationException


table_adage = Table.ADAGE


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
    adage_id = body['adageId']
    episode = body['episode']

    if is_empty(adage_id or episode):
        raise ApplicationException(
            HTTPStatus.FORBIDDEN,
            'adageId and episode is required.',
        )

    adage_title = table_adage.get_item(
        Key={
            'adageId': adage_id,
            'key': 'title',
        },
    )

    if is_empty(adage_title.get('Item')):
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            f'Dose not exists. adageId: {adage_id}',
        )

    exists_episode = table_adage.get_item(
        Key={
            'adageId': adage_id,
            'key': 'episode',
        }
    )

    episode_list = [episode]

    if not is_empty(exists_episode.get('Item')):
        episode_list.extend(exists_episode['Item']['episode'])

    table_adage.put_item(
        Item={
            'adageId': adage_id,
            'key': 'episode',
            'episode': episode_list,
        },
    )

    return Response(
        {
            'adageId': adage_id,
            'episode': episode_list,
        },
    )
