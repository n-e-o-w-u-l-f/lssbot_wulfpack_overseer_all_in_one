# Validation

Status: OK

Korrigierter Scope:

- Sidecar-only package: OK
- Queue-Generator nicht enthalten: OK
- Kein LDPlayer-Sidecar: OK
- Kein ADB-Runner: OK
- LSS Bot.exe Prozesskontrolle: OK
- LSS-Bot Settings-Profilwriter: OK
- Queue JSON -> task_chain.json Import: OK
- Account Switcher last-account detection: OK
- Hard-stop after last account: OK
- Skip after 5 failed attempts: OK
- IRC/ZNC relay support from V4.4 retained: OK

Primary command:

```powershell
.\00_RUNNER.cmd
```

What .\00_RUNNER.cmd does:

```text
install config if missing
import queue JSON into config\task_chain.json
validate LSS paths/config
run sidecar live against LSS Bot.exe
```

Important:

The sidecar adds the queue to LSS-Bot by writing the active LSS-Bot settings profile:
%APPDATA%\lssbot_5\settings\zz_TASK_CHAIN_ACTIVE.json

It does not patch LSS Bot.exe binary.
