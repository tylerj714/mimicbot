#! logging_manager.py
# a class for managing logging across modules

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv

load_dotenv()
BASE_PATH = os.getenv('BASE_PATH')

def create_logger(path):
    created_logger = logging.getLogger('bankerbot_logger')

    file_path = os.path.join(path, "bankerbot_log.txt")

    handler = TimedRotatingFileHandler(file_path,
                                       when="d",
                                       interval=1,
                                       backupCount=15)
    fmt = '[%(asctime)s] [%(levelname)s] - %(message)s'
    formatter = logging.Formatter(fmt=fmt, datefmt='%Y%m%d %H:%M:%S')
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(logging.INFO)

    created_logger.addHandler(handler)
    created_logger.addHandler(console)
    created_logger.setLevel(logging.INFO)

    return created_logger


logger = create_logger(BASE_PATH)
