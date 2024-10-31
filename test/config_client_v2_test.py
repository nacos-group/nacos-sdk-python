import asyncio
import unittest

from v2.nacos.common.client_config import GRPCConfig
from v2.nacos.common.client_config_builder import ClientConfigBuilder
from v2.nacos.config.model.config_param import ConfigParam, Listener
from v2.nacos.config.nacos_config_service import NacosConfigService

client_config = (ClientConfigBuilder()
                 .username('xxx')
                 .password('xxx')
                 .server_address('xxx')
                 .grpc_config(GRPCConfig())
                 .cache_dir('xxx')
                 .log_dir('xxx')
                 .build())

def generate_random_string(length=4):
    import random
    import string
    letters = string.ascii_letters + string.digits
    return ''.join(random.choices(letters, k=length))


class TestListener(Listener):
    def listen(self, namespace: str, group: str, data_id: str, content: str):
        print(namespace, group, data_id, content, "listener")


class TestClientV2(unittest.IsolatedAsyncioTestCase):
    async def test_publish_config(self):
        client = await NacosConfigService.create_config_service(client_config)
        try:
            await asyncio.sleep(5)
            response = await client.publish_config(
                param=ConfigParam(data_id="testttt", group="group", content="content", src_user='nacos'))
            self.assertEqual(response, True)
            if response:
                print("success to publish")
            await asyncio.sleep(1000)
        except Exception as e:
            print(str(e))

    async def test_get_config(self):
        client = await NacosConfigService.create_config_service(client_config)
        try:
            await asyncio.sleep(5)
            response = await client.get_config(
                param=ConfigParam(data_id="testttt", group="group"))
            print(response)
            # self.assertEqual(response, True)
            if response:
                print("success to get config")
            await asyncio.sleep(1000)
        except Exception as e:
            print(str(e))

    async def test_remove_config(self):
        client = await NacosConfigService.create_config_service(client_config)
        try:
            await asyncio.sleep(5)
            response = await client.remove_config(
                param=ConfigParam(data_id="testttt", group="group"))
            if response:
                print("success to remove config")
            await asyncio.sleep(1000)
        except Exception as e:
            print(str(e))

    async def test_add_listener(self):
        client = await NacosConfigService.create_config_service(client_config)
        try:
            a = generate_random_string()
            b = generate_random_string()

            await asyncio.sleep(5)
            response = await client.publish_config(
                param=ConfigParam(data_id="testttt", group="group", content="1{}".format(a), src_user='nacos'))
            if response:
                print("publish1")

            await asyncio.sleep(5)

            listener = TestListener()
            response = await client.add_listener(
                param=ConfigParam(data_id="testttt", group="group"), listener=listener)

            print("add listen")
            await asyncio.sleep(5)

            response = await client.publish_config(
                param=ConfigParam(data_id="testttt", group="group", content="3{}".format(b), src_user='nacos'))
            if response:
                print("publish2")
            await asyncio.sleep(1000)
        except Exception as e:
            print(str(e))

    async def test_cipher_config(self):
        client = await NacosConfigService.create_config_service(client_config)
        try:

            # await asyncio.sleep(5)
            response = await client.publish_config(
                param=ConfigParam(data_id="cipher-aes-testttt", group="group", content="你好nacos", src_user='nacos'))
            if response:
                print("publish1")

            await asyncio.sleep(5)

            response = await client.get_config(
                param=ConfigParam(data_id="cipher-aes-testttt", group="group"))
            print(response)

            await asyncio.sleep(1000)
        except Exception as e:
            print(str(e))

    async def test_cipher_listener(self):
        client = await NacosConfigService.create_config_service(client_config)
        try:
            a = generate_random_string()
            b = generate_random_string()

            await asyncio.sleep(5)
            response = await client.publish_config(
                param=ConfigParam(data_id="cipher-aes-testttt", group="group", content="1{}".format(a)))
            print("publish1")

            await asyncio.sleep(5)

            listener = TestListener()
            response = await client.add_listener(
                param=ConfigParam(data_id="cipher-aes-testttt", group="group"), listener=listener)

            print("add listen")
            await asyncio.sleep(5)

            response = await client.publish_config(
                param=ConfigParam(data_id="cipher-aes-testttt", group="group", content="3{}".format(b)))
            print("publish2")

            # self.assertEqual(response, True)
            if response:
                print("success to test listen")

            await asyncio.sleep(1000)
        except Exception as e:
            print(str(e))

    async def test_remove_listener(self):
        client = await NacosConfigService.create_config_service(client_config)
        try:
            await client.remove_listener(
                param=ConfigParam(data_id="testttt", group="group"))
            await asyncio.sleep(1000)
        except Exception as e:
            print(str(e))
