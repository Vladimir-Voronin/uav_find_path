from abc import ABCMeta, abstractmethod, abstractproperty


# This is an abstract for all search methods
class SearchMethod:
    __metaclass__ = ABCMeta
    @abstractmethod
    def runmethod(self): raise NotImplementedError


class One(SearchMethod):
    def runmethod(self):
        return self.__class__.__name__


class Two(SearchMethod):
    def runmethod(self):
        return self.__class__.__name__


# Этот класс не наследуется от SearchMethod
class Liar:
    def runmethod(self):
        return self.__class__.__name__


def check(method):
    if isinstance(method, SearchMethod):
        print(method.runmethod())


a = One()
b = Two()
c = Liar()
check(a)
check(b)
check(c)
