import logging

LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(filename)s, line.%(lineno)d]: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name):
    """https://www.cnblogs.com/huang-yc/p/9209096.html"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level=logging.INFO)
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(sh)

    return logger
