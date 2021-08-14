import json

from google.protobuf.any_pb2 import Any

from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.grpcauto.nacos_grpc_service_pb2 import Payload, Metadata
from v2.nacos.remote.requests.request import Request
from v2.nacos.remote.responses.response import Response
from v2.nacos.utils.net_utils import NetUtils


class GrpcUtils:
    @staticmethod
    def  parse(payload: Payload) -> object:
        metadata_type = payload.metadata.type
        if metadata_type:
            obj = json.loads(payload.body.value.decode('utf-8'))
            if isinstance(obj, Request):
                obj.put_all_header(payload.metadata.headers)
            return obj
        else:
            raise NacosException(NacosException.SERVER_ERROR+"Unknown payload type:"+payload.metadata.type)

    @staticmethod
    def convert_request(request: Request) -> Payload:
        payload_body_bytes = json.dumps(request).encode('utf-8')
        payload_body = Any(value=payload_body_bytes)
        payload_metadata = Metadata(type=request.get_remote_type(), clientIp=NetUtils.get_local_ip(),
                                    headers=request.get_headers())
        payload = Payload(metadata=payload_metadata, body=payload_body)
        return payload

    @staticmethod
    def convert_response(response: Response) -> Payload:
        payload_metadata = Metadata(type=response.get_remote_type())
        payload_body_bytes = bytes(json.dumps(response), encoding='utf-8')
        payload_body = Any(value=payload_body_bytes)
        payload = Payload(metadata=payload_metadata, body=payload_body)
        return payload


