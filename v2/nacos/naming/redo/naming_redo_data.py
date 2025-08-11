from typing import Any

from v2.nacos.redo.redo_data import RedoData


class NamingRedoData(RedoData):

	def __init__(self, data: Any, service_name: str, group_name: str) -> None:
		super().__init__(data)
		self.service_name = service_name
		self.group_name = group_name
