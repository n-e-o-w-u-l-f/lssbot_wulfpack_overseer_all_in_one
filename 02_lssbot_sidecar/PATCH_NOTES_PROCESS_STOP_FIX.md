# Process-Stop-Fix ohne Config-Änderung

Problem:
- LSS blieb/stoppt im Start-/Loading-Durchgang bzw. der Sidecar konnte nicht stabil bis zum Taskwechsel steuern.
- Der Profilwriter konnte aus alten Overrides `stopInstanceAfterLoop=true` in die aktive Profilkopie schreiben.
- Damit kann LSS den Lauf selbst beenden, bevor der Sidecar anhand von `Account Switcher ... -5` den nächsten Task schreiben kann.

Fix:
- Config-Dateien unverändert.
- VERSION bleibt `4.4.0`.
- `src/lss_sidecar_v4_4.py` erzwingt beim Schreiben von `zz_TASK_CHAIN_ACTIVE.json` code-seitig `stopInstanceAfterLoop=false`.
- Der Taskwechsel bleibt vollständig beim Sidecar: letzter Account = Logsignal `Account Switcher ... -5`, danach Freeze + Hard Stop + nächster Task.

Lokale Tests:
- `python -m py_compile src/lss_sidecar_v4_4.py`
- `python src/lss_sidecar_v4_4.py --self-test`
- `python src/lss_sidecar_v4_4.py --replay-task10-test --real-log <echter Logauszug>`
- Ergebnis: `SELFTEST OK`, `TASK10_REPLAY_OK completed=1..10`

Hinweis:
- Das ist weiterhin ein Sidecar-Fix. Keine LSS Bot.exe/JAR/APK wird gepatcht.
