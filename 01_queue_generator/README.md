# LSS Character Queue v5.0 FINAL

Eine verständliche, schrittweise README für neue Anwender.

Dieses Projekt ist ein Windows-Hilfswerkzeug für Nutzer von **LSS-Bot** und **Puzzles & Survival**, die mehrere Charaktere über einen oder mehrere Android-Emulatoren verwalten möchten.

Der wichtigste Startbefehl lautet:

```powershell
.\START.cmd
```

Ältere Startnamen wie `start_lss...` oder `START_lss...` sind veraltet und sollen nicht mehr benutzt werden.

---

## Was ist das?

**LSS Character Queue** ist ein kleines Werkzeug, das dir hilft, eine sinnvolle Reihenfolge für mehrere LSS-Bot-Aufgaben zu planen.

Es erkennt Emulatoren, fragt deine Charaktere ab, lässt dich Aufgaben in Queues einteilen und schreibt daraus eine übersichtliche Konfiguration.

Das Tool ist also kein Ersatz für LSS-Bot, sondern ein **Queue-Generator** beziehungsweise **Planungshelfer** für LSS-Bot.

Kurz gesagt:

```text
Mehrere Emulatoren
+ mehrere Charaktere
+ mehrere LSS-Bot Tasks
= sauber geplanter Queue-Ablauf
```

---

## Wozu dient das?

Wenn du nur einen Charakter hast, brauchst du normalerweise keine komplexe Queue.

Wenn du aber mehrere Accounts hast, zum Beispiel:

```text
Main
Farm 1
Farm 2
Farm 3
Farm 4
```

und diese Accounts auf einem oder mehreren Emulatoren laufen, wird die Reihenfolge schnell unübersichtlich.

Dieses Tool hilft dabei, Aufgaben logisch zu gruppieren:

```text
Queue 1 = Allianz-Aufgaben
Queue 2 = Basis / Forschung / Truppen
Queue 3 = Belohnungen / Items
Queue 4 = Puzzle / Zombies
```

Dadurch kannst du später besser steuern, was auf welchem Charakter und Emulator zuerst passieren soll.

---

## Was macht das?

Das Tool macht mehrere Dinge nacheinander:

1. Es fragt deine Sprache ab.
2. Es fragt deinen installierten Emulator ab.
3. Es sucht passende Emulator-Programme auf deinem PC.
4. Es erkennt vorhandene Emulator-Instanzen.
5. Es sucht nach LSS-Bot-Ordnern im aktuellen Windows-Benutzerprofil.
6. Es fragt, welche Emulatoren genutzt werden sollen.
7. Es fragt, wie viele Charaktere pro Emulator vorhanden sind.
8. Es fragt, wie viele Queues erstellt werden sollen.
9. Es fragt, welche Aufgaben in welche Queue gehören.
10. Es schreibt eine prüfbare Konfiguration und einen Plan.

Wichtig: Das Tool patcht LSS-Bot-Dateien standardmäßig **nicht direkt**.

Es erstellt zuerst einen Plan, damit du prüfen kannst, ob die Reihenfolge sinnvoll ist.

---

## Wie nutze ich das?

### Schritt 1: ZIP entpacken

Entpacke die ZIP-Datei in einen eigenen Ordner, zum Beispiel:

```text
C:\Users\<DEINNAME>\Desktop\lss_character_queue_v5_final
```

Der Ordner sollte diese Dateien enthalten:

```text
START.cmd
00_CHECKING.cmd
01_INSTALLING.cmd
lss_character_queue_v5_final.py
LICENSE.txt
README.md
```

---

### Schritt 2: PowerShell im Ordner öffnen

Öffne PowerShell in diesem Ordner.

Beispiel:

```powershell
cd "$env:USERPROFILE\Desktop\lss_character_queue_v5_final"
```

---

### Schritt 3: Tool starten

Starte das Tool mit:

```powershell
.\START.cmd
```

Nicht verwenden:

