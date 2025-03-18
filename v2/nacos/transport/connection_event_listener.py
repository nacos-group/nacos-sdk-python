from abc import ABC, abstractmethod


class ConnectionEventListener(ABC):

    @abstractmethod
    async def on_connected(self) -> None:
        pass

    @abstractmethod
    async def on_disconnect(self) -> None:
        pass
