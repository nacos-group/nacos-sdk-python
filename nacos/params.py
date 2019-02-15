VALID_CHAR = set(['_', '-', '.', ':'])
PARAM_KEYS = ["data_id", "group"]
DEFAULT_GROUP_NAME = "DEFAULT_GROUP"


def is_valid(param):
    if not param:
        return False
    for i in param:
        if i.isalpha() or i.isdigit() or i in VALID_CHAR:
            continue
        return False
    return True


def check_params(params):
    for p in PARAM_KEYS:
        if p in params and not is_valid(params[p]):
            return False
    return True


def group_key(data_id, group, namespace):
    return "+".join([data_id, group, namespace])


def parse_key(key):
    sp = key.split("+")
    return sp[0], sp[1], sp[2]
