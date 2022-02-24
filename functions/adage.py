from datetime import datetime
from decimal import Decimal
import json
from random import randint
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key
from common.response import (
    ErrorResponse,
    PostResponse,
    Response,
)
from common.decorator import handler
from common.resource import Table
from common.util import is_empty
from common.const import LAMBDA_STAGE


table_adage = Table.ADAGE


@handler
def get(event, context):
    """格言を参照する

    Args:
        event (dict): イベント
        context (__main__.LambdaContext): コンテキスト

    Returns:
        Response: レスポンス
    """
    month = datetime.now().month
    adage_list = get_adage(month)

    # 今月の格言リストを取得
    _adage_list = []
    for adage in adage_list: 
        body = {
            'adageId': adage['adageId'],
            'title': adage['title'],
            'registrationMonth': int(adage['registrationMonth']),
            'likePoints': int(adage['likePoints']),
            'episode': [],
        }

        adage_episode = table_adage.get_item(
            Key={
                'adageId': adage['adageId'],
                'key': 'episode',
            },
        )
        if not is_empty(adage_episode.get('Item')):
            body['episode'] = adage_episode['Item'].get('episode')

        _adage_list.append(body)

    # いいねポイントで降順にソート
    _adage_list.sort(
        key=lambda x: x['likePoints'],
        reverse=True,
    )

    return Response(_adage_list)


@handler
def post(event, context):
    """格言登録

    Args:
        event (dict): イベント
        context (dict): コンテキスト

    Returns:
        PostResponse: レスポンス
    """
    sub = event['requestContext']['authorizer']['claims']['sub']
    adage_id = str(uuid4())

    body = json.loads(event['body'])
    episode = body.get('episode', '')

    # 格言登録
    body = {
        'adageId': adage_id,
        'key': 'title',
        'title': body['title'],
        'likePoints': 0,
        'registrationMonth': datetime.now().month,
    }
    table_adage.put_item(Item=body)

    # エピソードも含まれる場合
    if not is_empty(episode):
        invoke_lambda_post_episode(adage_id, sub, episode)

    body['episode'] = episode

    return PostResponse(body)


@handler
def patch(event, context):
    """格言更新

    Args:
        event (dict): イベント
        context (dict): コンテキスト

    Returns:
        Response: レスポンス
    """
    adage_id = event['pathParameters']['adageId']

    patch_adage(adage_id)

    return Response(
        {'adageId': adage_id},
    )


def get_adage(month: int) -> list:
    """今月の格言リストを取得

    Args:
        month (int): 今月の値

    Returns:
        list: 今月の格言リスト
    """
    item = table_adage.query(
        IndexName='registrationMonth-Index',
        KeyConditionExpression=Key('registrationMonth').eq(month),
    )
    return [] if is_empty(item.get('Items')) else item['Items']


def invoke_lambda_post_episode(
        adage_id: str, user_id: str, episode: str) -> dict:
    """エピソード登録関数呼び出し

    Args:
        adage_id (str): 格言ID
        user_id (str): ユーザID
        episode (str): エピソード

    Returns:
        dict: 結果
    """
    client = boto3.client('lambda')

    return client.invoke(
        FunctionName=f'share-adage-service-{LAMBDA_STAGE}-episodePost',
        Payload=json.dumps(
            {
                'body': json.dumps(
                    {
                        'adageId': adage_id,
                        'episode': episode,
                        'userId': user_id,
                    },
                ),
            },
        ),
    )


def patch_adage(adage_id: str):
    """格言のいいねポイントを増やす

    Args:
        adage_id (str): 格言ID
    """
    return table_adage.update_item(
        Key= {
            'adageId': adage_id,
            'key': 'title',
        },
        UpdateExpression="ADD #likePoints :increment",
        ExpressionAttributeNames={
            '#likePoints':'likePoints'
        },
        ExpressionAttributeValues={
            ":increment": Decimal(1)
        },
        ReturnValues="UPDATED_NEW"
    )
