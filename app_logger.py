import logging
import sys
import app_service

__log_format = f"%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"

__log_file = app_service.resource_path('log/app.log')


def get_app_logger(name):
    logger = logging.getLogger(name)
    mode = 'a'
    if sys.getsizeof(__log_file) > 1000:
        mode = 'w'
    file_handler = logging.FileHandler(filename=__log_file, encoding='utf-8', mode=mode)
    file_handler.setFormatter(logging.Formatter(__log_format))
    logger.addHandler(file_handler)
    return logger
