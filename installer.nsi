; Video2Text NSIS Installer Script
; Requires NSIS 3.x

!include "MUI2.nsh"
!include "FileFunc.nsh"

; ----- General -----
Name "Video2Text"
OutFile "dist\Video2Text-Setup.exe"
InstallDir "$PROGRAMFILES64\Video2Text"
InstallDirRegKey HKLM "Software\Video2Text" "InstallDir"
RequestExecutionLevel admin

; ----- Interface Settings -----
!define MUI_ABORTWARNING
!define MUI_ICON "assets\icon.ico"
!define MUI_UNICON "assets\icon.ico"

; ----- Pages -----
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; ----- Languages -----
!insertmacro MUI_LANGUAGE "SimpChinese"

; ----- Installer Sections -----
Section "Install"
    SetOutPath "$INSTDIR"

    ; Copy all files from PyInstaller output
    File /r "dist\video2text\*.*"

    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\Video2Text"
    CreateShortcut "$SMPROGRAMS\Video2Text\Video2Text.lnk" "$INSTDIR\Video2Text.exe"
    CreateShortcut "$SMPROGRAMS\Video2Text\卸载 Video2Text.lnk" "$INSTDIR\Uninstall.exe"

    ; Create Desktop shortcut
    CreateShortcut "$DESKTOP\Video2Text.lnk" "$INSTDIR\Video2Text.exe"

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Registry keys for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video2Text" "DisplayName" "Video2Text"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video2Text" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video2Text" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video2Text" "Publisher" "Video2Text"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video2Text" "DisplayVersion" "0.1.0"

    ; Estimate installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video2Text" "EstimatedSize" "$0"
SectionEnd

; ----- Uninstaller Section -----
Section "Uninstall"
    ; Remove files and directory
    RMDir /r "$INSTDIR"

    ; Remove shortcuts
    Delete "$DESKTOP\Video2Text.lnk"
    RMDir /r "$SMPROGRAMS\Video2Text"

    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video2Text"
SectionEnd