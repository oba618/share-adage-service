from decimal import Decimal
import json
from http import HTTPStatus

from common.decorator import handler
from common.exception import ApplicationException
from common.resource import Table
from common.response import Response
from common.util import add_point_history, is_empty
from common.const import SendReason


table_user = Table.USER


@handler
def post_from_admin_to_me(event, context):
    """管理人からユーザへハートを送信

    Raises:
        ApplicationException: 受信者が存在しない場合

    Returns:
        Response: レスポンス
    """
    sub = event['requestContext']['authorizer']['claims']['sub']

    # ユーザの存在確認
    user = get_user(sub, ['userId'])
    if is_empty(user):
        raise ApplicationException(
            HTTPStatus.NOT_FOUND,
            f'User does not exists. userId: {sub}',
        )

    # ハートを付与
    send_reason = SendReason.THANK_YOU
    increment_user_heart(sub, send_reason.point)
    add_point_history(sub, send_reason)

    return Response({})


@handler
def post_from_me_to_user(event, context):
    """ユーザから得てのユーザへハートを送信

    Raises:
        ApplicationException: 送信者が存在しない場合
        ApplicationException: 受信者が存在しない場合

    Returns:
        Response: レスポンス
    """
    sender_user_id = event['requestContext']['authorizer']['claims']['sub']
    receiver_user_id = event['pathParameters']['userId']

    # 送信者取得
    sender_user = get_user(sender_user_id, ['userId', 'userName'])
    if is_empty(sender_user):
        raise ApplicationException(
            HTTPStatus.NOT_FOUND,
            f'Does not exists. sender userId: {sender_user_id}',
        )

    # 受信者
    receiver_user = get_user(receiver_user_id, ['userId'])
    if is_empty(receiver_user):
        raise ApplicationException(
            HTTPStatus.NOT_FOUND,
            f'Does not exists. receiver userId: {receiver_user_id}',
        )

    # ハート追加
    increment_user_heart(receiver_user_id, 1)

    # ハート履歴追加
    add_point_history(
        receiver_user['userId'],
        SendReason.THANK_YOU,
        sender_user['userId'],
        sender_user['userName'],
    )

    return Response({})


@handler
def delete_history(event, context):
    """ハート履歴削除

    Raises:
        ApplicationException: Keyが空の場合
        ApplicationException: ハート履歴が空の場合

    Returns:
        Response: レスポンス
    """
    user_id = event['requestContext']['authorizer']['claims']['sub']
    body = json.loads(event['body'])
    key = body.get('key')

    # keyが空の場合
    if is_empty(key):
        raise ApplicationException(
            HTTPStatus.BAD_REQUEST,
            'key is required.',
        )

    # ハート履歴取得
    heart = get_heart(user_id, key)
    if is_empty(heart):
        raise ApplicationException(
            HTTPStatus.NOT_FOUND,
            f'Does not exists heartHistory. key: {key}',
        )

    # ハート履歴削除
    table_user.delete_item(
        Key={
            'userId': user_id,
            'key': key,
        },
    )

    return Response({})


def get_heart(user_id: str, key: str) -> dict:
    """ハート履歴取得

    Args:
        user_id (str): ユーザID
        key (str): ソートキー

    Returns:
        dict: ハート履歴
    """
    item = table_user.get_item(
        Key={
            'userId': user_id,
            'key': key,
        },
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


def increment_user_heart(user_id: str, point: int):
    """ユーザのハート増加

    Args:
        user_id (str): ユーザID
        point (int): 増加分ポイント
    """
    table_user.update_item(
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
        }
    )
