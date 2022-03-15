from datetime import datetime, timedelta, timezone
from decimal import Decimal

from common.const import JST, SendReason
from common.resource import Table


table_user = Table.USER


def is_empty(item: any) -> bool:
    """空の判定

    Args:
        item (any): アイテム

    Returns:
        bool: 空か否か
    """
    if item == {}:
        return True

    if item == []:
        return True

    if item == '':
        return True

    if item == None:
        return True

    return False


def add_point_history(
        user_id: str,
        reason: SendReason,
        sender_id: str='admin',
        sender_name: str='管理人'):
    """ポイント履歴登録

    Args:
        user_id (str): ユーザID
        reason (SendReason): 送信理由
        sender_id (str): 送信者ID
        sender_name (str): 送信者名
    """
    jst_timestamp: float = get_jst_timestamp()

    table_user.put_item(
        Item={
            'userId': user_id,
            'key': '#'.join(['point', sender_id, str(jst_timestamp)]),
            'senderId': sender_id,
            'senderName': sender_name,
            'reason': reason.value,
            'point': reason.point,
            'dateTime': Decimal(jst_timestamp),
        },
    )


def get_jst_timestamp() -> float:
    """JST現在時間のtimestampを取得

    Returns:
        float: JST_timestamp
    """
    return datetime.now(JST).timestamp()
