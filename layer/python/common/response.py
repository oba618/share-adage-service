from http import HTTPStatus
import json

from common.exception import ApplicationException
from common.util import is_empty


class Response:

    def __init__(self, body: dict, http_status: int=HTTPStatus.OK):
        self._http_status = http_status
        self._body = body

    def format(self) -> dict:
        """レスポンス用フォーマット

        Returns:
            dict: レスポンス
        """
        return {
            'statusCode': self._http_status,
            'headers': {
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps(self._body)
        }


class PostResponse(Response):

    def __init__(self, body: dict, http_status: int=HTTPStatus.CREATED):
        super().__init__(body, http_status)


class ErrorResponse(Response):

    def __init__(self, exception_obj=None):
        http_status = HTTPStatus.INTERNAL_SERVER_ERROR \
            if is_empty(exception_obj) \
            else exception_obj
        self._http_status = http_status.value
        self._body = {
            'errorCode': http_status.value,
            'phrase': http_status.phrase,
            'message': '',
        }
        if isinstance(http_status, ApplicationException):
            self._body['message'] = http_status.message
        else:
            self._body['message'] = str(exception_obj)
