# nacos-sdk-python v3

[English](README.md) | 简体中文

Nacos OpenAPI 的 Python 实现。

参考: https://nacos.io/zh-cn/docs/open-API.html

[![Pypi Version](https://badge.fury.io/py/nacos-sdk-python.svg)](https://badge.fury.io/py/nacos-sdk-python)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/nacos-group/nacos-sdk-python/blob/master/LICENSE)

### 支持的 Python 版本

Python 3.7+

### 支持的 Nacos 版本

支持 Nacos 3.x 及以上版本

**注意：** AI Client 功能需要 Nacos 服务端 3.1.0 或更高版本。

## 安装

```shell
 pip install nacos-sdk-python
```

## 客户端配置

```python
from v2.nacos import NacosNamingService, NacosConfigService, NacosAIService, ClientConfigBuilder, GRPCConfig, \
    Instance, SubscribeServiceParam, RegisterInstanceParam, DeregisterInstanceParam, \
    BatchRegisterInstanceParam, GetServiceParam, ListServiceParam, ListInstanceParam, ConfigParam
    
client_config = (ClientConfigBuilder()
                 .access_key(os.getenv('NACOS_ACCESS_KEY'))
                 .secret_key(os.getenv('NACOS_SECRET_KEY'))
                 .server_address(os.getenv('NACOS_SERVER_ADDR', 'localhost:8848'))
                 .log_level('INFO')
                 .grpc_config(GRPCConfig(grpc_timeout=5000))
                 .build())
```

* *server_address* - **必填** - Nacos 服务器地址
* *access_key* - 阿里云 accessKey，用于身份验证
* *secret_key* - 阿里云 secretKey，用于身份验证
* *credentials_provider* - 自定义访问密钥管理器
* *username* - 用于身份验证的用户名
* *password* - 用于身份验证的密码
* *log_level* - 日志级别 | 默认值: `logging.INFO`
* *cache_dir* - 缓存目录路径 | 默认值: `~/nacos/cache`
* *log_dir* - 日志目录路径 | 默认值: `~/logs/nacos`
* *namespace_id* - 命名空间 ID | 默认值: ``
* *grpc_config* - gRPC 配置
  * *max_receive_message_length* - gRPC 最大接收消息长度 | 默认值: 100 * 1024 * 1024
  * *max_keep_alive_ms* - gRPC 最大保活时间(毫秒) | 默认值: 60 * 1000
  * *initial_window_size* - gRPC 初始窗口大小 | 默认值: 10 * 1024 * 1024
  * *initial_conn_window_size* - gRPC 初始连接窗口大小 | 默认值: 10 * 1024 * 1024
  * *grpc_timeout* - gRPC 超时时间(毫秒) | 默认值: 3000
* *tls_config* - TLS 配置
  * *enabled* - 是否启用 TLS
  * *ca_file* - CA 证书文件路径
  * *cert_file* - 证书文件路径
  * *key_file* - 密钥文件路径
* *kms_config* - 阿里云 KMS 配置
  * *enabled* - 是否启用阿里云 KMS
  * *endpoint* - 阿里云 KMS 端点
  * *access_key* - 阿里云 accessKey
  * *secret_key* - 阿里云 secretKey
  * *password* - 阿里云 KMS 密码

## 配置客户端

```python
config_client = await NacosConfigService.create_config_service(client_config)
```

### 配置客户端通用参数

> `param: ConfigParam`

* `param` *data_id* 数据 ID
* `param` *group* 分组，如果未指定分组则使用 `DEFAULT_GROUP`
* `param` *content* 配置内容
* `param` *tag* 配置标签
* `param` *app_name* 应用名称
* `param` *beta_ips* Beta 测试 IP 地址
* `param` *cas_md5* MD5 校验码
* `param` *type* 配置类型
* `param` *src_user* 源用户
* `param` *encrypted_data_key* 加密数据密钥
* `param` *kms_key_id* KMS 加密数据密钥 ID
* `param` *usage_type* 使用类型

### 获取配置

```python
content = await config_client.get_config(ConfigParam(
            data_id=data_id,
            group=group
        ))
```

* `param` *ConfigParam* 配置客户端通用参数。获取配置时，需要在 param 中指定必填的 data_id 和 group
* `return` 成功时返回配置内容，失败时抛出异常

按以下优先级获取配置项的值：

* 步骤 1 - 从本地故障转移目录获取

* 步骤 2 - 从服务器获取，直到获取到值或尝试所有服务器
    * 从服务器获取后，内容将保存到快照目录

* 步骤 3 - 从快照目录获取

### 添加监听器

```python
async def config_listener(tenant, data_id, group, content):
    print("listen, tenant:{} data_id:{} group:{} content:{}".format(tenant, data_id, group, content))

await config_client.add_listener(dataID, groupName, config_listener)
```

* `param` *ConfigParam* 配置客户端通用参数
* `listener` *listener* 配置监听器，由 namespace_id、group、data_id、content 定义
* `return`

为指定的配置项添加监听器。

* 一旦配置项发生变化或删除，将调用回调函数
* 如果配置项在服务器中已存在，回调函数将被调用一次
* 回调函数从当前进程调用

### 移除监听器

```python
await client.remove_listener(dataID, groupName, config_listener)
```

* `param` *ConfigParam* 配置客户端通用参数
* `return` 成功时返回 True，失败时抛出异常

从指定的键移除监听器。

### 发布配置

```python
res = await client.publish_config(ConfigParam(
            data_id=dataID,
            group=groupName,
            content="Hello world")
        )
```

* `param` *ConfigParam* 配置客户端通用参数。发布配置时，需要在 param 中指定必填的 data_id、group 和 content
* `return` 成功时返回 True，失败时抛出异常

向 Nacos 发布一个配置数据项。

* 如果数据键不存在，首先创建一个
* 如果数据键存在，更新为指定的内容
* 内容不能设置为 None，如果需要删除配置项，请使用 **remove** 函数

### 删除配置

```python
res = await client.remove_config(ConfigParam(
            data_id=dataID,
            group=groupName
        ))
```

* `param` *ConfigParam* 配置客户端通用参数。删除配置时，需要在 param 中指定必填的 data_id 和 group
* `return` 成功时返回 True，失败时抛出异常

从 Nacos 删除一个配置数据项。

### 停止配置客户端

```python
await client.shutdown()
```

## 命名客户端

```python
naming_client = await NacosNamingService.create_naming_service(client_config)
```

### 注册实例

```python
response = await client.register_instance(
            request=RegisterInstanceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', ip='1.1.1.1',
                port=7001, weight=1.0, cluster_name='c1', metadata={'a': 'b'},
                enabled=True,
                healthy=True, ephemeral=True))
```

### 批量注册实例

```python
param1 = RegisterInstanceParam(service_name='nacos.test.1',
                                       group_name='DEFAULT_GROUP',
                                       ip='1.1.1.1',
                                       port=7001,
                                       weight=1.0,
                                       cluster_name='c1',
                                       metadata={'a': 'b'},
                                       enabled=True,
                                       healthy=True,
                                       ephemeral=True
                                       )
param2 = RegisterInstanceParam(service_name='nacos.test.1',
                               group_name='DEFAULT_GROUP',
                               ip='1.1.1.1',
                               port=7002,
                               weight=1.0,
                               cluster_name='c1',
                               metadata={'a': 'b'},
                               enabled=True,
                               healthy=True,
                               ephemeral=True
                               )
param3 = RegisterInstanceParam(service_name='nacos.test.1',
                               group_name='DEFAULT_GROUP',
                               ip='1.1.1.1',
                               port=7003,
                               weight=1.0,
                               cluster_name='c1',
                               metadata={'a': 'b'},
                               enabled=True,
                               healthy=False,
                               ephemeral=True
                               )
response = await client.batch_register_instances(
    request=BatchRegisterInstanceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP',
                                       instances=[param1, param2, param3]))
```

### 注销实例

```python
response = await client.deregister_instance(
          request=DeregisterInstanceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', ip='1.1.1.1',
                                          port=7001, cluster_name='c1', ephemeral=True)
      )
```

### 更新实例

```python
response = await client.update_instance(
            request=RegisterInstanceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', ip='1.1.1.1',
                                          port=7001, weight=2.0, cluster_name='c1', metadata={'a': 'b'},
                                          enabled=True,
                                          healthy=True, ephemeral=True))
```

### 获取服务

```python
service = await client.get_service(
            GetServiceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', cluster_name='c1'))
```

### 列出服务

```python
service_list = await client.list_services(ListServiceParam())
```

### 列出实例

```python
instance_list = await client.list_instances(ListInstanceParam(service_name='nacos.test.1', healthy_only=True))
instance_list = await client.list_instances(ListInstanceParam(service_name='nacos.test.1', healthy_only=False))
instance_list = await client.list_instances(ListInstanceParam(service_name='nacos.test.1', healthy_only=None))
```

### 订阅服务

```python
async def cb(instance_list: List[Instance]):
  print('received subscribe callback', str(instance_list))

await client.subscribe(
  SubscribeServiceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', subscribe_callback=cb))
```

### 取消订阅服务

```python
async def cb(instance_list: List[Instance]):
  print('received subscribe callback', str(instance_list))

await client.unsubscribe(
            SubscribeServiceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', subscribe_callback=cb))
```

### 停止命名客户端

```python
await client.shutdown()
```

## AI 客户端

**重要提示：** AI Client 功能需要 Nacos 服务端 3.1.0 或更高版本。

```python
from v2.nacos import NacosAIService, ClientConfigBuilder

client_config = (ClientConfigBuilder()
                 .server_address(os.getenv('NACOS_SERVER_ADDR', 'localhost:8848'))
                 .build())
                 
ai_client = await NacosAIService.create_ai_service(client_config)
```

### MCP Server 管理

Nacos 提供了对 MCP (Model Context Protocol) Server 的管理能力，包括注册、发现和订阅，支持 MCP Server 的动态注册和服务发现。

#### 获取 MCP Server

```python
from v2.nacos.ai.model.ai_param import GetMcpServerParam

mcp_server = await ai_client.get_mcp_server(
    GetMcpServerParam(mcp_name='my-mcp-server', version='1.0.0')
)
```

* `param` *GetMcpServerParam* 获取 MCP Server 信息的参数
  * `mcp_name` - 要查询的 MCP Server 名称（必填）
  * `version` - 要查询的 MCP Server 版本（可选）
* `return` 成功时返回 McpServerDetailInfo，失败时抛出异常

#### 发布 MCP Server

```python
from v2.nacos.ai.model.ai_param import ReleaseMcpServerParam
from v2.nacos.ai.model.mcp.mcp import McpServerBasicInfo, ServerVersionDetail

server_spec = McpServerBasicInfo(
    name='my-mcp-server',
    description='My MCP Server',
    protocol='http',
    versionDetail=ServerVersionDetail(version='1.0.0')
)

result = await ai_client.release_mcp_server(
    ReleaseMcpServerParam(server_spec=server_spec)
)
```

* `param` *ReleaseMcpServerParam* 发布 MCP Server 的参数
  * `server_spec` - MCP Server 的基本信息规范（必填）
  * `tool_spec` - 定义 MCP Server 提供的工具的规范（可选）
  * `mcp_endpoint_spec` - MCP Server 网络配置的端点规范（可选）
* `return` 成功时返回 Server ID，失败时抛出异常

#### 注册 MCP Server 端点

```python
from v2.nacos.ai.model.ai_param import RegisterMcpServerEndpointParam

await ai_client.register_mcp_server_endpoint(
    RegisterMcpServerEndpointParam(
        mcp_name='my-mcp-server',
        address='127.0.0.1',
        port=8080,
        version='1.0.0'
    )
)
```

* `param` *RegisterMcpServerEndpointParam* 注册 MCP Server 端点的参数
  * `mcp_name` - MCP Server 名称（必填）
  * `address` - MCP Server 端点的 IP 地址或主机名（必填）
  * `port` - MCP Server 端点的端口号（必填）
  * `version` - MCP Server 版本（可选）

#### 订阅 MCP Server

```python
from v2.nacos.ai.model.ai_param import SubscribeMcpServerParam

async def mcp_listener(mcp_id, namespace_id, mcp_name, mcp_server_detail):
    print(f"MCP Server changed: {mcp_name}, version: {mcp_server_detail.version}")

await ai_client.subscribe_mcp_server(
    SubscribeMcpServerParam(
        mcp_name='my-mcp-server',
        version='1.0.0',
        subscribe_callback=mcp_listener
    )
)
```

* `param` *SubscribeMcpServerParam* 订阅 MCP Server 变化的参数
  * `mcp_name` - 要订阅的 MCP Server 名称（必填）
  * `version` - 要订阅的 MCP Server 版本（可选）
  * `subscribe_callback` - 处理 MCP Server 变化的回调函数（必填）

#### 取消订阅 MCP Server

```python
await ai_client.unsubscribe_mcp_server(
    SubscribeMcpServerParam(
        mcp_name='my-mcp-server',
        version='1.0.0',
        subscribe_callback=mcp_listener
    )
)
```

### Agent Card 管理

Nacos 提供了对 AI Agent 的管理能力，包括注册、发现和订阅，支持基于 A2A 协议的 Agent Card 动态注册和服务发现。

#### 获取 Agent Card

```python
from v2.nacos.ai.model.ai_param import GetAgentCardParam

agent_card = await ai_client.get_agent_card(
    GetAgentCardParam(agent_name='my-agent', version='1.0.0')
)
```

* `param` *GetAgentCardParam* 获取 Agent Card 信息的参数
  * `agent_name` - Agent Card 名称（必填）
  * `version` - 目标版本，如果为空则获取最新版本（可选）
  * `registration_type` - 注册类型：'url' 或 'service'（可选）
* `return` 成功时返回 AgentCardDetailInfo，失败时抛出异常

#### 发布 Agent Card

```python
from v2.nacos.ai.model.ai_param import ReleaseAgentCardParam
from a2a.types import AgentCard

agent_card = AgentCard(
    name='my-agent',
    version='1.0.0',
    protocol_version='1.0'
)

await ai_client.release_agent_card(
    ReleaseAgentCardParam(
        agent_card=agent_card,
        registration_type='service',
        set_as_latest=True
    )
)
```

* `param` *ReleaseAgentCardParam* 发布 Agent Card 的参数
  * `agent_card` - Agent Card 信息（必填）
  * `registration_type` - 注册类型：'url' 或 'service'（可选，默认值：'service'）
  * `set_as_latest` - 是否设置为最新版本（可选，默认值：False）

#### 注册 Agent 端点

```python
from v2.nacos.ai.model.ai_param import RegisterAgentEndpointParam

await ai_client.register_agent_endpoint(
    RegisterAgentEndpointParam(
        agent_name='my-agent',
        address='127.0.0.1',
        port=8080,
        version='1.0.0',
        transport='JSONRPC',
        path='/agent',
        support_tls=False
    )
)
```

* `param` *RegisterAgentEndpointParam* 注册 Agent 端点的参数
  * `agent_name` - Agent 名称（必填）
  * `address` - Agent 端点的 IP 地址或主机名（必填）
  * `port` - Agent 端点的端口号（必填）
  * `version` - Agent 版本（必填）
  * `transport` - 传输协议（可选，默认值：'JSONRPC'）
  * `path` - 端点的 URL 路径（可选）
  * `support_tls` - 是否支持 TLS（可选，默认值：False）

#### 注销 Agent 端点

```python
from v2.nacos.ai.model.ai_param import DeregisterAgentEndpointParam

await ai_client.deregister_agent_endpoint(
    DeregisterAgentEndpointParam(
        agent_name='my-agent',
        address='127.0.0.1',
        port=8080,
        version='1.0.0'
    )
)
```

* `param` *DeregisterAgentEndpointParam* 注销 Agent 端点的参数
  * `agent_name` - Agent 名称（必填）
  * `address` - Agent 端点的 IP 地址或主机名（必填）
  * `port` - Agent 端点的端口号（必填）
  * `version` - Agent 版本（必填）

#### 订阅 Agent Card

```python
from v2.nacos.ai.model.ai_param import SubscribeAgentCardParam

async def agent_listener(agent_name, agent_card_detail):
    print(f"Agent card changed: {agent_name}, version: {agent_card_detail.version}")

await ai_client.subscribe_agent_card(
    SubscribeAgentCardParam(
        agent_name='my-agent',
        version='1.0.0',
        subscribe_callback=agent_listener
    )
)
```

* `param` *SubscribeAgentCardParam* 订阅 Agent Card 变化的参数
  * `agent_name` - Agent 名称（必填）
  * `version` - Agent 版本（可选）
  * `subscribe_callback` - 处理 Agent Card 变化的回调函数（必填）

#### 取消订阅 Agent Card

```python
await ai_client.unsubscribe_agent_card(
    SubscribeAgentCardParam(
        agent_name='my-agent',
        version='1.0.0',
        subscribe_callback=agent_listener
    )
)
```

### 停止 AI 客户端

```python
await ai_client.shutdown()
```

