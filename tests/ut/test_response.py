from http import HTTPStatus
import json

from common.response import Response


class TestResponse:

    def test_response(self):
        """正常

        レスポンスが返却されること
        """
        body = {
            'test': 'test is OK',
        }
        response = Response(body).format()

        assert response['statusCode'] == HTTPStatus.OK.value
        assert response['body'] == json.dumps(body)
        assert response['headers']['Access-Control-Allow-Origin'] \
            == '*'
        assert response['headers']['Access-Control-Allow-Headers'] \
            == 'Content-Type'
