import ssl
import logging
import grpc
import asyncio
import json
from v2.nacos.transport.rpc_client import RpcClient, ConnectionType
from v2.nacos.common.constants import Constants
from v2.nacos.transport.grpc_util import GrpcUtils
from v2.nacos.transport.model import internal_request
from v2.nacos.common.model.response import Response
from v2.nacos.common.constants import Constants
from v2.nacos.transport.grpc_connection import GrpcConnection
from v2.nacos.transport.proto import nacos_grpc_service_pb2_grpc
from v2.nacos.transport.proto import nacos_grpc_service_pb2


class GrpcClient(RpcClient):

    def __init__(self, name, nacos_server, client_config, tls_config, ability_mode, client_version):
        super().__init__(name=name,nacos_server=nacos_server)
        
        self.client_config = client_config
        self.tls_config = tls_config
        self.stream_observer = asyncio.Queue()

    def get_connection_type(self):
        return ConnectionType.GRPC


    async def shutdown(self):
        super().shutdown()
        #还需要关闭异步协程

    def _create_new_managed_channel(self, server_ip, server_port):
        logging.info("grpc client connection server:{} ip,serverPort:{},grpcTslConfig:{}", server_ip, server_port,
                         json.dumps(self.client_config.tlsConfig()))
        ssl_context = self._get_tls_credentials(server_ip)
        managed_channel = self._build_channel(server_ip, server_port, ssl_context)

        return managed_channel

    def _build_channel(self, server_ip, server_port, ssl_context=None):
        if ssl_context:
            # 有提供ssl_context,则提供ssl上下文创建加密的通道凭证
            credentials = grpc.ssl_channel_credentials(root_certificates=ssl_context.root_certificates,
                                                       private_key=ssl_context.private_key,
                                                       certificate_chain=ssl_context.certificate_chain)
            options = [
                ('grpc.max_receive_message_length', self.client_config.max_inbound_message_size()),
                ('grpc.keepalive_time_ms', self.client_config.channel_keep_alive()),
                ('grpc.keepalive_timeout_ms', self.client_config.channel_keep_alive_timeout())
            ]
            channel = grpc.secure_channel(server_ip, credentials=credentials, options=options)
        else:
            channel = grpc.insecure_channel(f'{server_ip}:{server_port}')
        return channel

    def _create_async_stub(self, channel):
        async_stub = nacos_grpc_service_pb2_grpc.RequestStub(channel)
        return async_stub

    async def _server_check(self, server_ip, server_port, async_stub):
        try:
            server_check_request = internal_request.HealthCheckRequest().new_health_check_request()
            
            grpc_request = GrpcUtils.convert_request_to_payload(server_check_request)
            # Send a request and wait for a response
            response_payload = await asyncio.wait_for(
                async_stub.request(grpc_request),
                self.client_config.server_check_time_out / 1000.0
            )
            return GrpcUtils.parse(response_payload)
        except TimeoutError:
            logging.error(f"Server check timed out for {server_ip}:{server_port}")
        except Exception as e:
            logging.error(f"Server check fail for {server_ip}:{server_port}, error = {e}")
            if (hasattr(self.client_config,
                        'tls_config') and self.client_config.tls_config()
                    and self.client_config.tls_config().get_enable_tls()):
                logging.error("Current client requires tls encrypted, server must support tls, please check.")
        return None
    
    def rpc_port_offset(self):
        return Constants.RPC_PORT_OFFSET
    
    def  _shunt_down_channel(self, managed_channel):
        if managed_channel is not None and not managed_channel.is_shutdown():
            managed_channel.close()

    def connect_to_server(self, server_info):
        connection_id = ""
        try:
            port = server_info.port + self.rpc_port_offset()
            # Establish a channel
            managed_channel = self._create_new_managed_channel(server_info.server_ip, port)
            # Create a stub
            channel_stub = self._create_async_stub(managed_channel)
            response = self._server_check(server_info.server_ip, server_info.server_port, channel_stub)
            server_check_response = response
            connection_id = server_check_response.get_connection_id()

            bi_request_stream_stub = nacos_grpc_service_pb2_grpc.BiRequestStreamStub(
                managed_channel)
            

            grpc_conn = GrpcConnection(server_info, server_check_response.get_connection_id(), managed_channel, channel_stub, bi_request_stream_stub)
            grpc_conn.set_connection_id(connection_id)

            self._bind_request_stream(bi_request_stream_stub,
                                                                grpc_conn)
            self.send_connection_setup_request(grpc_conn)
            return grpc_conn
        except Exception as e:
            logging.error(f"[{self.name}] Fail to connect to server!, error={str(e)}")

        return None

    def _get_tls_credentials(self, server_ip):
        logging.info(f"build tls config for connecting to server {server_ip}, tlsConfig = {self.tls_config}")

        # Obtain the system certificate pool
        cert_pool = ssl.create_default_context().get_ca_certs()
        if not cert_pool:
            raise Exception("load root cert pool fail")

        # If the CA file is specified in the configuration, the certificate in the file is loaded
        if self.tls_config.ca_file:
            try:
                with open(self.tls_config.ca_file, 'rb') as f:
                    ca_cert = f.read()
                    ssl_context = ssl.create_default_context(cadata=ca_cert)
            except Exception as e:
                logging.error(f"Failed to load CA file: {str(e)}")
                raise 

        # Set whether to trust all certificates
        ssl_context.check_hostname = not self.tls_config.get('trust_all', False)
        ssl_context.verify_mode = ssl.CERT_REQUIRED if not self.tls_config.get('trust_all', False) else ssl.CERT_NONE

        # If the client certificate and private key files are specified in the configuration, these files are loaded
        if self.tls_config.cert_file and self.tls_config.key_file:
            try:
                ssl_context.load_cert_chain(certfile=self.tls_config.cert_file, keyfile=self.tls_config.key_file)
            except Exception as e:
                logging.error("Failed to load client cert and key: %v", e)
                raise 

        return ssl_context

    def _handle_server_request(self, payload, grpc_conn):
        # client = self.get_rpc_client()
        payload_type = payload.metadata.type
        handler_mapping = self.server_request_handler_mapping.get(payload_type)
        if not handler_mapping:
            logging.error("%s Unsupported payload type", grpc_conn.get_connection_id())
            return

        # Gets the server request object and deserializes it
        server_request = handler_mapping.server_request()
        try:
            json.loads(payload.body.value, object_hook=lambda d: server_request.update(d))
        except json.JSONDecodeError as err:
            logging.error("%s Fail to json Unmarshal for request:%s, ackId->%s", grpc_conn.get_connection_id(),
                              server_request.request_type, server_request.request_id)
            return

        server_request.headers = payload.get.metadata.headers
        response = handler_mapping.handler.request_reply(server_request)
        if not response:
            logging.warning("%s Fail to process server request, ackId->%s", grpc_conn.get_connection_id(),
                                server_request.request_id)
            return

        response.request_id = server_request.request_id
        grpc_conn.bi_stream_send(GrpcUtils.convert_response_to_payload(response))
        if err and err != EOFError:
            logging.warning("%s Fail to send response:%s,ackId->%s", grpc_conn.get_connection_id(),
                                response.response_type, server_request.request_id)


    async def _bind_request_stream(self, stream_stub, grpc_conn):
        asyncio.create_task(request_stream_handler())
        async def bi_stream_request_iterator(request_queue):
            while True:
                request_data = await request_queue.get()
                print(f"Received request: {request_data}")
                response_data = f"response_to_{request_data}"
                yield response_data

        
        async def request_stream_handler():
            response_iterator = stream_stub.bi_stream_service(bi_stream_request_iterator(self.stream_observer))

            async for response_data in response_iterator:
                try:
                    payload = response_data
                    request = GrpcUtils.parse(payload)
                    if request:
                        response = await self._handle_server_request(request)
                        if response:
                            response.request_id = request.request_id
                            await self._send_response(response)
                        else:
                            logging.warning(
                                f"[{grpc_conn.connection_id}] Fail to process server request, ackId->{request.request_id}")
                except Exception as e:
                    logging.error(f"[{grpc_conn.connection_id}] Handle server request exception: {e}")
                    err_response = Response.build(Constants.CLIENT_ERROR, "Handle server request error")
                    err_response.request_id = request.request_id
                    await self._send_response(err_response)


    def _send_response(self, response):
        try:
            self.current_connection.send_response(response)
        except Exception as e:
            logging.error(
                f"[{self.current_connection.connection_id}] Error to send ack response, ackId-> {response.request_id}")
    
    async def send_connection_setup_request(self, grpc_conn):
        csr = internal_request.ConnectionSetupRequest.new_connection_setup_request()
        csr.client_version = Constants.CLIENT_VERSION
        csr.tenant = self.tenant
        csr.labels = self.labels
        csr.client_abilities = self.client_abilities

        try:
            payload = GrpcUtils.request_convert_payload(csr)
            stream = nacos_grpc_service_pb2._BIREQUESTSTREAM(payload)
            await self.stream_observer.put(stream)
        except Exception as err: 
            logging.warn(f"send connectionSetupRequest error: {err}")
        await asyncio.sleep(0.1)