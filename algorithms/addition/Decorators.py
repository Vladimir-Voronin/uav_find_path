import functools
import time

measuretime_enabled = True
def measuretime(func):
    '''Decorator.

    Prints function execution time'''

    @functools.wraps(func)
    def inner(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter - start
        return result

    return inner if measuretime_enabled == True else func
