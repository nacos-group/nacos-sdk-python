import threading
import time
from abc import ABCMeta
from typing import List, Iterator

import grpc

from v2.nacos.common.constants import Constants
from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.grpcauto import nacos_grpc_service_pb2
from v2.nacos.grpcauto.nacos_grpc_service_pb2 import Payload
from v2.nacos.grpcauto.nacos_grpc_service_pb2_grpc import BiRequestStreamStub, RequestStub
from v2.nacos.remote.connection import Connection
from v2.nacos.remote.grpc.grpc_connection import GrpcConnection
from v2.nacos.remote.grpc.grpc_utils import GrpcUtils
from v2.nacos.remote.requests.connection_setup_request import ConnectionSetupRequest
from v2.nacos.remote.requests.push_ack_request import PushAckRequest
from v2.nacos.remote.requests.request import Request
from v2.nacos.remote.requests.server_check_request import ServerCheckRequest
from v2.nacos.remote.responses.response import Response
from v2.nacos.remote.responses.server_check_response import ServerCheckResponse
from v2.nacos.remote.rpc_client import RpcClient, ServerInfo
from v2.nacos.remote.utils import ConnectionType, rpc_client_status


class GrpcClient(RpcClient):
    DEFAULT_MAX_INBOUND_MESSAGE_SIZE = 10 * 1024 * 1024

    DEFAULT_KEEP_ALIVE_TIME = 6 * 60 * 1000

    def get_connection_type(self) -> str:
        return ConnectionType.GRPC

    def get_rpc_port_offset(self) -> int:
        return 1000

    def connect_to_server(self, server_info: ServerInfo) -> Connection:
        try:

            port = server_info.get_server_port()
            self._channel = grpc.insecure_channel(str(server_info.get_server_ip())+":"+str(port))
            request_stub = RequestStub(self._channel)
            if request_stub:
                response = self.server_check(request_stub, server_info.get_server_ip(), port)
                if not response or not isinstance(response, ServerCheckResponse):
                    self.shutdown_channel(self._channel)
                    return None

                bi_request_stream_stub = BiRequestStreamStub(self._channel)
                grpc_conn = GrpcConnection(server_info)
                bi_request_stream_stub = self.bind_request_stream(bi_request_stream_stub, grpc_conn)
                grpc_conn.set_connection_id(response.get_connection_id())
                grpc_conn.set_bi_request_stream_stub(bi_request_stream_stub)
                grpc_conn.set_request_stub(request_stub)
                grpc_conn.set_channel(self._channel)

                # send a setup request
                connection_setup_request = ConnectionSetupRequest()
                connection_setup_request.set_client_version(Constants.CLIENT_VERSION)
                connection_setup_request.set_labels(self.get_labels())
                connection_setup_request.set_abilities(self.get_client_abilities())
                connection_setup_request.set_tenant(self.get_tenant())
                grpc_conn.send_request(connection_setup_request)

                time.sleep(0.1)
                return grpc_conn

        except NacosException as e:
            self.logger.error("[%s]Fail to connect to server, error=%s"
                              % (self.get_name(), e))
        return

    @staticmethod
    def shutdown_channel(channel: grpc.Channel) -> None:
        if channel:
            channel.close()

    def server_check(self, request_stub: RequestStub, ip: str, port: str) -> object:
        try:
            request = ServerCheckRequest()
            payload = GrpcUtils.convert_request(request)
            resq = request_stub.request(payload)
            return GrpcUtils.parse(resq)
        except NacosException as e:
            self.logger.error("Server check fail, please check server %s, port %s is available, error =%s"
                              % (ip, port, e))
            return

    def bind_request_stream(self, stream_stub: BiRequestStreamStub, grpc_conn: GrpcConnection):
        def job():
            try:
                for payload in stream_stub.requestBiStream(grpc_conn.gen_message()):
                    self.logger.info("[%s] Stream server request receive, original info: %s"
                                     % (grpc_conn.get_connection_id(), str(payload)))
                    try:
                        request = GrpcUtils.parse(payload)
                        if request:
                            try:
                                response = self.handle_server_request(request)
                                if response:
                                    response.set_request_id(request.get_request_id())
                                    self._send_response(response)
                                else:
                                    self.logger.warning("[%s] Fail to process server request, ackId->%s"
                                                        % (grpc_conn.get_connection_id(), request.get_request_id()))
                            except NacosException as e:
                                self.logger.error("[%s] Handle server request exception: %s, %s"
                                                  % (grpc_conn.get_connection_id(), str(payload), e))
                    except NacosException:
                        self.logger.error("[%s] Error to process server push response: %s"
                                          % (grpc_conn.get_connection_id(), str(payload.body)))
            except Exception as e:
                is_running = self.is_running()
                is_abandon = grpc_conn.is_abandon()
                if is_running and not is_abandon:
                    self.logger.error("[%s] Request stream error, switch server, error=%s" %
                                      (grpc_conn.get_connection_id(), str(e))
                                      )
                    with self.lock:
                        self._rpc_client_status = rpc_client_status["UNHEALTHY"]
                        self.switch_server_async()
                else:
                    self.logger.warning("[%s]Ignore error event, isRunning:%s, isAbandon:%s"
                                        % (grpc_conn.get_connection_id(), is_running, is_abandon)
                                        )

        self._client_event_executor.submit(job)

        return stream_stub

    def _send_response_with_flag(self, ack_id: str, success: bool):
        try:
            request = PushAckRequest.build(ack_id, success)
            self._current_connection.request(request, 3000)
        except NacosException:
            self.logger.error("[%s]Error to send ack response, ack id -> %s"
                              % (self._current_connection.get_connection_id(), ack_id))

    def _send_response(self, response: Response):
        try:
            self._current_connection.send_response(response)
        except NacosException:
            self.logger.error("[%s]Error to send ack response, ackId->%s"
                              % (self._current_connection.get_connection_id(), response.get_request_id()))
