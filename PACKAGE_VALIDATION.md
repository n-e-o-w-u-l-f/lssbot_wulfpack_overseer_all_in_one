# Package Validation

Status: OK

Package: lssbot_wulfpack_overseer_all_in_one_v0.0.9

Added:

- Complete 4-queue preset.
- Complete 5-queue preset.
- Complete 6-queue preset.
- Preset JSON:
  - docs\wulfpack_queue_presets_v0_0_9.json
  - 01_queue_generator\config_wulfpack_queue_presets_v0_0_9.json
- Preset documentation:
  - docs\TASK_PRESETS.md
  - 01_queue_generator\docs\TASK_PRESETS.md

Rules enforced by presets:

- Q1/Q2/Q3/Q4/Q5/Q6 direct input.
- Repeatable wrapper in every queue block.
- Collect Quest Rewards only in final queue.
- Shield: 2hr + everyday + Gathering Search Menu.
- Gather Speedup: Gathering Search Menu + Alliance Gathering.
- Collect Base Resources includes Serum/Food/Wood/Steel/Gas and antiserum storage limit confirmation.
- Zombies max level 40.

Primary command:

```powershell
.\00_START_ALL.cmd
```
