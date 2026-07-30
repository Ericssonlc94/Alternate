; Instalador do Severance System (Inno Setup 6).
;
; Compile a partir da RAIZ do projeto, DEPOIS de gerar o executavel:
;     pyinstaller packaging\severance_gui.spec
;     iscc packaging\installer.iss
; Ou use packaging\build_installer.bat, que faz os dois passos.
;
; Instalacao POR USUARIO, de proposito:
;   - Nao pede UAC, entao instalar nao exige direitos de administrador.
;   - O destino fica gravavel, entao data/ vive ao lado do executavel e o
;     usuario pode levar a pasta inteira para outro PC (modo portatil).
;   Instalado numa pasta protegida (se alguem mudar o destino para Arquivos de
;   Programas), o app nao quebra: core._writable_dir cai para %APPDATA%.

#define AppName "Severance System"
#define AppVersion "2.0.0"
#define AppPublisher "Ericsson"
#define AppURL "https://github.com/Ericssonlc94/Severance-System"
#define ExeName "SeveranceSystem.exe"

[Setup]
AppId={{7B3F2A64-9C51-4E0D-9E77-3A5D2C1B8F40}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

; Por usuario: sem UAC e com destino gravavel.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

OutputDir=..\dist
OutputBaseFilename=SeveranceSystem-{#AppVersion}-setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

; Descomente quando assets\logo.ico voltar ao repositorio.
; SetupIconFile=..\assets\logo.ico
UninstallDisplayName={#AppName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Iniciar o {#AppName} junto com o Windows"; GroupDescription: "Inicializacao"; Flags: unchecked

[Files]
; O executavel do PyInstaller ja carrega as traducoes e o Python embarcados.
Source: "..\dist\{#ExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md";       DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "..\README_BR.md";    DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}";                 Filename: "{app}\{#ExeName}"
Name: "{group}\Desinstalar {#AppName}";     Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";           Filename: "{app}\{#ExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}";           Filename: "{app}\{#ExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#ExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; data/ e logs/ sao criados em tempo de execucao, entao o Inno nao os conhece e
; deixaria as pastas para tras. Removemos as pastas VAZIAS; o conteudo (config e
; bancos de apps) fica preservado de proposito, para reinstalar nao apagar os
; ajustes de quem so esta atualizando. Quem quiser zerar apaga a pasta na mao.
Type: dirifempty; Name: "{app}\data"
Type: dirifempty; Name: "{app}\logs"
Type: dirifempty; Name: "{app}"
