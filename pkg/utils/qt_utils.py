import threading
import time
from collections import Iterable

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QLabel
from loguru import logger as log


def reconnect(signal, slot):
    try:
        signal.disconnect()
    except Exception as e:
        log.debug(f'Qt disconnect error, detail: {str(e)}')
    finally:
        if isinstance(slot, list):
            for sl in slot:
                signal.connect(sl)
        else:
            signal.connect(slot)


def set_label_text(label: QLabel, text: str, level: str = 'INFO'):
    if level.upper() in ['INFO']:
        label.setStyleSheet("QLabel { color : #42a5f5; }")
    elif level.upper() in ['SUCCESS']:
        label.setStyleSheet("QLabel { color : #66bb6a; }")
    elif level.upper() in ['ERROR', 'FAIL']:
        label.setStyleSheet("QLabel { color : #ef5350; }")
    else:
        log.warning(f'Unknown label text level: {level}')
    label.setText(text)


def show_qthread_status(qt: QThread, name: str = None, delay: float = 0, log_level: str = 'INFO'):
    if delay > 0:
        time.sleep(delay)
    if not name:
        name = qt.objectName()
    msg = f'QThread: {name}, isRunning: {qt.isRunning()}, isFinished: {qt.isFinished()}'
    if log_level == 'WARNING':
        log.warning(msg)
    elif log_level == 'ERROR':
        log.error(msg)
    elif log_level == 'CRITICAL':
        log.critical(msg)
    elif log_level == 'DEBUG':
        log.debug(msg)
    else:
        log.info(msg)


def better_emit(signal, emit_args=None):
    """为避免Qt原发送信号过程中由于网络时延造成的UI卡顿，
    此处启动了额外的线程发送信号

    Args:
        signal: Qt信号
        emit_args: 信号参数
    """
    if emit_args is None:
        emit_args = []
    elif isinstance(emit_args, str):
        emit_args = (emit_args,)
    elif not isinstance(emit_args, Iterable):
        emit_args = (emit_args,)
    else:
        emit_args = tuple(emit_args)

    emit_thread = threading.Thread(target=signal.emit, args=emit_args)
    emit_thread.start()
