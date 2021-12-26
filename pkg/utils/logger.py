import logging
import sys
from loguru import logger

LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(filename)s, line.%(lineno)d]: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger2(name):
    """https://www.cnblogs.com/huang-yc/p/9209096.html"""
    my_logger = logging.getLogger(name)
    if not my_logger.handlers:
        my_logger.setLevel(level=logging.INFO)
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter(LOG_FORMAT))
        my_logger.addHandler(sh)

    return my_logger


def get_logger(name=None):
    # remove default logger
    logger.remove()

    # to console
    logger.add(
        sink=sys.stdout,
        level='DEBUG',
        format='<green>{time:MM-DD HH:mm:ss.SSS}</green> '
               '| <level>{level: <8}</level> '
               '| <cyan>{name: <30}</cyan>: <cyan>{function: <18}</cyan>: <cyan>line.{line: <4}</cyan> | '
               '<level>{message}</level> '
    )

    # to file
    logger.add(
        sink='./log/loguru_{time:YYYY_MM}.log',
        level='DEBUG',
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} "
               "| {level: <8} | {name: <20} -> {function: <16} -> line.{line} | {message}",
        rotation='5 MB',  # create a new log file when log file size > 5 MB
        retention='3 months',  # keep log file time: "1 week, 3 days"、"2 months"
        backtrace=True,
        enqueue=True,
        encoding="utf-8",
        compression='zip'  # zip、tar、gz、tar.gz
    )

    return logger

