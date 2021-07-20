from v2.nacos.ability.client_config_ability import ClientConfigAbility
from v2.nacos.ability.client_naming_ability import ClientNamingAbility
from v2.nacos.ability.client_remote_ability import ClientRemoteAbility


class ClientAbilities:
    def __init__(self):
        self.__remote_ability = ClientRemoteAbility()
        self.__config_ability = ClientConfigAbility()
        self.__naming_ability = ClientNamingAbility()

    def get_remote_ability(self) -> ClientRemoteAbility:
        return self.__remote_ability

    def set_remote_ability(self, remote_ability: ClientRemoteAbility) -> None:
        self.__remote_ability = remote_ability

    def get_config_ability(self) -> ClientConfigAbility:
        return self.__config_ability

    def set_config_ability(self, config_ability: ClientConfigAbility) -> None:
        self.__config_ability = config_ability

    def get_naming_ability(self) -> ClientNamingAbility:
        return self.__naming_ability

    def set_naming_ability(self, naming_ability: ClientNamingAbility) -> None:
        self.__naming_ability = naming_ability
