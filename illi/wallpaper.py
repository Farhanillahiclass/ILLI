from ctypes import windll
import ctypes
import os
from pathlib import Path
from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parent


def generate_hex_grid(path: str, size: int = 1920, spacing: int = 60, color=(0,255,255,25)) -> str:
    img = Image.new('RGBA', (size, size), (0,0,0,255))
    draw = ImageDraw.Draw(img)
    w, h = img.size
    import math
    r = spacing // 2
    hex_h = math.sqrt(3) * r
    for y in range(0, h + int(hex_h), int(hex_h)):
        for x in range(0, w + spacing, spacing + r):
            offset = (y // int(hex_h)) % 2 * (spacing//2)
            cx = x + offset
            cy = y
            draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=color)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert('RGB').save(out)
    return str(out)


def set_wallpaper(image_path: str) -> bool:
    if os.name != 'nt':
        raise RuntimeError('Windows only')
    SPI_SETDESKWALLPAPER = 20
    res = windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)
    return bool(res)
