[Setup]
AppName=MatrixQuesGen
AppVersion=1.0.1
AppPublisher=Your Organization
AppPublisherURL=https://github.com/Trung-edmicro/matrixquesgen
AppSupportURL=https://github.com/Trung-edmicro/matrixquesgen/issues
AppUpdatesURL=https://github.com/Trung-edmicro/matrixquesgen/releases
DefaultDirName={autopf}\MatrixQuesGen
DefaultGroupName=MatrixQuesGen
OutputDir=installer
OutputBaseFilename=MatrixQuesGen_Setup_1.0.1
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
Name: "playwright"; Description: "Install Playwright Chromium (for chart export to DOCX, ~150MB)"; GroupDescription: "Optional components:"; Flags: unchecked

[Files]
Source: "dist\MatrixQuesGen.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "client\dist\*"; DestDir: "{app}\client\dist"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: ".env"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_playwright_silent.bat"; DestDir: "{app}"; Flags: ignoreversion

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
; Launch Playwright install silently in background (optional task)
Filename: "{app}\install_playwright_silent.bat"; Description: "Installing Playwright Chromium..."; Flags: runhidden nowait; Tasks: playwright
; Launch the app after install (user can uncheck)
Filename: "{app}\MatrixQuesGen.exe"; Description: "{cm:LaunchProgram,MatrixQuesGen}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"





