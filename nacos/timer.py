# -*- coding=utf-8 -*-

"""
 Verion: 1.0
 Since : 2.7.18
 Author: zhangjian
 Site: https://github.com/xarrow/
 File: timer.py
 Time: 2020/8/30
 
 Add New Functional nacos-sdk-python
"""

import threading
import time
from typing import Callable


class NacosTimer(object):
    __slots__ = ['_name', '_timer', '_fn', '_interval', '_ignore_ex', '_on_result', '_on_exception',
                 '_args', '_kwargs']

    def __init__(self,
                 name: str,
                 fn: Callable,
                 interval: int = 7,
                 *args,
                 **kwargs):
        # timer name
        self._name = name
        # Thread.Timer
        self._timer = None
        # function which callable
        self._fn = fn
        # timer interval default 7s
        self._interval = interval
        # whether ignore invoke exception
        self._ignore_ex = False
        self._on_result = None
        self._on_exception = None
        # function args
        self._args = args
        # function kwargs
        self._kwargs = kwargs

    @property
    def name(self) -> str:
        return self._name

    def set_name(self, name: str):
        self._name = name
        return self

    @property
    def fn(self) -> Callable:
        return self._fn

    def set_fn(self, fn: Callable):
        self._fn = fn
        return self

    @property
    def interval(self, ) -> int:
        return self._interval

    def set_interval(self, interval: int):
        self._interval = interval
        return self

    @property
    def ignore_ex(self) -> bool:
        return self._ignore_ex

    def set_ignore_ex(self, ignore_ex: bool):
        self._ignore_ex = ignore_ex
        return self

    @property
    def on_result(self) -> Callable:
        return self._on_result

    def set_on_result(self, fn: Callable):
        self._on_result = fn
        return self

    @property
    def on_exception(self) -> Callable:
        return self._on_exception

    def set_on_exception(self, fn: Callable):
        self._on_exception = fn
        return self

    # ....

    def scheduler(self):
        try:
            res = self._fn(*self._args, **self._kwargs)
            if self._on_result:
                self._on_result(res)
        except Exception as ex:
            if self._on_exception:
                self._on_exception(ex)
            if not self._ignore_ex:
                # stop timer
                raise ex
        self._timer = threading.Timer(self._interval, self.scheduler, )
        self._timer.start()

    def cancel(self):
        if self._timer:
            self._timer.cancel()


class NacosTimerManager(object):
    def __init__(self, ):
        self._timers_container = {}
        self._executed = False

    def all_timers(self):
        return self._timers_container

    def add_timer(self, timer: NacosTimer):
        self._timers_container[timer.name] = timer
        return self

    def execute(self):
        if self._executed:
            return
        for name, timer in self._timers_container.items():
            timer.scheduler()
        self._executed = True

    def cancel_timer(self, timer_name: str = None, ):
        """
        cancel timer , and  nacos timer still in container
        it can execute again.
        :param timer_name:
        :return:
        """
        timer = self._timers_container.get(timer_name)
        if timer:
            timer.cancel()

    def cancel(self):
        """
        cancel all timer in container
        :return:
        """
        for _, timer in self._timers_container.items():
            timer.cancel()

    def stop_timer(self, timer_name: str):
        """
        cancel nacos timer and remove it from timer container
        :param timer_name:
        :return:
        """
        self.cancel_timer(timer_name)
        self._timers_container.pop(timer_name)

    def stop(self):
        """
        remove all timer, and it can not execute again
        """
        self.cancel()
        self._timers_container.clear()


def print_time(host, port):
    if port == 80:
        pass
    print(time.time(), host, port)
    return "OK"


def timer_on_result(res):
    print(res)


def timer_on_exception(ex):
    print(ex)

# sample1
# s1 = NacosTimer("s1", print_time, 2, "localhost", 8080)
# .set_on_result(timer_on_result)
# s2 = NacosTimer("s2", print_time, 2, "127.0.0.1", 80)
# .set_on_exception(timer_on_exception).set_ignore_ex(True)
# s1.scheduler()
# s2.scheduler()
# sm = NacosTimerManager()
# sm.add_timer(s1)
# sm.add_timer(s2)
# sm.execute()
# sm.execute()
# print("final")
