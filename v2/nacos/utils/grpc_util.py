import json
from ..common.model.request import Request
from ..common.payload_registry import PayloadRegistry
from ..transport.proto.nacos_grpc_service.proto import Payload, Metadata

class GrpcUtils:
    def __init__(self, logger):
        self.logger = logger

    def convert(self, request, meta=None):
        metadata = Metadata()
        if meta is not None:
            metadata.headers = request.headers.copy()
            metadata.type = request.__class__.__name__
        else:
            metadata.type = request.__class__.__name__
            metadata.headers = request.headers
        metadata.client_ip = metadata.local_ip()

        request_body = self.convert_request_to_byte(request)
        payload = Payload(metadata=metadata, body=request_body)
        return payload

    def convert_request_to_byte(self, request):
        request_headers = request.headers.copy()
        request.clear_headers()
        json_bytes = json.dumps(request)
        request.headers.update(request_headers)
        return json_bytes

    def parse(self, payload):
        class_type = PayloadRegistry.get_class_by_type(payload.metadata.type)
        if class_type is not None:
            byte_string = payload.body
            obj = json.loads(byte_string)
            if isinstance(obj, Request):
                obj.headers = payload.metadata.headers
            return obj
        else:
            self.logger.error("Unknown payload type:" + payload.metadata.type)