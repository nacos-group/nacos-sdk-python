from v2.nacos.common.lifecycle.closeable import Closeable


class FailoverReactor(Closeable):
    def shutdown(self) -> None:
        pass
