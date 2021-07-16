from abc import ABCMeta, abstractmethod


class ServerListFactory(metaclass=ABCMeta):
    @abstractmethod
    def gen_next_server(self):
        pass

    @abstractmethod
    def get_current_server(self):
        pass

    @abstractmethod
    def get_server_list(self):
        pass
