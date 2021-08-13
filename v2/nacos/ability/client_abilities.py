from v2.nacos.ability import client_naming_ability, client_config_ability, client_remote_ability


class ClientAbilities:
    def __init__(self):
        self.__remote_ability = client_remote_ability.ClientRemoteAbility()
        self.__config_ability = client_config_ability.ClientConfigAbility()
        self.__naming_ability = client_naming_ability.ClientNamingAbility()

    def get_remote_ability(self):
        return self.__remote_ability

    def set_remote_ability(self, remote_ability):
        self.__remote_ability = remote_ability

    def get_config_ability(self):
        return self.__config_ability

    def set_config_ability(self, config_ability):
        self.__config_ability = config_ability

    def get_naming_ability(self):
        return self.__naming_ability

    def set_naming_ability(self, naming_ability):
        self.__naming_ability = naming_ability
