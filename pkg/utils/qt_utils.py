from loguru import logger



log = logger


def reconnect(signal, slot):
    try:
        signal.disconnect()
    except Exception as e:
        log.warning(f'Qt disconnect error, detail: {str(e)}')
    finally:
        signal.connect(slot)
