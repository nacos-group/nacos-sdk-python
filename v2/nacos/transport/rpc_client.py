import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, Type, Optional

from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, CLIENT_DISCONNECT, SERVER_ERROR, UN_REGISTER
from v2.nacos.transport.connection import Connection
from v2.nacos.transport.model.internal_request import CONNECTION_RESET_REQUEST_TYPE, \
    CLIENT_DETECTION_REQUEST_TYPE, HealthCheckRequest, ConnectResetRequest
from v2.nacos.transport.model.internal_response import ErrorResponse, ConnectResetResponse
from v2.nacos.transport.model.rpc_request import Request
from v2.nacos.transport.model.server_info import ServerInfo
from v2.nacos.transport.nacos_server_connector import NacosServerConnector
from v2.nacos.transport.server_request_handler import ClientDetectionRequestHandler, IServerRequestHandler
from v2.nacos.utils.common_util import get_current_time_millis


class ConnectionType(Enum):
    GRPC = auto()


class RpcClientStatus(Enum):
    INITIALIZED = auto()
    STARTING = auto()
    UNHEALTHY = auto()
    RUNNING = auto()
    SHUTDOWN = auto()


class ConnectionStatus(Enum):
    DISCONNECTED = auto()
    CONNECTED = auto()


class ConnectionEvent:

    def __init__(self, event_type: ConnectionStatus):
        self.event_type = event_type

    def is_connected(self) -> bool:
        return self.event_type == ConnectionStatus.CONNECTED

    def is_disconnected(self) -> bool:
        return self.event_type == ConnectionStatus.DISCONNECTED

    def __str__(self):
        if self.is_connected():
            return "connected"
        elif self.is_disconnected():
            return "disconnected"
        else:
            return ""


class ReconnectContext:

    def __init__(self, server_info: Optional[ServerInfo], on_request_fail: bool):
        self.on_request_fail = on_request_fail
        self.server_info = server_info


