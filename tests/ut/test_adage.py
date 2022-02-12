from set_up import set_up

from datetime import datetime
from http import HTTPStatus
import json

from common.resource import Table

import adage


table_adage = Table.ADAGE


class TestAdage:

    @set_up
    def test_get(self):
        """正常: 格言が取得できること
        """
        item = {
            'adageId': 'test_adage_id_001',
            'title': 'One for all All for one',
            'likePoints': 0,
            'registrationMonth': datetime.now().month,
        }
        table_adage.put_item(Item=item)

        response = adage.get(None, None)

        # 検証
        assert response['statusCode'] == HTTPStatus.OK.value
        res_body = json.loads(response['body'])
        assert res_body['adageId'] == item['adageId']
        assert res_body['title'] == item['title']
        assert res_body['likePoints'] == item['likePoints']
        assert res_body['registrationMonth'] == item['registrationMonth']
