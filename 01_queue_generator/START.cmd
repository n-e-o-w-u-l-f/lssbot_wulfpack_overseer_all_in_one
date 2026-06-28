@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo LSS Character Queue v5.0 FINAL
echo.
echo Please choose your language:
echo 1. English          4. Espanol
echo 2. German           5. Polski
echo 3. French           6. Russian
echo.
set "LSS_QUEUE_LANG="
set /p "choice=Language [1-6, default 1]: "

if "%choice%"=="" set "choice=1"
if "%choice%"=="1" set "LSS_QUEUE_LANG=english"
if "%choice%"=="2" set "LSS_QUEUE_LANG=german"
if "%choice%"=="3" set "LSS_QUEUE_LANG=french"
if "%choice%"=="4" set "LSS_QUEUE_LANG=espanol"
if "%choice%"=="5" set "LSS_QUEUE_LANG=polski"
if "%choice%"=="6" set "LSS_QUEUE_LANG=russian"

if not defined LSS_QUEUE_LANG (
  echo Invalid selection. Falling back to English.
  set "LSS_QUEUE_LANG=english"
)

echo.
if "%LSS_QUEUE_LANG%"=="german" echo Bitte waehle deinen installierten Emulator:
if "%LSS_QUEUE_LANG%"=="english" echo Please choose your installed emulator:
if "%LSS_QUEUE_LANG%"=="french" echo Choisis ton emulateur installe:
if "%LSS_QUEUE_LANG%"=="espanol" echo Elige tu emulador instalado:
if "%LSS_QUEUE_LANG%"=="polski" echo Wybierz zainstalowany emulator:
if "%LSS_QUEUE_LANG%"=="russian" echo Vyberi ustanovlennyi emulyator:
echo 1. LDPlayer9        4. LDPlayer 14 beta
echo 2. LDPlayer5        5. MEmu Play
echo 3. LDPlayer4        6. Nox Player
echo 7. Auto / unknown
echo.
set "LSS_QUEUE_EMULATOR="
set "EMU_PROMPT=Emulator [1-7, default 7]: "
if "%LSS_QUEUE_LANG%"=="german" set "EMU_PROMPT=Emulator [1-7, Standard 7]: "
if "%LSS_QUEUE_LANG%"=="french" set "EMU_PROMPT=Emulateur [1-7, defaut 7]: "
if "%LSS_QUEUE_LANG%"=="espanol" set "EMU_PROMPT=Emulador [1-7, predeterminado 7]: "
if "%LSS_QUEUE_LANG%"=="polski" set "EMU_PROMPT=Emulator [1-7, domyslnie 7]: "
if "%LSS_QUEUE_LANG%"=="russian" set "EMU_PROMPT=Emulyator [1-7, po umolchaniyu 7]: "
set /p "emu_choice=%EMU_PROMPT%"

if "%emu_choice%"=="" set "emu_choice=7"
if "%emu_choice%"=="1" set "LSS_QUEUE_EMULATOR=ldplayer9"
if "%emu_choice%"=="2" set "LSS_QUEUE_EMULATOR=ldplayer5"
if "%emu_choice%"=="3" set "LSS_QUEUE_EMULATOR=ldplayer4"
if "%emu_choice%"=="4" set "LSS_QUEUE_EMULATOR=ldplayer14"
if "%emu_choice%"=="5" set "LSS_QUEUE_EMULATOR=memu"
if "%emu_choice%"=="6" set "LSS_QUEUE_EMULATOR=nox"
if "%emu_choice%"=="7" set "LSS_QUEUE_EMULATOR=auto"

if not defined LSS_QUEUE_EMULATOR (
  if "%LSS_QUEUE_LANG%"=="german" echo Ungueltige Emulator-Auswahl. Fallback auf Auto.
  if "%LSS_QUEUE_LANG%"=="english" echo Invalid emulator selection. Falling back to Auto.
  if "%LSS_QUEUE_LANG%"=="french" echo Selection emulateur invalide. Retour a Auto.
  if "%LSS_QUEUE_LANG%"=="espanol" echo Seleccion de emulador invalida. Volviendo a Auto.
  if "%LSS_QUEUE_LANG%"=="polski" echo Nieprawidlowy wybor emulatora. Uzywam Auto.
  if "%LSS_QUEUE_LANG%"=="russian" echo Nevernyi vybor emulyatora. Ispolzuyu Auto.
  set "LSS_QUEUE_EMULATOR=auto"
)

