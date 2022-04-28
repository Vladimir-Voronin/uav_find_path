from abc import ABCMeta, abstractmethod, abstractproperty


class SearchMethodAbstract:
    __metaclass__ = ABCMeta

    @abstractmethod
    def run(self): raise NotImplementedError


