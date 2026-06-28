@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python "%~dp0src\lssbot_sidecar_wulfpack_overseer.py" --install-config
python "%~dp0src\lssbot_sidecar_wulfpack_overseer.py" --import-queue %*
python "%~dp0src\lssbot_sidecar_wulfpack_overseer.py" --dry-run
if errorlevel 1 py "%~dp0src\lssbot_sidecar_wulfpack_overseer.py" --dry-run
exit /b %errorlevel%
