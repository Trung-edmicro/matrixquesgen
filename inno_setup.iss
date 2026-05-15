[Setup]
AppName=MatrixQuesGen
AppVersion=1.7.1
AppPublisher=Your Organization
AppPublisherURL=https://github.com/Trung-edmicro/matrixquesgen
AppSupportURL=https://github.com/Trung-edmicro/matrixquesgen/issues
AppUpdatesURL=https://github.com/Trung-edmicro/matrixquesgen/releases
DefaultDirName={autopf}\MatrixQuesGen
DefaultGroupName=MatrixQuesGen
OutputDir=installer
OutputBaseFilename=MatrixQuesGen_Setup_1.7.1
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
; SetupIconFile is optional - only set if a valid .ico file exists
; (set via command-line /DMyIcon=path or directly here if present)
SetupIconFile=favicon.ico
UninstallDisplayIcon={app}\MatrixQuesGen.exe
; Allow upgrade/reinstall without uninstalling first
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\MatrixQuesGen.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "client\dist\*"; DestDir: "{app}\client\dist"; Flags: ignoreversion recursesubdirs createallsubdirs
; Bundle English prompts and vocabulary
Source: "dist\data\prompts\*"; DestDir: "{app}\data\prompts"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\data\vocabulary_english\*"; DestDir: "{app}\data\vocabulary_english"; Flags: ignoreversion recursesubdirs createallsubdirs
; Configuration files
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Ensure all working directories exist after install
Name: "{app}\data\.drive_metadata"
Name: "{app}\data\content"
Name: "{app}\data\matrix"
Name: "{app}\data\output"
Name: "{app}\data\prompts"
Name: "{app}\data\upload"
Name: "{app}\data\questions"
Name: "{app}\data\sessions"
Name: "{app}\data\exports"
Name: "{app}\data\images"
Name: "{app}\logs"

[Icons]
Name: "{group}\MatrixQuesGen"; Filename: "{app}\MatrixQuesGen.exe"

Name: "{commondesktop}\MatrixQuesGen"; Filename: "{app}\MatrixQuesGen.exe"; Tasks: desktopicon

[Run]
; Launch the app after install (user can uncheck)
Filename: "{app}\MatrixQuesGen.exe"; Description: "{cm:LaunchProgram,MatrixQuesGen}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Only delete logs on uninstall - preserve user data and prompts
Type: filesandordirs; Name: "{app}\logs"
; Delete empty directories if user didn't add custom files
Type: dirifempty; Name: "{app}\data\.drive_metadata"
Type: dirifempty; Name: "{app}\data\uploads"
Type: dirifempty; Name: "{app}\data\output"
Type: dirifempty; Name: "{app}\data\temp_uploads"






































































