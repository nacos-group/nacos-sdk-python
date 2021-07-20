class ClientRemoteAbility:
    def __init__(self):
        self.support_remote_connection = False

    def is_support_remote_connection(self) -> bool:
        return self.support_remote_connection

    def set_support_remote_connection(self, support_remote_connection: bool) -> None:
        self.support_remote_connection = support_remote_connection
