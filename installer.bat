@echo off
REM Creates installer_output\VoiceFlowAI-Setup.exe with Inno Setup 6.
REM Install Inno Setup first:  winget install JRSoftware.InnoSetup
setlocal
cd /d "%~dp0"

if not exist dist\VoiceFlowAI\VoiceFlowAI.exe (
    echo dist\VoiceFlowAI\VoiceFlowAI.exe not found. Run build.bat first.
    exit /b 1
)

set ISCC=
for %%P in ("%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" "%ProgramFiles%\Inno Setup 6\ISCC.exe" "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe") do (
    if exist %%P set ISCC=%%P
)
if not defined ISCC (
    echo Inno Setup 6 not found. Install it with: winget install JRSoftware.InnoSetup
    exit /b 1
)

%ISCC% installer.iss || exit /b 1
echo Installer created in installer_output\
