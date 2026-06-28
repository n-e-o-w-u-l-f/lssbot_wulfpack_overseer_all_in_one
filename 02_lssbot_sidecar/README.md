# lssbot_sidecar_wulfpack_overseer_v0.0.6 — SIDE-CAR ONLY

Das ist **nur** der LSS-Bot-Sidecar.

Dieses Paket enthält **nicht** den Queue-Generator.  
Der Queue-Generator bleibt getrennt.

## Was dieser Sidecar macht

```text
1. liest die erzeugte Queue-JSON des getrennten Queue-Generators
2. importiert die Queue nach config\task_chain.json
3. schreibt pro Task ein aktives LSS-Bot-Profil:
   %APPDATA%\lssbot_5\settings\zz_TASK_CHAIN_ACTIVE.json
4. startet/stoppt LSS Bot.exe
5. überwacht LSS-Bot-Logs
6. erkennt Account Switcher -5 / letzter Account
7. stoppt LSS Bot.exe sofort nach dem letzten Account
8. schreibt den nächsten Task in das aktive Profil
9. startet LSS Bot.exe erneut
10. überspringt einen hängenden Task nach maximal 5 Versuchen
11. sendet optional IRC/ZNC-Statusmeldungen
```

## Was dieser Sidecar nicht ist

```text
- kein LDPlayer-Sidecar
- kein ADB-Runner
- kein kombinierter Queue-Generator
- kein blindes Patchen von LSS Bot.exe
```

## Reihenfolge

Erst im getrennten Queue-Generator:

```powershell
.\START.cmd
```

Dann in diesem Sidecar-Paket:

```powershell
.\00_RUNNER.cmd
```

## Einzelbefehle

Nur Queue importieren:

```powershell
.\01_IMPORT_QUEUE.cmd
```

Dry-Run ohne echten LSS-Start:

```powershell
.\02_DRY_RUN.cmd
```

Profile scannen:

```powershell
.\03_SCAN_PROFILES.cmd
```

Config prüfen:

```powershell
.\04_VALIDATE_CONFIG.cmd
```

Selbsttest:

```powershell
.\05_SELF_TEST.cmd
```

LSS Bot hart stoppen:

```powershell
.\07_STOP_LSSBOT.cmd
```

## Queue-Import

Automatisch gesucht werden:

```text
%USERPROFILE%\lss_character_queue_v5_final\lss_character_queue_v5_final.generated.json
%USERPROFILE%\lss_character_queue_v1_337a\lss_character_queue_v1_337a.generated.json
```

Manuell:

```powershell
.\01_IMPORT_QUEUE.cmd --queue-json "C:\Pfad\zur\lss_character_queue_v5_final.generated.json"
```

Nur bestimmte Queues importieren:

```powershell
.\01_IMPORT_QUEUE.cmd --queue-ids queue1,queue2
```

## LSS-Bot Ziel

Der Sidecar arbeitet mit:

```text
LSS Bot.exe:
%LOCALAPPDATA%\lssbot\LSS Bot.exe

LSS Settings:
%APPDATA%\lssbot_5\settings

Aktives Sidecar-Profil:
%APPDATA%\lssbot_5\settings\zz_TASK_CHAIN_ACTIVE.json
```

## Sicherheit

Vor dem Überschreiben von `task_chain.json` wird ein Backup geschrieben:

```text
config\_backups\
```

Vor dem Überschreiben des aktiven LSS-Profils schreibt der Sidecar Backups in:

```text
%APPDATA%\lssbot_5\settings\_sidecar_backups\
```

## Wichtige Klarstellung

Der Sidecar „fügt die Queue in LSS-Bot ein“, indem er das aktive LSS-Bot-Profil schreibt und LSS Bot.exe damit startet.  
Er schreibt nicht in die EXE-Datei selbst und patcht keine Binary.


## Queue-Presets Q1-Q6

Bei der Queue-Abfrage musst du nicht mehr Nummern tippen. Nutze:

```text
Q1
Q2
Q3
Q4
Q5
Q6
auto
```

Die Presets lösen die Tasks in Untertasks/Optionen auf und schreiben diese in JSON + Plan.

Wichtige Regeln:

```text
- wiederholbarer Wrapper in jedem Queue-Block
- Collect Quest Rewards nur in der letzten Queue
- Shield: 2hr + everyday + Gathering Search Menu
- Gather Speedup: Gathering Search Menu + Alliance Gathering
- Zombies max Level 40
```
