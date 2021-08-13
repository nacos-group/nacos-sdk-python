from abc import ABCMeta


class AbstractSelector(metaclass=ABCMeta):
    def __init__(self, set_type):
        self.type = set_type

    def get_type(self):
        return self.type
