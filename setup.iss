; Nordic Secure - Inno Setup Script
; Creates a Windows installer for Nordic Secure application

#define MyAppName "Nordic Secure"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Nordic Secure"
#define MyAppURL "https://nordicsecure.com"
#define MyAppExeName "NordicSecure.exe"

[Setup]
; Application information
AppId={{8F3A5C2B-9D7E-4F1A-B6C3-2E8A7D9F4B1C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output
OutputDir=Output
OutputBaseFilename=NordicSecureSetup
Compression=lzma2/ultra64
SolidCompression=yes

; Visual settings
WizardStyle=modern
WizardImageFile=compiler:WizModernImage-IS.bmp
WizardSmallImageFile=compiler:WizModernSmallImage-IS.bmp

; Privileges
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Architecture
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64

; Version info
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Installer
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main application files from PyInstaller output
Source: "dist\NordicSecure\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; External binaries (Ollama and Tesseract)
Source: "bin\*"; DestDir: "{app}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs

; License files (if they exist)
Source: "LICENSE*"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Optional: Install Visual C++ Redistributable if needed
; Download from Microsoft and include in installer
; Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/quiet /norestart"; StatusMsg: "Installing Visual C++ Redistributable..."; Flags: waituntilterminated

; Launch application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up data directory in user AppData (optional - ask user)
Type: filesandordirs; Name: "{userappdata}\{#MyAppName}"

[Code]
var
  DataDirPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  { Create a page to ask about data directory cleanup }
  DataDirPage := CreateInputQueryPage(wpWelcome,
    'Data Storage Location', 
    'Where should Nordic Secure store its data?',
    'Nordic Secure stores documents and embeddings locally. ' +
    'By default, data is stored in your user profile folder and will persist across updates.');
    
  DataDirPage.Add('Data will be stored in: ' + ExpandConstant('{userappdata}\NordicSecure'), False);
end;

function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  { Check if Visual C++ Redistributable is installed }
  { This is a simplified check - you may want to check registry keys }
  if not FileExists(ExpandConstant('{sys}\vcruntime140.dll')) then
  begin
    MsgBox('Microsoft Visual C++ Redistributable is required but not installed.' + #13#10 +
           'The installer will attempt to install it automatically.' + #13#10 +
           'If installation fails, please download and install it manually from:' + #13#10 +
           'https://aka.ms/vs/17/release/vc_redist.x64.exe', 
           mbInformation, MB_OK);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    { Create data directory in user AppData }
    ForceDirectories(ExpandConstant('{userappdata}\NordicSecure\data'));
  end;
end;

function InitializeUninstall(): Boolean;
var
  Response: Integer;
begin
  Result := True;
  
  { Ask user if they want to keep their data }
  Response := MsgBox('Do you want to remove all stored documents and data?' + #13#10 +
                     'Select "Yes" to remove all data (cannot be undone).' + #13#10 +
                     'Select "No" to keep your data for future installations.',
                     mbConfirmation, MB_YESNO);
  
  if Response = IDYES then
  begin
    { User wants to remove data - this is handled by [UninstallDelete] section }
  end
  else
  begin
    { User wants to keep data - skip the UninstallDelete }
    Result := True;
  end;
end;

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nNordic Secure is a private, offline document management and RAG (Retrieval-Augmented Generation) system. It requires no internet connection and stores all data locally on your computer.%n%nIt is recommended that you close all other applications before continuing.
