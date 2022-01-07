import logging
from logging import handlers

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
