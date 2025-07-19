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
Source: "..\..\dist\PrayerPlayer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Prayer Player"; Filename: "{app}\PrayerPlayer.exe"
Name: "{commondesktop}\Prayer Player"; Filename: "{app}\PrayerPlayer.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional shortcuts:";
