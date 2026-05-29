import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def main():
    if "--launch" in sys.argv:
        subprocess.run([sys.executable, str(BASE_DIR / "app.py")], check=False)
        return
    print("Usage: illi-ai --launch")
    print("This command starts the ILLI OS Streamlit HUD.")