```powershell
.\start_lss_character_queue_v5_final.cmd
.\START_lss_character_queue_v5_final.cmd
```

Diese Namen sind veraltet.

---

### Schritt 4: Sprache auswählen

Beim Start erscheint eine Sprachauswahl:

```text
1. English
2. German
3. French
4. Espanol
5. Polski
6. Russian
```

Für Deutsch wählst du:

```text
2
```

Danach wird die Auswahl gespeichert.

---

### Schritt 5: Emulator auswählen

Danach fragt das Tool nach dem installierten Emulator:

```text
1. LDPlayer9
2. LDPlayer5
3. LDPlayer4
4. LDPlayer 14 beta
5. MEmu Play
6. Nox Player
7. Auto / unknown
```

Empfehlung:

```text
LDPlayer9
```

Wenn du LDPlayer9 nutzt, wähle:

```text
1
```

---

## Welche Emulatoren werden empfohlen?

### 1. LDPlayer9 — empfohlen

**LDPlayer9** ist die bevorzugte Wahl.

Warum?

- LSS-Bot wird häufig mit LDPlayer genutzt.
- LDPlayer hat eine brauchbare Kommandozeilensteuerung.
- Das Tool kann LDPlayer-Instanzen über `dnconsole.exe list2` sauber auslesen.
- Instanznamen und IDs lassen sich gut zuordnen.
- Mehrere Instanzen sind gut handhabbar.

Beispiel:

```text
LDPlayer9-(Farmen) (ID: 0)
LDPlayer-(Mains)   (ID: 1)
```

Daraus erkennt das Tool:

```text
ID 0 -> emulator-5554
ID 1 -> emulator-5556
```

### 2. LDPlayer5 / LDPlayer4 — möglich

Ältere LDPlayer-Versionen können ebenfalls funktionieren.

Sie sind aber weniger bevorzugt als LDPlayer9.

Nutze sie nur, wenn deine bestehende LSS-Bot-Installation bereits darauf basiert.

### 3. LDPlayer 14 beta — experimentell

LDPlayer 14 beta ist als Auswahl vorhanden.

Da es eine Beta-Version ist, sollte sie nur genutzt werden, wenn du bewusst damit arbeitest.

### 4. MEmu Play — unterstützt

MEmu Play wird unterstützt.

Das Tool sucht nach:

```cmd
memuc.exe listvms --running
```

und als Fallback:

```cmd
memuc.exe listvms
```

MEmu ist brauchbar, aber nicht die bevorzugte Standardempfehlung.

### 5. Nox Player — unterstützt

Nox Player wird unterstützt.

Das Tool sucht nach:

```cmd
NoxConsole.exe list
```

Nox kann funktionieren, ist aber für diesen Workflow weniger bevorzugt als LDPlayer9.

### 6. Auto / unknown — nur wenn du unsicher bist

Wähle `Auto / unknown`, wenn du nicht weißt, welcher Emulator installiert ist.

Das Tool sucht dann breiter. Das kann aber langsamer und weniger exakt sein.

---

## Was erkennt das Tool bei LDPlayer?

Bei LDPlayer nutzt das Tool bevorzugt:

```cmd
dnconsole.exe list2
```

oder:

```cmd
ldconsole.exe list2
```

Ein typisches Ergebnis sieht so aus:

```text
0,LDPlayer9-(Farmen),...
1,LDPlayer-(Mains),...
```

Das Tool macht daraus:

```text
LDPlayer9-(Farmen) (ID: 0) -> emulator-5554
LDPlayer-(Mains)   (ID: 1) -> emulator-5556
```

Das ist wichtig, damit später nicht nur generische Namen wie `Emulator 1` erscheinen, sondern echte Instanznamen.

---

## Was muss vor dem Start vorbereitet sein?

Empfohlen:

```text
Windows 10 oder Windows 11
Python 3 installiert
LSS-Bot installiert
Puzzles & Survival im Emulator eingerichtet
mindestens ein Emulator installiert
optional mehrere Emulator-Instanzen
```

