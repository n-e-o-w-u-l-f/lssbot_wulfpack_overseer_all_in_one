# PATCH NOTES — Stale Recent-Scan Guard Fix

Status: code-only fix, configuration unchanged, VERSION remains 4.4.0.

## Fixed

The previous recent-scan guard read the last 256 KB of every matched LSS log file.
That could pull critical lines from older runs into the current task, for example
old `SWITCH_FAILED`, `Timeout`, `Skipped - on cooldown`, or `Switched to the last account`
events.

This caused Task 01 to abort immediately after startup with messages such as:

```text
[LOG][RECENT_SCAN] kritische Zeilen nachgezogen: 183
[LSS] Problem bei Task 01: SWITCH_FAILED
```

## Change

`Tailer.mark_end()` now stores a byte baseline for every existing log file.

`_recent_critical_scan()` now only scans:
- bytes written after the task baseline for existing files
- new files created after task start

It no longer scans old log tails wholesale.

## Validation performed

```text
python -m py_compile src/lss_sidecar_v4_4.py
python src/lss_sidecar_v4_4.py --self-test
python src/lss_sidecar_v4_4.py --replay-task10-test --real-log /mnt/data/Eingefügter Text.txt
```

Observed result:

```text
SELFTEST OK
TASK10_REPLAY_OK completed=1..10
```

Note: this is a local deterministic replay test against provided logs and simulated profiles, not a real Windows LDPlayer/LSS run in this sandbox.
