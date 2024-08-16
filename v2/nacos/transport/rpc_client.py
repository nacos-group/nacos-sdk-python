import time
import random
import logging
from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import Dict, Any
import asyncio
from v2.nacos.common.model import request
from v2.nacos.common.model import response
from v2.nacos.common.model import error_response
from v2.nacos.transport.model import internal_request
from v2.nacos.transport.connection import IConnection
from v2.nacos.common.constants import Constants
from v2.nacos.utils import common_util
from v2.nacos.transport.nacos_server_connector import NacosServerConnector
from v2.nacos.transport import server_request_handler
from v2.nacos.transport.model.server_info import ServerInfo


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


class ServerRequestHandlerMapping:

    def __init__(self, server_request, handler):
        self.server_request = server_request
        self.handler = handler


class ReconnectContext:

    def __init__(self, on_request_fail, server_info):
        self.on_request_fail = on_request_fail
        self.server_info = server_info


class RpcClient:

    def __init__(self, name: str, nacos_server):
        self.name = name
        self.labels = {}
        self.current_connection: IConnection = None
        self.rpc_client_status = RpcClientStatus.INITIALIZED
        self.event_chan = asyncio.Queue()
        self.reconnection_chan = asyncio.Queue()
        self.connection_event_listeners = []  
        self.nacos_server = None  
        self.server_request_handler_mapping = {}
        
        self.client_abilities = None
        self.tenant = None
        self.lock = asyncio.Lock()
        self.last_active_timestamp = common_util.get_current_time_millis()

    def put_all_labels(self, labels: Dict[str, str]):
        self.labels.update(labels)

    async def event_listener(self):
        while True:
            if self.is_shutdown(): 
                return
            try:
                event = await self.event_chan.get()
                self._notify_connection_event(event)
            except Exception as e:
                pass

    async def health_check_delay(self):
        await asyncio.sleep(5)

    async def reconnection_handler(self):
        while True:
            try:
                if self.is_shutdown(): 
                    return
                reconnect = None
                async def get_reconnection_chan_with_timout(queue,timeout):
                    try:
                        return await asyncio.wait_for(queue.get(), timeout)
                    except asyncio.TimeoutError:
                        print("Timeout occurred while trying to get from the queue")
                        return None
                reconnect = await get_reconnection_chan_with_timout(self.reconnection_chan,5)
                if not reconnect:
                    if common_util.get_current_time_millis() - self.last_active_timestamp >= Constants.KEEP_ALIVE_TIME:
                        if not self.health_check():
                            if not self.current_connection:
                                logging.info(f"[{self.name}] Server healthy check fail, currentConnection = {self.current_connection}")
                            async with self.lock:
                                rpc_client_status = self.rpc_client_status
                            if rpc_client_status == RpcClientStatus.SHUTDOWN:
                                break
                            if self._compare_and_swap_status(rpc_client_status, RpcClientStatus.UNHEALTHY):
                                reconnect = ReconnectContext(on_request_fail=False)
                            else:
                                continue
                        else:
                            self.last_active_timestamp = common_util.get_current_time_millis()
                    else:
                        continue

                if reconnect.server_info:
                    server_exist = False
                    for _, v in self.nacos_server.get_server_list():
                        if reconnect.server_info.server_ip == v.ip_addr:
                            reconnect.server_info.server_port == v.port
                            reconnect.server_info.server_grpc_port == v.grpc_port
                            server_exist = True
                            break
                        if not server_exist:
                            logging.info(f"[{self.name}] Recommend server is not in server list, ignore recommend server {reconnect.server_info.get_address()}")
                            reconnect.server_info = None
                self.reconnect(reconnect.server_info,reconnect.on_request_fail)
            except Exception as e:
                pass
    
    def connect_to_server(self, server_info):
        pass
            

    async def start(self):
        if not self._compare_and_swap_status(RpcClientStatus.INITIALIZED,
                                             RpcClientStatus.STARTING):
            return
        self.register_server_request_handlers()
        asyncio.create_task(self.event_listener())
        asyncio.create_task(self.reconnection_handler())
        connect_to_server = None
        async with self.lock:
            self.rpc_client_status = RpcClientStatus.STARTING
        start_up_retry_times = Constants.MAX_RETRY
        while start_up_retry_times >= 0 and connect_to_server is None:
            try:
                start_up_retry_times -= 1
                server_info = self._next_rpc_server()
                logging.info(
                    f"[RpcClient.Start] {self.name} trying to connect to server on start up, server: {server_info}"
                )
                connect_to_server = self.connect_to_server(
                    server_info) 
            except Exception as e:
                logging.warning(
                        f"[RpcClient.Start] {self.name} failed to connect to server on start up, error message={e}, start up retry times left={start_up_retry_times}")

        if connect_to_server :
            logging.info(
                f"{self.name} successfully connected to server {self.current_connection.get_server_info()}, connection_id={self.current_connection.get_connection_id()}"
            )
            self.current_connection = connect_to_server
            async with self.lock:
                self.rpc_client_status = RpcClientStatus.RUNNING
            self._notify_connection_change(ConnectionStatus.CONNECTED)
        else:
            self._switch_server_async(ServerInfo(), False)

    
    async def is_wait_initiated(self):
        async with self.lock:
            rpc_client_status = self.rpc_client_status
        return rpc_client_status == RpcClientStatus.INITIALIZED

    async def is_running(self):
        async with self.lock:
            rpc_client_status = self.rpc_client_status
        return rpc_client_status == RpcClientStatus.RUNNING

    async def is_shutdown(self):
        async with self.lock:
            rpc_client_status = self.rpc_client_status
        return rpc_client_status == RpcClientStatus.SHUTDOWN

    def _notify_connection_change(self, event_type: ConnectionStatus):
        self.event_chan.put(ConnectionEvent(event_type))

    def notify_server_srv_change(self):
        if self.current_connection is None:
            self._switch_server_async(ServerInfo(), False)
            return

        cur_server_info = self.current_connection.get_server_info()
        found = False
        for server in self.nacos_server.get_server_list():  
            if server.ip_addr == cur_server_info.server_ip:
                found = True
                break

        if not found:
            logging.info(
                f"Current connected server {cur_server_info.server_ip}:{cur_server_info.server_port} is not in the latest server list, switch to a new server."
            )
            self._switch_server_async(ServerInfo(), False)

    def register_server_request_handlers(self):
        self.register_server_request_handler(
            internal_request.ConnectResetRequest(),
            server_request_handler.ConnectResetRequestHandler())

        self.register_server_request_handler(
            internal_request.ClientDetectionRequest(),
            server_request_handler.ClientDetectionRequestHandler())

    async def register_server_request_handler(
            self, request: request.IRequest,
            handler: server_request_handler.IServerRequestHandler) -> None:
        
        request_instance = request
        request_type = request_instance.get_request_type()

        
        if not handler or not request_type:
            logging.error(
                f"{self.name} register server push request handler missing required parameters, request: {request_type}, handler: {handler.name() if handler else 'None'}"
            )
            return

        logging.debug(
            f"{self.name} register server push request: {request_type} handler: {handler.name()}"
        )

        async with self.lock:
            self.server_request_handler_mapping[
                request_type] = ServerRequestHandlerMapping(request, handler)

    async def register_connection_listener(self, listener):

        logging.debug(
            f"{self.name} register connection listener [{type(listener).__name__}] to current client"
        )

       
        async with self.lock:
            self.connection_event_listeners.append(listener)

    async def _compare_and_swap_status(self, expected: RpcClientStatus,
                                       new: RpcClientStatus) -> bool:
        async with self.lock:
            if self.rpc_client_status == expected:
                self.rpc_client_status = new
                return True
        return False

    def _next_rpc_server(self) -> ServerInfo:
        # Placeholder for getting the next server info
        
        server_config = self.nacos_server.get_next_server()
        if server_config:
            return ServerInfo(
                server_ip=server_config.ip_addr,
                server_port=server_config.port,
                server_grpc_port=server_config.grpc_port  
            )
        return ServerInfo()

    async def request(self, request: request.IRequest,
                      timeout_millis: int):
        retry_times = 0
        start = common_util.get_current_time_millis()  

        while (retry_times < Constants.REQUEST_DOMAIN_RETRY_TIME) and (timeout_millis < 0 or common_util.get_current_time_millis() < start + timeout_millis):
            wait_reconnect = False
            try:
                if not self.current_connection or not await self.is_running():
                    wait_reconnect = True
                    raise
                response = self.current_connection.request(
                    request, timeout_millis)  
                if not response:
                    raise

                if isinstance(response, error_response.ErrorResponse):
                    if response.get_error_code() == Constants.UN_REGISTER:
                        async with self.lock:
                            wait_reconnect = True  
                            if self._compare_and_swap_status(
                                    RpcClientStatus.RUNNING,
                                    RpcClientStatus.UNHEALTHY):
                                logging.error(
                                    "Connection is unregistered, switch server, connectionId=%s, request=%s",
                                    self.current_connection.get_connection_id(),
                                    request.get_request_type())
                                self._switch_server_async(ServerInfo(), False)
                    raise
                self.last_active_timestamp = common_util.get_current_time_millis()
                return response
            except Exception as e:
                if wait_reconnect:
                    try:
                        sleep_time = min(100, timeout_millis // 3)
                        await asyncio.sleep(sleep_time/1000)
                    except Exception:
                        pass

        async with self.lock:
            if self._compare_and_swap_status(RpcClientStatus.RUNNING,
                                             RpcClientStatus.UNHEALTHY):
                self._switch_server_async(ServerInfo(), True)

        return None

    async def shutdown(self):
        async with self.lock:
            self.rpc_client_status = RpcClientStatus.SHUTDOWN  
        self._close_connection()

    def _close_connection(self):
        if self.current_connection is not None:
            self.current_connection.close()
            self._notify_connection_change(ConnectionStatus.DISCONNECTED)

    async def _notify_connection_event(self, event: 'ConnectionEvent'):
        async with self.lock:
            listeners = list(self.connection_event_listeners[:])
        if not listeners or len(listeners) == 0:
            return
        logging.info(f"{self.name} notify {str(event)} event to listeners")
        for _, v in listeners:
            if event.is_connected():
                v.on_connected()
            if event.is_disconnected():
                v.on_dis_connected()
    
    async def health_check(self):
        health_check_request = internal_request.HealthCheckRequest().new_health_check_request()
        if not self.current_connection:
            return False
        re_try_times = Constants.MAX_RETRY
        random.seed()  
        while re_try_times >= 0:
            re_try_times -= 1
            try:
                if re_try_times > 1:
                    await asyncio.sleep(random.randint(0, 500) / 1000.0)  
                response = self.current_connection.request(health_check_request, Constants.DEFAULT_TIMEOUT_MILLS)
                return response.is_success() and not response is None 
            except Exception as e:
                # 忽略异常
                pass
        return False

    async def reconnect(self, server_info: ServerInfo, on_request_fail: bool):
        try:
            if on_request_fail and self._send_health_check():
                logging.info(
                    f"{self.name} server check success, currentServer is {self.current_connection.get_server_info()}"
                )
                async with self.lock:
                    self.rpc_client_status = RpcClientStatus.RUNNING
                self._notify_connection_change(ConnectionStatus.CONNECTED)
                return
 
            switch_success = False
            re_connect_times, retry_turns = 0, 0

            while not await self.is_shutdown() and not switch_success:
                server_info = None
                try:
                    server_info = self._next_rpc_server()
                    connection_new = self.connect_to_server(
                        server_info)
                    if connection_new:
                        logging.info(f"[{self.name}] Success to connect a server [{server_info.get_address()}], connectionId = {connection_new.get_connection_id()}")
                        if self.current_connection:
                            logging.info(f"[{self.name}] Abandon prev connection, server is {self.current_connection.server_info.get_address()}, connectionId is {self.current_connection.get_connection_id()}")
                            self.current_connection.set_abandon(True)
                            self._close_connection()
                        self.current_connection = connection_new
                        async with self.lock:
                            self.rpc_client_status = RpcClientStatus.RUNNING
                        switch_success = True
                        self._notify_connection_change(ConnectionStatus.CONNECTED)
                        return

                    if self.is_shutdown():
                        self._close_connection()
                    
                    last_exception = None
                
                except Exception as e:
                    logging.error(f"Fail to connect server, error = {str(e)}")
                    last_exception = str(e)
                finally:
                    pass

                if not self.nacos_server.get_server_list():
                    raise

                if re_connect_times > 0 and re_connect_times % len(
                        self.nacos_server.get_server_list()) == 0:
                    err_info = last_exception if last_exception else "unknown"
                    logging.warning(
                        f"{self.name} fail to connect server, after trying {re_connect_times} times, last try server is {server_info}, error={err_info}"
                    )
                    if retry_turns < 50:
                        retry_turns += 1

                re_connect_times += 1
                if not await self.is_running():
                    sleep_time = min(retry_turns, 50) * 100
                    time.sleep(sleep_time / 1000)

            if await self.is_shutdown():
                logging.warning(
                    f"{self.name} client is shutdown, stop reconnect to server")
        except Exception as e:
            logging.warning(f"[{self.name}] Fail to reconnect to server, error is {str(e)}")

    def _switch_server_async(self, recommend_server_info: ServerInfo,
                             on_request_fail: bool):
        self.reconnection_chan.put(
            ReconnectContext(recommend_server_info, on_request_fail))


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


class IServerRequestHandler(ABC):

    @abstractmethod
    def handle(self, request: Any):
        pass


if __name__ == "__main__":
    client = RpcClient("example_client")
    client.start()
