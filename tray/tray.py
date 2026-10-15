import requests
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from ui.history_dialog import HistoryDialog
from ui.settings_dialog import SettingsDialog
from ui.theme import make_icon
from utils.paths import VERSION


class Tray(QSystemTrayIcon):
    def __init__(self, controller, store, history):
        super().__init__(make_icon())
        self.controller, self.store, self.history = controller, store, history
        self._settings_dlg = self._history_dlg = None
        self._icons = {s: make_icon(s) for s in ("idle", "listening", "transcribing", "cleaning", "error")}

        menu = QMenu()
        self.dictate_action = QAction("Start Dictation", menu, triggered=controller.toggle)
        menu.addAction(self.dictate_action)
        menu.addSeparator()
        menu.addAction(QAction("Settings", menu, triggered=self.show_settings))
        menu.addAction(QAction("History", menu, triggered=self.show_history))
        menu.addAction(QAction("Check Update", menu, triggered=self.check_update))
        menu.addSeparator()
        menu.addAction(QAction("Exit", menu, triggered=QApplication.quit))
        self.setContextMenu(menu)
        self._menu = menu
        self.activated.connect(lambda reason: reason == QSystemTrayIcon.DoubleClick and self.show_history())

        controller.state_changed.connect(self.on_state)
        controller.message.connect(lambda t, b: self.showMessage(t, b, QSystemTrayIcon.Information, 4000))
        self.on_state("idle")

    def on_state(self, state: str) -> None:
        self.setIcon(self._icons.get(state, self._icons["idle"]))
        self.setToolTip(f"VoiceFlow AI — {state}  ({self.store.settings.hotkey})")
        self.dictate_action.setText("Stop Dictation" if state == "listening" else "Start Dictation")

    def show_settings(self) -> None:
        if self._settings_dlg is None or not self._settings_dlg.isVisible():
            self._settings_dlg = SettingsDialog(self.store, self.controller.apply_settings)
        self._settings_dlg.show()
        self._settings_dlg.raise_()
        self._settings_dlg.activateWindow()

    def show_history(self) -> None:
        if self._history_dlg is None or not self._history_dlg.isVisible():
            self._history_dlg = HistoryDialog(self.history)
        else:
            self._history_dlg.refresh()
        self._history_dlg.show()
        self._history_dlg.raise_()
        self._history_dlg.activateWindow()

    def check_update(self) -> None:
        url = self.store.settings.update_url
        if not url:
            QMessageBox.information(None, "Check Update",
                                    f"VoiceFlow AI {VERSION}\n\nNo update URL is configured "
                                    "(set \"update_url\" in settings.json). No network request was made.")
            return
        try:
            data = requests.get(url, timeout=8).json()
            latest = str(data.get("version", ""))
            if latest and _ver(latest) > _ver(VERSION):
                QMessageBox.information(None, "Update available",
                                        f"Version {latest} is available.\n{data.get('url', '')}")
            else:
                QMessageBox.information(None, "Check Update", f"You are on the latest version ({VERSION}).")
        except Exception as e:
            QMessageBox.warning(None, "Check Update", f"Update check failed: {e}")


def _ver(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.lstrip("v").split(".") if p.isdigit())
