import json
from common.decorator import handler
from common.resource import Table
from common.response import Response


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

    table_adage.put_item(
        Item={
            'adageId': adage_id,
            'key': 'episode',
            'episode': episode,
        },
    )

    return Response(
        {
            'adageId': adage_id,
            'episode': episode,
        },
    )
