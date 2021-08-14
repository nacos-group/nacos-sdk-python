from abc import ABCMeta, abstractmethod
from typing import List


class ServerListFactory(metaclass=ABCMeta):
    @abstractmethod
    def gen_next_server(self) -> str:
        pass

    @abstractmethod
    def get_current_server(self) -> str:
        pass

    @abstractmethod
    def get_server_list(self) -> List[str]:
        pass
