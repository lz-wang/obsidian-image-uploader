import os.path
import sys

from loguru import logger


def add_log_to_console():
    logger.add(
        sink=sys.stderr,
        level='INFO',
        format='<green>{time:MM-DD HH:mm:ss.SSS}</green> '
               '| <level>{level: <8}</level> '
               '| <cyan>{name: <30}</cyan>: <cyan>{function: <18}'
               '</cyan>: <cyan>line.{line: <4}</cyan> | '
               '<level>{message}</level> '
    )


def add_log_to_file(log_dir: str):
    logger.add(
        sink=os.path.join(log_dir, 'log_{time:YYYY_MM}.log'),
        level='DEBUG',
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} "
               "| {level: <8} | {name: <20} -> {function: <16} -> line.{line} | {message}",
        rotation='5 MB',  # create a new log file when log file size > 5 MB
        retention='3 months',  # keep log file time: "1 week, 3 days"、"2 months"
        backtrace=True,
        encoding="utf-8",
        compression='zip'  # zip、tar、gz、tar.gz
    )


def show_log_msgs():
    logger.warning('*'*50)
    logger.trace('This is a test TRACE message.')
    logger.debug('This is a test DEBUG message.')
    logger.info('This is a test INFO message.')
    logger.success('This is a test SUCCESS message.')
    logger.warning('This is a test WARNING message.')
    logger.error('This is a test ERROR message.')
    logger.critical('This is a test CRITICAL message.')
    logger.warning('*'*50)


def init_logger(log_dir: str = None):
    """loguru全局初始化，不需要再次导入"""
    # 移除掉自带的sink
    logger.remove()

    # to console
    add_log_to_console()

    # to file
    if log_dir is not None:
        add_log_to_file(log_dir)

    # simple test log output
    show_log_msgs()
