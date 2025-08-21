from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict

from v2.nacos.transport.ability import AbilityKey, AbilityStatus
from v2.nacos.transport.model.rpc_request import Request
from v2.nacos.transport.model.rpc_response import Response
from v2.nacos.transport.model.server_info import ServerInfo


class IConnection(ABC):
    @abstractmethod
    def request(self, request: Request, timeout_mills: int) -> Response:
        pass

    @abstractmethod
    def close(self):
        pass


class Connection(IConnection, ABC):
    def __init__(self, connection_id, server_info: ServerInfo):
        self.connection_id = connection_id
        self.abandon = False
        self.server_info = server_info
        self.ability_table : Optional[Dict[str,bool]] = None

    def get_connection_id(self) -> str:
        return self.connection_id

    def get_server_info(self) -> ServerInfo:
        return self.server_info

    def set_abandon(self, flag: bool):
        self.abandon = flag

    def is_abandon(self):
        return self.abandon

    def is_abilities_set(self):
        return self.ability_table is not None

    def get_connection_ability(self, ability_key: AbilityKey) -> AbilityStatus:
        if self.ability_table is None:
            return AbilityStatus.UNKNOWN
        return AbilityStatus.SUPPORTED if self.ability_table.get(ability_key.key_name, False) else AbilityStatus.NOT_SUPPORTED

    def set_ability_table(self, ability_table: Optional[Dict[str, bool]]):
        self.ability_table = ability_table
