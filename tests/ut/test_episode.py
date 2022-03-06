from http import HTTPStatus
import json

from common.resource import Table
from util.const import USER_ID
import episode


adage_table = Table.ADAGE


class TestEpisode:
    def test_post(self):
        """正常: エピソードが登録されること
        """
        adage_id = 'exists_adage_id'
        adage_table.put_item(
            Item={
                'adageId': adage_id,
                'key': 'title',
                'title': 'これはテスト用の格言です',
            }
        )
        post_episode = '既存の格言にエピソードを追加するテスト'
        body = {
            'adageId': adage_id,
            'episode': post_episode,
        }
        event = create_event(body, USER_ID)

        response = episode.post(event, None)
        assert response['statusCode'] == HTTPStatus.CREATED.value

        res = json.loads(response['body'])
        assert res['adageId'] == adage_id
        assert res['key'] == 'episode'
        assert res['episode']
        for item in res['episode']:
            assert type(item['userId']) == str
            assert type(item['userName']) == str
            assert type(item['episode']) == str


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
