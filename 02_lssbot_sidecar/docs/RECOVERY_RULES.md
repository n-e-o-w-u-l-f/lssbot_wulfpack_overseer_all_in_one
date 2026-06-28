# Recovery-Regeln

Als echter Task-Abschluss gilt nur:

```text
Stopping script "Account Switcher" ... -5 (Switched to the last account)
```

Direkt danach stoppt der Sidecar LSS, damit der bekannte alte Loop nicht startet:

```text
Starting from account ID 0
```

Harte Fehler:

```text
Snapshot error
State DISCONNECTED
Timeout getting a response from the device
Stopping script "Account Switcher" ... -2 (Failed)
```

Standard:
1. IRC-Meldung senden.
2. LSS stoppen.
3. denselben Task erneut setzen.
4. LSS neu starten.
5. nach `max_retries_per_task` abbrechen.
