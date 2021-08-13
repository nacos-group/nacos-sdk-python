import time

from v2.nacos.exception.nacos_exception import NacosException


def get_current_time_millis():
    t = time.time()
    return int(round(t * 1000))


def synchronized_with_attr(lock_name):
    def decorator(method):
        def synced_method(self, *args, **kws):
            lock = getattr(self, lock_name)
            with lock:
                return method(self, *args, **kws)

        return synced_method

    return decorator


class ConvertUtils:
    NULL_STR = "null"

    @staticmethod
    def to_int(val: str, default_value: int):
        if not val.strip() or val.lower() == ConvertUtils.NULL_STR:
            return default_value
        try:
            return int(val.strip())
        except NacosException:
            return default_value
