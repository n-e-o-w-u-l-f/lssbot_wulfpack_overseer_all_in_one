# LSS Sidecar V4.4.0 Patch Notes

## Geprüfte Quellen aus Uploads

- `LSS Bot.zip`: enthält `LSS Bot.exe`, `app/lssbot-launcher.jar` und LSS-Logs, aber keine Settings-Profile.
- `lssbot_5.zip`: enthält `lssbot5.jar`, `tools/lssbot-client.jar`, `tessdata/`, `images/lss/**`, `backups/`, aber keine `Farms.json`/`Mains.json`/echten LSS-Settings-Profile.
- `lssbot5.jar`: Bytecode-Inspektion zeigt `LSSBotInstanceSettings` Felder:
  - `stopInstanceAfterLoop`
  - `randomizeTaskOrder`
  - `ignoreCooldowns`
  - `sleepBaseEnterMills`
  - `sleepMapOpenMills`

## Behobene Fehler

1. Doppeltes `find_base()` entfernt.
   - V4.3.2 hatte zwei Definitionen.
   - Die zweite überschreibt die korrekte Signatur und verursachte:
     `TypeError: find_base() got an unexpected keyword argument 'cfg'`.

2. Dry-Run blockiert nicht mehr.
   - V4.3.2 wartete im Dry-Run auf echte Logs.
   - V4.4 simuliert Profil-Mutation und beendet nach `dry_run_task_limit` Tasks.

3. Tailer wird vor jedem LSS-Start auf Dateiende gesetzt.
   - Alte `-5` / `Starting from account ID 0` Zeilen können keinen neuen Task mehr fälschlich triggern.

4. `zz_TASK_CHAIN_ACTIVE.json` bleibt als Basisprofil ausgeschlossen.

5. Best-Effort LSS-Instanzfelder ergänzt:
   - `stopInstanceAfterLoop=true`
   - `randomizeTaskOrder=false`
   - `ignoreCooldowns=false`
   - längere Basis-/Map-Wartezeiten, wenn die Felder im JSON existieren.

6. `07_SELF_TEST.cmd` hinzugefügt.
   - Testet Profilwriter ohne echte LSS-Installation.

## Grenze

Die echten LSS-Profile liegen nicht in den gelieferten ZIPs. Der Sidecar kann nur dann `matched>0` erreichen, wenn in `%APPDATA%\lssbot_5\settings` ein echtes LSS-Profil mit Scriptliste liegt, z. B. `Farms.json` oder `Mains.json`.
