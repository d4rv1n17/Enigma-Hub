@echo off
setlocal
cd /d "%~dp0"
set "PY=python"
python --version >nul 2>nul
if errorlevel 1 set "PY=py -3"
for /d %%P in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%~fP\python.exe" (
        "%%~fP\python.exe" -c "import PyInstaller; from PyQt5.QtWidgets import QApplication" >nul 2>nul
        if not errorlevel 1 (
            set PY="%%~fP\python.exe"
            goto build
        )
    )
)
%PY% -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto failed
:build
%PY% build_release.py
if errorlevel 1 goto failed
echo.
echo Ready: Output\EnigmaHubSetup.exe
pause
exit /b 0
:failed
echo Build failed. Check the output above.
pause
exit /b 1
