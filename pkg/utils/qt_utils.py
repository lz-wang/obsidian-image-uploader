from pkg.utils.logger import get_logger


log = get_logger('qt utils')


def reconnect(signal, slot):
    try:
        signal.disconnect()
    except Exception as e:
        log.warning(f'Qt disconnect error, detail: {str(e)}')
    finally:
        signal.connect(slot)
