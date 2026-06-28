@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title LSSBot Wulfpack Overseer All-in-One v0.0.9

echo.
echo ################################################
echo ## LSSBot Wulfpack Overseer All-in-One v0.0.9 ##
echo ################################################
echo.
echo Ablauf:
echo   1. Queue erzeugen
echo   2. Queue in LSS-Bot importieren
echo   3. LSS-Bot-Sidecar starten
echo.

if not exist "%~dp001_queue_generator\START.cmd" (
  echo FEHLER: 01_queue_generator\START.cmd fehlt.
  exit /b 1
)

if not exist "%~dp002_lssbot_sidecar\00_RUNNER.cmd" (
  echo FEHLER: 02_lssbot_sidecar\00_RUNNER.cmd fehlt.
  exit /b 1
)

echo.
echo [1/3] Queue Generator startet...
echo.
pushd "%~dp001_queue_generator"
call ".\START.cmd"
set "GEN_RC=%errorlevel%"
popd

if not "%GEN_RC%"=="0" (
  echo.
  echo FEHLER: Queue Generator wurde abgebrochen oder meldete Fehler: %GEN_RC%
  exit /b %GEN_RC%
)

echo.
echo [2/3] Sidecar importiert Queue...
echo [3/3] Sidecar startet LSS Bot.exe...
echo.

pushd "%~dp002_lssbot_sidecar"
call ".\00_RUNNER.cmd" %*
set "SIDE_RC=%errorlevel%"
popd

if not "%SIDE_RC%"=="0" (
  echo.
  echo FEHLER: Sidecar meldete Fehler: %SIDE_RC%
  exit /b %SIDE_RC%
)

echo.
echo Fertig.
echo.
exit /b 0
