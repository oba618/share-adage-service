from enum import IntEnum
from datetime import timedelta, timezone
import os


LAMBDA_STAGE = os.environ['LAMBDA_STAGE']

JST = timezone(timedelta(hours=+9), 'JST')


class SendReason(IntEnum):

    def __new__(cls, value, point, message):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.point = point
        obj.message = message
        return obj

    REGISTRATION_USER = (
        100,
        100,
        'ユーザー登録ありがとうございます！',
    )
    SEND_HEART = (
        101,
        1,
        'ハート送信ありがとうございます！',
    )
    REGISTRATION_ADAGE = (
        102,
        200,
        '格言登録ありがとうございます！',
    )
    REGISTRATION_EPISODE = (
        103,
        200,
        'エピソード共有ありがとうございます！',
    )
    THANK_YOU = (
        200,
        1,
        'あなたに感謝します！',
    )
    THANK_YOU_FROM_GUEST = (
        201,
        1,
        'ゲストがあなたに感謝しています！',
    )