> "%~dp0.lss_queue_lang" echo %LSS_QUEUE_LANG%
> "%~dp0.lss_queue_emulator" echo %LSS_QUEUE_EMULATOR%

if "%LSS_QUEUE_LANG%"=="german" echo Gewaehlte Sprache: deutsch
if "%LSS_QUEUE_LANG%"=="english" echo Selected language: english
if "%LSS_QUEUE_LANG%"=="french" echo Langue choisie: francais
if "%LSS_QUEUE_LANG%"=="espanol" echo Idioma seleccionado: espanol
if "%LSS_QUEUE_LANG%"=="polski" echo Wybrany jezyk: polski
if "%LSS_QUEUE_LANG%"=="russian" echo Vybrannyi yazyk: russkii

if "%LSS_QUEUE_LANG%"=="german" echo Gewaehlter Emulator: %LSS_QUEUE_EMULATOR%
if "%LSS_QUEUE_LANG%"=="english" echo Selected emulator: %LSS_QUEUE_EMULATOR%
if "%LSS_QUEUE_LANG%"=="french" echo Emulateur choisi: %LSS_QUEUE_EMULATOR%
if "%LSS_QUEUE_LANG%"=="espanol" echo Emulador seleccionado: %LSS_QUEUE_EMULATOR%
if "%LSS_QUEUE_LANG%"=="polski" echo Wybrany emulator: %LSS_QUEUE_EMULATOR%
if "%LSS_QUEUE_LANG%"=="russian" echo Vybrannyi emulyator: %LSS_QUEUE_EMULATOR%
echo.

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

set "PS_REGEX=ld|dnplayer|ldplayer|memu|nox|adb|java|lss"
if "%LSS_QUEUE_EMULATOR%"=="ldplayer9" set "PS_REGEX=ld|dnplayer|ldplayer|adb|java|lss"
if "%LSS_QUEUE_EMULATOR%"=="ldplayer5" set "PS_REGEX=ld|dnplayer|ldplayer|adb|java|lss"
if "%LSS_QUEUE_EMULATOR%"=="ldplayer4" set "PS_REGEX=ld|dnplayer|ldplayer|adb|java|lss"
if "%LSS_QUEUE_EMULATOR%"=="ldplayer14" set "PS_REGEX=ld|dnplayer|ldplayer|adb|java|lss"
if "%LSS_QUEUE_EMULATOR%"=="memu" set "PS_REGEX=memu|adb|java|lss"
if "%LSS_QUEUE_EMULATOR%"=="nox" set "PS_REGEX=nox|adb|java|lss"

if "%LSS_QUEUE_LANG%"=="german" echo Schneller Emulator-/LSS-Prozesscheck:
if "%LSS_QUEUE_LANG%"=="english" echo Quick emulator/LSS process check:
if "%LSS_QUEUE_LANG%"=="french" echo Verification rapide des processus emulateur/LSS:
if "%LSS_QUEUE_LANG%"=="espanol" echo Verificacion rapida de procesos emulador/LSS:
if "%LSS_QUEUE_LANG%"=="polski" echo Szybkie sprawdzenie procesow emulatora/LSS:
if "%LSS_QUEUE_LANG%"=="russian" echo Bystraya proverka protsessov emulyatora/LSS:
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Process | Where-Object { $_.ProcessName -match '%PS_REGEX%' } | Select-Object ProcessName,Id,Path | Format-Table -AutoSize"
if errorlevel 1 (
  if "%LSS_QUEUE_LANG%"=="german" echo PowerShell-Prozesscheck uebersprungen oder nicht verfuegbar.
  if "%LSS_QUEUE_LANG%"=="english" echo PowerShell process check skipped or unavailable.
  if "%LSS_QUEUE_LANG%"=="french" echo Verification PowerShell ignoree ou indisponible.
  if "%LSS_QUEUE_LANG%"=="espanol" echo Verificacion PowerShell omitida o no disponible.
  if "%LSS_QUEUE_LANG%"=="polski" echo Sprawdzenie PowerShell pominiete albo niedostepne.
  if "%LSS_QUEUE_LANG%"=="russian" echo Proverka PowerShell propushchena ili nedostupna.
)
echo.

call "%~dp000_CHECKING.cmd" --lang %LSS_QUEUE_LANG% --emulator-type %LSS_QUEUE_EMULATOR% %*

endlocal
