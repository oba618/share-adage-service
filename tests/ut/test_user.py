from http import HTTPStatus
import json

from common.resource import Table
from util.const import LOGIN_ID, PASSWORD
import user


table_user = Table.USER


class TestUser:

    def test_login(self):
        """正常: ログインできること
        """
        event = create_event(
            {
                'loginId': LOGIN_ID,
                'password': PASSWORD,
            },
        )
        response = user.login(event, None)
        assert response['statusCode'] == HTTPStatus.CREATED.value

        res = json.loads(response['body'])
        assert res['idToken']
        assert res['accessToken']
        assert res['refreshToken']
        assert res['userName'] == 'No name'

    def test_login_wrong_password(self):
        """異常: パスワードが違う場合
        """
        event = create_event(
            {
                'loginId': LOGIN_ID,
                'password': 'worng_password',
            },
        )
        response = user.login(event, None)
        assert response['statusCode'] == HTTPStatus.BAD_REQUEST.value

        res = json.loads(response['body'])
        assert res['errorCode'] == HTTPStatus.BAD_REQUEST.value
        assert res['phrase'] == HTTPStatus.BAD_REQUEST.phrase
        assert res['message'] == 'Incorrect username or password.'

    def test_login_wrong_login_id(self):
        """異常: メールアドレスが違う場合
        """
        event = create_event(
            {
                'loginId': 'wrong_mail_address@example.com',
                'password': PASSWORD,
            },
        )
        response = user.login(event, None)
        assert response['statusCode'] == HTTPStatus.BAD_REQUEST.value

        res = json.loads(response['body'])
        assert res['errorCode'] == HTTPStatus.BAD_REQUEST.value
        assert res['phrase'] == HTTPStatus.BAD_REQUEST.phrase
        assert res['message'] == 'Incorrect username or password.'




def create_event(body: dict, user_id: str=None) -> dict:
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
