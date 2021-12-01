

def reconnect(signal, slot):
    try:
        signal.disconnect()
    except:
        pass
    signal.connect(slot)
