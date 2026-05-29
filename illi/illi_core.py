# illi_ai/illi_core.py
import os
import platform
import ctypes
import subprocess
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


def record_log(message: str):
    stamp = datetime.utcnow().strftime('%H:%M:%S')
    entry = f"[{stamp}] [ILLI CORE]: {message}"
    try:
        with open(LOG_DIR / 'core.log', 'a', encoding='utf-8') as fh:
            fh.write(entry + "\n")
    except Exception:
        pass


def set_windows_wallpaper(path: str) -> bool:
    if platform.system() != 'Windows':
        record_log('Wallpaper only supported on Windows')
        return False
    if not os.path.exists(path):
        record_log('Wallpaper path missing')
        return False
    SPI_SETDESKWALLPAPER = 20
    try:
        res = ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, str(path), 3)
        record_log(f'Wallpaper applied: {path}')
        return bool(res)
    except Exception as e:
        record_log(f'Wallpaper error: {e}')
        return False


def clear_recycle_bin() -> bool:
    if platform.system() != 'Windows':
        return False
    try:
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0)
        record_log('Recycle Bin cleared')
        return True
    except Exception as e:
        record_log(f'Clear recycle failed: {e}')
        return False


def run_power_command(action: str) -> bool:
    try:
        if platform.system() != 'Windows':
            record_log('Power commands are Windows-only')
            return False
        if action == 'shutdown':
            subprocess.Popen(['shutdown', '/s', '/t', '0'])
        elif action == 'restart':
            subprocess.Popen(['shutdown', '/r', '/t', '0'])
        elif action == 'sleep':
            subprocess.Popen(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'])
        else:
            record_log(f'Unknown power action: {action}')
            return False
        record_log(f'Power command executed: {action}')
        return True
    except Exception as e:
        record_log(f'Power command failed: {e}')
        return False


class AudioController:
    """Stub controller for audio; attempts to use Windows Core Audio if available.
    If not available, methods return False but do not raise."""
    def __init__(self):
        self.available = False
        try:
            import comtypes
            self.available = True
            record_log('comtypes present; audio control may be available')
        except Exception:
            record_log('comtypes not available; audio control disabled')
            self.available = False

    def mute(self):
        if not self.available:
            record_log('Audio mute requested but not available')
            return False
        record_log('Audio mute attempted')
        return False

    def unmute(self):
        if not self.available:
            record_log('Audio unmute requested but not available')
            return False
        record_log('Audio unmute attempted')
        return False


def safe_launch(path_or_name: str) -> bool:
    if not path_or_name:
        return False
    p = Path(path_or_name)
    try:
        if p.exists():
            os.startfile(str(p))
            record_log(f'Launched: {p}')
            return True
        candidates = [Path('C:/Program Files'), Path('C:/Program Files (x86)'), Path.home()]
        for c in candidates:
            if not c.exists():
                continue
            for root, dirs, files in os.walk(c):
                for f in files:
                    if path_or_name.lower() in f.lower():
                        target = Path(root) / f
                        os.startfile(str(target))
                        record_log(f'Launched via search: {target}')
                        return True
    except Exception as e:
        record_log(f'Launch failed: {e}')
    return False


if __name__ == '__main__':
    print('ILLI core helper available')
