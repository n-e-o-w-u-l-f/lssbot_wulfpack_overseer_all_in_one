# V4.2 Fixes

## 1. Hard stop after last account

Observed bad sequence:

```text
Account Switcher ... -5 (Switched to the last account)
Game Loading Solver
Starting script Commend Leaderboard
Starting from account ID 0
Skipped - on cooldown
```

V4.2 treats `-5 (Switched to the last account)` as a terminal event:
- send German IRC/status message,
- hard-stop LSS immediately,
- write next task profile,
- start LSS again.

## 2. Old-loop guard

If LSS survives the stop and writes `Starting from account ID 0` or `Skipped - on cooldown` shortly after the last-account event, V4.2 still treats the previous task as done, hard-stops the old process, and advances to the next task.

## 3. Loading solver / popup guard

V4.2 cannot directly change LSS internal loading solver timing. It adds:
- warning when a task starts too soon after `Stopping loading solver`,
- optional retry mode,
- best-effort profile wait/delay mutation via `config/wait_policy.json`.

## 4. Stronger process stop

V4.2 adds targeted command-line kill for `java.exe`/`javaw.exe` only when the command line contains LSS-related patterns such as `lssbot`, `LSS Bot`, or `lssbot_5`.
