# lssbot_wulfpack_overseer_all_in_one_v0.0.9

Dieses Paket enthält **beides in einem ZIP**, aber sauber getrennt:

```text
01_queue_generator\
02_lssbot_sidecar\
```

Du brauchst im Normalfall nur einen Befehl:

```powershell
.\00_START_ALL.cmd
```

## Was `00_START_ALL.cmd` macht

```text
1. startet 01_queue_generator\START.cmd
2. erzeugt die Queue-JSON und den Plan
3. startet 02_lssbot_sidecar\00_RUNNER.cmd
4. importiert die Queue nach LSS-Bot
5. schreibt das aktive LSS-Bot-Profil
6. startet/überwacht LSS Bot.exe
```

## Wenige Befehle

Alles starten:

```powershell
.\00_START_ALL.cmd
```

Alles testen ohne echten Live-Lauf:

```powershell
.\01_DRY_RUN_ALL.cmd
```

Nur vorhandene Queue importieren:

```powershell
.\02_IMPORT_ONLY.cmd
```

LSS Bot.exe hart stoppen:

```powershell
.\03_STOP_LSSBOT.cmd
```

## Struktur

```text
00_START_ALL.cmd
01_DRY_RUN_ALL.cmd
02_IMPORT_ONLY.cmd
03_STOP_LSSBOT.cmd

01_queue_generator\
  START.cmd
  00_CHECKING.cmd
  01_INSTALLING.cmd
  ...

02_lssbot_sidecar\
  00_RUNNER.cmd
  01_IMPORT_QUEUE.cmd
  02_DRY_RUN.cmd
  03_SCAN_PROFILES.cmd
  04_VALIDATE_CONFIG.cmd
  05_SELF_TEST.cmd
  07_STOP_LSSBOT.cmd
  src\
  config\
```

## Klarstellung

Der Queue-Generator erzeugt die Queue.

Der Sidecar übernimmt danach die LSS-Bot-Kontrolle:

```text
Queue JSON
→ config\task_chain.json
→ %APPDATA%\lssbot_5\settings\zz_TASK_CHAIN_ACTIVE.json
→ LSS Bot.exe starten/stoppen/überwachen
```

Das Paket ist kombiniert, aber die Rollen bleiben getrennt.


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


## v0.0.9 Task-Presets

Vollständige Presets liegen hier:

```text
docs\TASK_PRESETS.md
docs\wulfpack_queue_presets_v0_0_9.json
01_queue_generator\docs\TASK_PRESETS.md
01_queue_generator\config_wulfpack_queue_presets_v0_0_9.json
```

Direkteingabe im Generator:

```text
4 Queues: Q1 Q2 Q3 Q4
5 Queues: Q1 Q2 Q3 Q4 Q5
6 Queues: Q1 Q2 Q3 Q4 Q5 Q6
```
