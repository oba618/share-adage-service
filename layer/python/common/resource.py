from enum import Enum
import boto3
import os


COGNITO_CLIENT_ID = os.environ['COGNITO_CLIENT_ID']
COGNITO_USER_POOL_ID = os.environ['COGNITO_USER_POOL_ID']

TABLE_NAME_PREFIX = os.environ['TABLE_NAME_PREFIX']

class Cognito:

    def __init__(self):
        self._cognito = boto3.client('cognito-idp')

    def sing_up(self, **kwargs):
        """ユーザ登録: 認証コード送信

        Returns:
            dict: レスポンス
        """
        return self._cognito.sign_up(ClientId=COGNITO_CLIENT_ID, **kwargs)

    def confirm_sign_up(self, **kwargs):
        """ユーザ認証

        Returns:
            dict: レスポンス
        """
        return self._cognito.confirm_sign_up(
            ClientId=COGNITO_CLIENT_ID, **kwargs,
        )

    def resend_confirmation_code(self, **kwargs):
        """認証コード再送信

        Returns:
            dict: レスポンス
        """
        return self._cognito.resend_confirmation_code(
            ClientId=COGNITO_CLIENT_ID, **kwargs,
        )

    def initiate_auth(self, **kwargs):
        """ユーザログイン

        Returns:
            dict: レスポンス
        """
        return self._cognito.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            ClientId=COGNITO_CLIENT_ID,
            **kwargs,
        )

    def delete_user(self, **kwargs):
        """ユーザ削除

        Returns:
            dict: レスポンス
        """
        return self._cognito.delete_user(**kwargs)

    def admin_reset_user_password(self, **kwargs):
        return self._cognito.admin_reset_user_password(
            UserPoolId=COGNITO_USER_POOL_ID, **kwargs,
        )

    def confirm_forgot_password(self, **kwargs):
        return self._cognito.confirm_forgot_password(
            ClientId=COGNITO_CLIENT_ID, **kwargs,
        )


class Table(Enum):

    def __new__(cls, table_name):
        obj = boto3.resource('dynamodb').Table(table_name)
        return obj

    ADAGE = TABLE_NAME_PREFIX + 'adagesTable'
    USER = TABLE_NAME_PREFIX + 'usersTable'
