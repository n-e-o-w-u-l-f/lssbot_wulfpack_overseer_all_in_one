# Architektur

```text
LSS Sidecar V4
 ├─ Config Loader
 ├─ Profile Writer
 │   └─ schreibt zz_TASK_CHAIN_ACTIVE.json aus echtem LSS-Profil
 ├─ Process Controller
 │   ├─ startet LSS Bot.exe
 │   └─ stoppt LSS nach Task-Ende oder Fehler
 ├─ Log Tailer
 │   └─ liest LSS-Protokolle
 ├─ Event Classifier
 │   ├─ last account erkannt
 │   ├─ alter Account-ID-0-Loop erkannt
 │   ├─ Snapshot/Disconnect/Timeout erkannt
 │   └─ falsches Script erkannt
 ├─ Recovery Engine
 └─ IRC Relay
```

Der Sidecar greift nicht in den Speicher des LSS-Prozesses ein. Er steuert nur Prozessstart/-stop, lokale Config/Profile-Dateien und Log-Auswertung.
