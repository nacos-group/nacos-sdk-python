# nacos-sdk-python

A Python implementation of Nacos OpenAPI.

see: https://nacos.io/docs/latest/guide/user/open-api/

[![Pypi Version](https://badge.fury.io/py/nacos-sdk-python.svg)](https://badge.fury.io/py/nacos-sdk-python)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/nacos-group/nacos-sdk-python/blob/master/LICENSE)

### Supported Python version：

Python 2.7
Python 3.6
Python 3.7

### Supported Nacos version

Nacos 0.8.0+
Nacos 1.x
Nacos 2.x with http protocol

## Installation

```shell
pip install nacos-sdk-python
```

## Getting Started

```python
import nacos

# Both HTTP/HTTPS protocols are supported, if not set protocol prefix default is HTTP, and HTTPS with no ssl check(verify=False)
# "192.168.3.4:8848" or "https://192.168.3.4:443" or "http://192.168.3.4:8848,192.168.3.5:8848" or "https://192.168.3.4:443,https://192.168.3.5:443"
SERVER_ADDRESSES = "server addresses split by comma"
NAMESPACE = "namespace id"

# no auth mode
client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE)
# auth mode
# client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE, ak="{ak}", sk="{sk}")

# get config
data_id = "config.nacos"
group = "group"
print(client.get_config(data_id, group))
```

## Configuration

```
client = NacosClient(server_addresses, namespace=your_ns, ak=your_ak, sk=your_sk)
```

* *server_addresses* - **required**  - Nacos server address, comma separated if more than 1.
* *namespace* - Namespace. | default: `None`
* *ak* - The accessKey to authenticate. | default: null
* *sk* - The secretKey to authentication. | default: null
* *credentials_provider* - The custom access key manager | default: null
* *log_level* - Log level. | default: null
* *log_rotation_backup_count* - The number of log files to keep. | default: `7`

#### Extra Options

Extra option can be set by `set_options`, as following:

```
client.set_options({key}={value})
# client.set_options(proxies={"http":"192.168.3.50:809"})
```

Configurable options are:

* *default_timeout* - Default timeout for get config from server in seconds.
* *pulling_timeout* - Long polling timeout in seconds.
* *pulling_config_size* - Max config items number listened by one polling process.
* *callback_thread_num* - Concurrency for invoking callback.
* *failover_base* - Dir to store failover config files.
* *snapshot_base* - Dir to store snapshot config files.
* *no_snapshot* - To disable default snapshot behavior, this can be overridden by param *no_snapshot* in *get* method.
* *proxies* - Dict proxy mapping, some environments require proxy access, so you can set this parameter, this way http
  requests go through the proxy.

## API Reference

### Get Config

> `NacosClient.get_config(data_id, group, timeout, no_snapshot)`

* `param` *data_id* Data id.
* `param` *group* Group, use `DEFAULT_GROUP` if no group specified.
* `param` *timeout* Timeout for requesting server in seconds.
* `param` *no_snapshot* Whether to use local snapshot while server is unavailable.
* `return`
  W
  Get value of one config item following priority:


* Step 1 - Get from local failover dir(default: `${cwd}/nacos-data/data`).
    * Failover dir can be manually copied from snapshot dir(default: `${cwd}/nacos-data/snapshot`) in advance.
    * This helps to suppress the effect of known server failure.

* Step 2 - Get from one server until value is got or all servers tried.
    * Content will be save to snapshot dir after got from server.

* Step 3 - Get from snapshot dir.

### Add Watchers

> `NacosClient.add_config_watchers(data_id, group, cb_list)`

* `param` *data_id* Data id.
* `param` *group* Group, use `DEFAULT_GROUP` if no group specified.
* `param` *cb_list* List of callback functions to add.
* `return`

Add watchers to a specified config item.

* Once changes or deletion of the item happened, callback functions will be invoked.
* If the item is already exists in server, callback functions will be invoked for once.
* Multiple callbacks on one item is allowed and all callback functions are invoked concurrently by `threading.Thread`.
* Callback functions are invoked from current process.

### Remove Watcher

> `NacosClient.remove_config_watcher(data_id, group, cb, remove_all)`

* `param` *data_id* Data id.
* `param` *group* Group, use "DEFAULT_GROUP" if no group specified.
* `param` *cb* Callback function to delete.
* `param` *remove_all* Whether to remove all occurrence of the callback or just once.
* `return`

Remove watcher from specified key.

### Publish Config

> `NacosClient.publish_config(data_id, group, content, timeout)`

* `param` *data_id* Data id.
* `param` *group* Group, use "DEFAULT_GROUP" if no group specified.
* `param` *content* Config value.
* `param` *timeout* Timeout for requesting server in seconds.
* `return` True if success or an exception will be raised.

Publish one data item to Nacos.

* If the data key is not exist, create one first.
* If the data key is exist, update to the content specified.
* Content can not be set to None, if there is need to delete config item, use function **remove** instead.

### Remove Config

> `NacosClient.remove_config(data_id, group, timeout)`

* `param` *data_id* Data id.
* `param` *group* Group, use "DEFAULT_GROUP" if no group specified.
* `param` *timeout* Timeout for requesting server in seconds.
* `return` True if success or an exception will be raised.

Remove one data item from Nacos.

### Register Instance

>
`NacosClient.add_naming_instance(service_name, ip, port, cluster_name, weight, metadata, enable, healthy,ephemeral,group_name,heartbeat_interval)`

* `param` *service_name*  **required** Service name to register to.
* `param` *ip*  **required** IP of the instance.
* `param` *port* **required** Port of the instance.
* `param` *cluster_name* Cluster to register to.
* `param` *weight* A float number for load balancing weight.
* `param` *metadata* Extra info in JSON string format or dict format
* `param` *enable* A bool value to determine whether instance is enabled or not.
* `param` *healthy* A bool value to determine whether instance is healthy or not.
* `param` *ephemeral* A bool value to determine whether instance is ephemeral or not.
* `param` *heartbeat_interval* Auto daemon heartbeat interval in seconds.
* `return` True if success or an exception will be raised.

### Deregister Instance

> `NacosClient.remove_naming_instance(service_name, ip, port, cluster_name)`

* `param` *service_name*  **required** Service name to deregister from.
* `param` *ip*  **required** IP of the instance.
* `param` *port* **required** Port of the instance.
* `param` *cluster_name* Cluster to deregister from.
* `param` *ephemeral* A bool value to determine whether instance is ephemeral or not.
* `return` True if success or an exception will be raised.

### Modify Instance

> `NacosClient.modify_naming_instance(service_name, ip, port, cluster_name, weight, metadata, enable)`

* `param` *service_name*  **required** Service name.
* `param` *ip*  **required** IP of the instance.
* `param` *port* **required** Port of the instance.
* `param` *cluster_name* Cluster name.
* `param` *weight* A float number for load balancing weight.
* `param` *metadata* Extra info in JSON string format or dict format.
* `param` *enable* A bool value to determine whether instance is enabled or not.
* `param` *ephemeral* A bool value to determine whether instance is ephemeral or not.
* `return` True if success or an exception will be raised.

### Query Instances

> `NacosClient.list_naming_instance(service_name, clusters, namespace_id, group_name, healthy_only)`

* `param` *service_name*  **required** Service name to query.
* `param` *clusters* Cluster names separated by comma.
* `param` *namespace_id* Customized group name, default `blank`.
* `param` *group_name* Customized group name , default `DEFAULT_GROUP`.
* `param` *healthy_only* A bool value for querying healthy instances or not.
* `return` Instance info list if success or an exception will be raised.

### Query Instance Detail

> `NacosClient.get_naming_instance(service_name, ip, port, cluster_name)`

* `param` *service_name*  **required** Service name.
* `param` *ip*  **required** IP of the instance.
* `param` *port* **required** Port of the instance.
* `param` *cluster_name* Cluster name.
* `return` Instance info if success or an exception will be raised.

### Send Instance Beat

> `NacosClient.send_heartbeat(service_name, ip, port, cluster_name, weight, metadata)`

* `param` *service_name*  **required** Service name.
* `param` *ip*  **required** IP of the instance.
* `param` *port* **required** Port of the instance.
* `param` *cluster_name* Cluster to register to.
* `param` *weight* A float number for load balancing weight.
* `param` *ephemeral* A bool value to determine whether instance is ephemeral or not.
* `param` *metadata* Extra info in JSON string format or dict format.
* `return` A JSON object include server recommended beat interval if success or an exception will be raised.

### Subscribe Service Instances Changed

> `NacosClient.subscribe(listener_fn, listener_interval=7, *args, **kwargs)`

* `param` *listener_fn*  **required** Customized listener function.
* `param` *listener_interval*  Listen interval , default 7 second.
* `param` *service_name*  **required** Service name which subscribes.
* `param` *clusters* Cluster names separated by comma.
* `param` *namespace_id* Customized group name, default `blank`.
* `param` *group_name* Customized group name , default `DEFAULT_GROUP`.
* `param` *healthy_only* A bool value for querying healthy instances or not.
* `return`

### Unsubscribe Service Instances Changed

> `NacosClient.unsubscribe(service_name, listener_name)`

* `param` *service_name*  **required** Service name to subscribed.
* `param` *listener_name*  listener_name which is customized.
* `return`

### Stop All Service Subscribe

> `NacosClient.stop_subscribe()`

* `return`

## Debugging Mode

Debugging mode if useful for getting more detailed log on console.

Debugging mode can be set by:

```
client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE, username=USERNAME, password=PASSWORD,log_level="DEBUG")
```

# nacos-sdk-python v2

A Python implementation of Nacos OpenAPI.

see: https://nacos.io/zh-cn/docs/open-API.html

[![Pypi Version](https://badge.fury.io/py/nacos-sdk-python.svg)](https://badge.fury.io/py/nacos-sdk-python)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/nacos-group/nacos-sdk-python/blob/master/LICENSE)

### Supported Python version：

Python 3.7+

### Supported Nacos version

Supported Nacos version over 2.x

## Installation

```shell
 pip install nacos-sdk-python==2.0.0b5 
```

## Client Configuration

```
from v2.nacos import NacosNamingService, ClientConfigBuilder, GRPCConfig, Instance, SubscribeServiceParam, \
    RegisterInstanceParam, DeregisterInstanceParam, BatchRegisterInstanceParam, GetServiceParam, ListServiceParam, \
    ListInstanceParam, NacosConfigService, ConfigParam
    
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

```

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

```
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

```
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

```
await client.remove_listener(dataID, groupName, config_listener)
```

* `param` *ConfigParam* config client common parameters.
* `return` True if success or an exception will be raised.

Remove watcher from specified key.

### Publish Config

```
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

```
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

```
await client.shutdown()
```

## Naming Client

```

naming_client = await NacosNamingService.create_naming_service(client_config)

```

### Register Instance

```angular2html
response = await client.register_instance(
            request=RegisterInstanceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', ip='1.1.1.1',
                port=7001, weight=1.0, cluster_name='c1', metadata={'a': 'b'},
                enabled=True,
                healthy=True, ephemeral=True))
```

### Batch Register Instance
```angular2html
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

```angular2html
response = await client.deregister_instance(
          request=DeregisterInstanceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', ip='1.1.1.1',
                                          port=7001, cluster_name='c1', ephemeral=True)
      )
```

### Update Instance
```angular2html
response = await client.update_instance(
            request=RegisterInstanceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', ip='1.1.1.1',
                                          port=7001, weight=2.0, cluster_name='c1', metadata={'a': 'b'},
                                          enabled=True,
                                          healthy=True, ephemeral=True))
```

### Get Service
```angular2html
service = await client.get_service(
            GetServiceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', cluster_name='c1'))
```

### List Service
```angular2html

service_list = await client.list_services(ListServiceParam())

```

### List Instance

```angular2html

instance_list = await client.list_instances(ListInstanceParam(service_name='nacos.test.1', healthy_only=True))
instance_list = await client.list_instances(ListInstanceParam(service_name='nacos.test.1', healthy_only=False))
instance_list = await client.list_instances(ListInstanceParam(service_name='nacos.test.1', healthy_only=None))

```

### Subscribe

```angular2html
async def cb(instance_list: list[Instance]):
  print('received subscribe callback', str(instance_list))

await client.subscribe(
  SubscribeServiceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', subscribe_callback=cb))
```


### Unsubscribe

```angular2html
async def cb(instance_list: list[Instance]):
  print('received subscribe callback', str(instance_list))

await client.unsubscribe(
            SubscribeServiceParam(service_name='nacos.test.1', group_name='DEFAULT_GROUP', subscribe_callback=cb))
```