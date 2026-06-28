@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title LSSBot Wulfpack Overseer Dry Run v0.0.9

echo.
echo #########################################
echo ## LSSBot Wulfpack Overseer DRY-RUN   ##
echo #########################################
echo.
echo Erst Queue erzeugen, danach Sidecar ohne Live-Start testen.
echo.

pushd "%~dp001_queue_generator"
call ".\START.cmd"
set "GEN_RC=%errorlevel%"
popd

if not "%GEN_RC%"=="0" exit /b %GEN_RC%

pushd "%~dp002_lssbot_sidecar"
call ".\02_DRY_RUN.cmd" %*
set "SIDE_RC=%errorlevel%"
popd

exit /b %SIDE_RC%
