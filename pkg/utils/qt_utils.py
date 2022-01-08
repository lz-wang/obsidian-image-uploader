import threading

from loguru import logger as log
from PySide6.QtWidgets import QLabel


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


def better_emit(signal, emit_args: tuple = None):
    """为避免Qt原发送信号过程中由于网络时延造成的UI卡顿，
    此处启动了额外的线程发送信号

    Args:
        signal: Qt信号
        emit_args: 信号参数
    """
    emit_thread = threading.Thread(target=signal.emit,
                                   args=[] if emit_args is None else emit_args)
    emit_thread.start()
