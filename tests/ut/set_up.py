import boto3
from contextlib import ExitStack
from moto import (
    mock_dynamodb2,
    mock_cognitoidp,
)
from unittest import mock
import yaml
import os


def set_up(func):
    """AWSモック
    """
    @mock_dynamodb2
    @mock_cognitoidp
    def wrapper(*args, **kwargs):
        create_tables()
        user_pool_id, client_id = create_cognito()

        # 設定変更
        with ExitStack() as stack:
            stack.enter_context(mock.patch(
                target='common.resource.COGNITO_CLIENT_ID',
                new=client_id,
            ))
            stack.enter_context(mock.patch( 
                target='common.resource.COGNITO_USER_POOL_ID',
                new=user_pool_id,
            ))

            return func(*args, **kwargs)
    return wrapper


def create_tables():
    """DynamoDBモック
    """
    dynamo_db = boto3.resource('dynamodb')
    conf_path = './serverless/dynamodb.yml'
    serverless_prefix = '${self:custom.otherfile.environment.${self:provider.stage}.tableNamePrefix}'
    my_stage_prefix = os.environ['TABLE_NAME_PREFIX']

    # 定義取得
    with open(conf_path) as f:
        definitions = yaml.safe_load(f)

    # テーブル作成
    for definition in definitions['Resources'].values():
        definition['Properties']['TableName'] = \
            definition['Properties']['TableName'].replace(
                serverless_prefix,
                my_stage_prefix,
            )

        test = dynamo_db.create_table(**definition['Properties'])


def create_cognito() -> tuple:
    """Cognitoモック

    Returns:
        tuple: (
            str: ユーザプールID,
            str: ユーザプールクライアントID,
        )
    """
    cognito = boto3.client('cognito-idp')

    # cognito作成
    user_pool = cognito.create_user_pool(PoolName='TestUserPool')
    user_pool_client = cognito.create_user_pool_client(
        UserPoolId=user_pool['UserPool']['Id'],
        ClientName='TestUser',
    )

    return (
        user_pool['UserPool']['Id'],
        user_pool_client['UserPoolClient']['ClientId'],
    )
