#这个文件需要重点修
from .connection import IConnection
from .remote import rpc_request
from .remote import rpc_response
from .remote import naming_response
from .remote import internal_request
from connection_event_listener import IConnectionEventListener
from ...common.constant.const import Const
from ...util import commom
import server_request_handler
import os
import time
import math
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import Dict, Callable, Any
import asyncio
from asyncio import Lock


class ConnectionType(Enum):
    GRPC = auto()


class RpcClientStatus(Enum):
    INITIALIZED = auto()  #硬编码1234也可以
    STARTING = auto()
    UNHEALTHY = auto()
    RUNNING = auto()
    SHUTDOWN = auto()


class ConnectionStatus(Enum):
    DISCONNECTED = auto()
    CONNECTED = auto()


def wait_reconnect(timeout_millis, retry_times: int,
                   request: rpc_request.IRequest
                   ):  #这里的err需要更改一下,retry_times原来用的指针，python需要回传
    logging.error(
        f"Send request fail, request={request.get_request_type()}, body={request.get_body()}, retryTimes={retry_times}"
    )
    sleep_time = min(100, int(timeout_millis / 3))
    time.sleep(sleep_time / 1000.0)  # 将毫秒转换为秒
    retry_times += 1
    return retry_times
    


class IRpcClient(ABC):

    @abstractmethod
    def connect_to_server(self):
        pass

    @abstractmethod
    def get_connection_type(self):
        pass

    @abstractmethod
    def put_all_labels(self):
        pass

    @abstractmethod
    def rpc_port_offset(self):
        pass

    @abstractmethod
    def get_rpc_client(self):
        pass


class ServerInfo:  #缺一个默认初始值

    def __init__(self, server_ip: str, server_port: int,
                 server_grpc_port: int):
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_grpc_port = server_grpc_port

    def __eq__(self, other):
        if isinstance(other, ServerInfo):
            return self.__dict__ == other.__dict__
        return False 


class ServerRequestHandlerMapping:

    def __init__(self, server_request, handler):
        self.server_request = server_request
        self.handler = handler


class ReconnectContext:

    def __init__(self, on_request_fail, server_info):
        self.on_request_fail = on_request_fail
        self.server_info = server_info


class ClientMap:

    def __init__(self):
        self.client_map = {}


