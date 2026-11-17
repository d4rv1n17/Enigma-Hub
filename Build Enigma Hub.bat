@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  python -c "import sys; sys.exit(sys.version_info < (3,13))"
  if errorlevel 1 goto failed
  python -m venv .venv
  if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install -r requirements-build.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" build_release.py
if errorlevel 1 goto failed
echo Ready: Output\EnigmaHubSetup.exe
pause
exit /b 0
:failed
echo Build failed. Python 3.13 or newer is required.
pause
exit /b 1
