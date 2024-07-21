import json
import time


def to_json_string(obj):
    try:
        return json.dumps(obj)
    except (TypeError, ValueError) as e:
        print(f"Error serializing object to JSON: {e}")
        return None


def current_millis():
    return int(time.time() * 1000)
