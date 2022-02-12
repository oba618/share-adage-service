import logging

from common.response import ErrorResponse
from common.exception import ApplicationException


logger = logging.getLogger('share-adage-service')
logger.setLevel('INFO')


def handler(func):
    """Lambda関数ハンドラ
    """
    def wrapper(*args, **kwargs):

        try:
            response = func(*args, **kwargs)

        # 任意の例外の場合
        except ApplicationException as app_e:
            logger.critical(app_e.error_log)
            response = ErrorResponse(app_e)

        except Exception as e:
            save_exception_log(e)
            response = ErrorResponse(e)

        return response.format()
    return wrapper


def save_exception_log(error: Exception):
    """例外のログを保存

    Args:
        error (Exception): 例外
    """
    logger.critical(
        str(type(error)) + ':' + str(error),
    )
