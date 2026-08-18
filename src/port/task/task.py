import functools
import logging
import time


def log_task_duration(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        task_name = func.__name__
        start_time = time.perf_counter()
        logging.info("Tarea '%s' iniciada", task_name)
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start_time
            logging.info("Tarea '%s' finalizada en %.2f segundos", task_name, elapsed)

    return wrapper