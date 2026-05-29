# illi_ai/hotkeys.py
import threading

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    keyboard = None

_listeners = []
_state = { 'ctrl': False, 'alt': False, 'i': False }


def _on_press(key):
    try:
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            _state['ctrl'] = True
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            _state['alt'] = True
        if hasattr(key, 'char') and key.char == 'i':
            _state['i'] = True
        if _state['ctrl'] and _state['alt'] and _state['i']:
            for cb in _listeners:
                try:
                    cb()
                except Exception:
                    pass
    except Exception:
        pass


def _on_release(key):
    try:
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            _state['ctrl'] = False
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            _state['alt'] = False
        if hasattr(key, 'char') and key.char == 'i':
            _state['i'] = False
    except Exception:
        pass


def start_listener(callback):
    if not PYNPUT_AVAILABLE:
        return None
    if callback not in _listeners:
        _listeners.append(callback)
    def thread_main():
        with keyboard.Listener(on_press=_on_press, on_release=_on_release) as listener:
            listener.join()
    t = threading.Thread(target=thread_main, daemon=True)
    t.start()
    return t

