@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "LSS_QUEUE_LANG="
set "LSS_QUEUE_EMULATOR="

if exist "%~dp0.lss_queue_lang" (
  set /p LSS_QUEUE_LANG=<"%~dp0.lss_queue_lang"
)
if exist "%~dp0.lss_queue_emulator" (
  set /p LSS_QUEUE_EMULATOR=<"%~dp0.lss_queue_emulator"
)

if not defined LSS_QUEUE_LANG set "LSS_QUEUE_LANG=english"
if not defined LSS_QUEUE_EMULATOR set "LSS_QUEUE_EMULATOR=auto"

set "ARGS=%*"
echo %ARGS% | findstr /I /C:"--lang" >nul
if errorlevel 1 (
  set "LANG_ARG=--lang %LSS_QUEUE_LANG%"
) else (
  set "LANG_ARG="
)

echo %ARGS% | findstr /I /C:"--emulator-type" >nul
if errorlevel 1 (
  set "EMU_ARG=--emulator-type %LSS_QUEUE_EMULATOR%"
) else (
  set "EMU_ARG="
)

if "%LSS_QUEUE_LANG%"=="german" echo Lokalisierter Strg+C-Dialog:
if "%LSS_QUEUE_LANG%"=="english" echo Localized Ctrl+C prompt:
if "%LSS_QUEUE_LANG%"=="french" echo Question Ctrl+C localisee:
if "%LSS_QUEUE_LANG%"=="espanol" echo Pregunta Ctrl+C localizada:
if "%LSS_QUEUE_LANG%"=="polski" echo Lokalny komunikat Ctrl+C:
if "%LSS_QUEUE_LANG%"=="russian" echo Lokalizovannyi dialog Ctrl+C:
if "%LSS_QUEUE_LANG%"=="german" echo   Strg+C: Scriptlauf abbrechen? [J/N]
if "%LSS_QUEUE_LANG%"=="english" echo   Ctrl+C: Abort script run? [Y/N]
if "%LSS_QUEUE_LANG%"=="french" echo   Ctrl+C: Annuler l'execution du script ? [O/N]
if "%LSS_QUEUE_LANG%"=="espanol" echo   Ctrl+C: Cancelar la ejecucion del script? [S/N]
if "%LSS_QUEUE_LANG%"=="polski" echo   Ctrl+C: Przerwac dzialanie skryptu? [T/N]
if "%LSS_QUEUE_LANG%"=="russian" echo   Ctrl+C: Prervat vypolnenie skripta? [D/N]
echo.
py -3 "%~dp0lss_character_queue_v5_final.py" %LANG_ARG% %EMU_ARG% %*

endlocal
