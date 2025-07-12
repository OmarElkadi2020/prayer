[Setup]
AppName=Prayer Player
AppVersion=1.0.0
DefaultDirName={autopf}\PrayerPlayer
DefaultGroupName=Prayer Player
UninstallDisplayIcon={app}\PrayerPlayer.exe
WizardStyle=modern
OutputBaseFilename=PrayerPlayer-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "dist\PrayerPlayer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Prayer Player"; Filename: "{app}\PrayerPlayer.exe"
Name: "{commondesktop}\Prayer Player"; Filename: "{app}\PrayerPlayer.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional shortcuts:";
Name: "runatstartup"; Description: "Run Prayer Player at startup"; GroupDescription: "Startup options:";

[Run]
Filename: "{app}\PrayerPlayer.exe"; Description: "Launch Prayer Player"; Flags: nowait postinstall skipifsilent
Filename: "{app}\PrayerPlayer.exe"; Parameters: "--install-service"; Flags: runhidden; Tasks: runatstartup
