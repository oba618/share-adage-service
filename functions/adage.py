from datetime import datetime
from decimal import Decimal
from http import HTTPStatus
import json
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Attr, Key

from common.const import LAMBDA_STAGE
from common.decorator import handler
from common.exception import ApplicationException
from common.resource import Table
from common.response import (
    PostResponse,
    Response,
)
from common.util import is_empty


table_adage = Table.ADAGE
table_user = Table.USER


@handler
def get(event, context):
    """格言を参照する

    Returns:
        Response: レスポンス
    """
    # 今月の格言取得
    adage_list = get_adage_by_registration_month(datetime.now().month)

    # 今月の格言リストを作成
    _adage_list = []

    for adage in adage_list: 
        body = {
            'adageId': adage['adageId'],
            'title': adage['title'],
            'registrationMonth': int(adage['registrationMonth']),
            'likePoints': int(adage['likePoints']),
            'episode': [],
        }

        # 格言IDのエピソードを取得
        adage_episode = table_adage.query(
            KeyConditionExpression=Key('adageId').eq(adage['adageId']) &
                Key('key').begins_with('episode'),
            FilterExpression=Attr('byGuest').not_exists(),
        )
        if not is_empty(adage_episode.get('Items')):

            for episode in adage_episode['Items']:
                episode['likePoints'] = int(episode.get('likePoints', 0))

            body['episode'] = adage_episode['Items']

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

    Raise:
        ApplicationException: 必須項目が空の場合

    Returns:
        PostResponse: レスポンス
    """
    sub = event['requestContext']['authorizer']['claims']['sub']
    
    return post_core_process(event, sub)


@handler
def post_by_guest(event, context):
    """格言登録(ゲストユーザ)

    Raise:
        ApplicationException: 必須項目が空の場合

    Returns:
        PostResponse: レスポンス
    """
    return post_core_process(event, 'guest')


def post_core_process(event: dict, sub: str) -> PostResponse:
    """格言登録

    Args:
        event (dict): イベント
        sub (str, optional): ユーザID

    Raises:
        ApplicationException: 必須項目が空の場合

    Returns:
        PostResponse: レスポンス
    """
    adage_id = str(uuid4())

    body = json.loads(event['body'])
    adage_title = body.get('title')
    episode = body.get('episode', '')

    # 必須項目チェック
    if is_empty(adage_title):
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            'Title is required.',
        )

    # 格言登録
    body = {
        'adageId': adage_id,
        'key': 'title',
        'title': adage_title,
        'likePoints': 0,
        'registrationMonth': datetime.now().month,
    }

    # ゲストユーザの場合
    if sub == 'guest':
        body['byGuest'] = True

    # ユーザにポイント付与
    else:
        patch_user(sub, 100)

    # 格言登録
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


def get_adage_by_registration_month(month: int) -> list:
    """今月の格言リストを取得

    Args:
        month (int): 今月の値

    Returns:
        list: 今月の格言リスト
    """
    item = table_adage.query(
        IndexName='registrationMonth-Index',
        KeyConditionExpression=Key('registrationMonth').eq(month),
        FilterExpression=Attr('byGuest').not_exists(),
    )
    return [] if is_empty(item.get('Items')) else item['Items']


def invoke_lambda_post_episode(
        adage_id: str, sub: str, episode: str) -> dict:
    """エピソード登録関数呼び出し

    Args:
        adage_id (str): 格言ID
        sub (str): ユーザID
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
                        'userId': sub,
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


def patch_user(user_id: str, point: int):
    """ユーザのいいねポイントを増やす

    Args:
        user_id (str): ユーザID
        point (int): ポイント
    """
    return table_user.update_item(
        Key= {
            'userId': user_id,
            'key': 'userId',
        },
        UpdateExpression="ADD #likePoints :increment",
        ExpressionAttributeNames={
            '#likePoints':'likePoints',
        },
        ExpressionAttributeValues={
            ":increment": Decimal(point),
        },
    )
