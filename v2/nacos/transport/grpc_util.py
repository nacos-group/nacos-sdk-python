import json
import logging
from v2.nacos.common.model.request import IRequest
from v2.nacos.common.model.response import IResponse
from v2.nacos.common.model.request import Request
from v2.nacos.common.model.response import Response
from v2.nacos.utils.net_util import NetUtils
from v2.nacos.transport.proto.nacos_grpc_service_pb2 import Payload, Metadata

class GrpcUtils:

    @staticmethod
    def request_convert_payload(request):
        metadata = Metadata()
        metadata.type = request.get_request_type()
        metadata.headers = request.headers
        metadata.client_ip = NetUtils.get_local_ip()

        request_body = request.get_body()
        payload = Payload(metadata=metadata, body=request_body)
        return payload
    
    @staticmethod
    def response_convert_payload(response):
        metadata = Metadata()
        metadata.type = response.get_request_type()
        metadata.headers = response.headers
        metadata.client_ip = NetUtils.get_local_ip()

        response_body = response.get_body()
        payload = Payload(metadata=metadata, body=response_body)
        return payload

    @staticmethod
    def convert_request_to_payload(request:IRequest):
        metadata = Metadata(
        type=request.get_request_type(),
        headers=request.get_headers(),
        client_ip=NetUtils.get_local_ip()
        )
        body = request.get_body()  
        return Payload(
            metadata=metadata,
            body=body
        )
    
    @staticmethod
    def convert_response_to_payload(response:IResponse):
        metadata = Metadata(
        type=response.get_response_type(),
        client_ip=NetUtils.get_local_ip()
        )
        body = response.get_body()
        return Payload(
            metadata=metadata,
            body=body
        )
    
    @staticmethod
    def parse(payload):
        response = parse_payload_to_response(payload)
        return response
            

def parse_payload_to_response(payload):
    body = payload.body
    response = Response(**body)
    return response