Für LDPlayer:

```text
LDPlayer9 installiert
Instanzen im LDPlayer Multi-Instance Manager angelegt
Puzzles & Survival in den Instanzen installiert
LSS-Bot bereits einmal gestartet
```

---

## Welche Ordner werden gescannt?

Das Tool scannt standardmäßig nur den aktuellen Windows-Benutzer.

Typische Ordner:

```text
%USERPROFILE%\lssbot_5
%LOCALAPPDATA%\lssbot
%APPDATA%\lssbot
```

Es scannt **nicht** pauschal:

```text
C:\Users\*
andere Windows-Benutzerprofile
globale Program-Files-Ordner als LSS-Bot-Wurzel
```

Dadurch bleibt der Scan schneller und sicherer.

---

## Welche Ordner werden absichtlich ignoriert?

Damit der Scan nicht hängen bleibt, werden Runtime-Ordner ignoriert:

```text
runtime\
lib\
jre\
jdk\
java\
cache\
temp\
```

Auch diese Dateien werden ignoriert:

```text
psfontj2d.properties
*.runtimeconfig.json
*.deps.json
*.dll.config
```

Diese Dateien gehören zu Java oder .NET und helfen nicht beim Task-Mapping.

---

## Was bedeuten die Live-Meldungen?

Während des Scans siehst du Statuszeilen.

Beispiel:

```text
[..] Live-Scan starten
[..] Phase 1/4: Instanzsuche über Hersteller-CLI
[OK] Hersteller-CLI Kandidaten gefunden: 4
[..] LDPlayer-Instanzen über list2 prüfen
[OK] LDPlayer list2 gefunden
```

Bedeutung:

```text
[..] = Arbeitsschritt läuft oder wird gestartet
[OK] = Schritt erfolgreich
[!!] = Warnung oder Problem
```

Aktuelle Farbregeln:

```text
[..] dunkelgrau, Text rechts daneben grau
[OK] Klammern grau, OK grün, Text rechts daneben grau
[!!] Klammern grau, !! blau, Text rechts daneben grau
```

---

## Welche Tasks kennt das Tool?

Der aktuelle Task-Katalog enthält:

```text
[Alliance]
Alliance Research
Alliance Gifts
Alliance Gathering
Alliance Activities Generic

[Pit]
Pit Gather
Pit Attack

[Campaign Puzzle]
Campaign Puzzle Auto
Campaign Puzzle General
Dynamic Base Puzzles
Duel Survival

[Resources]
Resource Gathering
Gathering Boost
Supply Depot

[Base]
Building Upgrading
HQ Upgrading
Research
Wall Repair
Trap Crafting
Shield

[Military]
Troop Training
Troop Healing
Tavern Recruitment
Skills

[Rewards / Inventory / Economy]
Quest Rewards
Game Gifts
Bag Items
Bank Investment
Radio Quiz
Ruins

[Zombies]
Zombies 20-40 bis Zombies 39-59
Zombies 40
```

---

## Was bedeutet `split_confirmed`?

Einige Tasks sind bereits genauer aufgeteilt.

Beispiele:

```text
Alliance Research
Alliance Gifts
Alliance Gathering
Pit Gather
Pit Attack
Campaign Puzzle Auto
Campaign Puzzle General
Zombies-Levelblöcke
```

Diese Tasks haben konkrete Regeln.

Beispiel:

```text
Alliance Research
```

bedeutet:

```text
Alliance Technology öffnen
Economy auswählen
Military auswählen
Skill auswählen
Donate to alliance technology aktivieren
Check hot technology first aktivieren
Alliance Gifts nicht einsammeln
Alliance Territory Gathering nicht ausführen
```

---

## Was bedeutet `official_generic`?

`official_generic` bedeutet:

Der Task ist im bekannten LSS-Bot/Puzzles-&-Survival-Aufgabenkatalog enthalten, aber die exakten internen Feldnamen oder Checkboxnamen wurden noch nicht lokal bestätigt.

