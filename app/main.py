import logging
import sys

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from utils.log import setup_logging
from utils.paths import APP_NAME, VERSION, data_dir

log = logging.getLogger(__name__)


def run() -> int:
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)
    app.setQuitOnLastWindowClosed(False)

    lock = QLockFile(str(data_dir() / "instance.lock"))
    if not lock.tryLock(100):
        QMessageBox.information(None, "VoiceFlow AI", "VoiceFlow AI is already running (see the system tray).")
        return 0

    # Heavy imports after the lock so a second launch exits instantly.
    from app.controller import Controller
    from db.history import History
    from settings.settings import SettingsStore
    from tray.tray import Tray
    from ui.overlay import Overlay
    from ui.theme import DARK_QSS, make_icon

    app.setStyleSheet(DARK_QSS)
    app.setWindowIcon(make_icon())

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "VoiceFlow AI", "No system tray available.")
        return 1

    store = SettingsStore()
    history = History()
    controller = Controller(store, history)
    overlay = Overlay()
    controller.state_changed.connect(overlay.set_state)
    tray = Tray(controller, store, history)
    tray.show()
    controller.start()
    app.aboutToQuit.connect(controller.shutdown)

    first_run = not store.path.exists()
    if first_run:
        store.save()
        tray.showMessage("VoiceFlow AI is running",
                         f"Hold {store.settings.hotkey.upper()} and speak. Right-click the tray icon for settings.",
                         QSystemTrayIcon.Information, 6000)
    log.info("VoiceFlow AI %s started", VERSION)
    return app.exec()
