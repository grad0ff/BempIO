import os
import sys
import time
import functools


def resource_path(relative_path):
    """Возвращает путь для добавляемых в *.exe ресурсов (иконки, звуки и т.п.)"""

    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def time_check(func):
    """секундомер выполнения метода"""

    @functools.wraps(func)
    def wrapper(*args):
        t1 = time.time()
        func(*args)
        t2 = time.time()
        print(func.__name__, t2 - t1)

    return wrapper
