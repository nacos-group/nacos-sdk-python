from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM
from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.constants import Constants
from v2.nacos.nacos_client import NacosClient
from v2.nacos.naming.cache.service_info_cache import ServiceInfoCache
from v2.nacos.naming.model.instance import Instance
from v2.nacos.naming.model.naming_request import RegisterInstanceRequest, \
    BatchRegisterInstanceRequest, DeregisterInstanceRequest, UpdateInstanceRequest, GetServiceRequest
from v2.nacos.naming.remote.naming_client_proxy_delegate import NamingClientProxyDelegate


class NacosNamingService(NacosClient):
    def __init__(self, client_config: ClientConfig):
        super().__init__(client_config, Constants.NAMING_MODULE)
        self.namespace_id = client_config.namespace_id
        self.service_info_holder = ServiceInfoCache(client_config)
        self.client_proxy_delegate = NamingClientProxyDelegate(client_config, self.http_agent,
                                                               self.service_info_holder)

    def register_instance(self, request: RegisterInstanceRequest) -> bool:
        if not request.service_name or not request.serviceName.strip():
            raise NacosException(INVALID_PARAM, "service_name can not be empty")

        if not request.group_name:
            request.group_name = Constants.DEFAULT_GROUP

        if request.metadata is None:
            request.metadata = {}

        instance = Instance(ip=request.ip,
                            port=request.port,
                            metadata=request.metadata,
                            cluster_name=request.cluster_name,
                            healthy=request.healthy,
                            enable=request.enable,
                            weight=request.weight,
                            ephemeral=request.ephemeral,
                            )

        instance.check_instance_is_legal()

        return self.client_proxy_delegate.register_instance(request.service_name, request.group_name, instance)

    def batch_register_instance(self, request: BatchRegisterInstanceRequest) -> bool:
        if not request.service_name:
            raise NacosException(INVALID_PARAM, "service_name can not be empty")

        if not request.group_name:
            request.group_name = Constants.DEFAULT_GROUP

        if len(request.instances) == 0:
            raise NacosException(INVALID_PARAM, "instances can not be empty")

        model_instances = []
        for instance_param in request.instances:
            if not instance_param.ephemeral:
                raise NacosException(INVALID_PARAM,
                                     f"batch registration does not allow persistent instance registration! instance:{instance_param}")
            instance = Instance(
                ip=instance_param.ip,
                port=instance_param.port,
                metadata=instance_param.metadata,
                cluster_name=instance_param.cluster_name,
                healthy=instance_param.healthy,
                enable=instance_param.enable,
                weight=instance_param.weight,
                ephemeral=instance_param.ephemeral,
            )
            model_instances.append(instance)

        return self.client_proxy_delegate.batch_register_instance(request.service_name, request.group_name,
                                                                  model_instances)

    def deregister_instance(self, request: DeregisterInstanceRequest) -> None:
        if not request.service_name:
            raise NacosException(INVALID_PARAM, "service_name can not be empty")

        if not request.group_name:
            request.group_name = Constants.DEFAULT_GROUP

        instance = Instance(ip=request.ip,
                            port=request.port,
                            cluster_name=request.cluster_name,
                            ephemeral=request.ephemeral,
                            )

        return self.client_proxy_delegate.deregister_instance(request.service_name, request.group_name, instance)

    def update_instance(self, request: UpdateInstanceRequest):
        if not request.service_name or not request.serviceName.strip():
            raise NacosException(INVALID_PARAM, "service_name can not be empty")

        if not request.group_name:
            request.group_name = Constants.DEFAULT_GROUP

        if request.metadata is None:
            request.metadata = {}

        instance = Instance(ip=request.ip,
                            port=request.port,
                            metadata=request.metadata,
                            cluster_name=request.cluster_name,
                            healthy=request.healthy,
                            enable=request.enable,
                            weight=request.weight,
                            ephemeral=request.ephemeral,
                            )

        instance.check_instance_is_legal()

        return self.client_proxy_delegate.register_instance(request.service_name, request.group_name, instance)

    def get_service(self, request: GetServiceRequest)->:
        if not request.group_name:
            request.group_name = Constants.DEFAULT_GROUP

        clusters = ",".join(request.clusters)
        self.service_info_holder.g

    def get_all_instances(self):
        pass

    def select_instances(self):
        pass

    def select_one_healthy_instance(self):
        pass

    def subscribe(self):
        pass

    def unsubscribe(self):
        pass

    def get_services_of_server(self):
        pass

    def get_server_status(self) -> str:
        pass

    def shutdown(self) -> None:
        pass
