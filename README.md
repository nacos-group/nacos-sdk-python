# nacos-sdk-python v3

English | [简体中文](README_CN.md)

A Python implementation of Nacos OpenAPI.

see: https://nacos.io/zh-cn/docs/open-API.html

[![Pypi Version](https://badge.fury.io/py/nacos-sdk-python.svg)](https://badge.fury.io/py/nacos-sdk-python)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/nacos-group/nacos-sdk-python/blob/master/LICENSE)

### Supported Python version：

Python 3.10+

### Supported Nacos version

Supported Nacos version over 3.x

**Note:** AI Client feature requires Nacos server version 3.1.0 or above.

## Installation

```shell
 pip install nacos-sdk-python
```

## Client Configuration

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

* *server_address* - **required**  - Nacos server address
* *access_key* - The aliyun accessKey to authenticate.
* *secret_key* - The aliyun secretKey to authenticate.
* *credentials_provider* - The custom access key manager.
* *username* - The username to authenticate.
* *password* - The password to authenticate.
* *log_level* - Log level | default: `logging.INFO`
* *cache_dir* - cache dir path. | default: `~/nacos/cache`
* *log_dir* - log dir path. | default: `~/logs/nacos`
* *namespace_id* - namespace id.  | default: ``
* *grpc_config* - grpc config.
  * *max_receive_message_length* - max receive message length in grpc.  | default: 100 * 1024 * 1024
  * *max_keep_alive_ms* - max keep alive ms in grpc. | default: 60 * 1000
  * *initial_window_size* - initial window size in grpc.  | default: 10 * 1024 * 1024
  * *initial_conn_window_size* - initial connection window size in grpc. | default: 10 * 1024 * 1024
  * *grpc_timeout* - grpc timeout in milliseconds. default: 3000
* *tls_config* - tls config
  * *enabled* - whether enable tls.
  * *ca_file* - ca file path.
  * *cert_file* - cert file path.
  * *key_file* - key file path.
* *kms_config* - aliyun kms config 
  * *enabled* - whether enable aliyun kms.
  * *endpoint* - aliyun kms endpoint.
  * *access_key* - aliyun accessKey.
  * *secret_key* - aliyun secretKey.
  * *password* - aliyun kms password.

## Config Client

```python
config_client = await NacosConfigService.create_config_service(client_config)
```

### config client common parameters

> `param: ConfigParam`

* `param` *data_id* Data id.
* `param` *group* Group, use `DEFAULT_GROUP` if no group specified.
* `param` *content* Config content.
* `param` *tag* Config tag.
* `param` *app_name* Application name.
* `param` *beta_ips* Beta test ip address.
* `param` *cas_md5* MD5 check code.
* `param` *type* Config type.
* `param` *src_user* Source user.
* `param` *encrypted_data_key* Encrypted data key.
* `param` *kms_key_id* Kms encrypted data key id.
* `param` *usage_type* Usage type.

### Get Config

```python
content = await config_client.get_config(ConfigParam(
            data_id=data_id,
            group=group
        ))
```

* `param` *ConfigParam* config client common parameters. When getting configuration, it is necessary to specify the
  required data_id and group in param.
* `return` Config content if success or an exception will be raised.

Get value of one config item following priority:

* Step 1 - Get from local failover dir.

* Step 2 - Get from one server until value is got or all servers tried.
    * Content will be saved to snapshot dir after got from server.

* Step 3 - Get from snapshot dir.

### Add Listener

```python
async def config_listener(tenant, data_id, group, content):
    print("listen, tenant:{} data_id:{} group:{} content:{}".format(tenant, data_id, group, content))

await config_client.add_listener(dataID, groupName, config_listener)
```

* `param` *ConfigParam* config client common parameters.
* `listener` *listener* Configure listener, defined by the namespace_id、group、data_id、content.
* `return`

Add Listener to a specified config item.

* Once changes or deletion of the item happened, callback functions will be invoked.
* If the item is already exists in server, callback functions will be invoked for once.
* Callback functions are invoked from current process.

### Remove Listener

```python
await client.remove_listener(dataID, groupName, config_listener)
```

* `param` *ConfigParam* config client common parameters.
* `return` True if success or an exception will be raised.

Remove watcher from specified key.

### Publish Config

```python
res = await client.publish_config(ConfigParam(
            data_id=dataID,
            group=groupName,
            content="Hello world")
        )
```

* `param` *ConfigParam* config client common parameters. When publishing configuration, it is necessary to specify the
  required data_id, group and content in param.
* `return` True if success or an exception will be raised.

Publish one congfig data item to Nacos.

* If the data key is not exist, create one first.
* If the data key is exist, update to the content specified.
* Content can not be set to None, if there is need to delete config item, use function **remove** instead.

### Remove Config

```python
res = await client.remove_config(ConfigParam(
            data_id=dataID,
            group=groupName
        ))
```
* `param` *ConfigParam* config client common parameters.When removing configuration, it is necessary to specify the
  required data_id and group in param.
* `return` True if success or an exception will be raised.

Remove one config data item from Nacos.

### Stop Config Client

```python
await client.shutdown()
```

## Naming Client

```python
naming_client = await NacosNamingService.create_naming_service(client_config)
```

### Register Instance

```python
response = await client.register_instance(
            request=RegisterInstanceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', ip='1.1.1.1',
                port=7001, weight=1.0, cluster_name='c1', metadata={'a': 'b'},
                enabled=True,
                healthy=True, ephemeral=True))
```

### Batch Register Instance

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

### Deregister Instance

```python
response = await client.deregister_instance(
          request=DeregisterInstanceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', ip='1.1.1.1',
                                          port=7001, cluster_name='c1', ephemeral=True)
      )
```

### Update Instance

```python
response = await client.update_instance(
            request=RegisterInstanceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', ip='1.1.1.1',
                                          port=7001, weight=2.0, cluster_name='c1', metadata={'a': 'b'},
                                          enabled=True,
                                          healthy=True, ephemeral=True))
```

### Get Service

```python
service = await client.get_service(
            GetServiceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', cluster_name='c1'))
```

### List Service

```python
service_list = await client.list_services(ListServiceParam())
```

### List Instance

```python
instance_list = await client.list_instances(ListInstanceParam(service_name='nacos.test.1', healthy_only=True))
instance_list = await client.list_instances(ListInstanceParam(service_name='nacos.test.1', healthy_only=False))
instance_list = await client.list_instances(ListInstanceParam(service_name='nacos.test.1', healthy_only=None))
```

### Subscribe

```python
async def cb(instance_list: List[Instance]):
  print('received subscribe callback', str(instance_list))

await client.subscribe(
  SubscribeServiceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', subscribe_callback=cb))
```

### Unsubscribe

```python
async def cb(instance_list: List[Instance]):
  print('received subscribe callback', str(instance_list))

await client.unsubscribe(
            SubscribeServiceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', subscribe_callback=cb))
```

### Stop Naming Client

```python
await client.shutdown()
```

## AI Client

**Important:** AI Client feature requires Nacos server version 3.1.0 or above.

```python
from v2.nacos import NacosAIService, ClientConfigBuilder

client_config = (ClientConfigBuilder()
                 .server_address(os.getenv('NACOS_SERVER_ADDR', 'localhost:8848'))
                 .build())
                 
ai_client = await NacosAIService.create_ai_service(client_config)
```

### MCP Server Management

Nacos provides management capabilities for MCP (Model Context Protocol) Server, including registration, discovery, and subscription, supporting dynamic registration and service discovery of MCP servers.

#### Get MCP Server

```python
from v2.nacos.ai.model.ai_param import GetMcpServerParam

mcp_server = await ai_client.get_mcp_server(
    GetMcpServerParam(mcp_name='my-mcp-server', version='1.0.0')
)
```

* `param` *GetMcpServerParam* Parameter for retrieving MCP server information.
  * `mcp_name` - Name of the MCP server to query (required).
  * `version` - Version of the MCP server to query (optional).
* `return` McpServerDetailInfo if success or an exception will be raised.

#### Release MCP Server

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

* `param` *ReleaseMcpServerParam* Parameter for releasing/publishing MCP server.
  * `server_spec` - Basic information specification for the MCP server (required).
  * `tool_spec` - Tool specification defining the tools provided by MCP server (optional).
  * `mcp_endpoint_spec` - Endpoint specification for MCP server network configuration (optional).
* `return` Server ID if success or an exception will be raised.

#### Register MCP Server Endpoint

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

* `param` *RegisterMcpServerEndpointParam* Parameter for registering MCP server endpoint.
  * `mcp_name` - Name of the MCP server (required).
  * `address` - IP address or hostname of the MCP server endpoint (required).
  * `port` - Port number of the MCP server endpoint (required).
  * `version` - Version of the MCP server (optional).

#### Subscribe MCP Server

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

* `param` *SubscribeMcpServerParam* Parameter for subscribing to MCP server changes.
  * `mcp_name` - Name of the MCP server to subscribe to (required).
  * `version` - Version of the MCP server to subscribe to (optional).
  * `subscribe_callback` - Callback function to handle MCP server changes (required).

#### Unsubscribe MCP Server

```python
await ai_client.unsubscribe_mcp_server(
    SubscribeMcpServerParam(
        mcp_name='my-mcp-server',
        version='1.0.0',
        subscribe_callback=mcp_listener
    )
)
```

### Agent Card Management

Nacos provides management capabilities for AI Agent, including registration, discovery, and subscription, supporting dynamic registration and service discovery of Agent Card based on A2A protocol.

#### Get Agent Card

```python
from v2.nacos.ai.model.ai_param import GetAgentCardParam

agent_card = await ai_client.get_agent_card(
    GetAgentCardParam(agent_name='my-agent', version='1.0.0')
)
```

* `param` *GetAgentCardParam* Parameter for retrieving agent card information.
  * `agent_name` - Name of the agent card (required).
  * `version` - Target version, if null or empty, get latest version (optional).
  * `registration_type` - Registration type: 'url' or 'service' (optional).
* `return` AgentCardDetailInfo if success or an exception will be raised.

#### Release Agent Card

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

* `param` *ReleaseAgentCardParam* Parameter for releasing/publishing agent card.
  * `agent_card` - Agent card information (required).
  * `registration_type` - Registration type: 'url' or 'service' (optional, default: 'service').
  * `set_as_latest` - Whether to set as the latest version (optional, default: False).

#### Register Agent Endpoint

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

* `param` *RegisterAgentEndpointParam* Parameter for registering agent endpoint.
  * `agent_name` - Name of the agent (required).
  * `address` - IP address or hostname of the agent endpoint (required).
  * `port` - Port number of the agent endpoint (required).
  * `version` - Version of the agent (required).
  * `transport` - Transport protocol (optional, default: 'JSONRPC').
  * `path` - URL path for the endpoint (optional).
  * `support_tls` - Whether TLS is supported (optional, default: False).

#### Deregister Agent Endpoint

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

* `param` *DeregisterAgentEndpointParam* Parameter for deregistering agent endpoint.
  * `agent_name` - Name of the agent (required).
  * `address` - IP address or hostname of the agent endpoint (required).
  * `port` - Port number of the agent endpoint (required).
  * `version` - Version of the agent (required).

#### Subscribe Agent Card

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

* `param` *SubscribeAgentCardParam* Parameter for subscribing to agent card changes.
  * `agent_name` - Name of the agent (required).
  * `version` - Version of the agent (optional).
  * `subscribe_callback` - Callback function to handle agent card changes (required).

#### Unsubscribe Agent Card

```python
await ai_client.unsubscribe_agent_card(
    SubscribeAgentCardParam(
        agent_name='my-agent',
        version='1.0.0',
        subscribe_callback=agent_listener
    )
)
```

### Stop AI Client

```python
await ai_client.shutdown()
```
