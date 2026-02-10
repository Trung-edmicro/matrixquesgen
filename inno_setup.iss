[Setup]
AppName=MatrixQuesGen
AppVersion=1.0.0
DefaultDirName={pf}\MatrixQuesGen
DefaultGroupName=MatrixQuesGen
OutputDir=installer
OutputBaseFilename=MatrixQuesGen_Installer
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
SetupIconFile=favicon.ico
UninstallDisplayIcon={app}\MatrixQuesGen.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\MatrixQuesGen.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "client\dist\*"; DestDir: "{app}\client\dist"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: ".env"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\MatrixQuesGen"; Filename: "{app}\MatrixQuesGen.exe"
Name: "{commondesktop}\MatrixQuesGen"; Filename: "{app}\MatrixQuesGen.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\MatrixQuesGen.exe"; Description: "{cm:LaunchProgram,MatrixQuesGen}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"