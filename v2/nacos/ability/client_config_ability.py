class ClientConfigAbility:
    def __init__(self):
        self.support_remote_metrics = False

    def is_support_remote_metrics(self):
        return self.support_remote_metrics

    def set_support_remote_metrics(self, support_remote_metrics):
        self.support_remote_connection = support_remote_metrics