# Config Reference

## sidecar_config.json

```json
"dry_run": true
```

Bei `true`: keine echten Prozess-/Profiländerungen.

```json
"lss_exe_path": "C:\\Users\\megal\\AppData\\Local\\lssbot\\LSS Bot.exe"
```

Pfad zum Hauptprozess.

```json
"settings_dir": "C:\\Users\\megal\\AppData\\Roaming\\lssbot_5\\settings"
```

Zielordner für `zz_TASK_CHAIN_ACTIVE.json`.

```json
"managed_instances": ["Farms", "Mains"]
```

Instanzen, deren Logs in IRC landen.

## task_chain.json

```json
{
  "id": 11,
  "name": "Radio Quiz",
  "script_names": ["Radio Quiz"],
  "enabled": true
}
```

Die Scriptnamen müssen zum LSS-Profil/Log passen.

## irc_config.json

```json
"server": "10.1.0.11",
"port": 7777,
"nick": "LSS-Bot"
```

Passwort bevorzugt per Umgebungsvariable:

```powershell
setx LSS_IRC_PASSWORD "ZNC_USER/ZNC_NETWORK:ZNC_PASSWORD"
```
