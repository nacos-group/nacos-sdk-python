import asyncio
import os
import unittest

from v2.nacos.common.client_config import GRPCConfig, KMSConfig
from v2.nacos.common.client_config_builder import ClientConfigBuilder
from v2.nacos.config.model.config_param import ConfigParam
from v2.nacos.config.nacos_config_service import NacosConfigService

client_config = (ClientConfigBuilder()
                 .access_key(os.getenv('NACOS_ACCESS_KEY'))
                 .secret_key(os.getenv('NACOS_SECRET_KEY'))
                 .server_address(os.getenv('NACOS_SERVER_ADDR', 'localhost:8848'))
                 .log_level('INFO')
                 .grpc_config(GRPCConfig(grpc_timeout=5000))
                 .build())


class TestClientV2(unittest.IsolatedAsyncioTestCase):
    async def test_publish_config(self):
        client = await NacosConfigService.create_config_service(client_config)
        assert await client.server_health()

        data_id = "com.alibaba.nacos.test.config"
        group = "DEFAULT_GROUP"

        content = await client.get_config(ConfigParam(
            data_id=data_id,
            group=group,
        ))

        assert content == ""

        res = await client.publish_config(ConfigParam(
            data_id=data_id,
            group=group,
            content="Hello world")
        )
        assert res
        print("success to publish")

        await asyncio.sleep(0.1)
        content = await client.get_config(ConfigParam(
            data_id=data_id,
            group=group,
        ))

        assert content == "Hello world"
        print("success to get config")

        res = await client.remove_config(ConfigParam(
            data_id=data_id,
            group=group
        ))

        assert res
        print("success to remove")

        await asyncio.sleep(0.1)
        content = await client.get_config(ConfigParam(
            data_id=data_id,
            group=group,
        ))

        assert content == ""

    async def test_config_listener(self):
        client = await NacosConfigService.create_config_service(client_config)
        assert await client.server_health()

        dataID = "com.alibaba.nacos.test.config"
        groupName = "DEFAULT_GROUP"

        async def config_listener1(tenant, data_id, group, content):
            print("listen1, tenant:{} data_id:{} group:{} content:{}".format(tenant, data_id, group, content))

        async def config_listener2(tenant, data_id, group, content):
            print("listen2, tenant:{} data_id:{} group:{} content:{}".format(tenant, data_id, group, content))

        await client.add_listener(dataID, groupName, config_listener1)
        await client.add_listener(dataID, groupName, config_listener2)

        await asyncio.sleep(3)

        res = await client.publish_config(ConfigParam(
            data_id=dataID,
            group=groupName,
            content="Hello world")
        )
        assert res
        print("success to publish")

        await asyncio.sleep(3)

        res = await client.publish_config(ConfigParam(
            data_id=dataID,
            group=groupName,
            content="Hello world2")
        )
        assert res

        await asyncio.sleep(3)

        await client.remove_listener(dataID, groupName, config_listener1)

        await asyncio.sleep(3)

        res = await client.publish_config(ConfigParam(
            data_id=dataID,
            group=groupName,
            content="Hello world3")
        )
        assert res

        await asyncio.sleep(3)

        res = await client.remove_config(ConfigParam(
            data_id=dataID,
            group=groupName
        ))

        assert res
        print("success to remove")
        await asyncio.sleep(3)

    async def test_cipher_config(self):
        kms_config = KMSConfig(
            enabled=True,
            endpoint=os.getenv('KMS_ENDPOINT'),
            access_key=os.getenv('NACOS_ACCESS_KEY'),
            secret_key=os.getenv('NACOS_SECRET_KEY'),
        )

        client_config.set_kms_config(kms_config)

        client = await NacosConfigService.create_config_service(client_config)

        dataID = "cipher-kms-aes-128-crypt"
        groupName = "DEFAULT_GROUP"

        res = await client.publish_config(
            param=ConfigParam(
                data_id=dataID,
                group=groupName,
                content="加密内容-128",
                kms_key_id=os.getenv("KMS_KEY_ID")))

        assert res
        print("success to publish")
        await asyncio.sleep(0.1)

        content = await client.get_config(ConfigParam(
            data_id=dataID,
            group=groupName,
            kms_key_id=os.getenv("KMS_KEY_ID")
        ))
        print("success to get config:" + content)
        assert content == '加密内容-128'

        dataID = "cipher-kms-aes-256-crypt"
        groupName = "DEFAULT_GROUP"

        res = await client.publish_config(
            param=ConfigParam(
                data_id=dataID,
                group=groupName,
                content="加密内容-256",
                kms_key_id=os.getenv("KMS_KEY_ID")))

        assert res
        print("success to publish")
        await asyncio.sleep(0.1)

        content = await client.get_config(ConfigParam(
            data_id=dataID,
            group=groupName,
            kms_key_id=os.getenv("KMS_KEY_ID")
        ))
        print("success to get config:" + content)
        assert content == '加密内容-256'

    async def test_cipher_config_listener(self):
        kms_config = KMSConfig(
            enabled=True,
            endpoint=os.getenv("KMS_ENDPOINT"),
            access_key=os.getenv('NACOS_ACCESS_KEY'),
            secret_key=os.getenv('NACOS_SECRET_KEY'),
        )
        client_cfg = (ClientConfigBuilder()
                      .access_key(os.getenv('NACOS_ACCESS_KEY'))
                      .secret_key(os.getenv('NACOS_SECRET_KEY'))
                      .server_address(os.getenv('NACOS_SERVER_ADDR', 'localhost:8848'))
                      .log_level('INFO')
                      .kms_config(kms_config)
                      .grpc_config(GRPCConfig(grpc_timeout=5000))
                      .build())

        client = await NacosConfigService.create_config_service(client_cfg)

        dataID = "cipher-kms-aes-128-crypt"
        groupName = "DEFAULT_GROUP"

        async def config_listener(tenant, data_id, group, content):
            print("listen1, tenant:{} data_id:{} group:{} content:{}".format(tenant, data_id, group, content))

        await client.add_listener(dataID, groupName, config_listener)

        await asyncio.sleep(3)
        res = await client.publish_config(
            param=ConfigParam(
                data_id=dataID,
                group=groupName,
                content="加密内容-1",
                kms_key_id=os.getenv("KMS_KEY_ID")))

        assert res
        print("success to publish")

        await asyncio.sleep(3)

        res = await client.publish_config(
            param=ConfigParam(
                data_id=dataID,
                group=groupName,
                content="加密内容-2",
                kms_key_id=os.getenv("KMS_KEY_ID")))
        assert res

        await asyncio.sleep(3)

    async def test_gray_config(self):
        client_cfg = (ClientConfigBuilder()
                      .access_key(os.getenv('NACOS_ACCESS_KEY'))
                      .secret_key(os.getenv('NACOS_SECRET_KEY'))
                      .server_address(os.getenv('NACOS_SERVER_ADDR', 'localhost:8848'))
                      .log_level('INFO')
                      .app_conn_labels({"k1": "v1", "k2": "v2", "nacos_config_gray_label": "gray"})
                      .grpc_config(GRPCConfig(grpc_timeout=5000))
                      .build())
        client = await NacosConfigService.create_config_service(client_cfg)

        dataID = "com.alibaba.nacos.test.config.gray"
        groupName = "DEFAULT_GROUP"

        async def config_listener(tenant, data_id, group, content):
            print("listen1, tenant:{} data_id:{} group:{} content:{}".format(tenant, data_id, group, content))

        await client.add_listener(dataID, groupName, config_listener)

        await asyncio.sleep(1000)
