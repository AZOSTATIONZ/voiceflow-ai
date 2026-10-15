from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPixmap

ACCENT = "#7c5cff"
STATE_COLORS = {"idle": ACCENT, "listening": "#ff4d6d", "transcribing": "#ffb020",
                "cleaning": "#2ec4b6", "error": "#888888"}

DARK_QSS = f"""
QWidget {{ background: #15161a; color: #e6e6ea; font-family: 'Segoe UI'; font-size: 10pt; }}
QDialog {{ background: #15161a; }}
QGroupBox {{ border: 1px solid #2a2c33; border-radius: 8px; margin-top: 14px; padding: 10px; font-weight: 600; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #a9a9b3; }}
QLineEdit, QComboBox, QPlainTextEdit, QTableWidget, QSpinBox {{
    background: #1e2026; border: 1px solid #2f323a; border-radius: 6px; padding: 5px; selection-background-color: {ACCENT}; }}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{ border: 1px solid {ACCENT}; }}
QComboBox QAbstractItemView {{ background: #1e2026; selection-background-color: {ACCENT}; }}
QPushButton {{ background: #262830; border: 1px solid #33363f; border-radius: 6px; padding: 6px 14px; }}
QPushButton:hover {{ background: #30333c; }}
QPushButton#primary {{ background: {ACCENT}; border: none; color: white; font-weight: 600; }}
QPushButton#primary:hover {{ background: #8d71ff; }}
QCheckBox::indicator {{ width: 16px; height: 16px; }}
QHeaderView::section {{ background: #1b1d22; color: #a9a9b3; border: none; padding: 6px; }}
QTableWidget {{ gridline-color: #2a2c33; }}
QTabWidget::pane {{ border: 1px solid #2a2c33; border-radius: 8px; }}
QTabBar::tab {{ background: #1b1d22; padding: 8px 16px; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
QTabBar::tab:selected {{ background: #262830; color: white; }}
QMenu {{ background: #1e2026; border: 1px solid #2f323a; padding: 4px; }}
QMenu::item {{ padding: 6px 22px; border-radius: 4px; }}
QMenu::item:selected {{ background: {ACCENT}; }}
QToolTip {{ background: #1e2026; color: #e6e6ea; border: 1px solid #2f323a; }}
"""


def make_icon(state: str = "idle", size: int = 64) -> QIcon:
    return QIcon(make_pixmap(state, size))


def make_pixmap(state: str = "idle", size: int = 64) -> QPixmap:
    """Draws a microphone glyph on a coloured disc, so no binary assets are required."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(STATE_COLORS.get(state, ACCENT)))
    p.drawEllipse(QRectF(0, 0, size, size))
    s = size / 64
    p.setBrush(QColor("white"))
    p.drawRoundedRect(QRectF(24 * s, 12 * s, 16 * s, 26 * s), 8 * s, 8 * s)
    path = QPainterPath()
    path.moveTo(QPointF(18 * s, 30 * s))
    path.cubicTo(QPointF(18 * s, 50 * s), QPointF(46 * s, 50 * s), QPointF(46 * s, 30 * s))
    pen = p.pen()
    pen.setColor(QColor("white"))
    pen.setWidthF(4 * s)
    pen.setStyle(Qt.SolidLine)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)
    p.drawLine(QPointF(32 * s, 45 * s), QPointF(32 * s, 52 * s))
    p.end()
    return pm
