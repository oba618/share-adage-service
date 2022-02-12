from http import HTTPStatus


class ApplicationException(Exception):
    """実行時、任意の例外を発生させる場合に使用するクラス
    """

    @property
    def value(self) -> int:
        return self._value

    @property
    def phrase(self) -> str:
        return self._phrase

    @property
    def message(self) -> str:
        return self._message

    @property
    def error_log(self) -> str:
        return self._error_log

    def __init__(self, http_status: HTTPStatus, message: str=''):
        """例外オブジェクト作成

        Args:
            http_status (HTTPStatus): HTTPStatusオブジェクト
            message (str, optional): 例外メッセージ Defaults to ''.
        """
        self._value = http_status.value
        self._phrase = http_status.phrase
        self._message = message

        # ログ出力用
        self._error_log = ': '.join(
            [
                str(self._value),
                http_status.phrase,
                message
            ],
        )
