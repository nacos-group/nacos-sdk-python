from v2.nacos.common.lifecycle.closeable import Closeable


class FailoverReactor(Closeable):
    def __init__(self, service_info_holder, cache_dir):
        self.service_info_holder = service_info_holder
        self.cache_dir = cache_dir

    def shutdown(self) -> None:
        pass
