import logging
import time
from functools import wraps
from logging import Logger


def backoff(
    start_sleep_time=0.1,
    factor=2,
    border_sleep_time=10,
    logger: Logger = logging.getLogger('backoff'),
):
    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            n = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    n += 1
                    sleep_time = min(start_sleep_time * (factor**n), border_sleep_time)
                    logger.error(f'{func.__name__} failed with {e}. Retrying in {sleep_time} seconds')
                    time.sleep(sleep_time)

        return inner

    return func_wrapper
