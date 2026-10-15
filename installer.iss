; Inno Setup script for VoiceFlow AI (per-user install, no admin rights needed)
#define AppName "VoiceFlow AI"
#define AppVersion "1.0.0"
#define AppExe "VoiceFlowAI.exe"

[Setup]
AppId={{6F2B8C41-9D3E-4A57-B1C8-5E0F7A2D9C13}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=VoiceFlow AI
DefaultDirName={localappdata}\Programs\VoiceFlowAI
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=VoiceFlowAI-Setup
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/max
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
Name: "startup"; Description: "Start VoiceFlow AI when Windows starts"

[Files]
Source: "dist\VoiceFlowAI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "VoiceFlowAI"; ValueData: """{app}\{#AppExe}"""; Tasks: startup; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill"; Parameters: "/F /IM {#AppExe}"; Flags: runhidden; RunOnceId: "KillApp"
