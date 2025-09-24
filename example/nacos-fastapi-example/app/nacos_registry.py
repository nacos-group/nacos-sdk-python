import socket
import nacos

from loguru import logger
from app import settings

from v2.nacos import NacosNamingService, ClientConfigBuilder, GRPCConfig, Instance, SubscribeServiceParam, \
    RegisterInstanceParam, DeregisterInstanceParam, BatchRegisterInstanceParam, GetServiceParam, ListServiceParam, \
    ListInstanceParam, NacosConfigService, ConfigParam

def get_local_ip() -> str:
    """获取本地内网IP"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # 不会真的发包
        return s.getsockname()[0]
    finally:
        s.close()

class BasicNacosRegistrar:

    def __init__(self):
        self.client = nacos.NacosClient(
            server_addresses=settings.NACOS_SERVER_ADDR,
            namespace=settings.NACOS_NAMESPACE,
            username=settings.NACOS_USERNAME or None,
            password=settings.NACOS_PASSWORD or None,
        )
        self._registered = False

    @staticmethod
    async def register(service_name: str, port: int, enabled: bool = False):

        if not enabled:
            logger.info(f"Skip Nacos registration for service={service_name}, port={port}")
            return

        ip_or_host = get_local_ip()

        client_config = (ClientConfigBuilder()
                         .server_address(settings.NACOS_SERVER_ADDR).namespace_id(settings.NACOS_NAMESPACE)
                         .username(settings.NACOS_USERNAME).password(settings.NACOS_PASSWORD)
                         .log_level('INFO')
                         .grpc_config(GRPCConfig(grpc_timeout=5000, max_keep_alive_ms=60000))
                         .build())

        naming_client = await NacosNamingService.create_naming_service(client_config)

        response = await naming_client.register_instance(
            request=RegisterInstanceParam(
                service_name=service_name,
                group_name=settings.SERVICE_GROUP,
                ip=ip_or_host,
                port=port,
                ephemeral=True
            )
        )

        if response:
            logger.info(
                f"✅ Registered service={service_name}, host={ip_or_host}, port={port} to Nacos successfully"
            )
        else:
            logger.error(
                f"❌ Failed to register service={service_name}, host={ip_or_host}, port={port} to Nacos"
            )
        return naming_client

    @staticmethod
    async def deregister(nacos_naming_service: NacosNamingService,service_name: str, port: int):
        if nacos_naming_service:
            ip_or_host = get_local_ip()
            await nacos_naming_service.deregister_instance(
                request=DeregisterInstanceParam(service_name=service_name,
                                                group_name=settings.SERVICE_GROUP,
                                                ip=ip_or_host,
                                                port=port,
                                                ephemeral=True)
            )
