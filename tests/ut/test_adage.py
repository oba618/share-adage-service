from random import randint, random
from uuid import uuid4
from set_up import set_up

from datetime import datetime
from http import HTTPStatus
import json

from common.resource import Table
from common.util import is_empty
from util.const import USER_ID

import adage


table_adage = Table.ADAGE


class TestAdage:

    def test_get(self):
        """正常: 格言が取得できること
        """
        response = adage.get(None, None)

        # 検証
        assert response['statusCode'] == HTTPStatus.OK.value
        adages = json.loads(response['body'])

        for item in adages:
            assert type(item['adageId']) == str
            assert type(item['title']) == str
            assert item['likePoints'] >= 0
            assert item['registrationMonth'] == datetime.now().month
            assert type(item['episode']) == list

            for episode in item['episode']:
                assert type(episode) == str
    
    def test_post(self):
        """正常: 格言を登録できること
        """
        body = {
            'title': 'From unit test',
        }
        event = create_event(USER_ID, body)
        response = adage.post(event, None)

        assert response['statusCode'] == HTTPStatus.CREATED.value

        res = json.loads(response['body'])
        assert res['adageId']
        assert res['key'] == 'title'
        assert res['title'] == body['title']
        assert res['likePoints'] == 0
        assert res['registrationMonth'] == datetime.now().month

        item = get_adage(res['adageId'], 'title')
        assert item['adageId'] == res['adageId']
        assert item['key'] == res['key']
        assert item['title'] == res['title']
        assert item['likePoints'] == res['likePoints']
        assert item['registrationMonth'] == res['registrationMonth']


    def test_post_with_episode(self):
        """正常: 格言とエピソードを登録できること
        """
        pass


def create_event(user_id: str, body: dict) -> dict:
    """event作成

    Args:
        user_id (str): ユーザID
        body (dict): body

    Returns:
        dict: _description_
    """
    return {
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': user_id,
                },
            },
        },
        'body': json.dumps(body),
    }


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
        }
    )

    return {} if is_empty(item.get('Item')) else item['Item']