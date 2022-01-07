from abc import ABCMeta, abstractmethod, abstractproperty


class SearchMethodAbstract:
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, starting_point, target_point, obstacles): raise NotImplementedError

    @abstractmethod
    def run(self): raise NotImplementedError


