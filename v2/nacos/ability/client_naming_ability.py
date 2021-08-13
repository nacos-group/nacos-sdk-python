class ClientNamingAbility:
    def __init__(self):
        self.__support_delta_push = False
        self.__support_remote_metric = False

    def is_support_delta_push(self):
        return self.__support_delta_push

    def set_support_delta_push(self, support_delta_push):
        self.__support_delta_push = support_delta_push

    def is_support_remote_metric(self):
        return self.__support_remote_metric

    def set_support_remote_metric(self, support_remote_metric):
        self.__support_remote_metric = support_remote_metric