from enum import Enum
from typing import Any


class RedoType(Enum):
	"""Redo type enumeration."""
	REGISTER = "REGISTER"
	UNREGISTER = "UNREGISTER"
	NONE = "NONE"
	REMOVE = "REMOVE"

class RedoData:
	def __init__(self, data: Any) -> None:
		"""Initialize RedoData with default values."""
		self._expected_registered: bool = True
		self._registered: bool = False
		self._unregistering: bool = False
		self.data: Any = data

	def set_expected_registered(self, registered: bool) -> None:
		"""Set the expected registration status."""
		self._expected_registered = registered

	def is_expected_registered(self) -> bool:
		"""Check if the data is expected to be registered."""
		return self._expected_registered

	def is_registered(self) -> bool:
		"""Check if the data is currently registered."""
		return self._registered

	def is_unregistering(self) -> bool:
		"""Check if the data is currently unregistering."""
		return self._unregistering

	def set_registered(self, registered: bool) -> None:
		"""Set the registration status."""
		self._registered = registered

	def set_unregistering(self, unregistering: bool) -> None:
		"""Set the unregistering status."""
		self._unregistering = unregistering

	def get(self) -> Any:
		"""Get the data."""
		return self.data

	def set(self, data: Any) -> None:
		"""Set the data."""
		self.data = data

	def registered(self) -> None:
		"""Mark the data as registered."""
		self._registered = True
		self._unregistering = False

	def unregistered(self) -> None:
		"""Mark the data as unregistered."""
		self._registered = False
		self._unregistering = True

	def is_need_redo(self) -> bool:
		"""Check if redo operation is needed."""
		return not RedoType.NONE == self.get_redo_type()

	def get_redo_type(self) -> RedoType:
		"""
		Get redo type for current redo data without expected state.

		Returns:
			RedoType: The type of redo operation needed.
		"""
		if self.is_registered() and not self.is_unregistering():
			return RedoType.NONE if self._expected_registered else RedoType.UNREGISTER
		elif self.is_registered() and self.is_unregistering():
			return RedoType.UNREGISTER
		elif not self.is_registered() and not self.is_unregistering():
			return RedoType.REGISTER
		else:
			return RedoType.REGISTER if self._expected_registered else RedoType.REMOVE