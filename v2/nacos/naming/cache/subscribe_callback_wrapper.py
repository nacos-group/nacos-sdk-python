from abc import abstractmethod, ABC
from collections.abc import Callable
from typing import Optional, List

from v2.nacos import Instance, Service


class Selector(ABC):

	@abstractmethod
	def select_instance(self, service:Service) -> Optional[List[Instance]]:
		pass


class ClusterSelector(Selector):

	def select_instance(self, service: Service) -> Optional[List[Instance]]:
		if self.cluster_names == "":
			return service.hosts
		return [host for host in service.hosts if host.clusterName in self.clusters]

	def __init__(self,clusters:Optional[List[str]]):
		if not clusters:
			self.clusters = []
			self.cluster_names = ""
			return

		self.clusters: List[str] = clusters
		self.cluster_names: str = join_cluster(clusters)

	def __eq__(self, other):
		if not isinstance(other, ClusterSelector):
			return False
		return self.cluster_names == other.cluster_names


def join_cluster(clusters:List[str]):
	if not clusters:
		return ""
	# 使用set实现去重和过滤空字符串
	unique_set = {item.strip() for item in clusters if item and item.strip()}

	# 转换为列表并排序
	unique_list = sorted(list(unique_set))

	# 使用逗号连接
	return ",".join(unique_list)

class SubscribeCallbackFuncWrapper:

	def __init__(self, selector:Selector, callback_func:Callable):
		self.selector = selector
		self.callback_func = callback_func

	async def notify_listener(self, service: Service):
		instances =  self.selector.select_instance(service)
		if self.callback_func is None:
			return
		return await self.callback_func(instances)
