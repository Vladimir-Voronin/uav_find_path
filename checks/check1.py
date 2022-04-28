import importlib
import threading
import time
from math import sqrt

from memory_profiler import profile, memory_usage
import tracemalloc

import sys


def do(array):
    is_here = [False] * (max(array) + 2)
    for i in array:
        if i > 0:
            is_here[i] = True

    for i in range(1, len(is_here)):
        if is_here[i] == False:
            return i


res = do([7, 8, 1, 9, 3, 6, 2, 4, 5, 10])
print(res)
