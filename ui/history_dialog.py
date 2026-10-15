from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QAbstractItemView, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QLineEdit,
                               QMessageBox, QPlainTextEdit, QPushButton, QSplitter, QTableWidget,
                               QTableWidgetItem, QVBoxLayout)

from ui.theme import make_icon


class HistoryDialog(QDialog):
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.history = history
        self.rows: list[dict] = []
        self.setWindowTitle("VoiceFlow AI — History")
        self.setWindowIcon(make_icon())
        self.resize(820, 560)

        self.search = QLineEdit(placeholderText="Search dictations…")
        self._debounce = QTimer(self, singleShot=True, interval=200, timeout=self.refresh)
        self.search.textChanged.connect(self._debounce.start)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Time", "App", "Mode", "Text"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._show_selected)

        self.detail = QPlainTextEdit(readOnly=True)
        split = QSplitter(Qt.Vertical)
        split.addWidget(self.table)
        split.addWidget(self.detail)
        split.setSizes([380, 140])

        buttons = QHBoxLayout()
        buttons.addWidget(QPushButton("Copy", clicked=self._copy))
        buttons.addWidget(QPushButton("Delete", clicked=self._delete))
        buttons.addWidget(QPushButton("Clear all", clicked=self._clear))
        buttons.addStretch()
        buttons.addWidget(QPushButton("Export…", objectName="primary", clicked=self._export))

        lay = QVBoxLayout(self)
        lay.addWidget(self.search)
        lay.addWidget(split)
        lay.addLayout(buttons)
        self.refresh()

    def refresh(self) -> None:
        self.rows = self.history.search(self.search.text().strip())
        self.table.setRowCount(len(self.rows))
        for i, r in enumerate(self.rows):
            for j, val in enumerate([r["created_at"].replace("T", " "), r["app"], r["category"],
                                     (r["final_text"] or "").replace("\n", " ")]):
                self.table.setItem(i, j, QTableWidgetItem(val or ""))
        self.table.resizeColumnsToContents()
        self.detail.clear()

    def _selected(self) -> dict | None:
        idx = self.table.currentRow()
        return self.rows[idx] if 0 <= idx < len(self.rows) else None

    def _show_selected(self) -> None:
        r = self._selected()
        if r:
            self.detail.setPlainText(f"{r['final_text']}\n\n— raw ({r['provider']}, {r['duration']}s) —\n{r['raw_text']}")

    def _copy(self) -> None:
        r = self._selected()
        if r:
            QGuiApplication.clipboard().setText(r["final_text"])

    def _delete(self) -> None:
        r = self._selected()
        if r:
            self.history.delete(r["id"])
            self.refresh()

    def _clear(self) -> None:
        if QMessageBox.question(self, "Clear history", "Delete all dictation history?") == QMessageBox.Yes:
            self.history.clear()
            self.refresh()

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export history", "voiceflow_history.txt",
                                              "Text (*.txt);;CSV (*.csv);;JSON (*.json)")
        if path:
            self.history.export(path, self.rows if self.search.text().strip() else None)
            QMessageBox.information(self, "Export", f"Saved {path}")
