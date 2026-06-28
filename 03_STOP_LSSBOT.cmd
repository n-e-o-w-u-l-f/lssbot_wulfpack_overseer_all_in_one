@echo off
setlocal EnableExtensions
cd /d "%~dp0"

pushd "%~dp002_lssbot_sidecar"
call ".\07_STOP_LSSBOT.cmd" %*
set "RC=%errorlevel%"
popd
exit /b %RC%
