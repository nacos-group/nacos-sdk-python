import time


def get_current_time_millis():
    t = time.time()
    return int(round(t * 1000))