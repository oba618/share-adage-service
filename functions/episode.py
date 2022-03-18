from decimal import Decimal
from http import HTTPStatus
import json
from uuid import uuid4

from common.decorator import handler
from common.exception import ApplicationException
from common.response import PostResponse
from common.response import Response
from common.resource import Table
from common.util import add_point_history, is_empty
from common.const import SendReason


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
    adage_id = body.get('adageId')
    episode = body.get('episode')
    user_id = body.get('userId')

    # 必須項目チェック
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

    # ユーザチェック
    if is_empty(user_id):
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            'userId is required.',
        )

    # ゲストユーザの場合
    if user_id == 'guest':
        user_id = '#'.join([user_id, str(uuid4())])
        item = {
            'adageId': adage_id,
            'key': '#'.join(['episode', user_id]),
            'userId': user_id,
            'userName': 'ゲスト',
            'title': exists_adage['title'],
            'episode': episode,
            'byGuest': True,
            'likePoints': 0,
        }
        table_adage.put_item(Item=item)

    else:
        exists_user = get_user(user_id, ['userName'])
        if is_empty(exists_user):
            raise ApplicationException(
                HTTPStatus.BAD_REQUEST,
                f'User does not exists. userId: {user_id}',
            )

        # 格言IDにエピソード登録
        item = {
            'adageId': adage_id,
            'key': '#'.join(['episode', user_id]),
            'userId': user_id,
            'userName': exists_user['userName'],
            'title': exists_adage['title'],
            'episode': episode,
            'likePoints': 0,
        }
        table_adage.put_item(Item=item)

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

        # ユーザにポイント付与
        send_reason = SendReason.REGISTRATION_EPISODE
        patch_user(user_id, send_reason.point)
        add_point_history(user_id, send_reason)

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
def patch_from_guest(event, context):
    """エピソード更新、ゲストより

    Returns:
        Response: レスポンス
    """
    adage_id = event['pathParameters']['adageId']
    receiver_user_id = event['pathParameters']['userId']

    # エピソードのポイント追加
    table_adage.update_item(
        Key= {
            'adageId': adage_id,
            'key': '#'.join(['episode', receiver_user_id]),
        },
        UpdateExpression="ADD #likePoints :increment",
        ExpressionAttributeNames={
            '#likePoints':'likePoints'
        },
        ExpressionAttributeValues={
            ":increment": Decimal(1)
        }
    )

    # ユーザのポイント追加
    table_user.update_item(
        Key= {
            'userId': receiver_user_id,
            'key': 'userId',
        },
        UpdateExpression="ADD #likePoints :increment",
        ExpressionAttributeNames={
            '#likePoints':'likePoints'
        },
        ExpressionAttributeValues={
            ":increment": Decimal(1)
        }
    )

    # ユーザのポイント履歴追加
    add_point_history(receiver_user_id, SendReason.THANK_YOU_FROM_GUEST)

    return Response(
        {'episodeId': adage_id},
    )


@handler
def patch_from_user(event, context):
    """エピソード更新、ユーザより

    Returns:
        Response: レスポンス
    """
    adage_id = event['pathParameters']['adageId']
    receiver_user_id = event['pathParameters']['userId']
    sender_user_id = event['pathParameters']['senderUserId']

    # 格言の存在チェック
    adage = get_adage(adage_id, 'title')
    if is_empty(adage):
        raise ApplicationException(
            HTTPStatus.NOT_FOUND,
            f'Adage does not exists. adageId: {adage_id}',
        )

    # 受信者の存在チェック
    receiver = get_user(receiver_user_id, ['userId'])
    if is_empty(receiver):
        raise ApplicationException(
            HTTPStatus.NOT_FOUND,
            f'User does not exists. userId: {receiver_user_id}',
        )

    # 送信者の存在チェック
    sender = get_user(sender_user_id, ['userId', 'userName'])
    if is_empty(sender):
        raise ApplicationException(
            HTTPStatus.NOT_FOUND,
            f'User does not exists. userId: {sender_user_id}',
        )

    # エピソードのポイント追加
    table_adage.update_item(
        Key= {
            'adageId': adage_id,
            'key': '#'.join(['episode', receiver_user_id]),
        },
        UpdateExpression="ADD #likePoints :increment",
        ExpressionAttributeNames={
            '#likePoints':'likePoints'
        },
        ExpressionAttributeValues={
            ":increment": Decimal(1)
        }
    )

    # ユーザのポイント追加
    table_user.update_item(
        Key= {
            'userId': receiver_user_id,
            'key': 'userId',
        },
        UpdateExpression="ADD #likePoints :increment",
        ExpressionAttributeNames={
            '#likePoints':'likePoints'
        },
        ExpressionAttributeValues={
            ":increment": Decimal(1)
        }
    )

    # ユーザのポイント履歴追加
    add_point_history(
        receiver_user_id,
        SendReason.THANK_YOU,
        sender_user_id,
        sender['userName'],
    )

    return Response(
        {'episodeId': adage_id},
    )


@handler
def delete(event, context):
    """格言IDに投稿したユーザのエピソード削除

    Raises:
        ApplicationException: 必須項目不足の場合

    Returns:
        Response: レスポンス
    """
    user_id = get_user_id_from_event(event)
    adage_id = get_adage_id_from_event(event)

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


def get_user_id_from_event(event: dict) -> str:
    """イベント情報からユーザIDを取得

    Args:
        event (dict): イベント

    Returns:
        str: ユーザID
    """
    user_id = event.get('requestContext', {}).get('authorizer', {}) \
        .get('claims', {}).get('sub', {})

    if is_empty(user_id):
        body = json.loads(event['body'])
        user_id = body.get('userId')

        if is_empty(user_id):
            raise ApplicationException(
                HTTPStatus.NOT_FOUND,
                f'userId is required.',
            )

    return user_id


def get_adage_id_from_event(event: dict) -> str:
    """イベント情報から格言IDを取得

    Args:
        event (dict): イベント

    Returns:
        str: 格言ID
    """
    adage_id = event.get('pathParameters', {}).get('adageId', {})

    if is_empty(adage_id):
        body = json.loads(event['body'])
        adage_id = body.get('adageId')

        if is_empty(adage_id):
            raise ApplicationException(
                HTTPStatus.NOT_FOUND,
                f'adageId is required.',
            )

    return adage_id
