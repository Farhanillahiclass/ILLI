import subprocess
import platform
import ctypes
from ctypes import wintypes
import os


def sleep():
    if platform.system() != 'Windows':
        raise RuntimeError('Windows only')
    # Use SetSuspendState via powrprof
    subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState 0,1,0"], shell=False)


def restart():
    if platform.system() != 'Windows':
        raise RuntimeError('Windows only')
    subprocess.Popen(["shutdown", "/r", "/t", "0"], shell=False)


def shutdown():
    if platform.system() != 'Windows':
        raise RuntimeError('Windows only')
    subprocess.Popen(["shutdown", "/s", "/t", "0"], shell=False)


def clear_recycle_bin():
    if platform.system() != 'Windows':
        raise RuntimeError('Windows only')
    try:
        shell32 = ctypes.windll.shell32
        SHERB_NOCONFIRMATION = 0x00000001
        SHEmptyRecycleBin = shell32.SHEmptyRecycleBinW
        SHEmptyRecycleBin(None, None, SHERB_NOCONFIRMATION)
        return True
    except Exception:
        return False

