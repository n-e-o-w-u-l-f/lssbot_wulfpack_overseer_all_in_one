@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python "%~dp0src\lssbot_sidecar_wulfpack_overseer.py" --import-queue %*
if errorlevel 1 py "%~dp0src\lssbot_sidecar_wulfpack_overseer.py" --import-queue %*
exit /b %errorlevel%
