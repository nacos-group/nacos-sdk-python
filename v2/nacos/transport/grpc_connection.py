import asyncio

import grpc

from v2.nacos.common.nacos_exception import NacosException
from v2.nacos.transport.connection import Connection
from v2.nacos.transport.grpc_util import GrpcUtils
from v2.nacos.transport.grpcauto.nacos_grpc_service_pb2 import Payload
from v2.nacos.transport.grpcauto.nacos_grpc_service_pb2_grpc import RequestStub, BiRequestStreamStub
from v2.nacos.transport.model.rpc_request import Request
from v2.nacos.transport.model.rpc_response import Response


class GrpcConnection(Connection):
    def __init__(self, server_info, connection_id, channel, client: RequestStub, bi_stream_client: BiRequestStreamStub):
        super().__init__(connection_id=connection_id, server_info=server_info)
        self.channel = channel
        self.client = client
        self.bi_stream_client = bi_stream_client
        self.queue = asyncio.Queue()

    async def request(self, request: Request, timeout_millis) -> Response:
        payload = GrpcUtils.convert_request_to_payload(request)
        response_payload = await self.client.request(payload, timeout=timeout_millis / 1000.0)
        return GrpcUtils.parse(response_payload)

    def set_channel(self, channel: grpc.Channel) -> None:
        self.channel = channel

    async def close(self) -> None:
        if self.channel:
            await self.channel.close()

    async def send_bi_request(self, payload: Payload) -> None:
        await self.queue.put(payload)

    async def request_payloads(self):
        while True:
            try:
                payload = await self.queue.get()
                yield payload
            except NacosException:
                pass

    def bi_stream_send(self):
        return self.bi_stream_client.requestBiStream(self.request_payloads())
