@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo LSSBot Sidecar Wulfpack Overseer v0.0.9
echo Importiert die Queue in LSS-Bot und startet den LSS-Bot-Sidecar.
echo.

python --version >nul 2>nul
if errorlevel 1 (
  py --version >nul 2>nul
  if errorlevel 1 (
    echo Python wurde nicht gefunden.
    exit /b 1
  )
  set "PY=py"
) else (
  set "PY=python"
)

%PY% "%~dp0src\lssbot_sidecar_wulfpack_overseer.py" --install-config
if errorlevel 1 exit /b %errorlevel%

%PY% "%~dp0src\lssbot_sidecar_wulfpack_overseer.py" --import-queue %*
if errorlevel 1 exit /b %errorlevel%

%PY% "%~dp0src\lssbot_sidecar_wulfpack_overseer.py" --validate
if errorlevel 1 exit /b %errorlevel%

%PY% "%~dp0src\lssbot_sidecar_wulfpack_overseer.py" --live
exit /b %errorlevel%
