import asyncio
from typing import Optional

import grpc
import pydantic

from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException
from v2.nacos.transport.connection import Connection
from v2.nacos.transport.grpc_connection import GrpcConnection
from v2.nacos.transport.grpc_util import GrpcUtils
from v2.nacos.transport.grpcauto.nacos_grpc_service_pb2_grpc import BiRequestStreamStub, RequestStub
from v2.nacos.transport.model.internal_request import ConnectionSetupRequest, ServerCheckRequest
from v2.nacos.transport.model.internal_response import ServerCheckResponse
from v2.nacos.transport.model.rpc_request import Request
from v2.nacos.transport.model.server_info import ServerInfo
from v2.nacos.transport.nacos_server_connector import NacosServerConnector
from v2.nacos.transport.rpc_client import RpcClient, ConnectionType


class GrpcClient(RpcClient):

    def __init__(self, logger, name: str, client_config: ClientConfig, nacos_server: NacosServerConnector):
        super().__init__(logger=logger, name=name, nacos_server=nacos_server)
        self.logger = logger
        self.tls_config = client_config.tls_config
        self.grpc_config = client_config.grpc_config
        self.tenant = client_config.namespace_id

    async def _create_new_managed_channel(self, server_ip, grpc_port):
        options = [
            ('grpc.max_call_recv_msg_size', self.grpc_config.max_receive_message_length),
            ('grpc.keepalive_time_ms', self.grpc_config.max_keep_alive_ms),
        ]

        if self.tls_config and self.tls_config.enabled:
            with open(self.tls_config.ca_file, 'rb') as f:
                root_certificates = f.read()

            with open(self.tls_config.cert_file, 'rb') as f:
                cert_chain = f.read()

            with open(self.tls_config.key_file, 'rb') as f:
                private_key = f.read()

            credentials = grpc.ssl_channel_credentials(root_certificates=root_certificates,
                                                       private_key=private_key,
                                                       certificate_chain=cert_chain)

            channel = grpc.aio.secure_channel(f'{server_ip}:{grpc_port}', credentials=credentials,
                                              options=options)
        else:
            channel = grpc.aio.insecure_channel(f'{server_ip}:{grpc_port}',
                                                options=options)
        try:
            await asyncio.wait_for(channel.channel_ready(), self.grpc_config.grpc_timeout / 1000)
        except TimeoutError as e:
            await channel.close()
            raise NacosException('failed to connect nacos server') from e
        else:
            return channel

    async def _server_check(self, server_ip, server_port, channel_stub: RequestStub):
        for i in range(self.RETRY_TIMES):
            try:
                server_check_request = ServerCheckRequest()
                response_payload = await channel_stub.request(
                    GrpcUtils.convert_request_to_payload(server_check_request),
                    timeout=self.grpc_config.grpc_timeout / 1000.0)
                server_check_response = GrpcUtils.parse(response_payload)
                if not server_check_response or not isinstance(server_check_response, ServerCheckResponse):
                    return None

                if 300 <= server_check_response.get_error_code() < 400:
                    self.logger.error(
                        f"server check fail for {server_ip}:{server_port}, error code = {server_check_response.get_error_code()}")
                    await asyncio.sleep(1)
                    continue

                return server_check_response
            except grpc.FutureTimeoutError:
                self.logger.error(f"server check timed out for {server_ip}:{server_port}")
                continue
            except grpc.aio.AioRpcError as e:
                raise NacosException(error_code=e.code(), message=e.details())
            except Exception as e:
                self.logger.error(f"server check fail for {server_ip}:{server_port}, error = {e}")
                if self.tls_config and self.tls_config.enabled:
                    self.logger.error("current client requires tls encrypted, server must support tls, please check.")
            return None

    async def connect_to_server(self, server_info: ServerInfo) -> Optional[Connection]:
        managed_channel = await self._create_new_managed_channel(server_info.server_ip, server_info.server_port)
        # Create a stub
        channel_stub = RequestStub(managed_channel)
        server_check_response = await self._server_check(server_info.server_ip, server_info.server_port,
                                                         channel_stub)
        if not server_check_response:
            await self._shunt_down_channel(managed_channel)
            return None

        connection_id = server_check_response.get_connection_id()

        bi_request_stream_stub = BiRequestStreamStub(managed_channel)
        grpc_conn = GrpcConnection(server_info, connection_id, managed_channel,
                                   channel_stub, bi_request_stream_stub)

        connection_setup_request = ConnectionSetupRequest(Constants.CLIENT_VERSION, self.tenant, self.labels)
        await grpc_conn.send_bi_request(GrpcUtils.convert_request_to_payload(connection_setup_request))
        asyncio.create_task(self._server_request_watcher(grpc_conn))
        await asyncio.sleep(0.1)
        return grpc_conn

    async def _handle_server_request(self, request: Request, grpc_connection: GrpcConnection):
        request_type = request.get_request_type()
        server_request_handler_instance = self.server_request_handler_mapping.get(request_type)
        if not server_request_handler_instance:
            self.logger.error("unsupported payload type:%s, grpc connection id:%s", request_type,
                              grpc_connection.get_connection_id())
            return
        response = await server_request_handler_instance.request_reply(request)
        if not response:
            self.logger.warning("failed to process server request,connection_id:%s,ackID:%s",
                                grpc_connection.get_connection_id(), request.get_request_id())
            return

        try:
            response.set_request_id(request.requestId)

            await grpc_connection.send_bi_request(GrpcUtils.convert_response_to_payload(response))

        except Exception as e:
            if isinstance(e, EOFError):
                self.logger.error(
                    f"{grpc_connection.get_connection_id()} connection closed before response could be sent, ackId->{request.requestId}")
            else:
                self.logger.error(
                    f"{grpc_connection.get_connection_id()} failed to send response:{response.get_response_type()}, ackId:{request.requestId},error:{str(e)}")

    async def _server_request_watcher(self, grpc_conn: GrpcConnection):
        async for payload in grpc_conn.bi_stream_send():
            try:
                self.logger.info("receive stream server request, connection_id:%s, original info: %s"
                                 % (grpc_conn.get_connection_id(), str(payload)))
                request = GrpcUtils.parse(payload)
                if request:
                    await self._handle_server_request(request, grpc_conn)

            except Exception as e:
                self.logger.error(f"[{grpc_conn.connection_id}] handle server request occur exception: {e}")

    @staticmethod
    async def _shunt_down_channel(channel):
        if channel:
            await channel.close()

    def get_connection_type(self):
        return ConnectionType.GRPC

    def get_rpc_port_offset(self) -> int:
        return 1000
