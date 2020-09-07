# -*- coding=utf-8 -*-
from abc import abstractmethod


class Event(object):
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"
    pass


class AbstractListener(object):
    def __init__(self, listener_name):
        self._listener_name = listener_name

    @property
    def listener_name(self):
        return self._listener_name

    @abstractmethod
    def launch(self, *args, **kwargs):
        pass


class SubscribeListener(AbstractListener):
    def __init__(self, fn, listener_name):
        super(SubscribeListener, self).__init__(listener_name)
        self._fn = fn

    def launch(self, event, *args, **kwargs):
        self._fn(event, *args, **kwargs)


class ListenerManager(object):
    def __init__(self):
        self._listener_container = dict()

    @property
    def listener_container(self):
        return self._listener_container

    def all_listeners(self):
        return self._listener_container

    def add_listener(self, listener):
        self._listener_container[listener.listener_name] = listener
        return self

    def remove_listener(self, listener_name):
        if listener_name not in self._listener_container.keys():
            return self
        self._listener_container.pop(listener_name)
        return self

    def do_launch(self, *args, **kwargs):
        for listener in self._listener_container:
            listener.launch(*args, **kwargs)
