import json

from google.protobuf.any_pb2 import Any
from dacite import from_dict

from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.grpcauto.nacos_grpc_service_pb2 import Payload, Metadata
from v2.nacos.remote.requests.request import Request
from v2.nacos.remote.responses.response import Response
from v2.nacos.utils.net_utils import NetUtils
from v2.nacos.remote.responses import *
from v2.nacos.remote.requests import *


class GrpcUtils:
    @staticmethod
    def parse(payload: Payload) -> object:
        metadata_type = payload.metadata.type
        if metadata_type:
            # todo: how to deal with json_dict ?
            # method-1
            # json_dict = json.loads(payload.body.value.decode('utf-8'))
            # obj = from_dict(data_class=eval(metadata_type), data=json_dict)
            # if isinstance(obj, Request):
            #     obj.put_all_header(payload.metadata.headers)

            # method-2
            json_dict = json.loads(payload.body.value.decode('utf-8'))
            obj = eval(metadata_type+"(**json_dict)")
            if isinstance(obj, Request):
                obj.put_all_header(payload.metadata.headers)
            return obj
        else:
            raise NacosException(NacosException.SERVER_ERROR+"Unknown payload type:"+payload.metadata.type)

    @staticmethod
    def convert_request(request: Request) -> Payload:
        payload_body_bytes = json.dumps(request, default=GrpcUtils.to_json).encode('utf-8')
        # payload_body_bytes = request.json().encode('utf-8') # error
        payload_body = Any(value=payload_body_bytes)
        payload_metadata = Metadata(type=request.get_remote_type(), clientIp=NetUtils().get_local_ip(),
                                    headers=request.get_headers())
        payload = Payload(metadata=payload_metadata, body=payload_body)
        return payload

    @staticmethod
    def convert_response(response: Response) -> Payload:
        payload_metadata = Metadata(type=response.get_remote_type())
        payload_body_bytes = bytes(json.dumps(response, default=GrpcUtils.to_json), encoding='utf-8')
        # payload_body_bytes = bytes(response.json(), encoding='utf-8')
        payload_body = Any(value=payload_body_bytes)
        payload = Payload(metadata=payload_metadata, body=payload_body)
        return payload

    @staticmethod
    def to_json(obj):
        d = {}
        d.update(obj.__dict__)
        return d



