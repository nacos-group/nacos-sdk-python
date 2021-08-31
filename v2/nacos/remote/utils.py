remote_constants = {
    "LABEL_SOURCE": "source",
    "LABEL_SOURCE_SDK": "sdk",
    "LABEL_SOURCE_CLUSTER": "cluster",
    "LABEL_MODULE": "module",
    "LABEL_MODULE_CONFIG": "config",
    "LABEL_MODULE_NAMING": "naming"
}

rpc_client_status = {
    "WAIT_INIT": 0,
    "INITIALIZED": 1,
    "STARTING": 2,
    "UNHEALTHY": 3,
    "RUNNING": 4,
    "SHUTDOWN": 5
}

remote_connection_type = {
    "GRPC": 0,
    "RSOCKET": 1,
    "TB_REMOTEING": 2
}

remote_request_type = {
    "ConfigPublish": "ConfigPublishRequest",
    "ConfigRemove": "ConfigRemoveRequest",
    "ConfigQuery": "ConfigQueryRequest",
    "ConfigBatchListen": "ConfigBatchListenRequest",
    "NamingHeartBeat": "HeartBeatRequest",
    "NamingInstance": "InstanceRequest",
    "NamingServiceQuery": "ServiceQueryRequest",
    "NamingServiceList": "ServiceListRequest",
    "NamingNotifySubscriber": "NotifySubscriberRequest",
    "NamingSubscribeService": "SubscribeServiceRequest",
    "ConnectionSetup": "ConnectionSetupRequest",
    "ServerCheck": "ServerCheckRequest",
    "ConfigReSync": "ConfigReSyncRequest",
    "ConfigChangeNotify": "ConfigChangeNotifyRequest",
    "PushAck": "PushAckRequest",
    "ConnectReset": "ConnectResetRequest",
    "HealthCheck": "HealthCheckRequest",
    "ClientDetection": "ClientDetectionRequest"
}

remote_response_type = {
    "ConfigPublish": "ConfigPublishResponse",
    "ConfigChangeBatchListen": "ConfigChangeBatchListenResponse",
    "ConfigChangeNotify": "ConfigChangeNotifyResponse",
    "ConfigQuery": "ConfigQueryResponse",
    "ConfigRemove": "ConfigRemoveResponse",
    "SubscribeService": "SubscribeServiceResponse",
    "QueryService": "QueryServiceResponse",
    "ServiceList": "ServiceListResponse",
    "Instance": "InstanceResponse",
    "ConnectionUnregister": "ConnectionUnregisterResponse",
    "ConfigReSync": "ConfigReSyncResponse",
    "Error": "ErrorResponse",
    "ServerCheck": "ServerCheckResponse",
    "ConnectReset": "ConnectResetResponse",
    "HealthCheck": "HealthCheckResponse",
    "ClientDetection": "ClientDetectionResponse",
    "NotifySubscriber": "NotifySubscriberResponse"
}

response_code = {
    "success": 200,
    "fail": 500
}


class ConnectionType:
    GRPC = "GRPC"
