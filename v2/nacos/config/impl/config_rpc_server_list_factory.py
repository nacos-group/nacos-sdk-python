from typing import List

from v2.nacos.config.impl.server_list_manager import ServerListManager
from v2.nacos.remote.iserver_list_factory import ServerListFactory


class ConfigRpcServerListFactory(ServerListFactory):
    def __init__(self, server_list_manager: ServerListManager):
        self.server_list_manager = server_list_manager

    def gen_next_server(self) -> str:
        return self.server_list_manager.get_next_server_addr()

    def get_current_server(self) -> str:
        return self.server_list_manager.get_current_server_addr()

    def get_server_list(self) -> List[str]:
        return self.server_list_manager.get_server_urls()
