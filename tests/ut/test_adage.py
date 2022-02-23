from random import randint, random
from uuid import uuid4
from set_up import set_up

from datetime import datetime
from http import HTTPStatus
import json

from common.resource import Table

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
