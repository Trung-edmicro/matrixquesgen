[Setup]
AppName=MatrixQuesGen
AppVersion=1.0.0
AppPublisher=Your Organization
AppPublisherURL=https://github.com/your-org/matrixquesgen
AppSupportURL=https://github.com/your-org/matrixquesgen/issues
AppUpdatesURL=https://github.com/your-org/matrixquesgen/releases
DefaultDirName={autopf}\MatrixQuesGen
DefaultGroupName=MatrixQuesGen
OutputDir=installer
OutputBaseFilename=MatrixQuesGen_Setup_1.0.0
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
Name: "playwright"; Description: "CÃ i Ä‘áº·t Playwright Chromium (Ä‘á»ƒ xuáº¥t biá»ƒu Ä‘á»“ vÃ o DOCX, ~150MB)"; GroupDescription: "ThÃ nh pháº§n tuá»³ chá»n:"; Flags: unchecked

[Files]
Source: "dist\MatrixQuesGen.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "client\dist\*"; DestDir: "{app}\client\dist"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: ".env"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_playwright_silent.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_playwright.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\MatrixQuesGen"; Filename: "{app}\MatrixQuesGen.exe"
Name: "{group}\CÃ i Ä‘áº·t Playwright (Biá»ƒu Ä‘á»“ DOCX)"; Filename: "{app}\install_playwright.bat"
Name: "{commondesktop}\MatrixQuesGen"; Filename: "{app}\MatrixQuesGen.exe"; Tasks: desktopicon

[Run]
; Launch Playwright install silently in background (optional task)
Filename: "{app}\install_playwright_silent.bat"; Description: "Äang cÃ i Ä‘áº·t Playwright Chromium..."; Flags: runhidden nowait; Tasks: playwright
; Launch the app after install (user can uncheck)
Filename: "{app}\MatrixQuesGen.exe"; Description: "{cm:LaunchProgram,MatrixQuesGen}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"
