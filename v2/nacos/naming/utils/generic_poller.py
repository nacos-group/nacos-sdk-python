from threading import RLock

from v2.nacos.naming.utils.ipoller import Poller


class GenericPoller(Poller):
    def __init__(self, items: list):
        self.items = items
        self.index = 0
        self.lock = RLock()

    def next(self):
        with self.lock:
            self.index += 1
        return self.items[abs(self.index % len(self.items))]

    def refresh(self, items: list):
        return GenericPoller(items)
