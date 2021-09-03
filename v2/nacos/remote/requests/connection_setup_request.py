from typing import Optional
from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type
from v2.nacos.ability.client_abilities import ClientAbilities


class ConnectionSetupRequest(request.Request):
    clientVersion: Optional[str]
    abilities: Optional[ClientAbilities]
    tenant: Optional[str]
    labels: dict = {}

    def get_client_version(self) -> str:
        return self.clientVersion

    def set_client_version(self, client_version: str) -> None:
        self.clientVersion = client_version

    def get_labels(self) -> dict:
        return self.labels

    def set_labels(self, labels: dict) -> None:
        self.labels = labels

    def get_tenant(self) -> str:
        return self.tenant

    def set_tenant(self, tenant: str) -> None:
        self.tenant = tenant

    def get_abilities(self) -> ClientAbilities:
        return self.abilities

    def set_abilities(self, abilities: ClientAbilities) -> None:
        self.abilities = abilities

    def get_module(self):
        return "internal"

    def get_remote_type(self):
        return remote_request_type["ConnectionSetup"]