"""Small always-on-top pill that shows dictation state without stealing focus."""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from ui.theme import STATE_COLORS

LABELS = {"listening": "Listening…", "transcribing": "Transcribing…", "cleaning": "Polishing…",
          "error": "Something went wrong"}


class Overlay(QWidget):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool |
                         Qt.WindowDoesNotAcceptFocus | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.label)
        self._hide_timer = QTimer(self, singleShot=True, timeout=self.hide)

    def set_state(self, state: str) -> None:
        if state == "idle":
            self.hide()
            return
        color = STATE_COLORS.get(state, "#888")
        self.label.setText(f"●  {LABELS.get(state, state)}")
        self.label.setStyleSheet(
            f"background: rgba(20,21,26,235); color: white; border: 2px solid {color};"
            "border-radius: 18px; padding: 8px 20px; font: 600 10pt 'Segoe UI';")
        self.adjustSize()
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen.center().x() - self.width() // 2, screen.bottom() - self.height() - 40)
        self.show()
        self._hide_timer.stop()
        if state == "error":
            self._hide_timer.start(2500)
