import sys
import winreg
from pathlib import Path

from utils.paths import APP_NAME

_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pyw = Path(sys.executable).with_name("pythonw.exe")
    main = Path(__file__).resolve().parent.parent / "main.py"
    return f'"{pyw if pyw.exists() else sys.executable}" "{main}"'


def set_autostart(enabled: bool) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _KEY, 0, winreg.KEY_SET_VALUE) as k:
        if enabled:
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, _command())
        else:
            try:
                winreg.DeleteValue(k, APP_NAME)
            except FileNotFoundError:
                pass
