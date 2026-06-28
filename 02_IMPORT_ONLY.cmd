@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo Importiert nur die vorhandene Queue in den Sidecar.
echo Kein Queue-Generator, kein Live-Run.
echo.

pushd "%~dp002_lssbot_sidecar"
call ".\01_IMPORT_QUEUE.cmd" %*
set "RC=%errorlevel%"
popd
exit /b %RC%
