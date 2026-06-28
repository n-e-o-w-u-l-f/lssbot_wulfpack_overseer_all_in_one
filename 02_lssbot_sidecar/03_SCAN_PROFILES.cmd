@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python "%~dp0src\lssbot_sidecar_wulfpack_overseer.py" --scan-profiles
if errorlevel 1 py "%~dp0src\lssbot_sidecar_wulfpack_overseer.py" --scan-profiles
exit /b %errorlevel%
