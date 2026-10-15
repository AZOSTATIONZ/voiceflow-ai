# VoiceFlow AI

**Hold Ctrl + Win, speak, release — your words land polished in whatever app you're using.**

VoiceFlow AI is a privacy-first Windows voice dictation tool. Speech is transcribed locally with [faster-whisper](https://github.com/SYSTRAN/faster-whisper), then cleaned up by an AI model that knows *which app you're in* — email, code, chat, or document — and pastes the result at your cursor.

The default setup is **completely free and works offline**: faster-whisper + [Ollama](https://ollama.com) running Llama 3.2. No account, no API key, no data ever leaves your PC.

---

## Quick Install (no Python needed)

1. **[⬇ Download VoiceFlowAI-Setup.exe](../../releases/latest)** — double-click, no admin rights required.
2. Install [Ollama](https://ollama.com) for AI text cleanup (free, runs locally):
   ```
   winget install Ollama.Ollama
   ollama pull llama3.2
   ```
3. Done. VoiceFlow AI starts in the system tray. Hold **Ctrl + Win** to dictate.

> **No GPU? No problem.** The app falls back to CPU automatically. AI cleanup still works with any Ollama model.

---

## How it works

```
Hold Ctrl+Win       Speak               Release
      │                │                    │
      ▼                ▼                    ▼
 [detect app]    [record audio]    [transcribe with Whisper]
  VS Code?                                  │
  Outlook?                                  ▼
  Slack?                          [AI cleanup — knows the app]
      │                                     │
      └──────────────────────────────────── ▼
                                    [paste at cursor]
```

### Context-aware modes

| App | Mode | Example output |
|---|---|---|
| Outlook / Gmail | **Email** | `Hi John,`<br>`Thank you for attending...`<br>`Best regards,` |
| VS Code / Cursor | **Programming** | Preserves identifiers, wraps them in backticks |
| Slack / Teams / Discord | **Chat** | Casual, short, no greeting |
| Word / Notion / Docs | **Document** | Formal prose with paragraphs |
| Everything else | **General** | Clean natural text |

Browsers are classified by **window title**, so Gmail in Chrome counts as Email.

### Before / after example

> *you say:* "okay so basically we need to update the api endpoint um and then make sure the json response is validated"

| App | After AI cleanup |
|---|---|
| Notepad (general) | We need to update the API endpoint and make sure the JSON response is validated. |
| VS Code | We need to update the `API` endpoint and make sure the `JSON` response is validated. |
| Slack | okay we need to update the api endpoint and validate the json response |

---

## Features

- **Hold-to-talk** — Ctrl+Win (fully configurable). Start menu is suppressed on Win key release.
- **Local STT** — faster-whisper (`base` by default; `tiny` → `large-v3` available). GPU auto-detected.
- **Context detection** — reads the active window's process, title, and up to 500 chars around the caret.
- **Pluggable AI backends** — Ollama (default, free), Anthropic, OpenAI, Gemini, Mistral, DeepSeek.
- **Offline fallback** — if AI is unreachable, basic punctuation/capitalisation cleanup still runs.
- **Searchable history** — export to TXT, CSV or JSON. Double-click the tray icon to open.
- **No admin rights** — installer is per-user. No telemetry.

---

## AI providers

| Provider | Local? | Default model | Needs |
|---|---|---|---|
| **Ollama** (default) | ✅ | `llama3.2` | [Ollama](https://ollama.com) running locally |
| Anthropic Claude | ☁ | `claude-haiku-5-5` | API key |
| OpenAI GPT | ☁ | `gpt-4o-mini` | API key |
| Google Gemini | ☁ | `gemini-2.0-flash` | API key |
| Mistral | ☁ | `mistral-small-latest` | API key |
| DeepSeek | ☁ | `deepseek-chat` | API key |

Switch providers and enter API keys in **Settings → AI**. The test connection button confirms it works before you save.

---

## System requirements

- Windows 10 / 11, 64-bit
- Microphone
- 4 GB RAM minimum (8 GB recommended for Ollama)
- NVIDIA GPU optional — auto-used when available (CUDA 12)

---

## Install from source

```bat
git clone https://github.com/AZOSTATIONZ/voiceflow-ai
cd voiceflow-ai
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**Python 3.12 or newer required.**

Set up local AI (free):
```
winget install Ollama.Ollama
ollama pull llama3.2
```

---

## Build the installer yourself

```bat
build.bat        # creates dist\VoiceFlowAI\VoiceFlowAI.exe via PyInstaller
installer.bat    # creates installer_output\VoiceFlowAI-Setup.exe via Inno Setup
```

`build.bat` creates the venv, installs dependencies, runs the test suite, and packages the app. The build is a one-folder bundle (not a single `.exe`) so startup is fast.

---

## Project structure

```
voiceflow_ai/
├── main.py                 entry point
├── app/                    Qt bootstrap, pipeline controller, hotkey hook
├── audio/                  microphone recorder, faster-whisper transcriber
├── ai/                     prompts, provider backends, cleanup + fallback
├── context/                foreground app detector, category mapping
├── ui/                     dark theme, overlay pill, settings, history dialog
├── tray/                   system tray icon and menu
├── settings/               JSON settings with defaults
├── db/                     SQLite history with search and export
├── utils/                  paths, logging, paste, autostart, icon generator
└── tests/                  pytest suite (25 tests)
```

---

## Usage

- **Hold Ctrl + Win**, speak, release. The overlay pill shows *Listening → Transcribing → Polishing* then disappears.
- **Tray menu** — right-click the mic icon: Start Dictation, Settings, History, Exit.
- **Double-click** the tray icon to open History.
- **Settings** cover: microphone, Whisper model size, language, hotkey, AI provider + model, API key, auto-paste, clipboard mode, start on boot.

Data is stored in `%APPDATA%\VoiceFlowAI\` — `settings.json`, `history.db`, `voiceflow.log`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Start menu opens on Win release | Switch hotkey to `ctrl+shift+space` or `right alt` |
| Nothing pastes into one app | That app is elevated — run VoiceFlow AI as Administrator |
| "AI cleanup unavailable" | Make sure Ollama is running (`ollama list`) and model name in Settings matches |
| Wrong microphone | Settings → Microphone; also check Windows → Privacy → Microphone |
| Slow first dictation | Whisper model is downloading on first use — check the log |
| CUDA errors | App falls back to CPU automatically |
| Hotkey not triggering | Another app owns the combo — pick a different hotkey |
| Text context empty | Not every app exposes text via UI Automation (Electron apps often don't) |

---

## Privacy

- No telemetry, analytics or tracking.
- Audio never leaves the PC. Whisper runs locally.
- Network access happens only for: Whisper model first download (Hugging Face), Ollama on localhost, or a cloud provider if you select one.
- With Ollama (default) everything stays on your machine.

---

## Running tests

```bat
.venv\Scripts\python -m pytest -q tests
```

25 tests covering hotkey state machine, prompt building, AI output validation, history, and settings persistence.

---

## License

MIT — free to use, modify and distribute.
