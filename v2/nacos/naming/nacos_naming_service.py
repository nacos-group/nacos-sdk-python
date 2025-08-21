import asyncio
from typing import List

from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM
from v2.nacos.nacos_client import NacosClient
from v2.nacos.naming.cache.service_info_cache import ServiceInfoCache
from v2.nacos.naming.cache.service_info_updater import ServiceInfoUpdater
from v2.nacos.naming.cache.subscribe_callback_wrapper import ClusterSelector, \
    SubscribeCallbackFuncWrapper
from v2.nacos.naming.model.instance import Instance
from v2.nacos.naming.model.naming_param import RegisterInstanceParam, BatchRegisterInstanceParam, \
    DeregisterInstanceParam, ListInstanceParam, SubscribeServiceParam, GetServiceParam, ListServiceParam
from v2.nacos.naming.model.service import ServiceList
from v2.nacos.naming.model.service import Service
from v2.nacos.naming.remote.naming_grpc_client_proxy import NamingGRPCClientProxy
from v2.nacos.naming.util.naming_client_util import get_group_name


class NacosNamingService(NacosClient):
    def __init__(self, client_config: ClientConfig):
        super().__init__(client_config, Constants.NAMING_MODULE)
        if not client_config.namespace_id or len(
                client_config.namespace_id) == 0:
            self.namespace_id = "public"
        else:
            self.namespace_id = client_config.namespace_id
        self.service_info_holder = ServiceInfoCache(client_config)
        self.grpc_client_proxy = NamingGRPCClientProxy(client_config, self.http_agent, self.service_info_holder)
        self.service_info_updater = ServiceInfoUpdater(
                self.service_info_holder, client_config.update_thread_num,
                self.grpc_client_proxy)
        if client_config.async_update_service:
            asyncio.create_task(self.service_info_updater.async_update_service())

    @staticmethod
    async def create_naming_service(client_config: ClientConfig) -> 'NacosNamingService':
        naming_service = NacosNamingService(client_config)
        await naming_service.grpc_client_proxy.start()
        return naming_service

    async def register_instance(self, request: RegisterInstanceParam) -> bool:
        if not request.service_name or not request.service_name.strip():
            raise NacosException(INVALID_PARAM, "service_name can not be empty")

        if not request.group_name:
            request.group_name = Constants.DEFAULT_GROUP

        if request.metadata is None:
            request.metadata = {}

        instance = Instance(ip=request.ip,
                            port=request.port,
                            metadata=request.metadata,
                            clusterName=request.cluster_name,
                            healthy=request.healthy,
                            enabled=request.enabled,
                            weight=request.weight,
                            ephemeral=request.ephemeral,
                            )

        instance.check_instance_is_legal()

        return await self.grpc_client_proxy.register_instance(request.service_name, request.group_name, instance)

    async def batch_register_instances(self, request: BatchRegisterInstanceParam) -> bool:
        if not request.service_name:
            raise NacosException(INVALID_PARAM, "service_name can not be empty")

        instance_list = []
        for instance in request.instances:
            if not instance.ephemeral:
                raise NacosException(INVALID_PARAM,
                                     f"batch registration does not allow persistent instance:{instance}")
            instance_list.append(Instance(
                ip=instance.ip,
                port=instance.port,
                metadata=instance.metadata,
                clusterName=instance.cluster_name,
                healthy=instance.healthy,
                enabled=instance.enabled,
                weight=instance.weight,
                ephemeral=instance.ephemeral,
            ))

        return await self.grpc_client_proxy.batch_register_instance(request.service_name, request.group_name,
                                                                    instance_list)
    async def batch_deregister_instances(self, request: BatchRegisterInstanceParam) -> bool:
        if not request.service_name:
            raise NacosException(INVALID_PARAM, "service_name can not be empty")
        instance_list = []
        for instance in request.instances:
            if not instance.ephemeral:
                raise NacosException(INVALID_PARAM,
                                     f"batch de registration does not allow persistent instance:{instance}")
            instance_list.append(Instance(
                ip=instance.ip,
                port=instance.port,
                metadata=instance.metadata,
                clusterName=instance.cluster_name,
                healthy=instance.healthy,
                enabled=instance.enabled,
                weight=instance.weight,
                ephemeral=instance.ephemeral,
            ))

        return await self.grpc_client_proxy.batch_deregister_instance(request.service_name, request.group_name,
                                                                    instance_list)



    async def deregister_instance(self, request: DeregisterInstanceParam) -> bool:
        if not request.service_name:
            raise NacosException(INVALID_PARAM, "service_name can not be empty")

        if not request.group_name:
            request.group_name = Constants.DEFAULT_GROUP

        instance = Instance(ip=request.ip,
                            port=request.port,
                            clusterName=request.cluster_name,
                            ephemeral=request.ephemeral,
                            )

        return await self.grpc_client_proxy.deregister_instance(request.service_name, request.group_name, instance)

    async def update_instance(self, request: RegisterInstanceParam) -> bool:
        if not request.service_name:
            raise NacosException(INVALID_PARAM, "service_name can not be empty")

        if request.metadata is None:
            request.metadata = {}

        if not request.group_name:
            request.group_name = Constants.DEFAULT_GROUP

        instance = Instance(ip=request.ip,
                            port=request.port,
                            metadata=request.metadata,
                            clusterName=request.cluster_name,
                            enabled=request.enabled,
                            healthy=request.healthy,
                            weight=request.weight,
                            ephemeral=request.ephemeral,
                            )

        instance.check_instance_is_legal()

        return await self.grpc_client_proxy.register_instance(request.service_name, request.group_name, instance)

    async def get_service(self, request: GetServiceParam) -> Service:
        if not request.service_name:
            raise NacosException(INVALID_PARAM, "service_name can not be empty")

        if not request.group_name:
            request.group_name = Constants.DEFAULT_GROUP

        clusters = ",".join(request.clusters)
        service = await self.service_info_holder.get_service_info(request.service_name, request.group_name, "")
        cluster_selector = ClusterSelector(request.clusters)
        if not service:
            service = await self.grpc_client_proxy.subscribe(request.service_name, request.group_name, "")
        service.clusters = clusters
        service.hosts = cluster_selector.select_instance(service)
        return service

    async def list_services(self, request: ListServiceParam) -> ServiceList:
        if not request.group_name:
            request.group_name = Constants.DEFAULT_GROUP

        if not request.namespace_id:
            if not self.client_config.namespace_id:
                request.namespace_id = Constants.DEFAULT_NAMESPACE_ID
            else:
                request.namespace_id = self.client_config.namespace_id

        return await self.grpc_client_proxy.list_services(request)

    async def list_instances(self, request: ListInstanceParam) -> List[Instance]:
        if not request.service_name:
            raise NacosException(INVALID_PARAM, "service_name can not be empty")

        if not request.group_name:
            request.group_name = Constants.DEFAULT_GROUP

        cluster_selector = ClusterSelector(request.clusters)
        service_info = None
        # 如果subscribe为true, 则优先从缓存中获取服务信息，并订阅该服务
        if request.subscribe:
            service_info = await self.service_info_holder.get_service_info(request.service_name, request.group_name,
                                                                           "")
        if service_info is None:
            service_info = await self.grpc_client_proxy.subscribe(request.service_name, request.group_name, "")

        instance_list = []
        if service_info is not None and len(service_info.hosts) > 0:
            instance_list = cluster_selector.select_instance(service_info)

        # 如果设置了healthy_only参数,表示需要查询健康或不健康的实例列表，为true时仅会返回健康的实例列表，反之则返回不健康的实例列表。默认为None
        if request.healthy_only is not None:
            instance_list = list(
                filter(lambda host: host.healthy == request.healthy_only and host.enabled and host.weight > 0,
                       instance_list))

        return instance_list

    async def subscribe(self, request: SubscribeServiceParam) -> None:
        if not request.service_name:
            raise NacosException(INVALID_PARAM, "service_name can not be empty")

        if not request.group_name:
            request.group_name = Constants.DEFAULT_GROUP

        cluster_selector = ClusterSelector(request.clusters)
        callback_wrapper = SubscribeCallbackFuncWrapper(cluster_selector, request.subscribe_callback)
        await self.service_info_holder.register_callback(get_group_name(request.service_name, request.group_name),
                                                         "", callback_wrapper)
        await self.grpc_client_proxy.subscribe(request.service_name, request.group_name, "")

    async def unsubscribe(self, request: SubscribeServiceParam) -> None:
        if not request.service_name:
            raise NacosException(INVALID_PARAM, "service_name can not be empty")

        if not request.group_name:
            request.group_name = Constants.DEFAULT_GROUP

        cluster_selector = ClusterSelector(request.clusters)
        callback_wrapper = SubscribeCallbackFuncWrapper(cluster_selector, request.subscribe_callback)
        await self.service_info_holder.deregister_callback(get_group_name(request.service_name, request.group_name),
                                                           "", callback_wrapper)
        if not await self.service_info_holder.is_subscribed(get_group_name(request.service_name, request.group_name), ""):
            await self.grpc_client_proxy.unsubscribe(request.service_name, request.group_name, "")

    async def server_health(self) -> bool:
        return self.grpc_client_proxy.server_health()

    async def shutdown(self) -> None:
        await self.grpc_client_proxy.close_client()
        await self.service_info_updater.stop()
