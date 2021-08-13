import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from threading import RLock, Thread
import queue
from abc import ABCMeta, abstractmethod
from typing import Dict

from nacos.commons import synchronized_with_attr
from v2.nacos.common.constants import Constants
from v2.nacos.common.lifecycle.closeable import Closeable
from v2.nacos.common.utils import get_current_time_millis
from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.remote.requests.connect_reset_request import ConnectResetRequest
from v2.nacos.remote.responses.connect_reset_response import ConnectResetResponse
from v2.nacos.remote.responses.error_response import ErrorResponse
from v2.nacos.remote.utils import rpc_client_status
from v2.nacos.common import constants
from v2.nacos.remote.iserver_list_factory import ServerListFactory
from v2.nacos.ability.client_abilities import ClientAbilities
from v2.nacos.remote.iserver_request_handler import ServerRequestHandler
from v2.nacos.remote.connection import Connection
from v2.nacos.remote.responses.response import Response
from v2.nacos.remote.requests.request import Request
from v2.nacos.remote.requests.health_check_request import HealthCheckRequest
from v2.nacos.remote.irequest_future import RequestFuture


class ServerInfo:
    def __init__(self, server_ip=None, server_port=None):
        self._server_ip = server_ip
        self._server_port = server_port

    def get_address(self):
        return self._server_ip + constants.Constants.COLON + self._server_port

    def get_server_ip(self):
        return self._server_ip

    def set_server_ip(self, server_ip):
        self._server_ip = server_ip

    def get_server_port(self):
        return self._server_port

    def set_server_port(self, server_port):
        self._server_port = server_port

    def __str__(self):
        return "{serverIp='" + self._server_ip + "', server main port=" + self._server_port + "}"


class ConnectionEvent:
    CONNECTED = 1
    DISCONNECTED = 0

    def __init__(self, event_type: int):
        self.event_type = event_type

    def is_connected(self) -> bool:
        return self.event_type == ConnectionEvent.CONNECTED

    def is_disconnected(self) -> bool:
        return self.event_type == ConnectionEvent.DISCONNECTED


class ReconnectContext:
    def __init__(self, server_info: ServerInfo, on_request_fail: bool):
        self.server_info = server_info
        self.on_request_fail = on_request_fail


