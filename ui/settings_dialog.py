import logging

from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget)

from ai.providers import create_provider
from settings.settings import LANGUAGES, PROVIDERS, WHISPER_MODELS
from ui.theme import make_icon
from utils.autostart import set_autostart

log = logging.getLogger(__name__)

PROVIDER_LABELS = {"ollama": "Ollama (local, free)", "anthropic": "Anthropic Claude", "openai": "OpenAI GPT",
                   "gemini": "Google Gemini", "mistral": "Mistral", "deepseek": "DeepSeek"}


class SettingsDialog(QDialog):
    def __init__(self, store, on_saved, parent=None):
        super().__init__(parent)
        self.store, self.on_saved = store, on_saved
        self.setWindowTitle("VoiceFlow AI — Settings")
        self.setWindowIcon(make_icon())
        self.setMinimumWidth(520)
        s = store.settings
        self._models = dict(s.models)
        self._keys = dict(s.api_keys)

        tabs = QTabWidget()
        tabs.addTab(self._general_tab(s), "General")
        tabs.addTab(self._ai_tab(s), "AI")
        tabs.addTab(self._privacy_tab(), "Privacy")

        save = QPushButton("Save", objectName="primary", clicked=self._save)
        cancel = QPushButton("Cancel", clicked=self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        lay = QVBoxLayout(self)
        lay.addWidget(tabs)
        lay.addLayout(buttons)

    def _general_tab(self, s) -> QWidget:
        w = QWidget()
        f = QFormLayout(w)
        self.mic = QComboBox()
        self.mic.addItem("System default", None)
        try:
            from audio.recorder import list_input_devices
            for idx, name in list_input_devices():
                self.mic.addItem(name, idx)
        except Exception as e:
            log.warning("could not list microphones: %s", e)
        self.mic.setCurrentIndex(max(0, self.mic.findData(s.mic_device)))
        self.whisper = QComboBox()
        self.whisper.addItems(WHISPER_MODELS)
        self.whisper.setCurrentText(s.whisper_model)
        self.whisper.setToolTip("tiny/base: fastest · small: balanced · medium/large: most accurate, needs more RAM")
        self.language = QComboBox()
        for label, code in LANGUAGES.items():
            self.language.addItem(label, code)
        self.language.setCurrentIndex(max(0, self.language.findData(s.language)))
        self.hotkey = QLineEdit(s.hotkey)
        self.hotkey.setPlaceholderText("e.g. ctrl+windows, ctrl+shift+space, right alt")
        self.auto_paste = QCheckBox("Paste result into the active app automatically", checked=s.auto_paste)
        self.clipboard = QCheckBox("Keep result in the clipboard after pasting", checked=s.clipboard_mode)
        self.boot = QCheckBox("Start VoiceFlow AI when Windows starts", checked=s.start_on_boot)
        f.addRow("Microphone", self.mic)
        f.addRow("Whisper model", self.whisper)
        f.addRow("Language", self.language)
        f.addRow("Hold-to-talk hotkey", self.hotkey)
        f.addRow(self.auto_paste)
        f.addRow(self.clipboard)
        f.addRow(self.boot)
        return w

    def _ai_tab(self, s) -> QWidget:
        w = QWidget()
        f = QFormLayout(w)
        self.ai_cleanup = QCheckBox("Polish text with AI before pasting", checked=s.ai_cleanup)
        self.use_context = QCheckBox("Use active app and surrounding text as context", checked=s.use_context)
        self.provider = QComboBox()
        for p in PROVIDERS:
            self.provider.addItem(PROVIDER_LABELS[p], p)
        self.model = QLineEdit()
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.Password)
        self.ollama_host = QLineEdit(s.ollama_host)
        self.cloud_note = QLabel()
        self.cloud_note.setWordWrap(True)
        test = QPushButton("Test connection", clicked=self._test)
        self._current = None
        self.provider.currentIndexChanged.connect(self._provider_changed)
        self.provider.setCurrentIndex(max(0, self.provider.findData(s.provider)))
        self._provider_changed()
        f.addRow(self.ai_cleanup)
        f.addRow(self.use_context)
        f.addRow("Provider", self.provider)
        f.addRow("Model", self.model)
        f.addRow("API key", self.api_key)
        f.addRow("Ollama host", self.ollama_host)
        f.addRow(self.cloud_note)
        f.addRow(test)
        return w

    def _privacy_tab(self) -> QWidget:
        w = QWidget()
        lab = QLabel(
            "<b>VoiceFlow AI collects no telemetry, analytics or tracking.</b><br><br>"
            "Audio is transcribed locally with Whisper and never leaves this PC.<br><br>"
            "Network use happens only when:<ul>"
            "<li>a Whisper model is downloaded the first time it is selected (Hugging Face);</li>"
            "<li>a <b>cloud</b> AI provider is selected — the transcript, app name, window title and up to "
            "500 characters around the cursor are sent to that provider;</li>"
            "<li>you click <i>Check for updates</i> and an update URL is configured.</li></ul>"
            "With Ollama (default), everything stays on localhost.<br><br>"
            "Settings, API keys and history are stored in %APPDATA%\\VoiceFlowAI.")
        lab.setWordWrap(True)
        QVBoxLayout(w).addWidget(lab)
        return w

    def _provider_changed(self) -> None:
        if self._current:
            self._models[self._current] = self.model.text().strip()
            self._keys[self._current] = self.api_key.text().strip()
        p = self.provider.currentData()
        self._current = p
        self.model.setText(self._models.get(p, ""))
        self.api_key.setText(self._keys.get(p, ""))
        local = p == "ollama"
        self.api_key.setEnabled(not local)
        self.ollama_host.setEnabled(local)
        self.model.setToolTip("Any Ollama model you have pulled, e.g. llama3, llama3.2, gemma2, mistral, deepseek-r1"
                              if local else "Model id from the provider's documentation")
        self.cloud_note.setText("Runs fully on this PC." if local else
                                "⚠ Cloud provider: transcripts and context are sent to this service.")

    def _collect(self):
        self._provider_changed()  # flush current fields into dicts
        s = self.store.settings
        s.mic_device = self.mic.currentData()
        s.whisper_model = self.whisper.currentText()
        s.language = self.language.currentData()
        s.hotkey = self.hotkey.text().strip().lower() or "ctrl+windows"
        s.auto_paste = self.auto_paste.isChecked()
        s.clipboard_mode = self.clipboard.isChecked()
        s.start_on_boot = self.boot.isChecked()
        s.ai_cleanup = self.ai_cleanup.isChecked()
        s.use_context = self.use_context.isChecked()
        s.provider = self.provider.currentData()
        s.models = {k: v for k, v in self._models.items() if v}
        s.api_keys = {k: v for k, v in self._keys.items() if v}
        s.ollama_host = self.ollama_host.text().strip() or "http://127.0.0.1:11434"
        return s

    def _test(self) -> None:
        s = self._collect()
        try:
            out = create_provider(s).complete("Reply with exactly: OK", "ping")
            QMessageBox.information(self, "Connection OK", f"{s.provider} replied: {out.strip()[:200]}")
        except Exception as e:
            QMessageBox.warning(self, "Connection failed", str(e))

    def _save(self) -> None:
        from app.hotkey import parse_hotkey
        s = self._collect()
        try:
            parse_hotkey(s.hotkey)
        except ValueError:
            QMessageBox.warning(self, "Invalid hotkey", "Enter keys joined with +, e.g. ctrl+windows")
            return
        try:
            set_autostart(s.start_on_boot)
        except OSError as e:
            QMessageBox.warning(self, "Startup", f"Could not update startup entry: {e}")
        self.store.save()
        self.on_saved()
        self.accept()