Das ist wichtig, damit das Tool nicht so tut, als wären unbekannte Klickpfade schon sicher.

Kurz gesagt:

```text
Task ist bekannt,
aber exakte LSS-Bot-Felder müssen noch bestätigt werden.
```

---

## Wie viele Queues sollte ich erstellen?

Empfehlung:

```text
4 bis 6 Queues
```

### Einfache Variante: 4 Queues

Gut für neue Anwender:

```text
Q1 Alliance:
   Alliance Research + Alliance Gifts + Alliance Gathering

Q2 Base / Military:
   Building + HQ + Research + Troops + Healing + Tavern + Wall + Traps

Q3 Rewards / Utility:
   Quest Rewards + Game Gifts + Bag Items + Supply Depot + Bank + Radio Quiz + Ruins

Q4 Combat / Puzzle / Zombies:
   Campaign Puzzle + Dynamic Base Puzzles + Duel Survival + genau ein Zombie-Block
```

### Bessere Trennung: 5 Queues

```text
Q1 Alliance
Q2 Base Maintenance
Q3 Military
Q4 Rewards / Inventory / Economy
Q5 Puzzle / Zombies
```

### Saubere Profi-Struktur: 6 Queues

```text
Q1 Alliance
Q2 Base Maintenance
Q3 Military
Q4 Resources / Economy
Q5 Rewards / Puzzle
Q6 Zombies
```

Mehrere Zombie-Blöcke solltest du nur wählen, wenn du das bewusst willst.

---

## Welche Ausführungsmodi gibt es?

### Modus 1: Emulator nacheinander

Erst wird Emulator 1 komplett abgearbeitet.

Danach kommt Emulator 2.

Beispiel:

```text
E1 C1 Q1 -> E1 C2 Q1 -> E1 C1 Q2 -> E1 C2 Q2 -> E2 ...
```

Das ist sinnvoll, wenn ein Emulator komplett fertig sein soll, bevor der nächste beginnt.

### Modus 2: Gleiche Queue zuerst überall

Erst läuft Queue 1 auf allen gewählten Emulatoren und Charakteren.

Danach läuft Queue 2 auf allen.

Beispiel:

```text
E1 C1 Q1 -> E1 C2 Q1 -> E2 C1 Q1 -> E2 C2 Q1 -> Q2 ...
```

Für zwei Emulatoren ist dieser Modus meistens sinnvoller.

---

## Wie wähle ich Tasks aus?

Bei der Queue-Abfrage kannst du mehrere Schreibweisen nutzen.

Beispiele:

```text
1,2,3
1 2 3
1+2+3
1-4
all
alle
```

Beispiel für 4 Queues:

```text
Queue 1: 1+2+3
Queue 2: 4+5
Queue 3: 6+7
Queue 4: 28
```

Die Zahlen hängen davon ab, welche Taskliste im Terminal angezeigt wird.

---

## Welche Dateien erzeugt das Tool?

Das Tool erzeugt prüfbare Ausgabedateien wie:

```text
lss_character_queue_config.json
lss_character_queue_plan.txt
```

Darin stehen unter anderem:

```text
erkannte Emulatoren
ausgewählte Emulatoren
Charaktere
Queues
Tasks
Mapping-Status
geplanter Ablauf
Sicherheitsflags
```

---

## Warum patcht das Tool LSS-Bot nicht sofort?

Absichtlich.

Der erste Schritt soll sicher und nachvollziehbar sein.

Das Tool erzeugt zuerst einen Plan.

Erst wenn der Plan stimmt, kann daraus später ein echter Runner oder ein Patch-Workflow entstehen.

Das verhindert falsche Klicks, falsche Checkboxen oder falsche Emulator-Zuordnungen.

---

## Typische Nutzung für einen neuen Anwender

