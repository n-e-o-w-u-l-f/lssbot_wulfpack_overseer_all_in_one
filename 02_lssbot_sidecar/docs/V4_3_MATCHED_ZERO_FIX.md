# V4.3 matched=0 Fix

## Problem

Wenn der Sidecar meldet:

```text
matched=0 touched=0
```

wurde kein passender Scriptname im Basisprofil gefunden. In V4.2 konnte das passieren, weil `zz_TASK_CHAIN_ACTIVE.json` selbst als Basisprofil bevorzugt wurde.

## Fix

V4.3 nutzt `zz_TASK_CHAIN_ACTIVE.json` nicht mehr als Basis. Die neue Reihenfolge ist:

```json
"base_profile_preference": [
  "Farms.json",
  "Mains.json",
  "default.json"
]
```

Zusätzlich gibt es:

```text
05_SCAN_PROFILES.cmd
```

Der Scanner sucht in `%APPDATA%\lssbot_5\settings\*.json` nach Scriptnamen aus `task_chain.json`.

## Wenn weiterhin matched=0 kommt

Dann enthält dein Settings-Ordner kein Profil mit echter Scriptliste. In LSS Bot ein normales Profil speichern/exportieren, in dem die Scripts sichtbar sind, danach `05_SCAN_PROFILES.cmd` erneut ausführen.
