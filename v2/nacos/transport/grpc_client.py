# 需要大改

from collections import deque
from datetime import timedelta
import json
import certifi
from rpc_client import RpcClient, ServerInfo, RpcClientStatus, IConnectionEventListener
import time
import contextlib
import os
import logging
import ssl
from tls import TLSConfig
import grpc
from grpc import ssl_channel_credentials, aio
import keepalive
# from nacos.common.constant import constants
# import rpc_response
from threading import Lock
from v2.nacos.transport.grpc_connection import GrpcConnection
import v2.nacos.transport.proto.nacos_grpc_service_pb2 as nacos_grpc_service_pb2
import v2.nacos.transport.proto.nacos_grpc_service_pb2_grpc as nacos_grpc_service_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GrpcClient(RpcClient):
    def __init__(self, rpc_client, tls_config, ctx, name: str):
        super().__init__(ctx, name)
        self.rpc_client = rpc_client
        self.tls_config = tls_config

    # ctx如何转为python的实现
    def new_grpc_client(self, ctx, client_name, nacos_server):
        """
        创建并返回一个新的 gRPC 客户端实例。
        :param client_name: 客户端的名称，用于标识客户端。
        :param nacos_server: Nacos服务端(见rpc入参注释)。
        :param tls_config: TLS 配置信息。
        :return: GrpcClient 实例。
        """
        self.rpc_client = RpcClient(
            # 按rpc传参修改
            ctx=None,
            name=client_name,
            label=dict(),
            rpc_client_status=constants.INITIALIZED,
            event_chan=deque(),  # 线程安全的通道
            reconnection_chan=deque(),
            nacos_server=nacos_server,
            mux=Lock(),
            tls_config=self.tls_config
        )
        # RpcClient最后一次活跃的时间戳
        self.rpc_client.lastActiveTimestamp = time.time()

        listeners = [IConnectionEventListener() for _ in range(8)]
        with contextlib.suppress(KeyError):
            self.rpc_client.connectionEventListeners[listeners] = None

        grpc_client = GrpcClient(ctx, self.rpc_client, self.tls_config)
        return grpc_client

    def get_max_call_recv_msg_size(self):
        """
        获取 gRPC 调用接收消息的最大尺寸。
        """
        max_call_recv_msg_size_str = os.getenv("nacos.remote.client.grpc.maxinbound.message.size")
        if max_call_recv_msg_size_str is None:
            return 10 * 1024 * 1024  # 默认值 10MB
        try:
            max_call_recv_msg_size = int(max_call_recv_msg_size_str)
            return max_call_recv_msg_size
        except ValueError:
            return 10 * 1024 * 1024

    def get_initial_window_size(self):
        """
        初始化GRPC传输窗口
        """
        initial_window_size_str = os.getenv("nacos.remote.client.grpc.initial.window.size")
        if initial_window_size_str is None:
            return 10 * 1024 * 1024  # 默认值 10MB
        try:
            initial_window_size = int(initial_window_size_str)
            return initial_window_size
        except ValueError:
            return 10 * 1024 * 1024

    def get_initial_conn_window_size(self):
        """
        初始化连接窗口
        """
        initial_conn_window_size_str = os.getenv("nacos.remote.client.grpc.initial.conn.window.size")
        if initial_conn_window_size_str is None:
            return 10 * 1024 * 1024  # 默认值 10MB
        try:
            initial_conn_window_size = int(initial_conn_window_size_str)
            return initial_conn_window_size
        except ValueError:
            return 10 * 1024 * 1024

    def get_tls_credentials(self, server_info):
        """
        构建用于连接服务器的TLS配置并返回TransportCredentials对象。
        :param server_info: 服务器信息的对象
        :return: TransportCredentials对象
        """
        logger.info("build tls config for connecting to server %s, tlsConfig = %s", server_info['server_ip'],
                    self.tls_config)

        # 获取系统证书池
        cert_pool = ssl.create_default_context().get_ca_certs()
        if not cert_pool:
            raise Exception("load root cert pool fail")

        # 如果配置中指定了CA文件，则加载该文件中的证书
        if self.tls_config.ca_file:
            try:
                with open(self.tls_config['ca_file'], 'rb') as f:
                    ca_cert = f.read()
                    ssl_context = ssl.create_default_context(cadata=ca_cert)
            except Exception as e:
                logger.error("Failed to load CA file: %v", e)
                raise e
        # else:
            # 使用了python库certifi默认的证书
            # ssl_context = ssl.create_default_context(cafile=certifi.where())

        # 设置是否信任所有证书
        ssl_context.check_hostname = not self.tls_config.get('trust_all', False)
        ssl_context.verify_mode = ssl.CERT_REQUIRED if not self.tls_config.get('trust_all', False) else ssl.CERT_NONE

        # 如果配置中指定了客户端证书和私钥文件，则加载这些文件
        if self.tls_config.cert_file and self.tls_config.key_file:
            try:
                ssl_context.load_cert_chain(certfile=self.tls_config.cert_file, keyfile=self.tls_config.key_file)
            except Exception as e:
                logger.error("Failed to load client cert and key: %v", e)
                raise e

        return ssl_context

    def get_initial_grpc_timeout(self):
        """
        获取 gRPC 连接的初始超时时间（毫秒）。

        如果环境变量 "nacos.remote.client.grpc.timeout" 存在，则尝试将其转换为整数。
        如果转换失败，则返回默认的超时时间。
        """
        try:
            # 从环境变量中获取超时时间字符串
            timeout_str = os.getenv("nacos.remote.client.grpc.timeout", str(constants.DEFAULT_TIMEOUT_MILLS))
            # 将字符串转换为整数
            initial_grpc_timeout = int(timeout_str)
        except ValueError:
            # 如果转换失败，返回默认的超时时间
            initial_grpc_timeout = constants.DEFAULT_TIMEOUT_MILLS

        return initial_grpc_timeout

    def get_keep_alive_time_millis(self):
        """
        长连接存活时间keep_alive_time
        """
        try:
            # 从环境变量中获取 keepalive 时间字符串
            keep_alive_str = os.getenv("nacos.remote.grpc.keep.alive.millis", "60000")
            # 将字符串转换为整数
            keep_alive_time_millis = int(keep_alive_str)
        except ValueError:
            # 如果转换失败，使用默认的 keepalive 时间（60秒）
            keep_alive_time_millis = 60 * 1000

        # 60s
        keep_alive_time = timedelta(seconds=keep_alive_time_millis/1000)

        # 创建并返回keepalive，自己写了一个keepalive类参数
        return keepalive.ClientParameters(
            time=keep_alive_time,  # 如果没有活动，每60秒发送一次ping
            timeout=timedelta(seconds=20),  # 等待20秒以接收ping的回应，然后认为连接断开
            permit_without_stream=True  # 即使没有活动流，也发送ping
        )

    async def create_new_connection(self, server_info):
        options = [
            ('grpc.max_receive_message_length', self.get_max_call_recv_msg_size()),
            ('grpc.keepalive_time_ms', self.get_keep_alive_time_millis().time.total_seconds() * 1000),  # 这里要测下时间戳对不对
            ('grpc.initial_window_size', self.get_initial_window_size()),
            ('grpc.initial_connection_window_size', self.get_initial_conn_window_size())
        ]

        self.get_env_tls_config(self.tls_config)
        rpc_port = server_info.get('serverGrpcPort', 0)
        if rpc_port == 0:
            rpc_port = server_info['serverPort'] + self.rpc_client.rpc_port_offset

        if self.tls_config.enable:
            logging.info(f"TLS enabled, trying to connect to server {server_info['serverIp']} with TLS config {self.tls_config}")
            credentials = grpc.ssl_channel_credentials(self.get_tls_credentials(self.tls_config, server_info))
            return await aio.secure_channel(f"{server_info['serverIp']}:{rpc_port}", credentials, options)
        else:
            return await aio.insecure_channel(f"{server_info['serverIp']}:{rpc_port}", options)

    def get_env_tls_config(self, config):
        """
        从环境变量中获取TLS配置。
        :param config: TLSConfig对象
        """
        logger.info("check tls config %s", config)

        # 如果TLS配置已经指定，直接返回
        if config.appointed:
            return

        logger.info("try to get tls config from env")

        # 获取启用TLS的环境变量值
        enable_tls = os.getenv("nacos_remote_client_rpc_tls_enable")
        if enable_tls:
            config.enable = True
            logger.info("get tls config from env, key = enableTls value = %s", enable_tls)

        # 如果未启用TLS，直接返回
        if not config.enable:
            logger.info("tls config from env is not enabled")
            return

        # 获取信任所有证书的环境变量值
        trust_all = os.getenv("nacos_remote_client_rpc_tls_trustAll")
        if trust_all is not None:
            config.trust_all = trust_all.lower() in ['true', '1']
            logger.info("get tls config from env, key = trustAll value = %s", trust_all)

        # 获取CA文件路径的环境变量值
        config.ca_file = os.getenv("nacos_remote_client_rpc_tls_trustCollectionChainPath")
        logger.info("get tls config from env, key = trustCollectionChainPath value = %s", config.ca_file)

        # 获取证书文件路径的环境变量值
        config.cert_file = os.getenv("nacos_remote_client_rpc_tls_certChainFile")
        logger.info("get tls config from env, key = certChainFile value = %s", config.cert_file)

        # 获取私钥文件路径的环境变量值
        config.key_file = os.getenv("nacos_remote_client_rpc_tls_certPrivateKey")
        logger.info("get tls config from env, key = certPrivateKey value = %s", config.key_file)

    # 以上部分上传
    async def connect_to_server(self, server_info):
        conn = await self.create_new_connection(server_info)
        if conn is None:
            raise Exception("gRPC create new connection failed")

        # 有问题
        client = nacos_grpc_service_pb2_grpc.RequestClient(conn)
        response = self.server_check(client)
        if response is None:
            await conn.close()
            raise Exception("Server check request failed")

        server_check_response = response

        # 有问题
        bi_stream_client = nacos_grpc_service_pb2_grpc.BiRequestStreamClient(conn)
        bi_stream_request_client = await bi_stream_client.RequestBiStream(aio.insecure_channel)
        if bi_stream_request_client is None:
            raise Exception("Create biStreamRequestClient failed")

        grpc_conn = GrpcConnection(server_info, server_check_response.connection_id, conn, client, bi_stream_request_client)
        await self.bind_bi_request_stream(bi_stream_request_client, grpc_conn)
        await self.send_connection_setup_request(grpc_conn)

        return grpc_conn

    def send_connection_setup_request(self, grpc_conn):
        """
        发送连接设置请求。
        :param grpc_conn: GrpcConnection对象
        :return: 错误信息或None
        """
        # 创建ConnectionSetupRequest对象
        csr = self.new_connection_setup_request()

        # 设置ConnectionSetupRequest的属性
        csr['client_version'] = '1.0.0'  # constant.CLIENT_VERSION
        csr['tenant'] = self.tenant
        csr['labels'] = self.labels
        csr['client_abilities'] = self.client_abilities

        # 发送请求并处理错误
        err = grpc_conn['bi_stream_send'](self.convert_request(csr))
        if err is not None:
            logger.warning("send connectionSetupRequest error: %s", err)

        # 等待100毫秒
        time.sleep(0.1)

        return err

    def get_connection_type(self):
        """
        获取连接类型。
        :return: 连接类型
        """
        return 'GRPC'

    def rpc_port_offset(self):
        """
        获取RPC端口偏移量。
        :return: RPC端口偏移量
        """
        return constants.RpcPortOffset

    async def bind_bi_request_stream(self, stream_client, grpc_conn):
        async for payload in stream_client:
            if payload:
                self.handle_server_request(payload, grpc_conn)
            else:
                print(f"ConnectionId {grpc_conn.connection_id} stream client closed")

    # def bind_bi_request_stream(self, stream_client, grpc_conn):
    #     """
    #     绑定双向请求流。
    #     :param stream_client: 双向请求流客户端
    #     :param grpc_conn: gRPC连接对象
    #     """
    #
    #     def stream_listener():
    #         while True:
    #             try:
    #                 # 接收服务器发送的数据
    #                 payload = stream_client.recv()
    #                 self.handle_server_request(payload, grpc_conn)
    #             except grpc.RpcError as err:
    #                 # 处理接收错误
    #                 if stream_client.done().is_set():
    #                     logger.warning("connectionId %s stream client close", grpc_conn.get_connection_id())
    #                     break
    #                 running = self.is_running()
    #                 abandon = grpc_conn.get_abandon()
    #                 if running and not abandon:
    #                     if err.code() == grpc.StatusCode.CANCELLED:
    #                         logger.info("connectionId %s request stream onCompleted, switch server",
    #                                     grpc_conn.get_connection_id())
    #                     else:
    #                         logger.error("connectionId %s request stream error, switch server, error=%s",
    #                                      grpc_conn.get_connection_id(), err)
    #                     # 常量字段和雨龙对一下
    #                     if self.rpc_client_status == RpcClientStatus.RUNNING:
    #                         self.rpc_client_status = RpcClientStatus.UNHEALTHY
    #                         self.switch_server_async(ServerInfo(), False)
    #                         break
    #                 else:
    #                     logger.error("connectionId %s received error event, isRunning: %s, isAbandon: %s, error: %s",
    #                                  grpc_conn.get_connection_id(), running, abandon, err)
    #                     break
    #
    #     # 使用线程池执行stream_listener方法
    #     self.executor.submit(stream_listener)

    def server_check(self, client):
        """
        执行服务器检查。
        :param client: 请求客户端
        :return: 服务器检查响应或错误
        """
        response = rpc_response.ServerCheckResponse
        timeout = self.get_initial_grpc_timeout()

        for i in range(31):
            with grpc.insecure_channel("localhost:50051") as channel:
                stub = client(channel)
                request = self.rpc_client.convert_request(self.rpc_client.new_server_check_request())
                try:
                    # 设置上下文超时
                    payload = stub.Request(request, timeout=timeout / 1000.0)
                except grpc.RpcError as e:
                    return None, e

                # 解析响应
                try:
                    response = json.loads(payload.body.value)
                except json.JSONDecodeError as e:
                    return None, e

                # 检查服务器是否准备好
                if 300 <= response.get("error_code", 0) < 400:
                    if i == 30:
                        return None, Exception(
                            "the nacos server is not ready to work in 30 seconds, connect to server failed")
                    time.sleep(1)
                    continue
                break
        return response, None

    def handle_server_request(self, payload, grpc_conn):
        """
        处理服务器请求。
        :param payload: 服务器发送的负载
        :param grpc_conn: gRPC连接对象grpc_connection
        """
        client = self.rpc_client.get_rpc_client()
        payload_type = payload.get("metadata").get("type")

        # 获取处理器映射
        handler_mapping = client.server_request_handler_mapping.get(payload_type)
        if not handler_mapping:
            logger.error("%s Unsupported payload type", grpc_conn.get_connection_id())
            return

        # 获取服务器请求对象并反序列化
        server_request = handler_mapping["server_request"]()
        try:
            json.loads(payload.get("body").get("value"), object_hook=lambda d: server_request.update(d))
        except json.JSONDecodeError as err:
            logger.error("%s Fail to json Unmarshal for request:%s, ackId->%s", grpc_conn.get_connection_id(),
                         server_request.get("request_type"), server_request.get("request_id"))
            return

        # 添加所有头信息到服务器请求对象
        server_request["headers"] = payload.get("metadata").get("headers")

        # 处理请求并发送响应
        response = handler_mapping["handler"].request_reply(server_request, client)
        if not response:
            logger.warning("%s Fail to process server request, ackId->%s", grpc_conn.get_connection_id(),
                           server_request.get("request_id"))
            return

        response["request_id"] = server_request.get("request_id")
        err = grpc_conn.bi_stream_send(grpc_conn.convert_response(response))
        if err and err != EOFError:
            logger.warning("%s Fail to send response:%s,ackId->%s", grpc_conn.get_connection_id(),
                           response.get("response_type"), server_request.get("request_id"))