class RpcClient(ABC):
    RETRY_TIMES = 3

    DEFAULT_TIMEOUT_MILLS = 3000

    def __init__(self, logger, name: str):
        self.logger = logger
        self.name = name
        self.labels = {}
        self.current_connection = None
        self.rpc_client_status = None
        self.event_chan = asyncio.Queue()
        self.reconnection_chan = asyncio.Queue()
        self.connection_event_listeners = []
        self.server_request_handler_mapping = {}
        self.nacos_server = None
        self.tenant = None
        self.lock = asyncio.Lock()
        self.last_active_timestamp = get_current_time_millis()

    def put_all_labels(self, labels: Dict[str, str]):
        self.labels.update(labels)
        self.logger.info("[%s]RpcClient init label, labels = %s" % (self.__class__.__name__, self.labels))

    async def event_listener(self):
        while True:
            if self.is_shutdown():
                break
            try:
                event = await self.event_chan.get()
                async with self.lock:
                    listeners = list(self.connection_event_listeners[:])
                if not listeners or len(listeners) == 0:
                    return
                self.logger.info("%s notify %s event to listeners,connectionId:%s ", self.name, str(event),
                                 self.current_connection.get_connection_id())
                for listener in listeners:
                    if event.is_connected():
                        try:
                            await listener.on_connected()
                        except NacosException as e:
                            self.logger.error("%s notify connect listener error, listener = %s,error:%s"
                                              , self.name, listener.__class__.__name__, str(e))
                    if event.is_disconnected():
                        try:
                            await listener.on_disconnect()
                        except NacosException as e:
                            self.logger.error("%s notify disconnect listener error, listener = %s,error:%s"
                                              , self.name, listener.__class__.__name__, str(e))
            except NacosException as e:
                pass

    async def health_check_periodically(self):
        while True:
            if self.is_shutdown():
                break

            await asyncio.sleep(Constants.KEEP_ALIVE_TIME_MILLS / 1000)
            if get_current_time_millis() - self.last_active_timestamp < Constants.KEEP_ALIVE_TIME_MILLS:
                continue

            is_healthy = await self.send_health_check()
            if is_healthy:
                self.last_active_timestamp = get_current_time_millis()
                continue
            else:
                if not self.current_connection:
                    continue

                self.logger.info("%s server healthy check fail, currentConnection=%s"
                                 , self.name, self.current_connection.get_connection_id())

                async with self.lock:
                    rpc_client_status = self.rpc_client_status
                    if rpc_client_status == RpcClientStatus.SHUTDOWN:
                        continue
                    self.rpc_client_status = RpcClientStatus.UNHEALTHY
                    reconnect_ctx = ReconnectContext(server_info=None, on_request_fail=False)
                    await self.reconnect(reconnect_ctx.server_info, reconnect_ctx.on_request_fail)

    async def reconnection_handler(self):
        while True:
            if self.is_shutdown():
                break
            reconnect_ctx = await self.reconnection_chan.get()

            if reconnect_ctx.server_info:
                server_exist = False
                for server_info in self.nacos_server.get_server_list():
                    if reconnect_ctx.server_info.server_ip == server_info.ip_addr:
                        reconnect_ctx.server_info.server_port = server_info.port
                        break

                    if not server_exist:
                        self.logger.info(
                            f"[{self.name}] recommend server is not in server list, ignore recommend server {reconnect_ctx.server_info.get_address()}")
                        reconnect_ctx.server_info = None
            await self.reconnect(reconnect_ctx.server_info, reconnect_ctx.on_request_fail)

    async def start(self):
        async with self.lock:
            self.rpc_client_status = RpcClientStatus.STARTING

        await self.register_server_request_handlers()
        asyncio.create_task(self.event_listener())
        asyncio.create_task(self.reconnection_handler())
        asyncio.create_task(self.health_check_periodically())

        connection = None
        start_up_retry_times = RpcClient.RETRY_TIMES
        while start_up_retry_times > 0 and connection is None:
            try:
                start_up_retry_times -= 1
                server_info = self._next_rpc_server()
                self.logger.info("%s trying to connect to server on start up, server: %s", self.name,
                                 server_info.get_address())
                connection = await self.connect_to_server(server_info)
            except Exception as e:
                self.logger.warning(
                    "%s failed to connect to server on start up, error: %s,start up retry times left :%s",
                    self.name, str(e), start_up_retry_times)

            if connection:
                self.current_connection = connection
                self.logger.info("%s successfully connected to server:%s, connection_id:%s", self.name,
                                 self.current_connection.server_info.get_address(),
                                 self.current_connection.get_connection_id())
                async with self.lock:
                    self.rpc_client_status = RpcClientStatus.RUNNING
                    await self._notify_connection_change(ConnectionStatus.CONNECTED)
            else:
                await self.switch_server_async(None, False)

    @abstractmethod
    async def connect_to_server(self, server_info: ServerInfo) -> Optional[Connection]:
        pass

    @abstractmethod
    def get_connection_type(self):
        pass

    @abstractmethod
    def get_rpc_port_offset(self):
        pass

    def get_current_server(self):
        if self.current_connection:
            return self.current_connection.server_info

    async def switch_server_async(self, server_info: Optional[ServerInfo], on_request_fail: bool):
        await self.reconnection_chan.put(ReconnectContext(server_info=server_info, on_request_fail=on_request_fail))

    def is_wait_initiated(self):
        return self.rpc_client_status == RpcClientStatus.INITIALIZED

    def is_running(self):
        return self.rpc_client_status == RpcClientStatus.RUNNING

    def is_shutdown(self):
        return self.rpc_client_status == RpcClientStatus.SHUTDOWN

    async def _notify_connection_change(self, event_type: ConnectionStatus):
        await self.event_chan.put(ConnectionEvent(event_type))

    async def notify_server_srv_change(self):
        if self.current_connection is None:
            await self.switch_server_async(None, False)
            return

        cur_server_info = self.current_connection.get_server_info()
        found = False
        for server in self.nacos_server.get_server_list():
            if server.ip_addr == cur_server_info.server_ip:
                found = True
                break

        if not found:
            self.logger.info("current connected server %s is not in the latest server list, switch to a new server.",
                             cur_server_info.get_address())
            await self.switch_server_async(None, False)

    async def register_server_request_handlers(self):
        await asyncio.gather(
            self.register_server_request_handler(CONNECTION_RESET_REQUEST_TYPE, ConnectResetRequestHandler(self)),
            self.register_server_request_handler(CLIENT_DETECTION_REQUEST_TYPE, ClientDetectionRequestHandler())
        )

    async def register_server_request_handler(self, request_type: str, handler) -> None:
        if not handler or not request_type:
            self.logger.error(
                "%s register server push request handler missing required parameters, request: %s, handler: %s",
                self.name, request_type, handler.name() if handler else 'None')
            return

        self.logger.info("%s register server push request: %s handler: %s", self.name, request_type, handler.name())

        async with self.lock:
            self.server_request_handler_mapping[request_type] = handler

    async def register_connection_listener(self, listener):
        self.logger.info("%s register connection listener %s to current client", self.name, listener.__class__.__name__)
        async with self.lock:
            self.connection_event_listeners.append(listener)

    def _next_rpc_server(self) -> Optional[ServerInfo]:
        server_config = self.nacos_server.get_next_server()
        return self._resolve_server_info(server_config)

    def _resolve_server_info(self, server_address: str) -> ServerInfo:
        server_port = self.get_rpc_port_offset()
        if Constants.HTTP_PREFIX in server_address:
            split = server_address.rstrip("/").split(Constants.COLON)
            server_ip = split[1].replace("//", "")
            if len(split) > 2 and len(split[2].strip()) > 0:
                server_port += int(split[2])
        else:
            split = server_address.rstrip("/").split(Constants.COLON)
            server_ip = split[0]
            if len(split) > 1 and len(split[1].strip()) > 0:
                server_port += int(split[1])

        server_info = ServerInfo(server_ip, server_port)
        return server_info

    async def request(self, request: Request, timeout_millis: int = DEFAULT_TIMEOUT_MILLS):
        retry_times = 0
        start = get_current_time_millis()
        exception_throw = None
        while retry_times < RpcClient.RETRY_TIMES and get_current_time_millis() < start + timeout_millis:
            wait_reconnect = False
            try:
                if not self.current_connection or not self.is_running():
                    wait_reconnect = True
                    raise NacosException(CLIENT_DISCONNECT,
                                         "client not connected,status:" + str(self.rpc_client_status))
                response = await self.current_connection.request(request, timeout_millis)

                if not response:
                    raise NacosException(SERVER_ERROR, "request failed, response is null")

                if isinstance(response, ErrorResponse):
                    if response.get_error_code() == UN_REGISTER:
                        async with self.lock:
                            wait_reconnect = True
                            self.rpc_client_status = RpcClientStatus.UNHEALTHY
                            self.logger.error("connection is unregistered, switch server, connectionId=%s, request=%s",
                                              self.current_connection.get_connection_id(), request.get_request_type())
                            await self.switch_server_async(None, False)
                    raise NacosException(SERVER_ERROR, response.get_message())
                self.last_active_timestamp = get_current_time_millis()
                return response
            except NacosException as e:
                if wait_reconnect:
                    sleep_time = min(0.1, timeout_millis / 3000)
                    await asyncio.sleep(sleep_time)
                self.logger.error("send request fail, request=%s, retryTimes=%s, errorMessage=%s", request, retry_times,
                                  str(e))
                exception_throw = e
            retry_times += 1

        async with self.lock:
            self.rpc_client_status = RpcClientStatus.UNHEALTHY
        await self.switch_server_async(None, True)
        raise exception_throw

    async def shutdown(self):
        async with self.lock:
            self.rpc_client_status = RpcClientStatus.SHUTDOWN
        await self._close_connection()

    async def _close_connection(self):
        if self.current_connection is not None:
            await self.current_connection.close()
            await self._notify_connection_change(ConnectionStatus.DISCONNECTED)

    async def set_nacos_server_connector(self, nacos_server: NacosServerConnector) -> None:
        if not self.is_wait_initiated():
            return
        self.nacos_server = nacos_server
        async with self.lock:
            self.rpc_client_status = RpcClientStatus.INITIALIZED
        self.logger.info("%s rpcClient init, NacosServerConnector = %s"
                         % (self.__class__.__name__, nacos_server.__class__.__name__))

    async def send_health_check(self):
        if not self.current_connection:
            return False

        health_check_request = HealthCheckRequest()
        try:
            response = await self.current_connection.request(health_check_request, RpcClient.DEFAULT_TIMEOUT_MILLS)
            if not response.is_success():
                # when client request immediately after  server starts, server may not ready to serve new request
                # the server will return code 3xx, tell the client to retry after a while
                # this situation, just return true,because the healthCheck will start again after 5 seconds
                if response.get_error_code() >= 300 and response.get_error_code < 400:
                    return True
                return False
            return response and response.is_success()
        except NacosException as e:
            self.logger.error("health check failed, response is null or not success, err=%s", str(e))
        return False

    async def reconnect(self, server_info: ServerInfo, on_request_fail: bool):
        try:
            recommend_server = server_info
            if on_request_fail and await self.send_health_check():
                self.logger.info("%s server check success, currentServer is %s", self.name,
                                 self.current_connection.server_info.get_address())
                async with self.lock:
                    self.rpc_client_status = RpcClientStatus.RUNNING
                    await self._notify_connection_change(ConnectionStatus.CONNECTED)
                return

            switch_success = False
            reconnect_times, retry_turns = 0, 0

            while not self.is_shutdown() and not switch_success:
                server_info = None
                try:
                    server_info = recommend_server if recommend_server else self._next_rpc_server()
                    connection_new = await self.connect_to_server(server_info)
                    if connection_new:
                        self.logger.info("%s success to connect a server:%s, connectionId:%s", self.name,
                                         server_info.get_address(), connection_new.get_connection_id())
                        if self.current_connection:
                            self.logger.info("%s abandon prev connection, server is:%s, connectionId:%s", self.name,
                                             self.current_connection.server_info.get_address(),
                                             self.current_connection.get_connection_id())
                            self.current_connection.set_abandon(True)
                            await self._close_connection()
                        self.current_connection = connection_new
                        async with self.lock:
                            self.rpc_client_status = RpcClientStatus.RUNNING
                        switch_success = True
                        await self._notify_connection_change(ConnectionStatus.CONNECTED)
                        return

                    if self.is_shutdown():
                        await self._close_connection()

                    last_exception = None

                except NacosException as e:
                    logging.error(f"failed to connect server, error = {str(e)}")
                    last_exception = str(e)
                finally:
                    pass

                if reconnect_times > 0 and reconnect_times % len(self.nacos_server.get_server_list()) == 0:
                    err_info = last_exception if last_exception else "unknown"
                    self.logger.warning(
                        "%s failed to connect to server,after trying %s times,last try server is %s,error:%s",
                        self.name, reconnect_times, server_info.get_address(), str(err_info))
                    if retry_turns < 50:
                        retry_turns += 1

                reconnect_times += 1
                if not self.is_running():
                    await asyncio.sleep(min((retry_turns + 1) / 10, 5))

            if self.is_shutdown():
                self.logger.warning("%s client is shutdown, stop reconnect to server", self.name)
        except NacosException as e:
            self.logger.warning("%s failed to reconnect to server, error is %s", self.name, str(e))


class ConnectResetRequestHandler(IServerRequestHandler):
    def __init__(self, rpc_client: RpcClient):
        self.rpc_client = rpc_client

    def name(self) -> str:
        return "ConnectResetRequestHandler"

    async def request_reply(self, request) -> Optional[ConnectResetResponse]:
        if not isinstance(request, ConnectResetRequest):
            return None

        try:
            with self.rpc_client.lock:
                if self.rpc_client.is_running():
                    if request.server_ip.strip():
                        server_info = ServerInfo(request.server_ip, int(request.server_port))
                        await self.rpc_client.switch_server_async(server_info=server_info,
                                                                  on_request_fail=False)
                    else:
                        await self.rpc_client.switch_server_async(server_info=ServerInfo("", 0),
                                                                  on_request_fail=True)
                    return ConnectResetResponse()
        except NacosException as e:
            self.rpc_client.logger.error("rpc client %s failed to switch server,error:%s", self.rpc_client.name, e)
        return
