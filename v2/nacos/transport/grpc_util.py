import json

from google.protobuf.any_pb2 import Any

from v2.nacos.ai.model.ai_response import QueryMcpServerResponse, \
    ReleaseMcpServerResponse, McpServerEndpointResponse, QueryAgentCardResponse, \
    ReleaseAgentCardResponse, AgentEndpointResponse
from v2.nacos.common.nacos_exception import NacosException, SERVER_ERROR
from v2.nacos.config.model.config_request import ConfigChangeNotifyRequest
from v2.nacos.config.model.config_response import ConfigPublishResponse, ConfigQueryResponse, \
    ConfigChangeBatchListenResponse, ConfigRemoveResponse
from v2.nacos.naming.model.naming_request import NotifySubscriberRequest
from v2.nacos.naming.model.naming_response import InstanceResponse, \
    SubscribeServiceResponse, BatchInstanceResponse, \
    ServiceListResponse, QueryServiceResponse
from v2.nacos.transport.grpcauto.nacos_grpc_service_pb2 import Payload, Metadata
from v2.nacos.transport.model import ServerCheckResponse
from v2.nacos.transport.model.internal_request import ClientDetectionRequest, \
    SetupAckRequest
from v2.nacos.transport.model.internal_response import ErrorResponse, HealthCheckResponse
from v2.nacos.transport.model.rpc_request import Request
from v2.nacos.transport.model.rpc_response import Response
from v2.nacos.utils.net_util import NetUtils


class GrpcUtils:
    SERVICE_INFO_KEY = "serviceInfo"

    remote_type = {
        "QueryServiceResponse": QueryServiceResponse,
        "ServerCheckResponse": ServerCheckResponse,
        "NotifySubscriberRequest": NotifySubscriberRequest,
        "ErrorResponse": ErrorResponse,
        "InstanceResponse": InstanceResponse,
        "ServiceListResponse": ServiceListResponse,
        "BatchInstanceResponse": BatchInstanceResponse,
        "ClientDetectionRequest": ClientDetectionRequest,
        "HealthCheckResponse": HealthCheckResponse,
        "SubscribeServiceResponse": SubscribeServiceResponse,
        "ConfigPublishResponse": ConfigPublishResponse,
        "ConfigQueryResponse": ConfigQueryResponse,
        "ConfigChangeNotifyRequest": ConfigChangeNotifyRequest,
        "ConfigChangeBatchListenResponse": ConfigChangeBatchListenResponse,
        "ConfigRemoveResponse": ConfigRemoveResponse,
        "SetupAckRequest": SetupAckRequest,
        "QueryMcpServerResponse": QueryMcpServerResponse,
		"McpServerEndpointResponse": McpServerEndpointResponse,
		"ReleaseMcpServerResponse": ReleaseMcpServerResponse,
        "QueryAgentCardResponse": QueryAgentCardResponse,
        "ReleaseAgentCardResponse": ReleaseAgentCardResponse,
        "AgentEndpointResponse": AgentEndpointResponse,
    }

    @staticmethod
    def convert_request_to_payload(request: Request):
        payload_metadata = Metadata(type=request.get_request_type(), clientIp=NetUtils.get_local_ip(),
                                    headers=request.get_headers())

        payload_body_bytes = json.dumps(request, default=GrpcUtils.to_json).encode('utf-8')
        payload_body = Any(value=payload_body_bytes)
        payload = Payload(metadata=payload_metadata, body=payload_body)
        return payload

    @staticmethod
    def convert_response_to_payload(response: Response):
        metadata = Metadata(type=response.get_response_type(), clientIp=NetUtils.get_local_ip())

        payload_body_bytes = json.dumps(response, default=GrpcUtils.to_json).encode('utf-8')
        payload_body = Any(value=payload_body_bytes)
        payload = Payload(metadata=metadata, body=payload_body)
        return payload

    @staticmethod
    def parse(payload: Payload):
        metadata_type = payload.metadata.type
        if metadata_type and metadata_type in GrpcUtils.remote_type.keys():
            json_dict = json.loads(payload.body.value.decode('utf-8'))
            response_class = GrpcUtils.remote_type[metadata_type]
            obj = response_class.model_validate(json_dict)

            if isinstance(obj, Request):
                obj.put_all_headers(payload.metadata.headers)
            return obj
        else:
            raise NacosException(SERVER_ERROR, "unknown payload type:" + payload.metadata.type)

    @staticmethod
    def to_json(obj):
        # Check if object is a Pydantic BaseModel and use model_dump with aliases
        if hasattr(obj, 'model_dump'):
            try:
                # Use model_dump with by_alias=True to convert snake_case to camelCase
                return obj.model_dump(by_alias=True, exclude_none=True)
            except Exception:
                # Fallback to original method if model_dump fails
                pass
        
        # Fallback for non-Pydantic objects or when model_dump fails
        d = {}
        d.update(obj.__dict__)
        return d


def parse_payload_to_response(payload):
    body = payload.body
    response = Response(**body)
    return response
