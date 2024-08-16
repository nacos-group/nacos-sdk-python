import grpc
import logging
from v2.nacos.common.nacos_exception import NacosException
from v2.nacos.transport.connection import Connection
from v2.nacos.transport.grpc_util import GrpcUtils
from v2.nacos.transport.proto.nacos_grpc_service_pb2 import Payload, Metadata

class GrpcConnection(Connection):
    def __init__(self, server_info, connection_id, channel, client, bi_stream_client):
        super().__init__(conn=channel,server_info=server_info,connection_id=connection_id,abandon=False)
        self.client = client
        self.bi_stream_client = bi_stream_client

    def request(self, request, timeout_millis):
        try:
            payload = GrpcUtils.request_convert_payload(request)
            response_payload = yield self.client.request(payload, timeout=timeout_millis / 1000.0)
            return self.parse_response(response_payload)
        except grpc.RpcError as e:
            logging.debug(f"{self.connection_id} grpc request nacos server failed, request={str(request)}, err={e}")
            raise NacosException(str(e)) from e

    def close(self):
        self._conn.close()