class RpcClient(metaclass=ABCMeta, Closeable):
    RETRY_TIMES = 3
    DEFAULT_TIMEOUT_MILLS = 3000

    def __init__(self, name: str = None, server_list_factory: ServerListFactory = None):
        logging.basicConfig()
        self.logger = logging.getLogger(__name__)

        self.__server_list_factory = server_list_factory
        self._event_linked_blocking_queue = queue.Queue()

        self.lock = RLock()
        self._rpc_client_status = rpc_client_status["WAIT_INIT"]

        self._client_event_executor = None
        self.__reconnection_signal = queue.Queue()
        self._current_connection = None
        self._labels = {}
        self.__name = name
        self.__tenant = ""
        self._client_abilities = None

        self.__last_active_time_stamp = get_current_time_millis()
        self.__keep_alive_time = 5000

        self._connection_event_listeners = []
        self._server_request_handlers = []

        if server_list_factory:
            with self.lock:
                self._rpc_client_status = rpc_client_status["INITIALIZED"]
            self.logger.info("RpcClient init in constructor, ServerListFactory = %s"
                             % server_list_factory.__class__.__name__)

    def set_client_abilities(self, client_abilities: ClientAbilities) -> None:
        self._client_abilities = client_abilities

    def get_client_abilites(self) -> ClientAbilities:
        return self._client_abilities

    def set_server_list_factory(self, server_list_factory: ServerListFactory) -> None:
        if not self.is_wait_initiated():
            return
        self.__server_list_factory = server_list_factory
        with self.lock:
            self._rpc_client_status = rpc_client_status["INITIALIZED"]
        self.logger.info("[%s]RpcClient init, ServerListFactory = %s"
                         % (self.__name, server_list_factory.__class__.__name__))
        return

    def set_labels(self, labels: Dict[str, str]) -> None:
        self._labels.update(labels)
        self.logger.info("[%s]RpcClient init label, labels = %s"
                         % (self.__name, self._labels))

    def notify_disconnected(self) -> None:
        if not self._connection_event_listeners:
            return
        self.logger.info("[%s]Notify disconnected event to listeners" % self.__name)
        for connection_event_listener in self._connection_event_listeners:
            try:
                connection_event_listener.on_disconnect()
            except NacosException:
                self.logger.error("[%s]Notify disconnect listener error, listener = %s"
                                  % self.__name, connection_event_listener.__class__.__name__)

    def notify_connected(self) -> None:
        if not self._connection_event_listeners:
            return
        self.logger.info("[%s]Notify connected event to listeners" % self.__name)
        for connection_event_listener in self._connection_event_listeners:
            try:
                connection_event_listener.on_connected()
            except NacosException:
                self.logger.error("[%s]Notify connect listener error, listener = %s"
                                  % self.__name, connection_event_listener.__class__.__name__)

    def is_wait_initiated(self) -> bool:
        return self._rpc_client_status == rpc_client_status["WAIT_INIT"]

    def is_running(self) -> bool:
        return self._rpc_client_status == rpc_client_status["RUNNING"]

    def is_shutdown(self) -> bool:
        return self._rpc_client_status == rpc_client_status["SHUTDOWN"]

    def on_server_list_change(self) -> None:
        if self._current_connection and self._current_connection.server_info:
            server_info = self._current_connection.server_info
            found = False
            for server_address in self.__server_list_factory.get_server_list():
                if self.resolve_server_info(server_address).get_address().lower() == server_info.get_address().lower():
                    found = True
                    break
            if not found:
                self.logger.info("Current connected server %s is not in latest server list, switch switchServerAsync"
                                 % server_info.get_address())
                self.switch_server_async()

    def start(self) -> None:
        with self.lock:
            self._rpc_client_status = rpc_client_status["STARTING"]

        self._client_event_executor = ThreadPoolExecutor(max_workers=2)
        self._client_event_executor.submit(self._start_connect())
        self._client_event_executor.submit(self._start_reconnect())

        connect_to_server = None  # Connection()
        with self.lock:
            self._rpc_client_status = rpc_client_status["STARTING"]

        start_up_retry_times = RpcClient.RETRY_TIMES
        while start_up_retry_times > 0 and (not connect_to_server):
            try:
                start_up_retry_times -= 1
                server_info = self.next_rpc_server()
                self.logger.info("[%s]Try to connect to server on start up, server:%s"
                                 % (self.__name, server_info))
                connect_to_server = self.connect_to_server(server_info)
            except NacosException as e:
                self.logger.warning("[%s]Fail to connect to server on start up, error message=%s, start up "
                                    "retry times left:%s" % (self.__name, e, start_up_retry_times))

        if connect_to_server:
            self.logger.info("[%s]Success to connect to server [%s] on start up, connectionId=%s"
                             % (self.__name, connect_to_server.get_server_info().get_address()
                                , connect_to_server.get_connection_id))
            self._current_connection = connect_to_server
            with self.lock:
                self._rpc_client_status = rpc_client_status["RUNNING"]
            self._event_linked_blocking_queue.put(ConnectionEvent.CONNECTED)
        else:
            self.switch_server_async()

        self.register_server_request_handler(ConnectResetRequestHandler())

    def shutdown(self) -> None:
        self.logger.info("Shutdown rpc client, set status to shutdown")
        with self.lock:
            self._rpc_client_status = rpc_client_status["SHUTDOWN"]
        self.logger.info("Shutdown client event executor " + self._client_event_executor)
        self._client_event_executor.shutdown()
        self.logger.info("Close current connection " + self._current_connection.get_connection_id())
        self.close_connection(self._current_connection)

    def _start_connect(self):
        while True:
            if self.is_shutdown():
                break
            try:
                take = self._event_linked_blocking_queue.get()
                if take.is_connected():
                    self.notify_connected()
                elif take.is_disconnected():
                    self.notify_disconnected()
            except NacosException:
                pass

    def _start_reconnect(self):
        while True:
            try:
                if self.is_shutdown():
                    break
                reconnect_context = self.__reconnection_signal.get(block=True, timeout=self.__keep_alive_time / 1000)
                if not reconnect_context:
                    if get_current_time_millis() - self.__last_active_time_stamp >= self.__keep_alive_time:
                        is_healthy = self.health_check()
                        if not is_healthy:
                            if not self._current_connection:
                                continue
                            self.logger.info("[%s]Server healthy check fail, currentConnection=%s"
                                             % (self.__name, self._current_connection.get_connection_id))
                            if self._rpc_client_status == rpc_client_status["SHUTDOWN"]:
                                break
                            with self.lock:
                                self._rpc_client_status = rpc_client_status["UNHEALTHY"]
                            reconnect_context = ReconnectContext(None, False)
                        else:
                            self.__last_active_time_stamp = get_current_time_millis()
                            continue
                    else:
                        continue

                if reconnect_context.server_info:
                    server_exist = False
                    for server in self.get_server_list_factory().get_server_list():
                        server_info = self.resolve_server_info(server)
                        if server_info.get_server_ip() == reconnect_context.server_info.get_server_ip():
                            server_exist = True
                            reconnect_context.server_info.set_server_port(server_info.get_server_port())
                            break

                    if not server_exist:
                        self.logger.info("[%s]Recommend server is not in server list, ignore recommend server %s"
                                         % (self.__name, reconnect_context.server_info.get_address()))
                self.reconnect(reconnect_context.server_info, reconnect_context.on_request_fail)
            except NacosException:
                pass

    def health_check(self) -> bool:
        health_check_request = HealthCheckRequest()
        if not self._current_connection:
            return False
        try:
            response = self._current_connection.request(health_check_request, 3000)
            return response and response.is_success()
        except NacosException:
            pass
        return False

    def switch_server_async_on_request_fail(self) -> None:
        self._switch_server_async(None, True)

    # def switch_server_async(self):
    #     self._switch_server_async(None, False)

    # def _switch_server_async(self, recommend_server_info, on_request_fail) -> None:
    #     self.__reconnection_signal.put(ReconnectContext(recommend_server_info, on_request_fail))

    def switch_server_async(self, recommend_server_info=None, on_request_fail=False) -> None:
        self.__reconnection_signal.put(ReconnectContext(recommend_server_info, on_request_fail))

    def reconnect(self, recommend_server_info, on_request_fail) -> None:
        try:
            recommend_server = recommend_server_info
            if on_request_fail and self.health_check():
                self.logger.info("[%s]Server check success, currentServer is %s"
                                 % (self.__name, self._current_connection.server_info.get_address()))
                with self.lock:
                    self._rpc_client_status = rpc_client_status["RUNNING"]
                return

            switch_success = False
            reconnect_times = 0
            retry_turns = 0
            while (not switch_success) and (not self.is_shutdown()):
                server_info = None
                try:
                    server_info = [recommend_server if recommend_server else self.next_rpc_server()]
                    connection_new = self.connect_to_server(server_info)
                    if connection_new:
                        self.logger.info("[%s]Success to connect to a server [%s], connectionId=%s"
                                         % (self.__name, server_info.get_address(), connection_new.get_connection_id()))
                        if self._current_connection:
                            self.logger.info("[%s]Abandon previous connection, server is %s, connectionId is %s"
                                             % (self.__name, self._current_connection.server_info.get_address(),
                                                self._current_connection.get_connection_id()))
                            self._current_connection.set_abandon(True)
                            self.close_connection(self._current_connection)

                        self._current_connection = connection_new
                        with self.lock:
                            self._rpc_client_status = rpc_client_status["RUNNING"]
                        switch_success = True
                        self._event_linked_blocking_queue.put(ConnectionEvent(ConnectionEvent.CONNECTED))
                        return

                    if self.is_shutdown():
                        self.close_connection(self._current_connection)
                except NacosException:
                    pass
                finally:
                    recommend_server = None

                if reconnect_times > 0 and reconnect_times % len(self.__server_list_factory.get_server_list()) == 0:
                    self.logger.info("[%s]fail to connect to server, after trying %s times, last try server is %s"
                                     % (self.__name, reconnect_times, server_info))
                    if retry_turns == sys.maxsize:
                        retry_turns = 50
                    else:
                        retry_turns += 1

                reconnect_times += 1

                try:
                    if not self.is_running():
                        # first round ,try servers at a delay 100ms;second round ,200ms;
                        # max delays 5s. to be reconsidered.
                        time.sleep(min((retry_turns + 1) / 10, 5))

                except NacosException:
                    pass

            if self.is_shutdown():
                self.logger.info("[%s]Client is shutdown, stop reconnecting to server"
                                 % self.__name)

        except NacosException as e:
            self.logger.warning("[%s]Fail to reconnect to server, error is %s"
                                % (self.__name, e))

    def close_connection(self, connection: Connection) -> None:
        if connection:
            connection.close()
            self._event_linked_blocking_queue.put(ConnectionEvent(ConnectionEvent.DISCONNECTED))

    @abstractmethod
    def get_rpc_port_offset(self):
        pass

    @abstractmethod
    def get_connection_type(self):
        pass

    def get_current_server(self) -> ServerInfo:
        if self._current_connection:
            return self._current_connection.server_info

    def request(self, request: Request, timeout_mills: int = None) -> Response:
        if not timeout_mills:
            timeout_mills = RpcClient.DEFAULT_TIMEOUT_MILLS
        retry_times = 0
        response = None
        start = get_current_time_millis()
        exception_throw = None
        while retry_times < RpcClient.RETRY_TIMES and get_current_time_millis() < timeout_mills + start:
            wait_reconnect = False
            try:
                if not self._current_connection or not self.is_running():
                    wait_reconnect = True
                    raise NacosException("Client not connected, current status:" + self._rpc_client_status)
                response = self._current_connection.request(request, timeout_mills)
                if not response:
                    raise NacosException("Unknown Exception")

                if isinstance(response, ErrorResponse):
                    if response.get_error_code() == NacosException.UN_REGISTER:
                        with self.lock:
                            wait_reconnect = True
                            self._rpc_client_status = rpc_client_status["UNHEALTHY"]
                        self.logger.error("Connection is unregistered, swith server, connectionId=%s, request=%s"
                                          % (self._current_connection.get_connection_id(),
                                             request.__class__.__name__))
                        self.switch_server_async()
                    raise NacosException

                self.__last_active_time_stamp = get_current_time_millis()
                return response

            except NacosException as e:
                if wait_reconnect:
                    try:
                        time.sleep(min(0.1, timeout_mills / 3000))
                    except NacosException:
                        pass
                self.logger.error("Send request fail, request=%s, retryTimes=%s, errorMessage=%s"
                                  % (request, retry_times, e))
                exception_throw = e

            retry_times += 1

        with self.lock:
            self._rpc_client_status = rpc_client_status["UNHEALTHY"]
        self.switch_server_async_on_request_fail()

        raise exception_throw

    # def async_request(self, request: Request, callback: RequestCallBack) -> None:
    #     pass

    def request_future(self, request: Request) -> RequestFuture:
        retry_times = 0
        start = get_current_time_millis()
        while retry_times < RpcClient.RETRY_TIMES and \
                get_current_time_millis() < start + RpcClient.DEFAULT_TIMEOUT_MILLS:
            wait_reconnect = False
            try:
                if not self._current_connection or not self.is_running():
                    wait_reconnect = True
                    raise NacosException("Client not connected")
                return self._current_connection.requestFuture(request)
            except NacosException as e:
                if wait_reconnect:
                    try:
                        time.sleep(0.1)
                    except NacosException:
                        pass
                self.logger.error("[%s]Send request fail, request=%s, retryTimes=%s, errorMessage=%s"
                                  % (self.__name, request, retry_times, e))

            retry_times += 1

        with self.lock:
            self._rpc_client_status = rpc_client_status["UNHEALTHY"]
        self.switch_server_async_on_request_fail()

        raise NacosException

    @abstractmethod
    def connect_to_server(self, server_info: ServerInfo) -> Connection:
        pass

    def handle_server_request(self, request) -> Response:
        self.logger.info("[%s]receive server push request, request=%s, requestId=%s"
                         % (self.__name, request.__class__.__name__, request.get_request_id()))
        self.__last_active_time_stamp = get_current_time_millis()
        for server_request_handler in self._server_request_handlers:
            try:
                response = server_request_handler.request_reply(request)
                if response:
                    self.logger.info("[%s]ack server push request, request=%s, requestId=%s"
                                     % (self.__name, request.__class__.__name__, request.get_request_id()))
                    return response
            except NacosException as e:
                self.logger.info("[%s]handleServerRequest:%s, errorMessage=%s"
                                 % (self.__name, server_request_handler.__class__.__name__, e))

    @synchronized_with_attr("lock")
    def register_connection_listener(self, connection_event_listener) -> None:
        self.logger.info("[%s]Register connection listener to current client:%s"
                         % (self.__name, connection_event_listener.__class__.__name__))
        self._connection_event_listeners.append(connection_event_listener)

    @synchronized_with_attr("lock")
    def register_server_request_handler(self, server_request_handler) -> None:
        self.logger.info("[%s]Register server push request handler:%s"
                         % (self.__name, server_request_handler.__class__.__name__))
        self._server_request_handlers.append(server_request_handler)

    def get_name(self) -> str:
        return self.__name

    def set_name(self, name: str) -> None:
        self.__name = name

    def get_server_list_factory(self) -> ServerListFactory:
        return self.__server_list_factory

    def next_rpc_server(self) -> ServerInfo:
        server_address = self.get_server_list_factory().gen_next_server()
        return self.resolve_server_info(server_address)

    def current_rpc_server(self) -> ServerInfo:
        server_address = self.get_server_list_factory().get_current_server()
        return self.resolve_server_info(server_address)

    def resolve_server_info(self, server_address: str) -> ServerInfo:
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

    def get_labels(self) -> Dict[str, str]:
        return self._labels

    def get_tenant(self) -> str:
        return self.__tenant

    def set_tenant(self, tenant: str) -> None:
        self.__tenant = tenant


class ConnectResetRequestHandler(ServerRequestHandler):

    def __init__(self, rpc_client: RpcClient):
        self._rpc_client = rpc_client

    def request_reply(self, request: Request) -> Response:
        if isinstance(request, ConnectResetRequest):
            try:
                with self._rpc_client.lock:
                    if self._rpc_client.is_running():
                        if request.get_server_ip().strip():
                            server_info = self._rpc_client.resolve_server_info(
                                request.get_server_ip() + Constants.COLON + request.get_server_port()
                            )
                            self._rpc_client.switch_server_async(server_info, False)
                        else:
                            self._rpc_client.switch_server_async()
            except NacosException as e:
                self._rpc_client.logger.error("[%s]Switch server error, %s" %
                                              (self._rpc_client.get_name(), e))
            return ConnectResetResponse()

        return