1. LDPlayer9 installieren.
2. Puzzles & Survival in LDPlayer9 installieren.
3. Falls nötig mehrere LDPlayer-Instanzen anlegen.
4. LSS-Bot installieren.
5. LSS-Bot mindestens einmal starten.
6. Dieses Tool entpacken.
7. PowerShell im Tool-Ordner öffnen.
8. Starten mit:

```powershell
.\START.cmd
```

9. Sprache wählen.
10. Emulator wählen, empfohlen `LDPlayer9`.
11. Erkannte Emulatoren prüfen.
12. Charakteranzahl pro Emulator eintragen.
13. Queue-Modus wählen.
14. 4 bis 6 Queues erstellen.
15. Tasks pro Queue auswählen.
16. erzeugte JSON-/Plan-Dateien prüfen.

---

## Fehlerbehebung

### Die README nennt `start_lss`

Das ist veraltet.

Richtig ist:

```powershell
.\START.cmd
```

### Deutsch wurde gewählt, aber der Scan bleibt englisch

Nutze Hotfix23 oder neuer.

Ab Hotfix23 wird der Live-Scan nach Sprachwahl lokalisiert.

### Fehler: `NameError: WIN_PATH_RE is not defined`

Nutze Hotfix23 oder neuer.

Dieser Fehler ist dort behoben.

### Farben sehen falsch aus

Nutze Hotfix24 oder neuer.

Dort wurden die Statusfarben korrigiert:

```text
[..] dunkelgrau
[OK] Klammern grau, OK grün
[!!] Klammern grau, !! blau
```

### Scan bleibt bei Runtime-Dateien hängen

Nutze Hotfix18 oder neuer.

Runtime-Dateien werden dort übersprungen.

---

## Sicherheit

Das Tool ist bewusst vorsichtig:

```text
kein Direktpatching von LSS-Bot-Dateien im Standardmodus
kein Scan anderer Windows-Benutzerprofile
kein C:\Users\* Scan
kein Runtime-/Lib-Vollscan
Live-Anzeige gegen scheinbares Hängen
unsichere Tasks als official_generic markiert
Output zuerst prüfen
```

---

## Lizenz

MIT License

Copyright (c) 2026 Andreas Tobias Sebastian Bolder

---

```text
##############
## Liebe Grüße ##
##############
an S1035 ~Shared Kaos~ Hans, Moha und all meine Freunde
```



## Wulfpack v0.0.9 Queue Presets

Bei der Task-Auswahl kannst du jetzt direkt eingeben:

```text
Q1
Q2
Q3
Q4
Q5
Q6
auto
```

Beispiel:

```text
Wieviele Queues erstellen [4]: 4
Aus welchen Tasks soll Queue1 bestehen: Q1
Aus welchen Tasks soll Queue2 bestehen: Q2
Aus welchen Tasks soll Queue3 bestehen: Q3
Aus welchen Tasks soll Queue4 bestehen: Q4
```

Alle Preset-Queues enthalten den wiederholbaren Wrapper:

```text
Speedup Help
Nova Daily > Praise
Nova Research
Noah Tavern
Radio Quiz
Collect Base Resources: Serum/Food/Wood/Steel/Gas + Antiserum-Limit bestätigen
Alliance > Research
Alliance > Gifts
```

Regeln:

```text
Shield = Buff > Shield > 2hr + shield_on_everyday + Gathering Search Menu
Gather Speedup = Buff > Gather Speedup + Gathering Search Menu + Alliance Gathering
Collect Quest Rewards = nur in der letzten Queue
Zombies max = 40
```


## v0.0.9 Task-Presets

Vollständige Presets liegen hier:

```text
docs\TASK_PRESETS.md
docs\wulfpack_queue_presets_v0_0_9.json
01_queue_generator\docs\TASK_PRESETS.md
01_queue_generator\config_wulfpack_queue_presets_v0_0_9.json
```

Direkteingabe im Generator:

```text
4 Queues: Q1 Q2 Q3 Q4
5 Queues: Q1 Q2 Q3 Q4 Q5
6 Queues: Q1 Q2 Q3 Q4 Q5 Q6
```
