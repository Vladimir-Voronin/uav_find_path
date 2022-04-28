class SearchMethodException(Exception):
    def __init__(self, txt):
        self.txt = txt


class FailFindPathException(SearchMethodException):
    def __init__(self, txt):
        self.txt = txt


class TimeToSucceedException(SearchMethodException):
    def __init__(self, txt):
        self.txt = txt
