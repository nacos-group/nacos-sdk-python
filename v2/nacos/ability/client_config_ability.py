class ClientConfigAbility:
    def __init__(self):
        self.support_remote_metrics = False

    def is_support_remote_metrics(self) -> bool:
        return self.support_remote_metrics

    def set_support_remote_metrics(self, support_remote_metrics: bool) -> None:
        self.support_remote_metrics = support_remote_metrics
