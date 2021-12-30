import logging
from logging import handlers
import sys
import traceback

from loguru import logger
import loguru

# %(asctime)s       年-月-日 时-分-秒,毫秒 2013-04-26 20:10:43,745
# %(filename)s      文件名，不含目录
# %(pathname)s      目录名，完整路径
# %(funcName)s      函数名
# %(levelname)s     级别名
# %(lineno)d        行号
# %(module)s        模块名
# %(message)s       消息体
# %(name)s          日志模块名
# %(process)d       进程id
# %(processName)s   进程名
# %(thread)d        线程id
# %(threadName)s    线程名

LOG_FORMAT = "%(asctime)s  |\t%(levelname)s\t| " \
             "%(filename)s, %(funcName)s, line.%(lineno)d | (%(threadName)s): %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name):
    """https://www.cnblogs.com/nancyzhu/p/8551506.html"""
    my_logger = logging.getLogger(name)
    if not my_logger.handlers:
        my_logger.setLevel(level=logging.INFO)
        # to console
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter(LOG_FORMAT))
        my_logger.addHandler(sh)
        # to file
        th = handlers.TimedRotatingFileHandler(
            filename='./log/oiu.log',
            when='W0',  # Wx --> Each Week x, S -> Seconds, M -> Minute, H -> Hour, D ->Day
            backupCount=5,
            encoding='utf-8')
        th.setFormatter(logging.Formatter(LOG_FORMAT))
        my_logger.addHandler(th)

    return my_logger


def get_logger2(name=None):
    """TODO: some bugs here, may leak memory"""
    # to console
    log_console_handler = dict(
        sink=sys.stdout,
        level='DEBUG',
        format='<green>{time:MM-DD HH:mm:ss.SSS}</green> '
               '| <level>{level: <8}</level> '
               '| <cyan>{name: <30}</cyan>: <cyan>{function: <18}</cyan>: <cyan>line.{line: <4}</cyan> | '
               '<level>{message}</level> ',
        enqueue=True
    )

    # to file
    log_file_handler = dict(
        sink='/Users/lzwang/Downloads/log/loguru_{time:YYYY_MM}.log',
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

    logger.configure(handlers=[log_console_handler, log_file_handler])

    return logger