class RpcClient:

    def __init__(self, name: str):
        self.ctx = asyncio.get_running_loop()
        self.name = name
        self.labels = {}
        self.current_connection: IConnection = None
        self.rpc_client_status = RpcClientStatus.INITIALIZED
        self.event_chan = asyncio.Queue()
        self.reconnection_chan = asyncio.Queue()
        self.connection_event_listeners = []  #需要原子操作
        self.last_active_timestamp = None  #需要原子操作
        self.execute_client: IRpcClient = None
        self.nacos_server = None  #nacos_server，固定为本地服务器
        self.server_request_handler_mapping = {}
        #少了这两个
        self.client_abilities = None
        self.tenant = None
        self.lock = asyncio.Lock()  #mux
        self.loop = asyncio.get_event_loop()
        # 使用 asyncio.Queue 来模拟 Go 中的 channel

    # def get_name(self):
    #     return self.name

    def put_all_labels(self, labels: Dict[str, str]):
        self.labels.update(labels)

    def get_rpc_client(self) -> 'RpcClient':
        return self

    async def event_listener(self):
        while True:
            if self.ctx.is_closed():  #这个判断实现原来的done，return
                break
            try:
                # 使用 asyncio.wait_for 设置超时，以检查是否需要停止
                event = await asyncio.wait_for(self.event_chan.get(),
                                               timeout=1)  #时间需要斟酌
                await self._notify_connection_event(event)
            except asyncio.TimeoutError:
                # 这里检查是否需要停止事件循环
                pass

    async def health_check_delay(self):
        # await asyncio.sleep(5)
        # await self.health_check()
        await asyncio.gather(asyncio.sleep(5), self.health_check())

    async def reconnection_handler(self):
        # self.health_check_timer = asyncio.create_task(self.health_check_delay())
        while True:
            if self.ctx.is_closed():  #这个判断实现原来的done，return
                break
            done, pending = await asyncio.wait(
                [
                    self.reconnection_chan.get(),
                    asyncio.ensure_future(self.health_check_delay()),
                    asyncio.ensure_future(
                        self.nacos_server.notify_server_src_change())  #这里需要改
                ],
                return_when=asyncio.FIRST_COMPLETED)

            if self.reconnection_chan.get() in done:
                rc = await self.reconnection_chan.get()  #这里的await感觉有点多余
                if rc.server_info != ServerInfo():
                    server_exist = False
                    for server in self.nacos_server.get_server_list():
                        if rc.server_info.server_ip == server.server_ip:
                            rc.server_info.serve_port = server.server_port
                            rc.server_info.server_grpc_port = server.server_grpc_port
                            server_exist = True
                            break
                    if not server_exist:
                        logging.info(
                            f"{self.name} recommend server is not in server list, ignore recommend server {rc.serverInfo}"
                        )
                        rc.serverInfo = ServerInfo()
                await self.reconnect(rc.server_info, rc.on_request_fail)

            elif asyncio.ensure_future(self.health_check_delay()) in done:
                # timer = asyncio.sleep(5)  # Reset the timer
                # await self.health_check()
                pass

            elif asyncio.ensure_future(
                    self.nacos_server.notify_server_src_change()) in done:
                await self.notify_server_srv_change()

            for task in pending:
                task.cancel()

    def start(self):
        if not self._compare_and_swap_status(RpcClientStatus.INITIALIZED,
                                             RpcClientStatus.STARTING):
            return
        self.register_server_request_handlers()
        # threading.Thread(target=self._handle_events).start()
        # threading.Thread(target=self._reconnect_loop).start()
        self.loop.create_task(self.event_listener())
        self.loop.create_task(self.reconnection_handler())

        current_connection: IConnection = None
        start_up_retry_times = Const.REQUEST_DOMAIN_RETRY_TIME
        while start_up_retry_times > 0 and self.current_connection is None:
            start_up_retry_times -= 1
            try:
                server_info = self._next_rpc_server()
                logging.info(
                    f"[RpcClient.Start] {self.name} trying to connect to server on start up, server: {server_info}"
                )
                connection, err = self.execute_client.connect_to_server(
                    server_info)  #err要改
                if err:
                    logging.warning(
                        f"[RpcClient.Start] {self.name} failed to connect to server on start up, error message={err}, start up retry times left={start_up_retry_times}"
                    )
                else:
                    self.current_connection = connection
                    break
            except Exception as e:
                logging.error(f"[RpcClient.nextRpcServer], error: {e}")
                break

        if self.current_connection is not None:
            logging.info(
                f"{self.name} successfully connected to server {self.current_connection.get_server_info()}, connection_id={self.current_connection.get_connection_id()}"
            )
            self.current_connection = self.current_connection
            self.rpc_client_status = RpcClientStatus.RUNNING
            self._notify_connection_change(ConnectionStatus.CONNECTED)
        else:
            self._switch_server_async(ServerInfo(), False)

    #补充几个基础函数
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

    # def _handle_events(self):
    #     while True:
    #         event = self.event_chan.pop(0) if self.event_chan else None
    #         if event:
    #             self._notify_connection_event(event)

    # def _reconnect_loop(self):
    #     timer = threading.Timer(5, self._health_check)
    #     timer.start()
    #     while True:
    #         reconnect_context = self.reconnection_chan.pop(0) if self.reconnection_chan else None
    #         if reconnect_context:
    #             self._reconnect(reconnect_context)
    #         time.sleep(1)

    def _notify_connection_change(self, event_type: ConnectionStatus):
        self.event_chan.put(ConnectionEvent(event_type))

    def notify_server_srv_change(self):
        if self.current_connection is None:
            self._switch_server_async(ServerInfo(), False)
            return

        cur_server_info = self.current_connection.get_server_info()
        found = False
        for server in self.nacos_server.get_server_list():  #这里测试时可以固定为本地
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
            self, request: rpc_request.IRequest,
            handler: server_request_handler.IServerRequestHandler) -> None:
        # 使用request函数创建请求实例
        request_instance = request
        request_type = request_instance.get_request_type()

        # 检查handler是否为None或request_type是否为空
        if not handler or not request_type:
            logging.error(
                f"{self.name} register server push request handler missing required parameters, request: {request_type}, handler: {handler.name() if handler else 'None'}"
            )
            return

        # 记录调试信息
        logging.debug(
            f"{self.name} register server push request: {request_type} handler: {handler.name()}"
        )

        # 存储请求处理程序映射
        async with self.lock:
            self.server_request_handler_mapping[
                request_type] = ServerRequestHandlerMapping(request, handler)

    async def register_connection_listener(self, listener):
        # if not isinstance(listener, IConnectionEventListener):
        #     raise TypeError("listener must be an instance of IConnectionEventListener")

        logging.debug(
            f"{self.name} register connection listener [{type(listener).__name__}] to current client"
        )

        # 将监听器添加到列表中
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
        #这里还需要细改
        server_config = self.nacos_server.get_next_server()
        if server_config:
            return ServerInfo(
                server_ip=server_config.ip_addr,
                server_port=server_config.port,
                server_grpc_port=server_config.grpc_port  # 使用get方法提供默认值
            )
        return ServerInfo()

    async def request(self, request: rpc_request.IRequest,
                      timeout_millis: int):
        retry_times = 0
        start = commom.current_millis()  # 转换成毫秒
        # current_err = None

        while retry_times < Const.REQUEST_DOMAIN_RETRY_TIME and commom.current_millis(
        ) * 1000 < start + timeout_millis:
            if not self.current_connection or not await self.is_running():
                retry_times = wait_reconnect(timeout_millis, retry_times,
                                             request)
                continue
            try:
                response = self.current_connection.request(
                    request, timeout_millis)  #判断err的机制得改，可以用try代替
            except Exception as err:
                retry_times = wait_reconnect(timeout_millis, retry_times,
                                             request)
                continue

            if isinstance(response, naming_response.ErrorResponse):
                if response.get_error_code() == Const.UN_REGISTER:
                    async with self.lock:  #锁要改
                        if self._compare_and_swap_status(
                                RpcClientStatus.RUNNING,
                                RpcClientStatus.UNHEALTHY):
                            logging.info(
                                "Connection is unregistered, switch server, connectionId=%s, request=%s",
                                self.current_connection.get_connection_id(),
                                request.get_request_type())
                            self._switch_server_async(ServerInfo(), False)
                retry_times = wait_reconnect(timeout_millis, retry_times,
                                             request)
                continue

            if response and not response.is_success():
                logging.warn(
                    "%s request received fail response, error code: %d, result code: %d, message: [%s]",
                    request.get_request_type(), response.get_error_code(),
                    response.get_result_code(), response.get_message())
            async with self.lock:
                self.last_active_timestamp = time.time()
            return response

        async with self.lock:
            if self._compare_and_swap_status(RpcClientStatus.RUNNING,
                                             RpcClientStatus.UNHEALTHY):
                self._switch_server_async(ServerInfo(), True)

        return None

    async def shutdown(self):
        async with self.lock:
            self.rpc_client_status = RpcClientStatus.SHUTDOWN  #这边可能有点问题 设置状态需要原子化 考虑用multiprocessing.Value实现
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
        tasks = [
            listener.on_connected()
            if event.is_connected() else listener.on_disconnect()
            for listener in listeners
        ]
        # await asyncio.gather(*tasks) #这里需要斟酌一下

    async def health_check(self):
        async with self.lock:
            last_active_time = self.last_active_timestamp  #需要判断一下None
        if last_active_time is not None and (
                time.time() - last_active_time.timestamp()
        ) < Const.KEEP_ALIVE_TIME:  #这里时间格式可能需要改变
            return

        if await self._send_health_check():
            async with self.lock:
                self.last_active_timestamp = time.time()
            return
        else:
            if self.current_connection is None or await self.is_shutdown():
                return

            logging.info(
                f"{self.name} server healthy check fail, current_connection={self.current_connection.get_connection_id()}"
            )
            async with self.lock:
                self.rpc_client_status = RpcClientStatus.UNHEALTHY
            reconnect_context = ReconnectContext(
                server_info=None, on_request_fail=True)  #server_info设置默认值比较好

        await self.reconnect(reconnect_context.server_info,
                             reconnect_context.on_request_fail)
        # await asyncio.sleep(constant.KEEP_ALIVE_TIME)

    def _send_health_check(self) -> bool:
        if self.current_connection is None:
            return False
        try:
            response = self.current_connection.request(
                internal_request.HealthCheckRequest().new_health_check_request(
                ), Const.DEFAULT_TIMEOUT_MILLS)
        except Exception as err:
            logging.error("client send_health_check failed, err=%s", str(err))
            return False

        if not response.is_success():
            if 300 <= response.get_error_code() < 400:
                return True
            return False
        return True

    async def reconnect(self, server_info: ServerInfo, on_request_fail: bool):
        if on_request_fail and self._send_health_check():
            logging.info(
                f"{self.name} server check success, currentServer is {self.current_connection.get_server_info()}"
            )
            async with self.lock:
                self.rpc_client_status = RpcClientStatus.RUNNING
            self._notify_connection_change(ConnectionStatus.CONNECTED)
            return

        server_info_flag = False  #这里要确认一下
        re_connect_times, retry_turns = 0, 0
        err = None
        if server_info == ServerInfo():
            server_info_flag = True
            logging.info(
                f"{self.name} try to re connect to a new server, server is not appointed, will choose a random server."
            )

        while not await self.is_shutdown():
            if server_info_flag:
                try:
                    server_info = self._next_rpc_server()
                except Exception as err:
                    logging.error(
                        f"[RpcClient.next_rpc_server], err: {str(err)}")
                    break
            try:
                connection_new = self.execute_client.connect_to_server(
                    server_info)
            except Exception as err:
                logging.error(
                    f"[RpcClient.execute_client.next_rpc_server], err: {str(err)}"
                )
            if connection_new:
                logging.info(
                    f"{self.name} success to connect a server {server_info}, connectionId={connection_new.get_connection_id()}"
                )

                if self.current_connection:
                    logging.info(
                        f"{self.name} abandon prev connection, server is {server_info}, connectionId is {self.current_connection.get_connection_id()}"
                    )
                    self.current_connection.set_abandon(True)
                    self._close_connection()
                self.current_connection = connection_new
                async with self.lock:
                    self.rpc_client_status = RpcClientStatus.RUNNING
                self._notify_connection_change(ConnectionStatus.CONNECTED)
                return

            if self.is_shutdown():
                self._close_connection()

            if re_connect_times > 0 and re_connect_times % len(
                    self.nacos_server.get_server_list()) == 0:
                logging.warning(
                    f"{self.name} fail to connect server, after trying {re_connect_times} times, last try server is {server_info}, error={err}"
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

    def _switch_server_async(self, recommend_server_info: ServerInfo,
                             on_request_fail: bool):
        self.reconnection_chan.put(
            ReconnectContext(recommend_server_info, on_request_fail))


class ConnectionEvent:

    def __init__(self, event_type: ConnectionStatus):
        # self.event_type = event_type
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
