# Source Inspection

## Reihenfolge

1. `LSS Bot.zip`
2. `lssbot_5.zip`
3. `lss_sidecar_v4_3_2.zip`
4. V4.4-Patch

## Befund: LSS Bot.zip

Enthält:
- `LSS Bot.exe`
- `app/LSS Bot.cfg`
- `app/lssbot-launcher.jar`
- `logs/lssbot-log-*.log`
- Java Runtime Dateien

Keine echten LSS-Task-/Settings-Profile als JSON.

## Befund: lssbot_5.zip

Enthält:
- `lssbot5.jar`
- `tools/lssbot-client.jar`
- `launcher_configs.props`
- `version.props`
- `tessdata/eng.traineddata`, `tessdata/osd.traineddata`
- `images/lss/**`
- `backups/LDP_configs06-21-2026_12-16-21.zip`

Keine `Farms.json`, `Mains.json` oder echte LSS-Settings-Profile. Die Backup-ZIP enthält LDPlayer-Konfigurationen, keine LSS-Profile.

## Relevante LSS-Bytecode-Hinweise

Aus `lssbot5.jar`:
- `com.lssbot.core.framework.botinstance.LSSBotInstanceSettings`
  - `stopInstanceAfterLoop`
  - `randomizeTaskOrder`
  - `ignoreCooldowns`
  - `sleepBaseEnterMills`
  - `sleepMapOpenMills`

Diese Felder werden in V4.4 als Best-Effort-Overrides genutzt, wenn sie in einem JSON-Profil vorkommen.

## Schlussfolgerung

Die Icons/Bilder sind in `images/lss/**` und teilweise als Ressourcen in der JAR vorhanden. Der bisherige Sidecar-Fehler wurde nicht durch fehlende Icons verursacht, sondern durch:
1. fehlende echte Runtime-Profile im Upload,
2. falsche/überschriebene `find_base()`-Funktion in V4.3.2,
3. fehlende Selftests im Paket.
