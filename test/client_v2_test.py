import asyncio
import os
import unittest
from typing import List

from v2.nacos import ConfigParam
from v2.nacos.common.client_config import GRPCConfig
from v2.nacos.common.client_config_builder import ClientConfigBuilder
from v2.nacos.naming.model.instance import Instance
from v2.nacos.naming.model.naming_param import RegisterInstanceParam, DeregisterInstanceParam, \
    BatchRegisterInstanceParam, GetServiceParam, ListServiceParam, SubscribeServiceParam, ListInstanceParam
from v2.nacos.naming.nacos_naming_service import NacosNamingService
from v2.nacos.config.nacos_config_service import NacosConfigService
from v2.nacos.common.auth import CredentialsProvider, Credentials

client_config = (ClientConfigBuilder()
                 .access_key(os.getenv('NACOS_ACCESS_KEY'))
                 .secret_key(os.getenv('NACOS_SECRET_KEY'))
                 .server_address(os.getenv('NACOS_SERVER_ADDR', 'localhost:8848'))
                 .log_level('INFO')
                 .grpc_config(GRPCConfig(grpc_timeout=5000))
                 .build())

class CustomCredentialsProvider(CredentialsProvider):
    def __init__(self, ak="", sk="", token=""):
        self.credential = Credentials(ak, sk, token)

    def get_credentials(self):
        return self.credential

class TestClientV2(unittest.IsolatedAsyncioTestCase):

    async def test_init_naming_and_config_service(self):
        config_client = await NacosConfigService.create_config_service(client_config)
        assert await config_client.server_health()
        naming_client = await NacosNamingService.create_naming_service(client_config)
        assert await naming_client.server_health()
        response = await naming_client.register_instance(
            request=RegisterInstanceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', ip='1.1.1.1',
                                          port=7001, weight=1.0, cluster_name='c1', metadata={'a': 'b'},
                                          enabled=True,
                                          healthy=True, ephemeral=True))
        self.assertEqual(response, True)
        print('register instance')

        data_id = "com.alibaba.nacos.test.config"
        group = "DEFAULT_GROUP"

        content = await config_client.get_config(ConfigParam(
            data_id=data_id,
            group=group,
        ))

        assert content == ""
        await asyncio.sleep(10000)



    async def test_register_with_endpoint_and_fixed_ak(self):
        config = (ClientConfigBuilder()
                         .access_key(os.getenv('NACOS_ACCESS_KEY'))
                         .secret_key(os.getenv('NACOS_SECRET_KEY'))
                         .endpoint(os.getenv('NACOS_SERVER_ENDPOINT', 'localhost:8848'))
                         .log_level('INFO')
                         .grpc_config(GRPCConfig(grpc_timeout=5000))
                         .build())

        client = await NacosNamingService.create_naming_service(config)
        assert await client.server_health()

    async def test_register_with_endpoint_and_provider(self):
        config = (ClientConfigBuilder()
                         .credentials_provider(CustomCredentialsProvider(os.getenv('NACOS_ACCESS_KEY'), os.getenv('NACOS_SECRET_KEY')))
                         .endpoint(os.getenv('NACOS_SERVER_ENDPOINT', 'localhost:8848'))
                         .log_level('INFO')
                         .grpc_config(GRPCConfig(grpc_timeout=5000))
                         .build())

        client = await NacosNamingService.create_naming_service(config)
        assert await client.server_health()

    async def test_register(self):
        client = await NacosNamingService.create_naming_service(client_config)
        assert await client.server_health()

        async def cb(instance_list: List[Instance]):
            print('received subscribe callback', str(instance_list))

        await client.subscribe(
            SubscribeServiceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', subscribe_callback=cb))

        print('subscribe service')

        response = await client.register_instance(
            request=RegisterInstanceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', ip='1.1.1.1',
                                          port=7001, weight=1.0, cluster_name='c1', metadata={'a': 'b'},
                                          enabled=True,
                                          healthy=True, ephemeral=True))
        self.assertEqual(response, True)

        print('register instance')

        await asyncio.sleep(1)

        response = await client.update_instance(
            request=RegisterInstanceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', ip='1.1.1.1',
                                          port=7001, weight=2.0, cluster_name='c1', metadata={'a': 'b'},
                                          enabled=True,
                                          healthy=True, ephemeral=True))
        self.assertEqual(response, True)

        print('update instance')

        await asyncio.sleep(1)

        response = await client.deregister_instance(
            request=DeregisterInstanceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', ip='1.1.1.1',
                                            port=7001, cluster_name='c1', ephemeral=True)
        )
        self.assertEqual(response, True)

        print('deregister instance')

        await asyncio.sleep(1)

        param1 = RegisterInstanceParam(service_name='nacos.test.1',
                                       group_name='DEFAULT_GROUP',
                                       ip='1.1.1.1',
                                       port=7001,
                                       weight=1.0,
                                       cluster_name='c1',
                                       metadata={'a': 'b'},
                                       enabled=True,
                                       healthy=True,
                                       ephemeral=True
                                       )
        param2 = RegisterInstanceParam(service_name='nacos.test.1',
                                       group_name='DEFAULT_GROUP',
                                       ip='1.1.1.1',
                                       port=7002,
                                       weight=1.0,
                                       cluster_name='c1',
                                       metadata={'a': 'b'},
                                       enabled=True,
                                       healthy=True,
                                       ephemeral=True
                                       )
        param3 = RegisterInstanceParam(service_name='nacos.test.1',
                                       group_name='DEFAULT_GROUP',
                                       ip='1.1.1.1',
                                       port=7003,
                                       weight=1.0,
                                       cluster_name='c1',
                                       metadata={'a': 'b'},
                                       enabled=True,
                                       healthy=False,
                                       ephemeral=True
                                       )
        response = await client.batch_register_instances(
            request=BatchRegisterInstanceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP',
                                               instances=[param1, param2, param3]))
        self.assertEqual(response, True)

        print('batch register instance')
        await asyncio.sleep(1)

        service = await client.get_service(
            GetServiceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', cluster_name='c1'))
        print('get service', str(service))
        assert service.name == 'nacos.test.1'

        service_list = await client.list_services(ListServiceParam())
        assert service_list.count == 1

        instance_list = await client.list_instances(ListInstanceParam(service_name='nacos.test.1', healthy_only=True))
        assert len(instance_list) == 2

        instance_list = await client.list_instances(ListInstanceParam(service_name='nacos.test.1', healthy_only=False))
        assert len(instance_list) == 1

        instance_list = await client.list_instances(ListInstanceParam(service_name='nacos.test.1', healthy_only=None))
        assert len(instance_list) == 3

        await client.unsubscribe(
            SubscribeServiceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', subscribe_callback=cb))

        await client.shutdown()


if __name__ == '__main__':
    unittest.main()
