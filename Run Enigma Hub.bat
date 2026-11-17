@echo off
setlocal
cd /d "%~dp0"
set "PY=python"
python -c "import sys; sys.exit(sys.version_info < (3,8))" >nul 2>nul
if errorlevel 1 set "PY=py -3"
%PY% -c "import sys; sys.exit(sys.version_info < (3,8))" >nul 2>nul
if errorlevel 1 goto failed
%PY% -c "from PyQt5.QtWidgets import QApplication" >nul 2>nul
if errorlevel 1 (
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 goto failed
)
%PY% -X faulthandler -u enigma_hub.py > "%~dp0startup-output.log" 2>&1
if errorlevel 1 goto app_failed
exit /b 0
:app_failed
type "%~dp0startup-output.log"
echo Log: "%~dp0startup-output.log"
:failed
echo Enigma Hub could not start. See the error above.
pause
exit /b 1
