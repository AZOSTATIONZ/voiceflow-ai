"""Renders assets/icon.ico for the executable: python -m utils.make_icon"""
import sys

from PySide6.QtGui import QGuiApplication

from ui.theme import make_pixmap
from utils.paths import resource_path

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    out = resource_path("assets/icon.ico")
    out.parent.mkdir(exist_ok=True)
    if not make_pixmap("idle", 256).save(str(out), "ICO"):
        make_pixmap("idle", 256).save(str(out.with_suffix(".png")), "PNG")
        print("ICO writer unavailable; wrote icon.png instead")
    else:
        print(f"wrote {out}")
