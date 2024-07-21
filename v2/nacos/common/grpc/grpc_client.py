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
from nacos.common.constant import constants
import rpc_response
from threading import Lock
from grpc_connection import GrpcConnection
import nacos_grpc_service_pb2
import nacos_grpc_service_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#grpc_client还没改成asyncio
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

  def get_tls_credentials(self, server_inf
                          o):
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