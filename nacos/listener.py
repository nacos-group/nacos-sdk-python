# -*- coding=utf-8 -*-
from abc import abstractmethod


class Event(object):
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"
    pass


class Listener(object):
    def __init__(self, fn, ):
        self._fn = fn

    @abstractmethod
    def action(self, event, *args, **kwargs):
        self._fn(*args, **kwargs)
