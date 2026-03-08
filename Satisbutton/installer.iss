; Inno Setup script for Satisfying Buttons
; To use, install Inno Setup Compiler: https://jrsoftware.org/isinfo.php

[Setup]
AppName=Satisfying Buttons
AppVersion=1.1
AppPublisher=Refined
AppPublisherURL=https://buymeacoffee.com/refined
AppSupportURL=https://www.youtube.com/channel/UCGe5VOk80siQe0r2OfQQWPw
DefaultDirName={autopf}\Satisfying Buttons
DefaultGroupName=Satisfying Buttons
DisableProgramGroupPage=yes
OutputBaseFilename=satisfying-buttons-setup-v1.1
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Satisfying Buttons.exe

; Require Windows 10 or newer for better compatibility with modern features
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; This assumes you have run build.py and the .exe is in the 'dist' subfolder.
Source: "dist\Satisfying Buttons.exe"; DestDir: "{app}"; Flags: ignoreversion

; NOTE: The source file must exist for the compiler to work.
; If the compiler cannot find the file, check the path.

[Icons]
; Start Menu entry
Name: "{group}\Satisfying Buttons"; Filename: "{app}\Satisfying Buttons.exe"
Name: "{group}\{cm:UninstallProgram,Satisfying Buttons}"; Filename: "{uninstallexe}"

; Optional Desktop icon
Name: "{autodesktop}\Satisfying Buttons"; Filename: "{app}\Satisfying Buttons.exe"; Tasks: desktopicon

[Run]
; Launch the application after installation is complete.
Filename: "{app}\Satisfying Buttons.exe"; Description: "{cm:LaunchProgram,Satisfying Buttons}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\*"