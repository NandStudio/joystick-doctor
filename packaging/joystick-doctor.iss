; Inno Setup 6 — compile after PyInstaller has filled dist\JoystickDoctor\
;   iscc packaging\joystick-doctor.iss
; or .\packaging\build.ps1

#define MyAppName "Joystick Doctor"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Nand Studio by Lucma"
#define MyAppURL "https://www.nandstudio.dev/"
#define MyAppExeName "JoystickDoctor.exe"
#define DistDir SourcePath + "..\dist\JoystickDoctor"
#define AppIcon SourcePath + "..\assets\icon.ico"

[Setup]
AppId={{8F3C2E1A-6B47-4D09-9C5A-1E7D2A4B9083}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\NandStudio\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#SourcePath}..\dist
OutputBaseFilename=JoystickDoctorSetup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=6.1sp1
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile={#AppIcon}
CloseApplications=yes
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
