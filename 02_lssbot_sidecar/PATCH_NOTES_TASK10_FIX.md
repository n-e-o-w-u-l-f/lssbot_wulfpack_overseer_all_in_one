# V4.4 Task-10 Loop Fix

Status: code-only hotfix, internal VERSION remains 4.4.0.

Fixes:
- Adds internal LSS log path expansion for `%LOCALAPPDATA%\lssbot\**\*.log` and other runtime locations without changing config files.
- Adds hard fallback detection for `Stopping script "Account Switcher" ... -5 (Switched to the last account)`.
- Freezes `zz_TASK_CHAIN_ACTIVE.json` immediately after last-account detection before killing LSS, so a failed/late kill cannot keep Task 1 active after restart.
- Strengthens process kill patterns internally without changing config files.
- Adds `08_REPLAY_TASK10.cmd`.
- Adds `--replay-task10-test`.

Local validation performed:
- `python -m py_compile src/lss_sidecar_v4_4.py`
- `python src/lss_sidecar_v4_4.py --self-test`
- `python src/lss_sidecar_v4_4.py --replay-task10-test --real-log /mnt/data/Eingefügter Text.txt`

Result:
- SELFTEST OK
- TASK10_REPLAY_OK completed=1..10

Limit:
- This environment cannot start the real Windows LSS Bot.exe / LDPlayer process. The Task-10 validation is a deterministic local replay using the provided real loop log and synthetic LSS profiles.
