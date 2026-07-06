import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from v2.nacos.common.nacos_exception import NacosException, SERVER_ERROR
from v2.nacos.naming.model.instance import Instance
from v2.nacos.naming.model.naming_param import GetServiceParam, ListInstanceParam
from v2.nacos.naming.model.service import Service
from v2.nacos.naming.nacos_naming_service import NacosNamingService
from v2.nacos.naming.remote.naming_grpc_client_proxy import NamingGRPCClientProxy


def make_service(version: str, hosts=None) -> Service:
    if hosts is None:
        hosts = [
            Instance(
                ip="127.0.0.1",
                port=8848,
                healthy=True,
                enabled=True,
                weight=1.0,
                clusterName="DEFAULT",
                metadata={"version": version},
            )
        ]
    return Service(name="demo-service", groupName="DEFAULT_GROUP", hosts=hosts)


def make_naming_service(service_info_holder, grpc_client_proxy) -> NacosNamingService:
    service = NacosNamingService.__new__(NacosNamingService)
    service.service_info_holder = service_info_holder
    service.grpc_client_proxy = grpc_client_proxy
    return service


class TestNamingServiceCacheSemantics(unittest.IsolatedAsyncioTestCase):

    async def test_list_instances_subscribe_refreshes_cached_service(self):
        stale_service = make_service("stale")
        fresh_service = make_service("fresh")
        service_info_holder = SimpleNamespace(
            get_service_info=AsyncMock(return_value=stale_service)
        )
        grpc_client_proxy = SimpleNamespace(
            subscribe=AsyncMock(return_value=fresh_service),
            query_instance_of_service=AsyncMock(),
        )
        naming_service = make_naming_service(service_info_holder, grpc_client_proxy)

        instances = await naming_service.list_instances(
            ListInstanceParam(
                service_name="demo-service",
                group_name="DEFAULT_GROUP",
                healthy_only=None,
                subscribe=True,
            )
        )

        self.assertEqual([{"version": "fresh"}], [instance.metadata for instance in instances])
        grpc_client_proxy.subscribe.assert_awaited_once_with("demo-service", "DEFAULT_GROUP", "")
        grpc_client_proxy.query_instance_of_service.assert_not_awaited()
        service_info_holder.get_service_info.assert_not_awaited()

    async def test_list_instances_without_subscribe_queries_server(self):
        hosts = [
            Instance(
                ip="127.0.0.1",
                port=8848,
                healthy=True,
                enabled=True,
                weight=1.0,
                clusterName="blue",
            ),
            Instance(
                ip="127.0.0.2",
                port=8848,
                healthy=False,
                enabled=True,
                weight=1.0,
                clusterName="blue",
            ),
            Instance(
                ip="127.0.0.3",
                port=8848,
                healthy=True,
                enabled=True,
                weight=1.0,
                clusterName="green",
            ),
        ]
        queried_service = make_service("fresh", hosts)
        service_info_holder = SimpleNamespace(get_service_info=AsyncMock())
        grpc_client_proxy = SimpleNamespace(
            subscribe=AsyncMock(),
            query_instance_of_service=AsyncMock(return_value=queried_service),
        )
        naming_service = make_naming_service(service_info_holder, grpc_client_proxy)

        instances = await naming_service.list_instances(
            ListInstanceParam(
                service_name="demo-service",
                group_name="DEFAULT_GROUP",
                clusters=["blue"],
                healthy_only=True,
                subscribe=False,
            )
        )

        self.assertEqual(["127.0.0.1"], [instance.ip for instance in instances])
        grpc_client_proxy.query_instance_of_service.assert_awaited_once_with(
            "demo-service", "DEFAULT_GROUP", "blue", False
        )
        grpc_client_proxy.subscribe.assert_not_awaited()
        service_info_holder.get_service_info.assert_not_awaited()

    async def test_get_service_refreshes_cached_service(self):
        stale_service = make_service("stale")
        fresh_service = make_service("fresh")
        service_info_holder = SimpleNamespace(
            get_service_info=AsyncMock(return_value=stale_service)
        )
        grpc_client_proxy = SimpleNamespace(subscribe=AsyncMock(return_value=fresh_service))
        naming_service = make_naming_service(service_info_holder, grpc_client_proxy)

        service = await naming_service.get_service(
            GetServiceParam(service_name="demo-service", group_name="DEFAULT_GROUP")
        )

        self.assertEqual([{"version": "fresh"}], [instance.metadata for instance in service.hosts])
        grpc_client_proxy.subscribe.assert_awaited_once_with("demo-service", "DEFAULT_GROUP", "")
        service_info_holder.get_service_info.assert_not_awaited()


class TestNamingGrpcClientProxyCacheFallback(unittest.IsolatedAsyncioTestCase):

    async def test_subscribe_refreshes_cache_when_cached_service_is_not_subscribed(self):
        cached_service = make_service("stale")
        fresh_service = make_service("fresh")
        proxy = NamingGRPCClientProxy.__new__(NamingGRPCClientProxy)
        proxy.service_info_cache = SimpleNamespace(
            get_service_info=AsyncMock(return_value=cached_service),
            process_service=AsyncMock(),
        )
        proxy.redo_service = SimpleNamespace(
            is_subscribe_registered=AsyncMock(return_value=False)
        )
        proxy.do_subscribe = AsyncMock(return_value=fresh_service)

        result = await proxy.subscribe("demo-service", "DEFAULT_GROUP", "")

        self.assertIs(fresh_service, result)
        proxy.do_subscribe.assert_awaited_once_with("demo-service", "DEFAULT_GROUP", "")
        proxy.service_info_cache.process_service.assert_awaited_once_with(fresh_service)

    async def test_subscribe_uses_cache_when_service_is_already_subscribed(self):
        cached_service = make_service("fresh")
        proxy = NamingGRPCClientProxy.__new__(NamingGRPCClientProxy)
        proxy.service_info_cache = SimpleNamespace(
            get_service_info=AsyncMock(return_value=cached_service),
            process_service=AsyncMock(),
        )
        proxy.redo_service = SimpleNamespace(
            is_subscribe_registered=AsyncMock(return_value=True)
        )
        proxy.do_subscribe = AsyncMock()

        result = await proxy.subscribe("demo-service", "DEFAULT_GROUP", "")

        self.assertIs(cached_service, result)
        proxy.do_subscribe.assert_not_awaited()
        proxy.service_info_cache.process_service.assert_awaited_once_with(cached_service)

    async def test_subscribe_uses_cached_service_when_refresh_fails(self):
        cached_service = make_service("stale")
        proxy = NamingGRPCClientProxy.__new__(NamingGRPCClientProxy)
        proxy.logger = MagicMock()
        proxy.service_info_cache = SimpleNamespace(
            get_service_info=AsyncMock(return_value=cached_service),
            process_service=AsyncMock(),
        )
        proxy.redo_service = SimpleNamespace(
            is_subscribe_registered=AsyncMock(return_value=False)
        )
        proxy.do_subscribe = AsyncMock(side_effect=NacosException(SERVER_ERROR, "server unavailable"))

        result = await proxy.subscribe("demo-service", "DEFAULT_GROUP", "")

        self.assertIs(cached_service, result)
        proxy.do_subscribe.assert_awaited_once_with("demo-service", "DEFAULT_GROUP", "")
        proxy.service_info_cache.process_service.assert_awaited_once_with(cached_service)
        proxy.logger.warning.assert_called_once()


if __name__ == "__main__":
    unittest.main()
