# nacos-sdk-python
A Python implementation of Nacos OpenAPI.

see: https://nacos.io/zh-cn/docs/open-API.html

[![Pypi Version](https://badge.fury.io/py/nacos-sdk-python.svg)](https://badge.fury.io/py/nacos-sdk-python)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/nacos-group/nacos-sdk-python/blob/master/LICENSE)


### Supported Python version：

Python 2.7
Python 3.6
Python 3.7

### Supported Nacos version
Nacos 0.8.0 ~ 1.3.2


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
#client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE, ak="{ak}", sk="{sk}")

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
* *proxies* - Dict proxy mapping, some environments require proxy access, so you can set this parameter, this way http requests go through the proxy.

## API Reference
 
### Get Config
>`NacosClient.get_config(data_id, group, timeout, no_snapshot)`

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
>`NacosClient.add_config_watchers(data_id, group, cb_list)`

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
>`NacosClient.remove_config_watcher(data_id, group, cb, remove_all)`

* `param` *data_id* Data id.
* `param` *group* Group, use "DEFAULT_GROUP" if no group specified.
* `param` *cb* Callback function to delete.
* `param` *remove_all* Whether to remove all occurrence of the callback or just once.
* `return`

Remove watcher from specified key.

### Publish Config
>`NacosClient.publish_config(data_id, group, content, timeout)`

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
>`NacosClient.remove_config(data_id, group, timeout)`
* `param` *data_id* Data id.
* `param` *group* Group, use "DEFAULT_GROUP" if no group specified.
* `param` *timeout* Timeout for requesting server in seconds.
* `return` True if success or an exception will be raised.

Remove one data item from Nacos.

### Register Instance
>`NacosClient.add_naming_instance(service_name, ip, port, cluster_name, weight, metadata, enable, healthy,ephemeral,group_name,heartbeat_interval)`
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
>`NacosClient.remove_naming_instance(service_name, ip, port, cluster_name)`
* `param` *service_name*  **required** Service name to deregister from.
* `param` *ip*  **required** IP of the instance.
* `param` *port* **required** Port of the instance.
* `param` *cluster_name* Cluster to deregister from.
* `param` *ephemeral* A bool value to determine whether instance is ephemeral or not.
* `return` True if success or an exception will be raised.

### Modify Instance
>`NacosClient.modify_naming_instance(service_name, ip, port, cluster_name, weight, metadata, enable)`
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
>`NacosClient.list_naming_instance(service_name, clusters, namespace_id, group_name, healthy_only)`
* `param` *service_name*  **required** Service name to query.
* `param` *clusters* Cluster names separated by comma.
* `param` *namespace_id* Customized group name, default `blank`.
* `param` *group_name* Customized group name , default `DEFAULT_GROUP`.
* `param` *healthy_only* A bool value for querying healthy instances or not.
* `return` Instance info list if success or an exception will be raised.

### Query Instance Detail
>`NacosClient.get_naming_instance(service_name, ip, port, cluster_name)`
* `param` *service_name*  **required** Service name.
* `param` *ip*  **required** IP of the instance.
* `param` *port* **required** Port of the instance.
* `param` *cluster_name* Cluster name.
* `return` Instance info if success or an exception will be raised.

### Send Instance Beat
>`NacosClient.send_heartbeat(service_name, ip, port, cluster_name, weight, metadata)`
* `param` *service_name*  **required** Service name.
* `param` *ip*  **required** IP of the instance.
* `param` *port* **required** Port of the instance.
* `param` *cluster_name* Cluster to register to.
* `param` *weight* A float number for load balancing weight.
* `param` *ephemeral* A bool value to determine whether instance is ephemeral or not.
* `param` *metadata* Extra info in JSON string format or dict format.
* `return` A JSON object include server recommended beat interval if success or an exception will be raised.

### Subscribe Service Instances Changed
>`NacosClient.subscribe(listener_fn, listener_interval=7, *args, **kwargs)`
* `param` *listener_fn*  **required** Customized listener function.
* `param` *listener_interval*  Listen interval , default 7 second.
* `param` *service_name*  **required** Service name which subscribes.
* `param` *clusters* Cluster names separated by comma.
* `param` *namespace_id* Customized group name, default `blank`.
* `param` *group_name* Customized group name , default `DEFAULT_GROUP`.
* `param` *healthy_only* A bool value for querying healthy instances or not.
* `return`

### Unsubscribe Service Instances Changed
>`NacosClient.unsubscribe(service_name, listener_name)`
* `param` *service_name*  **required** Service name to subscribed.
* `param` *listener_name*  listener_name which is customized.
* `return`

### Stop All Service Subscribe 
>`NacosClient.stop_subscribe()`
* `return`

## Debugging Mode
Debugging mode if useful for getting more detailed log on console.

Debugging mode can be set by:
```
client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE, username=USERNAME, password=PASSWORD,log_level="DEBUG")
```

