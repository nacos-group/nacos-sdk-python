from abc import ABCMeta, abstractmethod


class Listener(etaclass=ABCMeta):
    @abstractmethod
    def get_executor(self):
        pass

    @abstractmethod
    def receive_config_info(self, config_info: str):
        pass
