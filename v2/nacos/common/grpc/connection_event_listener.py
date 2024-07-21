from abc import ABC, abstractmethod
class IConnectionEventListener(ABC):

  @abstractmethod
  def on_connected(self) -> None:
      pass

  @abstractmethod
  def on_disconnect(self) -> None:
      pass