from queue import Queue

import grpc

from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.grpcauto.nacos_grpc_service_pb2_grpc import RequestStub, BiRequestStreamStub
from v2.nacos.remote.connection import Connection
from v2.nacos.remote.grpc.grpc_utils import GrpcUtils
from v2.nacos.remote.requests.request import Request
from v2.nacos.remote.responses.response import Response
from v2.nacos.remote.rpc_client import ServerInfo


class GrpcConnection(Connection):
    def __init__(self, server_info: ServerInfo):
        super().__init__(server_info)
        self.channel = None
        self.request_stub = None
        self.bi_request_stream_stub = None
        self.queue = Queue()  # todo delete?

    def request(self, request: Request, timeout_mills: int) -> Response:
        grpc_request = GrpcUtils.convert_request(request)
        try:
            grpc_response = self.request_stub.request(grpc_request, timeout=timeout_mills/1000)
        except NacosException as e:
            raise NacosException(NacosException.SERVER_ERROR + e)

        response = GrpcUtils.parse(grpc_response)
        if isinstance(response, Response):
            return response

    def send_request(self, request: Request) -> None:
        convert = GrpcUtils.convert_request(request)
        responses = self.bi_request_stream_stub.requestBiStream(iter((convert,)))
        self.queue.put(responses)

    # def request_future(self, request: Request) -> RequestFuture:
    #     pass
    #
    # def async_request(self, request: Request, request_callback: RequestCallBack) -> None:
    #     pass

    def send_response(self, response: Response) -> None:
        convert = GrpcUtils.convert_response(response)
        responses = self.bi_request_stream_stub.requestBiStream(iter((convert,)))
        self.queue.put(responses)

    def close(self) -> None:
        if self.channel:
            self.channel.close()

    def get_channel(self) -> grpc.Channel:
        return self.channel

    def set_channel(self, channel: grpc.Channel) -> None:
        self.channel = channel

    def set_request_stub(self, stub: RequestStub) -> None:
        self.request_stub = stub

    def set_bi_request_stream_stub(self, stub: BiRequestStreamStub) -> None:
        self.bi_request_stream_stub = stub
