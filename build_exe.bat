@echo off
echo =======================================================
echo Building JARVIS 2.0 Standalone Single-File Executable...
echo Bundling .env file directly into PyInstaller _MEIPASS
echo =======================================================

pyinstaller --clean jarvis.spec

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================
    echo BUILD SUCCESSFUL!
    echo Output executable: dist\JARVIS-2.0.exe
    echo (.env is bundled directly inside the .exe)
    echo =======================================================
) else (
    echo.
    echo BUILD FAILED with error code %ERRORLEVEL%
)
pause

