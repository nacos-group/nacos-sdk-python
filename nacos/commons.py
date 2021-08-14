import sys


def synchronized_with_attr(attr_name):
    def decorator(func):
        def synced_func(*args, **kws):
            self = args[0]
            lock = getattr(self, attr_name)
            with lock:
                return func(*args, **kws)

        return synced_func

    return decorator


def truncate(ori_str, length=100):
    if not ori_str:
        return ""
    return ori_str[:length] + "..." if len(ori_str) > length else ori_str


def python_version_bellow(version):
    if not version:
        return False

    sp = [int(s) for s in version.split(".")]
    for i in range(len(sp) if len(sp) <= 3 else 3):
        if sp[i] == sys.version_info[i]:
            continue

        return sys.version_info[i] < sp[i]

    return False