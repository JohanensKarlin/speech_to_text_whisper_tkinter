; Inno Setup Script: Speech-to-Text Installer
; Voraussetzung: Zuerst build.bat ausfuehren (erzeugt dist\SpeechToText.exe)
; Dann: Inno Setup installieren (https://jrsoftware.org/isinfo.php), diese .iss oeffnen, Build / Compile

#define MyAppName "Speech to Text"
#define MyAppExe "SpeechToText.exe"
#define MyAppBuild "dist\" + MyAppExe

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion=1.0
DefaultDirName={autopf}\SpeechToText
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=SpeechToText_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
; EXE liegt neben dieser .iss im Projektroot nach Build
SourceDir=..

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Desktop-Symbol erstellen"; GroupDescription: "Symbole:"; Flags: unchecked

[Files]
Source: "{#MyAppBuild}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{group}\Deinstallieren {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "App starten"; Flags: nowait postinstall skipifsilent
