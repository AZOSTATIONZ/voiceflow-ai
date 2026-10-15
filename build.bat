@echo off
REM Builds dist\VoiceFlowAI\VoiceFlowAI.exe with PyInstaller.
setlocal
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
    echo Creating virtual environment...
    python -m venv .venv || goto :error
)
set PY=.venv\Scripts\python.exe

%PY% -m pip install --upgrade pip || goto :error
%PY% -m pip install -r requirements.txt || goto :error

echo Running tests...
%PY% -m pytest -q tests || goto :error

echo Generating icon...
%PY% -m utils.make_icon || goto :error

echo Building executable...
%PY% -m PyInstaller --noconfirm --clean --windowed --name VoiceFlowAI ^
    --icon assets\icon.ico ^
    --add-data "assets;assets" ^
    --collect-all faster_whisper ^
    --collect-all ctranslate2 ^
    --collect-data uiautomation ^
    --collect-binaries uiautomation ^
    --hidden-import win32timezone ^
    main.py || goto :error

echo.
echo Build complete: dist\VoiceFlowAI\VoiceFlowAI.exe
echo Run installer.bat to create a Windows installer.
exit /b 0

:error
echo Build failed with error %errorlevel%.
exit /b 1
