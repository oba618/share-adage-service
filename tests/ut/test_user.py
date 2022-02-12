from set_up import set_up

from http import HTTPStatus
import json

from common.resource import Table

import user


table_user = Table.USER


class TestUser:

    @set_up
    def test_post(self):
        """正常: ユーザを登録できること
        """
        body = {
            'loginId': 'test@example.com',
            'password': 'Test123456',
            'userName': 'test_user_1',
        }
        event = {
            'httpMethod': 'POST',
            'body': json.dumps(body),
        }
        response = user.post(event, {})

        assert response['statusCode'] == HTTPStatus.CREATED.value

        res_body = json.loads(response['body'])
        item = table_user.get_item(
            Key={'userId': res_body['userId']}
        )['Item']
        assert res_body['userId'] == item['userId']
        assert res_body['loginId'] == item['loginId']
        assert res_body['userName'] == item['userName']

    @set_up
    def test_post_exists_login_id(self):
        """異常: 既に存在するログインIDの場合、エラーとなること
        """
        login_id = 'test@example.com'
        body = {
            'loginId': login_id,
            'password': 'Test123456',
            'userName': 'test_user_1',
        }
        event = {
            'httpMethod': 'POST',
            'body': json.dumps(body),
        }
        user.post(event, {})

        # 既存ログインID
        body = {
            'loginId': login_id,
            'password': 'Test123456',
            'userName': 'test_user_1',
        }
        event = {
            'httpMethod': 'POST',
            'body': json.dumps(body),
        }
        response = user.post(event, {})

        # 検証
        bad_request = HTTPStatus.BAD_REQUEST
        assert response['statusCode'] == bad_request.value
        res_body = json.loads(response['body'])
        assert res_body['errorCode'] == bad_request.value
        assert res_body['phrase'] == bad_request.phrase
        assert res_body['message']
