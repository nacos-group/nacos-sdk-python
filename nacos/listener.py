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


class AbstractListenerManager(object):
    @abstractmethod
    def manager_context(self):
        pass

    @abstractmethod
    def add_listener(self, listener):
        pass

    @abstractmethod
    def remove_listener(self, listener_name):
        pass

    @abstractmethod
    def empty_listeners(self):
        pass

    @abstractmethod
    def do_launch(self):
        pass


class SubscribeListener(AbstractListener):
    def __init__(self, fn, listener_name):
        """

        :rtype: object
        """
        super(SubscribeListener, self).__init__(listener_name)
        self._fn = fn

    def launch(self, event, *args, **kwargs):
        self._fn(event, *args, **kwargs)


class SimpleListenerManager(AbstractListenerManager):

    def __init__(self):
        # listener_name --> listener
        self._listener_container = dict()

    @property
    def manager_context(self):
        return self._listener_container

    def merge_listeners(self, other_manager):
        if not other_manager or not isinstance(other_manager, AbstractListenerManager):
            return
        for listener_name, listener in other_manager.manager_context():
            self._listener_container[listener_name] = listener

    def all_listeners(self):
        return self._listener_container

    def add_listener(self, listener):
        self._listener_container[listener.listener_name] = listener
        return self

    def add_listeners(self, *listeners):
        [self.add_listener(listener) for listener in listeners]
        return self

    def remove_listener(self, listener_name):
        if listener_name not in self._listener_container.keys():
            return self
        self._listener_container.pop(listener_name)
        return self

    def empty_listeners(self):
        self._listener_container.clear()

    def do_launch(self, *args, **kwargs):
        for _, listener in self._listener_container.items():
            listener.launch(*args, **kwargs)
