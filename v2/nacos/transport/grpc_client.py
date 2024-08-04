import concurrent.futures
import threading
from connection import Connection
import re
import grpc
import asyncio
import json
from rpc_client import RpcClient, ConnectionType
import time
import ssl
from ..util.grpc_util import GrpcUtils
from ..common.model.request import Request
from ..common.model.response import Response
from ..common.constants import Constants
from grpc_connection import GrpcConnection
import proto.nacos_grpc_service_pb2_grpc as ngs


class GrpcClient(RpcClient):

    def __init__(self, logger, name, client_config, tls_config, ability_mode, client_version):
        super().__init__(name)
        self.rpc_client = RpcClient(name)
        self.logger = logger
        self.client_config = client_config
        self.grpc_executor = None
        self.rec_ability_context = self.RecAbilityContext(None)
        self.server_list_factory = None
        self.tls_config = tls_config
        self.ability_mode = ability_mode
        self.client_version = client_version

    def get_connection_type(self):
        return ConnectionType.GRPC

    def _create_grpc_executor(self, server_ip):
        server_ip = re.sub(r'%', '-', server_ip)
        grpc_executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.client_config.thread_pool_size,
                                                              thread_name_prefix='nacos-grpc_executor-' + server_ip)
        return grpc_executor

    def _create_new_managed_channel(self, server_ip, server_port):
        self.logger.info("grpc client connection server:{} ip,serverPort:{},grpcTslConfig:{}", server_ip, server_port,
                         json.dumps(self.client_config.tlsConfig()))
        ssl_context = self._get_tls_credentials(server_ip)
        managed_channel = self._build_channel(server_ip, server_port, ssl_context)

        return managed_channel

    def _build_channel(self, server_ip, server_port, ssl_context=None):
        if ssl_context:
            credentials = grpc.ssl_channel_credentials(root_certificates=ssl_context.root_certificates,
                                                       private_key=ssl_context.private_key,
                                                       certificate_chain=ssl_context.certificate_chain)
            options = [
                ('grpc.max_receive_message_length', self.client_config().max_inbound_message_size()),
                ('grpc.keepalive_time_ms', self.client_config().channel_keep_alive()),
                ('grpc.keepalive_timeout_ms', self.client_config().channel_keep_alive_timeout())
            ]
            channel = grpc.secure_channel(server_ip, credentials=credentials, options=options)
        else:
            channel = grpc.insecure_channel(f'{server_ip}:{server_port}')
        return channel

    async def _create_async_stub(self, channel):
        async_stub = ngs.RequestStub(channel)
        return async_stub

    async def _server_check(self, server_ip, server_port, async_stub):
        server_check_request = Request
        grpc_request = GrpcUtils.convert(server_check_request)
        try:
            # Send a request and wait for a response
            response = await asyncio.wait_for(
                async_stub.request(grpc_request),
                self.client_config.server_check_time_out() / 1000.0
            )
            return GrpcUtils.parse(response)
        except TimeoutError:
            self.logger.error(f"Server check timed out for {server_ip}:{server_port}")
        except Exception as e:
            self.logger.error(f"Server check fail for {server_ip}:{server_port}, error = {e}")
            if (hasattr(self.client_config,
                        'tls_config') and self.client_config.tls_config()
                    and self.client_config.tls_config().get_enable_tls()):
                self.logger.error("Current client requires tls encrypted, server must support tls, please check.")
        return None

    def connect_to_server(self, server_info):
        try:
            if self.grpc_executor is None:
                self.grpc_executor = self._create_grpc_executor(
                    server_info.server_ip)
                port = server_info.port + self.rpc_client.rpc_port_offset()
            # Establish a channel
            managed_channel = self._create_new_managed_channel(server_info.server_ip, port)
            # Create a stub
            channel_stub = self._create_async_stub(managed_channel)
            response = self._server_check(server_info.server_ip, server_info.server_port, channel_stub)
            server_check_response = Response(response)
            connection_id = server_check_response.get_connection_id()

            bi_request_stream_stub = ngs.BiRequestStreamStub(
                managed_channel)

            grpc_conn = GrpcConnection(server_info, self.grpc_executor)
            grpc_conn.set_connection_id(connection_id)

            if server_check_response.is_support_ability_negotiation:  # If the server supports ability negotiation
                self.rec_ability_context.reset(grpc_conn)  # Reset the ability context
                grpc_conn.set_ability_table(None)  # Set the ability table to None

            payload_stream_observer = self._bind_request_stream(bi_request_stream_stub,
                                                                grpc_conn)
            grpc_conn.set_payload_stream_observer(payload_stream_observer)

            # Set the gRPC future service stub and channel
            grpc_conn.set_grpc_future_service_stub(channel_stub)
            grpc_conn.set_channel(managed_channel)

            # Send a setup request
            con_setup_request = Request()
            con_setup_request.set_client_version(self.client_version)
            con_setup_request.set_labels(self.labels)
            con_setup_request.set_ability_table(self.client_abilities(self.ability_mode))
            con_setup_request.set_tenant(self.tenant)
            grpc_conn.send_request(con_setup_request)

            # Wait for a response
            if self.rec_ability_context.is_need_to_sync():
                # Try to wait for a notification response
                self.rec_ability_context.rec_await(self.client_config.capability_negotiation_timeout())
                # If the server's abilities are not received, reconnect
                if not self.rec_ability_context.check(grpc_conn):
                    return None
            else:
                # Adapt to the old version of the server
                # Consider the registration successful within 100ms after the connection is registered
                time.sleep(0.1)

            return grpc_conn
        except Exception as e:
            # Log the error
            self.logger.error(f"[{self.name}] Fail to connect to server!, error={e}")
            # Remove and notify
            self.rec_ability_context.release(None)

        return None

    def _get_tls_credentials(self, server_ip):
        self.logger.info("build tls config for connecting to server %s, tlsConfig = %s", server_ip,
                         self.tls_config)

        # Obtain the system certificate pool
        cert_pool = ssl.create_default_context().get_ca_certs()
        if not cert_pool:
            raise Exception("load root cert pool fail")

        # If the CA file is specified in the configuration, the certificate in the file is loaded
        if self.tls_config.ca_file:
            try:
                with open(self.tls_config['ca_file'], 'rb') as f:
                    ca_cert = f.read()
                    ssl_context = ssl.create_default_context(cadata=ca_cert)
            except Exception as e:
                self.logger.error("Failed to load CA file: %v", e)
                raise e

        # Set whether to trust all certificates
        ssl_context.check_hostname = not self.tls_config.get('trust_all', False)
        ssl_context.verify_mode = ssl.CERT_REQUIRED if not self.tls_config.get('trust_all', False) else ssl.CERT_NONE

        # If the client certificate and private key files are specified in the configuration, these files are loaded
        if self.tls_config.cert_file and self.tls_config.key_file:
            try:
                ssl_context.load_cert_chain(certfile=self.tls_config.cert_file, keyfile=self.tls_config.key_file)
            except Exception as e:
                self.logger.error("Failed to load client cert and key: %v", e)
                raise e

        return ssl_context

    def _handle_server_request(self, payload, grpc_conn):
        client = self.get_rpc_client()
        payload_type = payload.get("metadata").get("type")
        handler_mapping = client.server_request_handler_mapping.get(payload_type)
        if not handler_mapping:
            self.logger.error("%s Unsupported payload type", grpc_conn.get_connection_id())
            return

        # Gets the server request object and deserializes it
        server_request = handler_mapping["server_request"]()
        try:
            json.loads(payload.get("body").get("value"), object_hook=lambda d: server_request.update(d))
        except json.JSONDecodeError as err:
            self.logger.error("%s Fail to json Unmarshal for request:%s, ackId->%s", grpc_conn.get_connection_id(),
                              server_request.get("request_type"), server_request.get("request_id"))
            return

        server_request["headers"] = payload.get("metadata").get("headers")
        response = handler_mapping["handler"].request_reply(server_request, client)
        if not response:
            self.logger.warning("%s Fail to process server request, ackId->%s", grpc_conn.get_connection_id(),
                                server_request.get("request_id"))
            return

        response["request_id"] = server_request.get("request_id")
        err = grpc_conn.bi_stream_send(grpc_conn.convert_response(response))
        if err and err != EOFError:
            self.logger.warning("%s Fail to send response:%s,ackId->%s", grpc_conn.get_connection_id(),
                                response.get("response_type"), server_request.get("request_id"))

    class RecAbilityContext:
        def __init__(self, logger, connection: Connection):
            self.logger = logger
            self.connection = connection
            self.blocker = threading.Event()
            self.need_to_sync = False

        def is_need_to_sync(self) -> bool:
            return self.need_to_sync

        def reset(self, connection: Connection):
            self.connection = connection
            self.blocker.clear()  # Equivalent to CountDownLatch reset
            self.need_to_sync = True

        def release(self, abilities: dict[str, bool]):
            if self.connection:
                self.connection.set_ability_table(abilities)
                self.connection = None  # Avoid duplicate Settings
            if self.blocker:
                self.blocker.set()  # Release wait
            self.need_to_sync = False

        def rec_await(self, timeout: int):
            if self.blocker:
                self.blocker.wait(timeout)
                self.need_to_sync = False

        def check(self, connection: Connection) -> bool:
            if not connection.is_abilities_set():
                self.logger.info(
                    "Client don't receive server abilities table even empty table but server supports ability negotiation."
                    " You can check if it is need to adjust the timeout of ability negotiation by property: "
                    + "if always fail to connect.")
                connection.set_abandon(True)
                connection.close()
                return False
            return True

    async def _bind_request_stream(self, stream_stub, grpc_conn):
        async def request_stream_handler(request):
            try:
                request = GrpcUtils.parse(request)
                if request:
                    response = await self._handle_server_request(request)
                    if response:
                        response.request_id = request.request_id
                        await self._send_response(response)
                    else:
                        self.logger.warning(
                            f"[{grpc_conn.connection_id}] Fail to process server request, ackId->{request.request_id}")
            except Exception as e:
                self.logger.error(f"[{grpc_conn.connection_id}] Handle server request exception: {e}")
                err_response = Response.build(Constants.CLIENT_ERROR, "Handle server request error")
                err_response.request_id = request.request_id
                await self._send_response(err_response)

        return stream_stub.requestBiStream(request_stream_handler)

    def _send_response(self, response):
        try:
            self.current_connection.send_response(response)
        except Exception as e:
            self.logger.error(
                f"[{self.current_connection.connection_id}] Error to send ack response, ackId-> {response.request_id}",
                exc_info=True)
