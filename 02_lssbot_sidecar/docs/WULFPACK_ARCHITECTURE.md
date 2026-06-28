# Architektur

```text
Getrennter Queue-Generator
  └─ erzeugt lss_character_queue_v5_final.generated.json

LSSBot Sidecar Wulfpack Overseer
  ├─ importiert Queue JSON nach config\task_chain.json
  ├─ schreibt zz_TASK_CHAIN_ACTIVE.json in %APPDATA%\lssbot_5\settings
  ├─ startet LSS Bot.exe
  ├─ liest LSS-Bot Logs
  ├─ erkennt Account Switcher -5 / letzter Account
  ├─ stoppt LSS Bot.exe
  ├─ schreibt nächsten Task
  └─ wiederholt bis Queue fertig ist
```
