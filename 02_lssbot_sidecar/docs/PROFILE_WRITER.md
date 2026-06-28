# Profil-Schreiber

Der Sidecar schreibt `zz_TASK_CHAIN_ACTIVE.json` aus einem echten LSS-Profil.

Basisprofil-Suche:

```json
"base_profile_preference": [
  "zz_TASK_CHAIN_ACTIVE.json",
  "Farms.json",
  "Mains.json",
  "default.json"
]
```

Er sucht rekursiv nach Script-Objekten mit Feldern wie:

```text
name, scriptName, script, title, label
active, enabled, selected
position, order, priority
```

Aktiviert werden:
- der aktuelle Task
- `Account Switcher`

Vor dem Überschreiben erstellt er ein Backup in:

```text
settings\_sidecar_backups
```
