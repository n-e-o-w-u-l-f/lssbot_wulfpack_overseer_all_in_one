#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 Andreas Tobias Sebastian Bolder
SPDX-License-Identifier: MIT

LSS Character Queue v5.0 FINAL hotfix27 — multilingual sidecar generator.

Run on Windows through:
  START.cmd
  00_CHECKING.cmd
  00_INSTALLING.cmd

Also supported:
  --lang german,french,espanol,polski,russian
  This opens a language selection menu containing only those languages.

The script scans LSS-Bot folders and ADB devices, asks how many emulators,
characters and queues should be configured, separates overlapping LSS-Bot tasks
into logical queue tasks, then writes a JSON sidecar config and readable plan.
It does not blindly patch proprietary LSS-Bot configs.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import shutil
import subprocess
import unicodedata
import sys
import signal
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

VERSION = "5.0-final-wulfpack29"
CONFIG_BASENAME = "lss_character_queue_v5_final.generated.json"
PLAN_BASENAME = "lss_character_queue_v5_final.plan.txt"
TEXT_EXTENSIONS = {
    ".json", ".jsonl", ".ini", ".cfg", ".conf", ".txt", ".log", ".xml",
    ".yaml", ".yml", ".properties", ".toml"
}
MAX_FILE_BYTES = 2_000_000

SUPPORTED_LANGS = ["english", "german", "french", "espanol", "polski", "russian"]
LANG_ALIASES = {
    "en": "english", "eng": "english", "english": "english",
    "de": "german", "deutsch": "german", "german": "german",
    "fr": "french", "francais": "french", "français": "french", "french": "french",
    "es": "espanol", "spanish": "espanol", "espanol": "espanol", "español": "espanol",
    "pl": "polski", "polish": "polski", "polski": "polski",
    "ru": "russian", "rus": "russian", "russian": "russian", "русский": "russian",
}

I18N: Dict[str, Dict[str, str]] = {
    "english": {
        "title": "LSS Character Queue v5.0 FINAL",
        "scan_roots": "Scan roots",
        "emulator_scan": "Emulator scan",
        "detected_emulators": "LSS-Bot connected emulators",
        "detected_emulators_raw": "Raw emulator hints suppressed",
        "emu_menu": "Choose emulator: 1 = Emulator 1, 2 = Emulator 2, both = both",
        "connected": "connected to LSS-Bot",
        "no_emulators": "No emulators detected automatically.",
        "how_many_emulators": "For how many emulators should the queue be installed",
        "which_emulators": "Which emulators should be used",
        "manual_emulators": "How many emulators should be created manually",
        "emulator_name": "Name for emulator",
        "adb_serial": "ADB serial for emulator, empty if unknown",
        "characters_header": "Characters per emulator",
        "how_many_chars": "How many characters on",
        "char_name": "Name for character",
        "mode_header": "Queue mode",
        "mode1": "1. Emulator-local: all queues are completed per emulator before the next emulator.",
        "mode2": "2. Parallel by queue: Queue1 runs across all selected emulators/characters first.",
        "choose_mode": "Choose mode",
        "tasks_header": "Tasks and queues",
        "queues_count": "How many queues should be created",
        "queue_tasks": "Which tasks should Queue{n} contain",
        "select_hint": "e.g. 1+2+3, 1 2 3, 1-4, all",
        "invalid_number": "Please enter a number.",
        "minimum": "Minimum is",
        "maximum": "Maximum is",
        "invalid_select": "Invalid selection",
        "empty_select": "No selection detected.",
        "done": "Done",
        "json_written": "JSON written",
        "plan_written": "Plan written",
        "next_step": "Next step",
        "next_step_text": "Connect the generated JSON to your sidecar/queue-runner. Patch real LSS-Bot files only after confirmed mapping and backup.",
        "found": "found",
        "canonical": "canonical/default",
        "source": "Source",
        "language_menu": "Choose language",
    },
    "german": {
        "title": "LSS Character Queue v5.0 FINAL",
        "scan_roots": "Scan-Wurzeln",
        "emulator_scan": "Emulator-Scan",
        "detected_emulators": "Mit LSS-Bot verbundene Emulatoren",
        "detected_emulators_raw": "Unterdrückte Roh-Emulator-Hinweise",
        "emu_menu": "Emulator wählen: 1 = Emulator 1, 2 = Emulator 2, beide = beide",
        "connected": "mit LSS-Bot verbunden",
        "no_emulators": "Keine Emulatoren automatisch gefunden.",
        "how_many_emulators": "Für wieviele Emulatoren soll die Queue installiert werden",
        "which_emulators": "Welche Emulatoren sollen verwendet werden",
        "manual_emulators": "Wieviele Emulatoren manuell anlegen",
        "emulator_name": "Name für Emulator",
        "adb_serial": "ADB-Serial für Emulator, leer falls unbekannt",
        "characters_header": "Charaktere pro Emulator",
        "how_many_chars": "Wieviele Charaktere auf",
        "char_name": "Name für Charakter",
        "mode_header": "Queue-Modus",
        "mode1": "1. Emulator-lokal: alle Queues pro Emulator abarbeiten, dann nächster Emulator.",
        "mode2": "2. Parallel nach Queue: Queue1 zuerst über alle gewählten Emulatoren/Charaktere.",
        "choose_mode": "Modus wählen",
        "tasks_header": "Tasks und Queues",
        "queues_count": "Wieviele Queues erstellen",
        "queue_tasks": "Aus welchen Tasks soll Queue{n} bestehen",
        "select_hint": "z.B. 1+2+3, 1 2 3, 1-4, alle",
        "invalid_number": "Bitte eine Zahl eingeben.",
        "minimum": "Minimum ist",
        "maximum": "Maximum ist",
        "invalid_select": "Ungültige Auswahl",
        "empty_select": "Keine Auswahl erkannt.",
        "done": "Fertig",
        "json_written": "JSON geschrieben",
        "plan_written": "Plan geschrieben",
        "next_step": "Nächster Schritt",
        "next_step_text": "Die JSON in deinen Sidecar/Queue-Runner einbinden. Echte LSS-Bot-Dateien erst nach bestätigtem Mapping und Backup patchen.",
        "found": "gefunden",
        "canonical": "kanonisch/default",
        "source": "Quelle",
        "language_menu": "Sprache wählen",
    },
    "french": {
        "title": "LSS Character Queue v5.0 FINAL",
        "scan_roots": "Racines d’analyse",
        "emulator_scan": "Analyse des émulateurs",
        "detected_emulators": "Émulateurs connectés à LSS-Bot",
        "detected_emulators_raw": "Indices bruts d’émulateurs masqués",
        "emu_menu": "Choisir l’émulateur : 1 = Émulateur 1, 2 = Émulateur 2, both = les deux",
        "connected": "connecté à LSS-Bot",
        "no_emulators": "Aucun émulateur détecté automatiquement.",
        "how_many_emulators": "Pour combien d’émulateurs installer la queue",
        "which_emulators": "Quels émulateurs utiliser",
        "manual_emulators": "Combien d’émulateurs créer manuellement",
        "emulator_name": "Nom de l’émulateur",
        "adb_serial": "Serial ADB de l’émulateur, vide si inconnu",
        "characters_header": "Personnages par émulateur",
        "how_many_chars": "Combien de personnages sur",
        "char_name": "Nom du personnage",
        "mode_header": "Mode de queue",
        "mode1": "1. Local par émulateur : toutes les queues par émulateur, puis le suivant.",
        "mode2": "2. Par queue en parallèle : Queue1 passe d’abord sur tous les émulateurs/personnages.",
        "choose_mode": "Choisir le mode",
        "tasks_header": "Tâches et queues",
        "queues_count": "Combien de queues créer",
        "queue_tasks": "Quelles tâches pour Queue{n}",
        "select_hint": "ex. 1+2+3, 1 2 3, 1-4, all",
        "invalid_number": "Veuillez saisir un nombre.",
        "minimum": "Le minimum est",
        "maximum": "Le maximum est",
        "invalid_select": "Sélection invalide",
        "empty_select": "Aucune sélection détectée.",
        "done": "Terminé",
        "json_written": "JSON écrit",
        "plan_written": "Plan écrit",
        "next_step": "Étape suivante",
        "next_step_text": "Connecter le JSON au sidecar/queue-runner. Modifier les fichiers LSS-Bot seulement après mapping confirmé et sauvegarde.",
        "found": "trouvé",
        "canonical": "canonique/défaut",
        "source": "Source",
        "language_menu": "Choisir la langue",
    },
    "espanol": {
        "title": "LSS Character Queue v5.0 FINAL",
        "scan_roots": "Rutas de escaneo",
        "emulator_scan": "Escaneo de emuladores",
        "detected_emulators": "Emuladores conectados a LSS-Bot",
        "detected_emulators_raw": "Indicadores brutos de emulador ocultos",
        "emu_menu": "Elegir emulador: 1 = Emulador 1, 2 = Emulador 2, both = ambos",
        "connected": "conectado a LSS-Bot",
        "no_emulators": "No se detectaron emuladores automáticamente.",
        "how_many_emulators": "Para cuántos emuladores se instalará la cola",
        "which_emulators": "Qué emuladores se usarán",
        "manual_emulators": "Cuántos emuladores crear manualmente",
        "emulator_name": "Nombre del emulador",
        "adb_serial": "Serial ADB del emulador, vacío si se desconoce",
        "characters_header": "Personajes por emulador",
        "how_many_chars": "Cuántos personajes en",
        "char_name": "Nombre del personaje",
        "mode_header": "Modo de cola",
        "mode1": "1. Local por emulador: todas las colas por emulador, luego el siguiente.",
        "mode2": "2. Paralelo por cola: Queue1 primero en todos los emuladores/personajes.",
        "choose_mode": "Elegir modo",
        "tasks_header": "Tareas y colas",
        "queues_count": "Cuántas colas crear",
        "queue_tasks": "Qué tareas debe contener Queue{n}",
        "select_hint": "ej. 1+2+3, 1 2 3, 1-4, all",
        "invalid_number": "Introduce un número.",
        "minimum": "El mínimo es",
        "maximum": "El máximo es",
        "invalid_select": "Selección inválida",
        "empty_select": "No se detectó selección.",
        "done": "Listo",
        "json_written": "JSON escrito",
        "plan_written": "Plan escrito",
        "next_step": "Siguiente paso",
        "next_step_text": "Conecta el JSON al sidecar/queue-runner. Modifica archivos reales de LSS-Bot solo después de confirmar el mapping y crear backup.",
        "found": "encontrado",
        "canonical": "canónico/default",
        "source": "Fuente",
        "language_menu": "Elegir idioma",
    },
    "polski": {
        "title": "LSS Character Queue v5.0 FINAL",
        "scan_roots": "Ścieżki skanowania",
        "emulator_scan": "Skan emulatorów",
        "detected_emulators": "Emulatory połączone z LSS-Bot",
        "detected_emulators_raw": "Ukryte surowe wskazania emulatorów",
        "emu_menu": "Wybierz emulator: 1 = Emulator 1, 2 = Emulator 2, both = oba",
        "connected": "połączony z LSS-Bot",
        "no_emulators": "Nie wykryto emulatorów automatycznie.",
        "how_many_emulators": "Dla ilu emulatorów zainstalować kolejkę",
        "which_emulators": "Które emulatory mają być użyte",
        "manual_emulators": "Ile emulatorów dodać ręcznie",
        "emulator_name": "Nazwa emulatora",
        "adb_serial": "Serial ADB emulatora, puste jeśli nieznany",
        "characters_header": "Postacie na emulator",
        "how_many_chars": "Ile postaci na",
        "char_name": "Nazwa postaci",
        "mode_header": "Tryb kolejki",
        "mode1": "1. Lokalnie per emulator: wszystkie kolejki na emulatorze, potem następny.",
        "mode2": "2. Równolegle per kolejka: Queue1 najpierw na wszystkich emulatorach/postaciach.",
        "choose_mode": "Wybierz tryb",
        "tasks_header": "Zadania i kolejki",
        "queues_count": "Ile kolejek utworzyć",
        "queue_tasks": "Jakie zadania ma zawierać Queue{n}",
        "select_hint": "np. 1+2+3, 1 2 3, 1-4, all",
        "invalid_number": "Wpisz liczbę.",
        "minimum": "Minimum to",
        "maximum": "Maksimum to",
        "invalid_select": "Nieprawidłowy wybór",
        "empty_select": "Nie wykryto wyboru.",
        "done": "Gotowe",
        "json_written": "Zapisano JSON",
        "plan_written": "Zapisano plan",
        "next_step": "Następny krok",
        "next_step_text": "Podłącz JSON do sidecara/queue-runnera. Prawdziwe pliki LSS-Bot modyfikuj dopiero po potwierdzonym mapowaniu i kopii zapasowej.",
        "found": "znaleziono",
        "canonical": "kanoniczne/default",
        "source": "Źródło",
        "language_menu": "Wybierz język",
    },
    "russian": {
        "title": "LSS Character Queue v5.0 FINAL",
        "scan_roots": "Пути сканирования",
        "emulator_scan": "Сканирование эмуляторов",
        "detected_emulators": "Эмуляторы, подключённые к LSS-Bot",
        "detected_emulators_raw": "Скрытые сырые подсказки эмуляторов",
        "emu_menu": "Выбрать эмулятор: 1 = Emulator 1, 2 = Emulator 2, both = оба",
        "connected": "подключён к LSS-Bot",
        "no_emulators": "Эмуляторы автоматически не найдены.",
        "how_many_emulators": "Для скольких эмуляторов установить очередь",
        "which_emulators": "Какие эмуляторы использовать",
        "manual_emulators": "Сколько эмуляторов добавить вручную",
        "emulator_name": "Имя эмулятора",
        "adb_serial": "ADB serial эмулятора, пусто если неизвестно",
        "characters_header": "Персонажи на эмулятор",
        "how_many_chars": "Сколько персонажей на",
        "char_name": "Имя персонажа",
        "mode_header": "Режим очереди",
        "mode1": "1. Локально по эмулятору: все очереди на эмуляторе, затем следующий.",
        "mode2": "2. Параллельно по очереди: Queue1 сначала на всех эмуляторах/персонажах.",
        "choose_mode": "Выберите режим",
        "tasks_header": "Задачи и очереди",
        "queues_count": "Сколько очередей создать",
        "queue_tasks": "Какие задачи должна содержать Queue{n}",
        "select_hint": "напр. 1+2+3, 1 2 3, 1-4, all",
        "invalid_number": "Введите число.",
        "minimum": "Минимум",
        "maximum": "Максимум",
        "invalid_select": "Неверный выбор",
        "empty_select": "Выбор не найден.",
        "done": "Готово",
        "json_written": "JSON записан",
        "plan_written": "План записан",
        "next_step": "Следующий шаг",
        "next_step_text": "Подключите JSON к sidecar/queue-runner. Реальные файлы LSS-Bot изменять только после подтвержденного mapping и backup.",
        "found": "найдено",
        "canonical": "канонично/default",
        "source": "Источник",
        "language_menu": "Выберите язык",
    },
}

@dataclass
class Emulator:
    id: str
    label: str
    adb_serial: Optional[str] = None
    source: str = "manual"
    raw: Optional[str] = None
    lssbot_name: Optional[str] = None
    lssbot_id: Optional[str] = None
    resolved_from: Optional[str] = None

@dataclass
class Character:
    id: str
    label: str
    emulator_id: str

@dataclass
class TaskDefinition:
    id: str
    label: str
    group: str
    aliases: List[str]
    settings: Dict[str, Any]
    scan_hits: List[str]

@dataclass
class QueueDefinition:
    id: str
    label: str
    tasks: List[str]

@dataclass
class Assignment:
    order: int
    emulator_id: str
    character_id: str
    queue_id: str
    scheduling_mode: str


# ---------------------------------------------------------------------------
# ANSI / PowerShell styling
# ---------------------------------------------------------------------------
COLOR_ENABLED = True

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_WHITE_BOLD = "[1;97m"
ANSI_GRAY = "[38;2;188;188;188m"
ANSI_DARK_GRAY = "\033[38;2;95;95;95m"
ANSI_BOLD_GRAY = "[1;38;2;198;198;198m"
ANSI_BLUE = "[38;2;88;166;255m"
ANSI_GREEN = "[38;2;90;255;165m"
ANSI_MINT = "[38;2;64;224;208m"
ANSI_TURQUOISE = "[38;2;64;224;208m"
ANSI_HEADER_GREEN = "[38;2;64;224;208m"


def enable_windows_ansi() -> None:
    """Enable ANSI colors in modern Windows PowerShell/cmd where possible."""
    if os.name != "nt":
        return
    try:
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        try:
            os.system("")
        except Exception:
            pass


def ansi(code: str) -> str:
    return code if COLOR_ENABLED else ""


def style(text: str, code: str) -> str:
    return f"{ansi(code)}{text}{ansi(ANSI_RESET)}" if COLOR_ENABLED else text


def gray(text: str) -> str:
    return style(text, ANSI_GRAY)

def dark_gray(text: str) -> str:
    return style(text, ANSI_DARK_GRAY)



def bold_gray(text: str) -> str:
    return style(text, ANSI_BOLD_GRAY)


def progress_step(message: str) -> None:
    # Dark gray status marker, normal gray text.
    print("  " + dark_gray("[..] ") + gray(localize_status_message(str(message))), flush=True)


def progress_ok(message: str) -> None:
    # Gray brackets, green OK, normal gray text.
    print("  " + dark_gray("[") + green("OK") + dark_gray("] ") + gray(localize_status_message(str(message))), flush=True)


def progress_warn(message: str) -> None:
    # Gray brackets, blue warning marker, normal gray text.
    print("  " + dark_gray("[") + blue("!!") + dark_gray("] ") + gray(localize_status_message(str(message))), flush=True)


def blue(text: str) -> str:
    return style(text, ANSI_BLUE)


def green(text: str) -> str:
    return style(text, ANSI_GREEN)


def bold_white(text: str) -> str:
    return style(text, ANSI_WHITE_BOLD)


def terminal_width(text: str) -> int:
    """Visible console width without ANSI codes; handles Polish/Russian accents safely."""
    width = 0
    for ch in text:
        if unicodedata.combining(ch):
            continue
        if unicodedata.east_asian_width(ch) in {"F", "W"}:
            width += 2
        else:
            width += 1
    return width


def color_hash_line(width: int) -> str:
    # Reduced header palette:
    # border = turquoise only; middle text remains bold white.
    return style("#" * width, ANSI_TURQUOISE)


def color_source(source: str) -> str:
    """Grey source label, blue Windows path, green connection marker."""
    if not COLOR_ENABLED:
        return source
    parts = source.split(" | ")
    first = parts[0]
    rest = parts[1:]
    m = WIN_PATH_RE.search(first)
    if m:
        rendered = gray(first[:m.start()]) + blue(first[m.start():m.end()].rstrip())
        if first[m.end():].strip():
            rendered += gray(first[m.end():])
    else:
        rendered = gray(first)
    for item in rest:
        rendered += gray(" | ") + (green(item) if "connected" in item.lower() or "połącz" in item.lower() or "verbunden" in item.lower() else gray(item))
    return rendered


def format_prompt(text: str) -> str:
    return gray(text) if COLOR_ENABLED else text

def tr(key: str, lang: str, **kwargs: Any) -> str:
    text = I18N.get(lang, I18N["english"]).get(key, I18N["english"].get(key, key))
    return text.format(**kwargs)


ACTIVE_LANG = "english"

UI_TEXT: Dict[str, Dict[str, str]] = {
    "english": {
        "selected_emulator_type": "Selected emulator type: {value}",
        "fast_scan": "Fast scan: selected vendor CLI + ADB + recent LSS-Bot logs/configs only.",
    },
    "german": {
        "selected_emulator_type": "Gewählter Emulator-Typ: {value}",
        "fast_scan": "Schnellscan: gewählte Hersteller-CLI + ADB + aktuelle LSS-Bot Logs/Configs.",
    },
    "french": {
        "selected_emulator_type": "Type d'emulateur choisi : {value}",
        "fast_scan": "Scan rapide : CLI fournisseur choisie + ADB + logs/configs LSS-Bot recents.",
    },
    "espanol": {
        "selected_emulator_type": "Tipo de emulador seleccionado: {value}",
        "fast_scan": "Escaneo rapido: CLI del proveedor seleccionada + ADB + logs/configs recientes de LSS-Bot.",
    },
    "polski": {
        "selected_emulator_type": "Wybrany typ emulatora: {value}",
        "fast_scan": "Szybkie skanowanie: wybrany CLI producenta + ADB + aktualne logi/konfiguracje LSS-Bot.",
    },
    "russian": {
        "selected_emulator_type": "Vybrannyi tip emulyatora: {value}",
        "fast_scan": "Bystraya proverka: vybrannyi CLI proizvoditelya + ADB + poslednie logi/config LSS-Bot.",
    },
}


def ui_text(key: str, lang: str, **kwargs: Any) -> str:
    table = UI_TEXT.get(lang, UI_TEXT["english"])
    template = table.get(key, UI_TEXT["english"].get(key, key))
    return template.format(**kwargs)


def set_active_lang(lang: str) -> None:
    global ACTIVE_LANG
    ACTIVE_LANG = lang if lang in UI_TEXT else "english"


def localize_status_message(message: str) -> str:
    lang = ACTIVE_LANG
    if lang == "english":
        return message

    # Translation tables keep dynamic paths/names unchanged.
    tables: Dict[str, Dict[str, str]] = {
        "german": {
            "start live scan": "Live-Scan starten",
            "phase 1/4: vendor CLI instance discovery": "Phase 1/4: Instanzsuche über Hersteller-CLI",
            "phase 2/4: ADB discovery": "Phase 2/4: ADB-Erkennung",
            "phase 3/4: LSS-Bot log/config emulator-name discovery": "Phase 3/4: Emulatornamen aus LSS-Bot Logs/Configs suchen",
            "phase 4/4: task discovery": "Phase 4/4: Task-Erkennung",
            "merge emulator results": "Emulator-Ergebnisse zusammenführen",
            "full live scan finished": "vollständiger Live-Scan abgeschlossen",
            "search ADB executable": "ADB-Programm suchen",
            "ADB executable not found": "ADB-Programm nicht gefunden",
            "ADB devices command finished": "ADB-Geräteliste abgeschlossen",
            "scan recent LSS-Bot logs/configs for emulator names": "aktuelle LSS-Bot Logs/Configs nach Emulatornamen durchsuchen",
            "compile known task signatures": "bekannte Task-Signaturen vorbereiten",
            "scan recent LSS-Bot files for known tasks": "aktuelle LSS-Bot Dateien nach bekannten Tasks durchsuchen",
            "scan LSS-Bot folders for recent logs/configs; runtime/lib is skipped": "LSS-Bot Ordner nach aktuellen Logs/Configs durchsuchen; runtime/lib wird übersprungen",
        },
        "french": {
            "start live scan": "demarrer le scan en direct",
            "phase 1/4: vendor CLI instance discovery": "phase 1/4 : detection des instances via CLI fournisseur",
            "phase 2/4: ADB discovery": "phase 2/4 : detection ADB",
            "phase 3/4: LSS-Bot log/config emulator-name discovery": "phase 3/4 : recherche des noms d'emulateurs dans logs/configs LSS-Bot",
            "phase 4/4: task discovery": "phase 4/4 : detection des tasks",
            "merge emulator results": "fusionner les resultats des emulateurs",
            "full live scan finished": "scan en direct termine",
            "search ADB executable": "rechercher l'executable ADB",
            "ADB executable not found": "executable ADB introuvable",
            "ADB devices command finished": "commande ADB devices terminee",
            "scan recent LSS-Bot logs/configs for emulator names": "scanner les logs/configs LSS-Bot recents pour les noms d'emulateurs",
            "compile known task signatures": "preparer les signatures de tasks connues",
            "scan recent LSS-Bot files for known tasks": "scanner les fichiers LSS-Bot recents pour les tasks connues",
            "scan LSS-Bot folders for recent logs/configs; runtime/lib is skipped": "scanner les dossiers LSS-Bot; runtime/lib est ignore",
        },
        "espanol": {
            "start live scan": "iniciar escaneo en vivo",
            "phase 1/4: vendor CLI instance discovery": "fase 1/4: deteccion de instancias por CLI del proveedor",
            "phase 2/4: ADB discovery": "fase 2/4: deteccion ADB",
            "phase 3/4: LSS-Bot log/config emulator-name discovery": "fase 3/4: buscar nombres de emulador en logs/configs de LSS-Bot",
            "phase 4/4: task discovery": "fase 4/4: deteccion de tasks",
            "merge emulator results": "combinar resultados de emuladores",
            "full live scan finished": "escaneo en vivo terminado",
            "search ADB executable": "buscar ejecutable ADB",
            "ADB executable not found": "ejecutable ADB no encontrado",
            "ADB devices command finished": "comando ADB devices terminado",
            "scan recent LSS-Bot logs/configs for emulator names": "escanear logs/configs recientes de LSS-Bot para nombres de emulador",
            "compile known task signatures": "preparar firmas de tasks conocidas",
            "scan recent LSS-Bot files for known tasks": "escanear archivos recientes de LSS-Bot para tasks conocidas",
            "scan LSS-Bot folders for recent logs/configs; runtime/lib is skipped": "escanear carpetas LSS-Bot; runtime/lib se omite",
        },
        "polski": {
            "start live scan": "rozpoczynam skanowanie live",
            "phase 1/4: vendor CLI instance discovery": "faza 1/4: wykrywanie instancji przez CLI producenta",
            "phase 2/4: ADB discovery": "faza 2/4: wykrywanie ADB",
            "phase 3/4: LSS-Bot log/config emulator-name discovery": "faza 3/4: szukanie nazw emulatorow w logach/configach LSS-Bot",
            "phase 4/4: task discovery": "faza 4/4: wykrywanie taskow",
            "merge emulator results": "laczenie wynikow emulatorow",
            "full live scan finished": "pelne skanowanie live zakonczone",
            "search ADB executable": "szukam programu ADB",
            "ADB executable not found": "nie znaleziono programu ADB",
            "ADB devices command finished": "komenda ADB devices zakonczona",
            "scan recent LSS-Bot logs/configs for emulator names": "skanuje aktualne logi/configi LSS-Bot pod nazwy emulatorow",
            "compile known task signatures": "przygotowuje znane sygnatury taskow",
            "scan recent LSS-Bot files for known tasks": "skanuje aktualne pliki LSS-Bot pod znane taski",
            "scan LSS-Bot folders for recent logs/configs; runtime/lib is skipped": "skanuje foldery LSS-Bot; runtime/lib pomijane",
        },
        "russian": {
            "start live scan": "nachat live-scan",
            "phase 1/4: vendor CLI instance discovery": "faza 1/4: poisk instancii cherez CLI proizvoditelya",
            "phase 2/4: ADB discovery": "faza 2/4: poisk ADB",
            "phase 3/4: LSS-Bot log/config emulator-name discovery": "faza 3/4: poisk imen emulyatorov v log/config LSS-Bot",
            "phase 4/4: task discovery": "faza 4/4: poisk taskov",
            "merge emulator results": "obedinit rezultaty emulyatorov",
            "full live scan finished": "polnyi live-scan zavershen",
            "search ADB executable": "poisk programmy ADB",
            "ADB executable not found": "programma ADB ne naidena",
            "ADB devices command finished": "komanda ADB devices zavershena",
            "scan recent LSS-Bot logs/configs for emulator names": "proverka poslednih log/config LSS-Bot na imena emulyatorov",
            "compile known task signatures": "podgotovka izvestnyh signatur taskov",
            "scan recent LSS-Bot files for known tasks": "proverka poslednih failov LSS-Bot na izvestnye taski",
            "scan LSS-Bot folders for recent logs/configs; runtime/lib is skipped": "proverka papok LSS-Bot; runtime/lib propushchen",
        },
    }

    exact = tables.get(lang, {}).get(message)
    if exact:
        return exact

    patterns: Dict[str, List[Tuple[str, str]]] = {
        "german": [
            (r"search vendor CLI for emulator type: (.+)", r"Hersteller-CLI für Emulator-Typ suchen: \1"),
            (r"vendor CLI candidates found: (\d+)", r"Hersteller-CLI Kandidaten gefunden: \1"),
            (r"probe LDPlayer instances via list2: (.+)", r"LDPlayer-Instanzen über list2 prüfen: \1"),
            (r"run command: (.+)", r"Befehl ausführen: \1"),
            (r"command finished: (.+)", r"Befehl abgeschlossen: \1"),
            (r"LDPlayer list2 found: ID (\d+) \| title=(.+) \| expected ADB=(.+)", r"LDPlayer list2 gefunden: ID \1 | Name=\2 | erwartetes ADB=\3"),
            (r"LDPlayer source accepted: (.+)", r"LDPlayer-Quelle akzeptiert: \1"),
            (r"vendor CLI scan found (\d+) unique instance\(s\)", r"Hersteller-CLI Scan fand \1 eindeutige Instanz(en)"),
            (r"run ADB devices: (.+)", r"ADB-Geräte abfragen: \1"),
            (r"ADB scan found (\d+) device\(s\)", r"ADB-Scan fand \1 Gerät(e)"),
            (r"phase 3/4 skipped: vendor CLI already returned exact emulator instance names", r"Phase 3/4 übersprungen: Hersteller-CLI lieferte bereits exakte Emulator-Instanznamen"),
            (r"emulator live scan finished: (\d+) emulator candidate\(s\)", r"Emulator-Live-Scan abgeschlossen: \1 Emulator-Kandidat(en)"),
            (r"compiled (\d+) task definitions", r"\1 Task-Definitionen vorbereitet"),
            (r"walk root: (.+)", r"Scan-Wurzel prüfen: \1"),
            (r"root checked: (.+) \((\d+) candidate files\)", r"Scan-Wurzel geprüft: \1 (\2 Kandidatendateien)"),
            (r"selected (\d+) files for fast scan", r"\1 Dateien für Schnellscan ausgewählt"),
            (r"queued file: (.+)", r"Datei vorgemerkt: \1"),
            (r"read task context: (.+)", r"Task-Kontext lesen: \1"),
            (r"read emulator context: (.+)", r"Emulator-Kontext lesen: \1"),
            (r"task scan finished: (\d+) known task group\(s\) matched", r"Task-Scan abgeschlossen: \1 bekannte Task-Gruppe(n) gefunden"),
        ],
        "french": [
            (r"search vendor CLI for emulator type: (.+)", r"rechercher CLI fournisseur pour type d'emulateur : \1"),
            (r"vendor CLI candidates found: (\d+)", r"candidats CLI fournisseur trouves : \1"),
            (r"probe LDPlayer instances via list2: (.+)", r"verifier les instances LDPlayer via list2 : \1"),
            (r"run command: (.+)", r"executer la commande : \1"),
            (r"command finished: (.+)", r"commande terminee : \1"),
            (r"LDPlayer list2 found: ID (\d+) \| title=(.+) \| expected ADB=(.+)", r"LDPlayer list2 trouve : ID \1 | nom=\2 | ADB attendu=\3"),
            (r"LDPlayer source accepted: (.+)", r"source LDPlayer acceptee : \1"),
            (r"vendor CLI scan found (\d+) unique instance\(s\)", r"scan CLI fournisseur : \1 instance(s) unique(s)"),
            (r"run ADB devices: (.+)", r"executer ADB devices : \1"),
            (r"ADB scan found (\d+) device\(s\)", r"scan ADB : \1 appareil(s)"),
            (r"phase 3/4 skipped: vendor CLI already returned exact emulator instance names", r"phase 3/4 ignoree : la CLI fournisseur a deja donne les noms exacts"),
            (r"emulator live scan finished: (\d+) emulator candidate\(s\)", r"scan emulateur termine : \1 candidat(s)"),
            (r"compiled (\d+) task definitions", r"\1 definitions de task preparees"),
            (r"walk root: (.+)", r"verifier racine : \1"),
            (r"root checked: (.+) \((\d+) candidate files\)", r"racine verifiee : \1 (\2 fichiers candidats)"),
            (r"selected (\d+) files for fast scan", r"\1 fichiers selectionnes pour scan rapide"),
            (r"queued file: (.+)", r"fichier en attente : \1"),
            (r"read task context: (.+)", r"lire contexte task : \1"),
            (r"read emulator context: (.+)", r"lire contexte emulateur : \1"),
            (r"task scan finished: (\d+) known task group\(s\) matched", r"scan tasks termine : \1 groupe(s) trouve(s)"),
        ],
        "espanol": [
            (r"search vendor CLI for emulator type: (.+)", r"buscar CLI del proveedor para tipo de emulador: \1"),
            (r"vendor CLI candidates found: (\d+)", r"candidatos CLI del proveedor encontrados: \1"),
            (r"probe LDPlayer instances via list2: (.+)", r"probar instancias LDPlayer via list2: \1"),
            (r"run command: (.+)", r"ejecutar comando: \1"),
            (r"command finished: (.+)", r"comando terminado: \1"),
            (r"LDPlayer list2 found: ID (\d+) \| title=(.+) \| expected ADB=(.+)", r"LDPlayer list2 encontrado: ID \1 | nombre=\2 | ADB esperado=\3"),
            (r"LDPlayer source accepted: (.+)", r"fuente LDPlayer aceptada: \1"),
            (r"vendor CLI scan found (\d+) unique instance\(s\)", r"escaneo CLI del proveedor encontro \1 instancia(s) unica(s)"),
            (r"run ADB devices: (.+)", r"ejecutar ADB devices: \1"),
            (r"ADB scan found (\d+) device\(s\)", r"escaneo ADB encontro \1 dispositivo(s)"),
            (r"phase 3/4 skipped: vendor CLI already returned exact emulator instance names", r"fase 3/4 omitida: la CLI ya devolvio nombres exactos"),
            (r"emulator live scan finished: (\d+) emulator candidate\(s\)", r"escaneo live de emuladores terminado: \1 candidato(s)"),
            (r"compiled (\d+) task definitions", r"\1 definiciones de task preparadas"),
            (r"walk root: (.+)", r"revisar raiz: \1"),
            (r"root checked: (.+) \((\d+) candidate files\)", r"raiz revisada: \1 (\2 archivos candidatos)"),
            (r"selected (\d+) files for fast scan", r"\1 archivos seleccionados para escaneo rapido"),
            (r"queued file: (.+)", r"archivo en cola: \1"),
            (r"read task context: (.+)", r"leer contexto de task: \1"),
            (r"read emulator context: (.+)", r"leer contexto de emulador: \1"),
            (r"task scan finished: (\d+) known task group\(s\) matched", r"escaneo de tasks terminado: \1 grupo(s) encontrado(s)"),
        ],
        "polski": [
            (r"search vendor CLI for emulator type: (.+)", r"szukam CLI producenta dla emulatora: \1"),
            (r"vendor CLI candidates found: (\d+)", r"znaleziono kandydatow CLI producenta: \1"),
            (r"probe LDPlayer instances via list2: (.+)", r"sprawdzam instancje LDPlayer przez list2: \1"),
            (r"run command: (.+)", r"uruchamiam komende: \1"),
            (r"command finished: (.+)", r"komenda zakonczona: \1"),
            (r"LDPlayer list2 found: ID (\d+) \| title=(.+) \| expected ADB=(.+)", r"LDPlayer list2 znaleziono: ID \1 | nazwa=\2 | oczekiwane ADB=\3"),
            (r"LDPlayer source accepted: (.+)", r"zaakceptowano zrodlo LDPlayer: \1"),
            (r"vendor CLI scan found (\d+) unique instance\(s\)", r"skan CLI producenta znalazl \1 unikalne instancje"),
            (r"run ADB devices: (.+)", r"uruchamiam ADB devices: \1"),
            (r"ADB scan found (\d+) device\(s\)", r"skan ADB znalazl \1 urzadzen"),
            (r"phase 3/4 skipped: vendor CLI already returned exact emulator instance names", r"faza 3/4 pominieta: CLI producenta juz zwrocilo dokladne nazwy instancji"),
            (r"emulator live scan finished: (\d+) emulator candidate\(s\)", r"skan emulatorow zakonczony: \1 kandydatow"),
            (r"compiled (\d+) task definitions", r"przygotowano \1 definicji taskow"),
            (r"walk root: (.+)", r"sprawdzam katalog glowny: \1"),
            (r"root checked: (.+) \((\d+) candidate files\)", r"katalog sprawdzony: \1 (\2 plikow kandydatow)"),
            (r"selected (\d+) files for fast scan", r"wybrano \1 plikow do szybkiego skanu"),
            (r"queued file: (.+)", r"plik w kolejce: \1"),
            (r"read task context: (.+)", r"czytam kontekst taska: \1"),
            (r"read emulator context: (.+)", r"czytam kontekst emulatora: \1"),
            (r"task scan finished: (\d+) known task group\(s\) matched", r"skan taskow zakonczony: znaleziono \1 grup"),
        ],
        "russian": [
            (r"search vendor CLI for emulator type: (.+)", r"poisk CLI proizvoditelya dlya tipa emulyatora: \1"),
            (r"vendor CLI candidates found: (\d+)", r"naideno kandidatov CLI proizvoditelya: \1"),
            (r"probe LDPlayer instances via list2: (.+)", r"proverka instancii LDPlayer cherez list2: \1"),
            (r"run command: (.+)", r"zapusk komandy: \1"),
            (r"command finished: (.+)", r"komanda zavershena: \1"),
            (r"LDPlayer list2 found: ID (\d+) \| title=(.+) \| expected ADB=(.+)", r"LDPlayer list2 naideno: ID \1 | imya=\2 | ozhidaemyi ADB=\3"),
            (r"LDPlayer source accepted: (.+)", r"istochnik LDPlayer prinyat: \1"),
            (r"vendor CLI scan found (\d+) unique instance\(s\)", r"scan CLI proizvoditelya nashel \1 unikalnyh instancii"),
            (r"run ADB devices: (.+)", r"zapusk ADB devices: \1"),
            (r"ADB scan found (\d+) device\(s\)", r"ADB scan nashel \1 ustroistv"),
            (r"phase 3/4 skipped: vendor CLI already returned exact emulator instance names", r"faza 3/4 propushchena: CLI uzhe vernul tochniye imena instancii"),
            (r"emulator live scan finished: (\d+) emulator candidate\(s\)", r"live-scan emulyatorov zavershen: \1 kandidatov"),
            (r"compiled (\d+) task definitions", r"podgotovleno \1 opredelenii taskov"),
            (r"walk root: (.+)", r"proverka kornevogo puti: \1"),
            (r"root checked: (.+) \((\d+) candidate files\)", r"kornevoi put proverен: \1 (\2 failov-kandidatov)"),
            (r"selected (\d+) files for fast scan", r"vybrano \1 failov dlya bystrogo skana"),
            (r"queued file: (.+)", r"fail v ocheredi: \1"),
            (r"read task context: (.+)", r"chtenie konteksta taska: \1"),
            (r"read emulator context: (.+)", r"chtenie konteksta emulyatora: \1"),
            (r"task scan finished: (\d+) known task group\(s\) matched", r"scan taskov zavershen: naideno \1 grupp"),
        ],
    }

    for pattern, repl in patterns.get(lang, []):
        if re.fullmatch(pattern, message):
            return re.sub(pattern, repl, message)

    return message


CANCEL_PROMPTS = {
    "english": {
        "ask": "Abort script run? [Y/N]: ",
        "abort": "Script run aborted by user.",
        "continue": "Continuing script run.",
    },
    "german": {
        "ask": "Scriptlauf abbrechen? [J/N]: ",
        "abort": "Scriptlauf durch Benutzer abgebrochen.",
        "continue": "Scriptlauf wird fortgesetzt.",
    },
    "french": {
        "ask": "Annuler l'execution du script ? [O/N] : ",
        "abort": "Execution annulee par l'utilisateur.",
        "continue": "Execution du script poursuivie.",
    },
    "espanol": {
        "ask": "Cancelar la ejecucion del script? [S/N]: ",
        "abort": "Ejecucion cancelada por el usuario.",
        "continue": "La ejecucion continua.",
    },
    "polski": {
        "ask": "Przerwac dzialanie skryptu? [T/N]: ",
        "abort": "Dzialanie skryptu przerwane przez uzytkownika.",
        "continue": "Kontynuuje dzialanie skryptu.",
    },
    "russian": {
        "ask": "Prervat vypolnenie skripta? [D/N]: ",
        "abort": "Vypolnenie skripta prervano polzovatelem.",
        "continue": "Vypolnenie skripta prodolzhaetsya.",
    },
}

CANCEL_YES = {
    "english": {"y", "yes"},
    "german": {"j", "ja", "y", "yes"},
    "french": {"o", "oui", "y", "yes"},
    "espanol": {"s", "si", "sí", "y", "yes"},
    "polski": {"t", "tak", "y", "yes"},
    "russian": {"d", "da", "y", "yes"},
}

CANCEL_NO = {
    "english": {"n", "no"},
    "german": {"n", "nein", "no"},
    "french": {"n", "non", "no"},
    "espanol": {"n", "no"},
    "polski": {"n", "nie", "no"},
    "russian": {"n", "net", "no"},
}


def install_cancel_handler(lang: str) -> None:
    """
    Localized Ctrl+C handling for the Python part of the tool.

    The native Windows cmd.exe text "Batchvorgang abbrechen (J/N)?"
    belongs to cmd.exe and cannot be translated from a batch file.
    This handler gives the Python process its own localized prompt.
    """
    active_lang = lang if lang in CANCEL_PROMPTS else "english"

    def _handle_sigint(signum: int, frame: Any) -> None:
        prompt = CANCEL_PROMPTS[active_lang]
        try:
            print()
            answer = input(prompt["ask"]).strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = next(iter(CANCEL_YES[active_lang]))

        if answer in CANCEL_YES[active_lang]:
            print(prompt["abort"])
            raise SystemExit(130)

        print(prompt["continue"])

    try:
        signal.signal(signal.SIGINT, _handle_sigint)
    except Exception:
        pass


def normalize_lang(value: str) -> str:
    key = value.strip().lower()
    if key in LANG_ALIASES:
        return LANG_ALIASES[key]
    return key


def resolve_language(raw: Optional[str]) -> str:
    if not raw:
        return "german"
    parts = [normalize_lang(p) for p in re.split(r"[,;\s]+", raw) if p.strip()]
    parts = [p for p in parts if p in SUPPORTED_LANGS]
    if not parts:
        return "german"
    if len(parts) == 1:
        return parts[0]
    header(I18N["german"]["language_menu"] + " / " + I18N["english"]["language_menu"])
    for idx, lang in enumerate(parts, 1):
        print(f"{idx}. {lang}")
    while True:
        raw_choice = input("> ").strip()
        try:
            n = int(raw_choice)
            if 1 <= n <= len(parts):
                return parts[n - 1]
        except ValueError:
            pass
        print("1-" + str(len(parts)))


def resource_flags(value: bool = True) -> Dict[str, bool]:
    return {"food": value, "wood": value, "steel": value, "gas": value, "all_resources": value}


def official_task_settings(script_name: str, category: str, mapping_status: str = "official_generic") -> Dict[str, Any]:
    return {
        "script_name": script_name,
        "category": category,
        "mapping_status": mapping_status,
        "source": "official_lssbot_puzzles_and_survival_feature_list",
        "split_rule_confirmed": mapping_status == "split_confirmed",
    }


def build_tasks() -> List[TaskDefinition]:
    base = [
        # -------------------------------------------------------------------
        # Confirmed split tasks from the user workflow.
        # -------------------------------------------------------------------
        TaskDefinition("alliance_research", "Alliance Research", "Alliance", [
            "Alliance Research", "Donate To Alliance Technology", "Donate to Alliance Technology",
            "Check Hot Technology First", "Alliance Technology"
        ], {
            "script_name": "Alliance Activities",
            "mapping_status": "split_confirmed",
            "alliance_tab": "Research",
            "donate_to_alliance_technology": True,
            "check_hot_technology_first": True,
            "technology_categories": {"economy": True, "military": True, "skill": True},
            "collect_alliance_gifts": False,
            "gather_alliance_territory": False,
        }, []),
        TaskDefinition("alliance_gifts", "Alliance Gifts", "Alliance", [
            "Alliance Gifts", "Collect Alliance Gifts", "Collect alliance gifts"
        ], {
            "script_name": "Alliance Activities",
            "mapping_status": "split_confirmed",
            "alliance_tab": "Gifts",
            "collect_alliance_gifts": True,
            "donate_to_alliance_technology": False,
            "gather_alliance_territory": False,
        }, []),
        TaskDefinition("alliance_gathering", "Alliance Gathering", "Alliance", [
            "Alliance Gathering", "Territory Gathering", "Gather Alliance Territory",
            "Gather alliance territory", "Gather Territory"
        ], {
            "script_name": "Alliance Activities",
            "mapping_status": "split_confirmed",
            "alliance_tab": "Territory Gathering",
            "gather_alliance_territory": True,
            "collect_alliance_gifts": False,
            "donate_to_alliance_technology": False,
            "resource_selection": resource_flags(True),
        }, []),

        TaskDefinition("pit_gather", "Pit Gather", "Pit", [
            "Pit Gather", "Pit Gathering", "Gather in Pit", "Resource Pit"
        ], {
            "script_name": "Pit",
            "mapping_status": "split_confirmed",
            "pit_mode": "Gather",
            "resource_selection": resource_flags(True),
            "attack_in_pit": False,
        }, []),
        TaskDefinition("pit_attack", "Pit Attack", "Pit", [
            "Pit Attack", "Attack in Pit", "Resource Pit"
        ], {
            "script_name": "Pit",
            "mapping_status": "split_confirmed",
            "pit_mode": "Attack",
            "attack_in_pit": True,
            "gather_in_pit": False,
        }, []),

        TaskDefinition("campaign_puzzle_auto", "Campaign Puzzle Auto", "Campaign Puzzle", [
            "Campaign Puzzle Auto", "Auto Mode", "Campaign Puzzles", "Puzzle Auto"
        ], {
            "script_name": "Campaign Puzzles",
            "mapping_status": "split_confirmed",
            "campaign_puzzle_section": "Auto",
            "auto_mode": True,
            "general_look_for_best_move": False,
        }, []),
        TaskDefinition("campaign_puzzle_general", "Campaign Puzzle General", "Campaign Puzzle", [
            "Campaign Puzzle General", "Look for best move", "Look For Best Move", "Puzzle General"
        ], {
            "script_name": "Campaign Puzzles",
            "mapping_status": "split_confirmed",
            "campaign_puzzle_section": "General",
            "auto_mode": False,
            "general": {"look_for_best_move": True},
        }, []),

        # -------------------------------------------------------------------
        # Full official Puzzles & Survival feature catalog from LSS-Bot page.
        # These are mapped as official_generic until a per-field UI split is
        # confirmed from local script config/JAR metadata.
        # -------------------------------------------------------------------
        TaskDefinition("dynamic_base_puzzles", "Dynamic Base Puzzles", "Campaign Puzzle", [
            "Dynamic Base Puzzles", "Dynamic Base Puzzle", "Base Puzzles"
        ], official_task_settings("Dynamic Base Puzzles", "Campaign Puzzle"), []),
        TaskDefinition("duel_survival", "Duel Survival", "Campaign Puzzle", [
            "Duel Survival", "Duel"
        ], official_task_settings("Duel Survival", "Campaign Puzzle"), []),

        TaskDefinition("resource_gathering", "Resource Gathering", "Resources", [
            "Resource Gathering", "Gather Resources", "Gathering Resources"
        ], {**official_task_settings("Resource Gathering", "Resources"), "resource_selection": resource_flags(True)}, []),
        TaskDefinition("gathering_boost", "Gathering Boost", "Resources", [
            "Gathering Boost", "Gathering Boosts", "Gather Boost"
        ], official_task_settings("Gathering Boost", "Resources"), []),
        TaskDefinition("supply_depot", "Supply Depot", "Resources", [
            "Supply Depot", "Depot"
        ], official_task_settings("Supply Depot", "Resources"), []),

        TaskDefinition("building_upgrading", "Building Upgrading", "Base", [
            "Building Upgrading", "Building Upgrade", "Upgrade Buildings"
        ], official_task_settings("Building Upgrading", "Base"), []),
        TaskDefinition("hq_upgrading", "HQ Upgrading", "Base", [
            "HQ Upgrading", "HQ Upgrade", "Headquarters Upgrading", "Headquarters Upgrade"
        ], official_task_settings("HQ Upgrading", "Base"), []),
        TaskDefinition("research", "Research", "Base", [
            "Research", "Research Center", "Base Research"
        ], official_task_settings("Research", "Base"), []),
        TaskDefinition("wall_repair", "Wall Repair", "Base", [
            "Wall Repair", "Repair Wall"
        ], official_task_settings("Wall Repair", "Base"), []),
        TaskDefinition("trap_crafting", "Trap Crafting", "Base", [
            "Trap Crafting", "Craft Traps", "Trap Factory"
        ], official_task_settings("Trap Crafting", "Base"), []),
        TaskDefinition("shield", "Shield", "Base", [
            "Shield", "Use Shield", "Apply Shield"
        ], official_task_settings("Shield", "Base"), []),

        TaskDefinition("troop_training", "Troop Training", "Military", [
            "Troop Training", "Train Troops", "Training Troops"
        ], official_task_settings("Troop Training", "Military"), []),
        TaskDefinition("troop_healing", "Troop Healing", "Military", [
            "Troop Healing", "Heal Troops", "Healing Troops", "Wounded"
        ], official_task_settings("Troop Healing", "Military"), []),
        TaskDefinition("tavern_recruitment", "Tavern Recruitment", "Military", [
            "Tavern Recruitment", "Recruitment", "Recruit Heroes", "Tavern"
        ], official_task_settings("Tavern Recruitment", "Military"), []),
        TaskDefinition("skills", "Skills", "Military", [
            "Skills", "Commander Skills", "Use Skills"
        ], official_task_settings("Skills", "Military"), []),

        TaskDefinition("quest_rewards", "Quest Rewards", "Rewards", [
            "Quest Rewards", "Quest Reward", "Collect Quest Rewards"
        ], official_task_settings("Quest Rewards", "Rewards"), []),
        TaskDefinition("game_gifts", "Game Gifts", "Rewards", [
            "Game Gifts", "Collect Game Gifts", "Gifts"
        ], official_task_settings("Game Gifts", "Rewards"), []),
        TaskDefinition("bag_items", "Bag Items", "Inventory", [
            "Bag Items", "Use Bag Items", "Bag"
        ], official_task_settings("Bag Items", "Inventory"), []),
        TaskDefinition("bank_investment", "Bank Investment", "Economy", [
            "Bank Investment", "Bank Invest", "Bank"
        ], official_task_settings("Bank Investment", "Economy"), []),
        TaskDefinition("radio_quiz", "Radio Quiz", "Rewards", [
            "Radio Quiz", "Quiz"
        ], official_task_settings("Radio Quiz", "Rewards"), []),
        TaskDefinition("ruins", "Ruins", "Rewards", [
            "Ruins", "Ruin"
        ], official_task_settings("Ruins", "Rewards"), []),

        # Official page lists Alliance Activities as one supported feature.
        # The user workflow splits it into the three confirmed tasks above.
        TaskDefinition("alliance_activities_generic", "Alliance Activities Generic", "Alliance", [
            "Alliance Activities", "Alliance Activity"
        ], {
            "script_name": "Alliance Activities",
            "mapping_status": "official_generic_parent",
            "split_into": ["alliance_research", "alliance_gifts", "alliance_gathering"],
            "use_split_tasks_instead": True,
            "source": "official_lssbot_puzzles_and_survival_feature_list",
        }, []),
    ]

    # Zombies 20-40 through 39-40, plus 40 alone. Game max level is 40.
    zombies: List[TaskDefinition] = []
    for start in range(20, 40):
        end = 40
        label = f"Zombies {start}-{end}"
        zombies.append(TaskDefinition(
            f"zombies_{start}_{end}", label, "Zombies",
            ["Zombies v1.0 by LSS-Bot", label],
            {
                "script_name": "Zombies v1.0 by LSS-Bot",
                "mapping_status": "split_confirmed",
                "selected_levels": list(range(start, end + 1)),
                "level_min": start,
                "level_max": end,
                "only_selected_levels": True,
            }, []))
    zombies.append(TaskDefinition(
        "zombies_40", "Zombies 40", "Zombies",
        ["Zombies v1.0 by LSS-Bot", "Zombies 40"],
        {
            "script_name": "Zombies v1.0 by LSS-Bot",
            "mapping_status": "split_confirmed",
            "selected_levels": [40],
            "level_min": 40,
            "level_max": 40,
            "only_selected_levels": True,
        }, []))



def make_task(task_id: str, label: str, group: str, script_name: str, aliases: List[str],
              subtasks: List[str], options: Dict[str, Any],
              mapping_status: str = "official_generic",
              repeatable: bool = True) -> TaskDefinition:
    settings = {
        "script_name": script_name,
        "mapping_status": mapping_status,
        "repeatable_wrapper": repeatable,
        "expanded_subtasks": subtasks,
        "options": options,
        "source": "wulfpack_user_resolved_task_catalog",
    }
    return TaskDefinition(task_id, label, group, aliases, settings, [])


def enrich_task_catalog(tasks: List[TaskDefinition]) -> List[TaskDefinition]:
    by_id = {t.id: t for t in tasks}

    details: Dict[str, Dict[str, Any]] = {
        "alliance_research": {
            "label": "Alliance > Research",
            "subtasks": [
                "Open Alliance menu",
                "Open Alliance Technology / Research",
                "Select recommended/hot technology first when visible",
                "Donate available resources/items",
                "Stop when donation limit is reached",
            ],
            "options": {
                "hot_technology_first": True,
                "donate_until_limit": True,
                "fallback_to_available_technology": True,
            },
        },
        "alliance_gifts": {
            "label": "Alliance > Gifts",
            "subtasks": [
                "Open Alliance menu",
                "Open Gifts",
                "Claim normal alliance gifts",
                "Claim rare/special alliance gifts when available",
                "Close all claim popups",
            ],
            "options": {
                "claim_all_visible": True,
                "claim_rare_gifts": True,
                "safe_close_popups": True,
            },
        },
        "alliance_gathering": {
            "label": "Alliance > Gathering",
            "subtasks": [
                "Open Alliance menu",
                "Open Alliance Territory Gathering",
                "Use Gathering Search menu when available",
                "Gather Food/Wood/Steel/Gas by availability",
                "Combine after Gather Speedup buff when that queue includes it",
            ],
            "options": {
                "combine_with_gathering_search_menu": True,
                "combine_with_gather_speedup": True,
                "resource_selection": resource_flags(True),
            },
        },
        "resource_gathering": {
            "label": "Gathering Search Menu > Resource Gathering",
            "subtasks": [
                "Open Gathering Search menu",
                "Search Food",
                "Search Wood",
                "Search Steel",
                "Search Gas",
                "March only if march slot is available",
            ],
            "options": {
                "search_menu": True,
                "resource_selection": resource_flags(True),
                "march_if_slot_available": True,
            },
        },
        "gathering_boost": {
            "label": "Buff > Gather Speedup + Gathering Search",
            "subtasks": [
                "Open Buff menu",
                "Select Gather Speedup",
                "Activate gather-speed buff if available",
                "Open Gathering Search menu afterwards",
                "Run Resource Gathering / Alliance Gathering in same queue block",
            ],
            "options": {
                "buff_type": "gather_speedup",
                "combine_with": ["resource_gathering", "alliance_gathering"],
                "use_before_gathering": True,
            },
        },
        "shield": {
            "label": "Buff > Shield 2hr Everyday + Gathering Search",
            "subtasks": [
                "Open Buff menu",
                "Open Shield",
                "Select 2hr Shield",
                "Enable shield every day when available",
                "Confirm shield activation",
                "Open Gathering Search menu afterwards",
            ],
            "options": {
                "buff_type": "shield",
                "shield_type": "2hr",
                "shield_on_everyday": True,
                "combine_with_gathering_search_menu": True,
            },
        },
        "building_upgrading": {
            "label": "Base > Building Upgrade",
            "subtasks": [
                "Open builder/building queue",
                "Find upgradeable building",
                "Prefer short/available upgrade",
                "Start upgrade when resources are available",
                "Do not spend premium currency unless explicitly configured",
            ],
            "options": {"premium_currency": False, "safe_upgrade_only": True},
        },
        "hq_upgrading": {
            "label": "Base > HQ Upgrade",
            "subtasks": [
                "Open Headquarters",
                "Check HQ upgrade requirements",
                "Start HQ upgrade only if requirements are met",
            ],
            "options": {"premium_currency": False, "requirements_must_be_met": True},
        },
        "research": {
            "label": "Base > Research",
            "subtasks": [
                "Open Research Center",
                "Pick available recommended research",
                "Start research when resources are available",
            ],
            "options": {"premium_currency": False, "fallback_available_research": True},
        },
        "wall_repair": {
            "label": "Base > Wall Repair",
            "subtasks": [
                "Open Wall",
                "Repair wall when damaged",
                "Close if no repair is required",
            ],
            "options": {"repair_only_if_damaged": True},
        },
        "trap_crafting": {
            "label": "Base > Trap Crafting",
            "subtasks": [
                "Open Trap Factory",
                "Craft available traps",
                "Respect resource limits",
            ],
            "options": {"craft_available_only": True},
        },
        "troop_training": {
            "label": "Military > Troop Training",
            "subtasks": [
                "Open troop training buildings",
                "Train available troop type",
                "Avoid gem speedups unless configured",
            ],
            "options": {"premium_currency": False, "train_available_only": True},
        },
        "troop_healing": {
            "label": "Military > Troop Healing",
            "subtasks": [
                "Open infirmary/hospital",
                "Heal wounded troops",
                "Use help/speedup only if configured",
            ],
            "options": {"heal_available_only": True},
        },
        "tavern_recruitment": {
            "label": "Noah Tavern Recruitment",
            "subtasks": [
                "Open Noah's Tavern",
                "Use free recruitment",
                "Claim recruit rewards/popups",
            ],
            "options": {"free_recruitment_only": True, "premium_currency": False},
        },
        "skills": {
            "label": "Commander Skills / Buffs",
            "subtasks": [
                "Open Commander Skills / Buffs",
                "Use configured utility skill if available",
                "Return to base screen",
            ],
            "options": {"safe_utility_skills_only": True},
        },
        "quest_rewards": {
            "label": "Collect Quest Rewards",
            "subtasks": [
                "Open Quest menu",
                "Collect visible quest rewards",
                "Collect daily/activity rewards",
                "Close claim popups",
            ],
            "options": {"only_in_last_queue": True, "claim_all_visible": True},
        },
        "game_gifts": {
            "label": "Collect Game Gifts",
            "subtasks": [
                "Open gift/events/mail-style reward entries when available",
                "Collect visible game gifts",
                "Close popups",
            ],
            "options": {"claim_all_visible": True},
        },
        "bag_items": {
            "label": "Bag Items / Inventory Cleanup",
            "subtasks": [
                "Open Bag",
                "Use safe daily/resource items only",
                "Do not use premium/rare items unless configured",
            ],
            "options": {"safe_items_only": True, "premium_items": False},
        },
        "supply_depot": {
            "label": "Supply Depot",
            "subtasks": [
                "Open Supply Depot",
                "Collect available supplies",
                "Close confirmation popups",
            ],
            "options": {"claim_available_only": True},
        },
        "bank_investment": {
            "label": "Bank Investment",
            "subtasks": [
                "Open Bank",
                "Collect matured investment",
                "Start configured safe investment if available",
            ],
            "options": {"safe_investment_only": True},
        },
        "radio_quiz": {
            "label": "Radio Quiz",
            "subtasks": [
                "Open Radio",
                "Run available quiz",
                "Answer/collect according to LSS-Bot script handling",
            ],
            "options": {"repeatable_wrapper": True},
        },
        "ruins": {
            "label": "Ruins",
            "subtasks": [
                "Open Ruins",
                "Run available ruins action",
                "Collect reward if available",
            ],
            "options": {"safe_available_only": True},
        },
        "campaign_puzzle_auto": {
            "label": "Campaign Puzzle > Auto",
            "subtasks": [
                "Open Campaign Puzzle",
                "Enable Auto mode",
                "Run available campaign battle",
            ],
            "options": {"auto_mode": True},
        },
        "campaign_puzzle_general": {
            "label": "Campaign Puzzle > General Best Move",
            "subtasks": [
                "Open Campaign Puzzle",
                "Use general mode",
                "Look for best move",
            ],
            "options": {"look_for_best_move": True},
        },
        "dynamic_base_puzzles": {
            "label": "Dynamic Base Puzzles",
            "subtasks": [
                "Open dynamic/base puzzle entry",
                "Run available puzzle action",
                "Return to base",
            ],
            "options": {"safe_available_only": True},
        },
        "duel_survival": {
            "label": "Duel Survival",
            "subtasks": [
                "Open Duel Survival",
                "Run available duel/survival action",
                "Collect reward if available",
            ],
            "options": {"safe_available_only": True},
        },
        "pit_gather": {
            "label": "Pit > Gather",
            "subtasks": [
                "Open Pit",
                "Select gather mode",
                "Gather available resource pit target",
            ],
            "options": {"pit_mode": "gather"},
        },
        "pit_attack": {
            "label": "Pit > Attack",
            "subtasks": [
                "Open Pit",
                "Select attack mode",
                "Attack available target according to LSS-Bot rules",
            ],
            "options": {"pit_mode": "attack"},
        },
    }

    for tid, d in details.items():
        if tid in by_id:
            t = by_id[tid]
            t.label = d["label"]
            t.settings["expanded_subtasks"] = d["subtasks"]
            t.settings["options"] = d["options"]
            t.settings["display_name"] = d["label"]
            t.settings["resolved_by"] = "wulfpack_overseer_v0.0.8"

    extra = [
        make_task("speedup_help", "Speedup Help", "Repeatable Wrapper", "Speedup Help",
                  ["Speedup Help", "Help Speedups", "Alliance Help Speedup"],
                  ["Open help/speedup related menu", "Send/request speedup help when available", "Close confirmation popups"],
                  {"repeat_in_each_queue": True}),
        make_task("nova_daily_praise", "Nova Daily > Praise", "Repeatable Wrapper", "Nova Daily",
                  ["Nova Daily", "Nova Praise", "Praise", "Nova Daily Praise"],
                  ["Open Nova Daily", "Open Praise", "Praise/claim when available", "Close popups"],
                  {"repeat_in_each_queue": True}),
        make_task("nova_research", "Nova Research", "Repeatable Wrapper", "Nova Research",
                  ["Nova Research", "Nova"],
                  ["Open Nova", "Open Research", "Start/continue available Nova research", "Close popups"],
                  {"repeat_in_each_queue": True, "premium_currency": False}),
        make_task("noah_tavern", "Noah Tavern", "Repeatable Wrapper", "Noah's Tavern",
                  ["Noah Tavern", "Noah's Tavern", "Noahs Tavern", "Tavern Recruitment"],
                  ["Open Noah's Tavern", "Use free recruitment", "Collect recruitment reward", "Close popups"],
                  {"repeat_in_each_queue": True, "free_recruitment_only": True}),
        make_task("collect_base_resources", "Collect Base Resources + Antiserum Limit Confirm", "Repeatable Wrapper", "Collect Base Resources",
                  ["Collect Base Resources", "Base Resources", "Collect Resources", "Antiserum Storage"],
                  [
                      "Collect Serum",
                      "Collect Food",
                      "Collect Wood",
                      "Collect Steel",
                      "Collect Gas",
                      "Confirm antiserum storage limit message when shown",
                  ],
                  {
                      "repeat_in_each_queue": True,
                      "resources": ["serum", "food", "wood", "steel", "gas"],
                      "confirm_antiserum_storage_limit_message": True,
                  }),
    ]
    for t in extra:
        if t.id not in by_id:
            tasks.append(t)
            by_id[t.id] = t

    for t in tasks:
        if t.group == "Zombies":
            t.label = t.label.replace("39-59", "39-40")
            t.settings["zombie_max_level"] = 40
            t.settings["expanded_subtasks"] = [
                "Open Zombies script",
                "Use selected level range only",
                "Search zombie/lair targets",
                "Attack while stamina/marches are available",
            ]
            if int(t.settings.get("level_max", 40)) > 40:
                t.settings["level_max"] = 40
                t.settings["selected_levels"] = [x for x in t.settings.get("selected_levels", []) if int(x) <= 40]

    return tasks

    return enrich_task_catalog(base + zombies)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def win_expand(value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(value)))


def is_inside_path(child: Path, parent: Path) -> bool:
    """Return True if child is inside parent. Case-insensitive on Windows paths."""
    try:
        child_resolved = child.resolve()
    except OSError:
        child_resolved = child.absolute()
    try:
        parent_resolved = parent.resolve()
    except OSError:
        parent_resolved = parent.absolute()

    child_s = str(child_resolved).lower()
    parent_s = str(parent_resolved).rstrip("\\/").lower()
    return (
        child_s == parent_s
        or child_s.startswith(parent_s + "\\")
        or child_s.startswith(parent_s + "/")
    )


def dedupe_existing_paths(paths: Sequence[Path]) -> List[Path]:
    out: List[Path] = []
    seen: set[str] = set()
    for p in paths:
        try:
            resolved = p.resolve()
        except OSError:
            resolved = p.absolute()
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        if resolved.exists():
            out.append(resolved)
    return out


def candidate_roots(extra: Sequence[str]) -> List[Path]:
    """
    Default policy: scan ONLY the Windows profile of the user running this process.

    No C:\\Users\\* scan.
    No other Windows user profiles.
    No Program Files / global folders by default.
    """
    user_profile = win_expand(r"%USERPROFILE%")

    candidates = [
        os.environ.get("LSSBOT_HOME", ""),
        r"%USERPROFILE%\\lssbot_5",
        r"%USERPROFILE%\\LSSBot",
        r"%USERPROFILE%\\LSS Bot",
        r"%LOCALAPPDATA%\\lssbot",
        r"%LOCALAPPDATA%\\LSS Bot",
        r"%LOCALAPPDATA%\\LSSBot",
        r"%APPDATA%\\lssbot",
        r"%APPDATA%\\LSS Bot",
        r"%APPDATA%\\LSSBot",
    ] + list(extra)

    resolved: List[Path] = []
    for c in candidates:
        if not c:
            continue
        p = win_expand(c)
        # Only scan the current Windows user's profile by default.
        if is_inside_path(p, user_profile):
            resolved.append(p)

    return dedupe_existing_paths(resolved)


def iter_text_files(root: Path) -> Iterable[Path]:
    try:
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            try:
                if p.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield p
    except (OSError, PermissionError):
        return


def read_text(path: Path) -> Optional[str]:
    try:
        data = path.read_bytes()
    except (OSError, PermissionError):
        return None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(enc, errors="replace")
        except Exception:
            pass
    return None


# Strong LSS-Bot emulator serials. TCP aliases like 127.0.0.1:5555 are intentionally
# treated as weak hints and are hidden when emulator-5554/emulator-5556 style serials exist.
ADB_SERIAL_RE = re.compile(r"\bemulator-\d{4,5}\b", re.I)
TCP_ADB_SERIAL_RE = re.compile(r"\b(?:127\.0\.0\.1|localhost):\d{4,5}\b", re.I)
WIN_PATH_RE = re.compile(r"[A-Za-z]:\\\\[^|\r\n]+")
# Important: no \s here. \s matches newlines and caused false hits like "emulator\n2026".
EMU_LABEL_RE = re.compile(r"\b(?:LDPlayer|LD Player|BlueStacks|Nox|MEmu|MuMu|GameLoop)[ \t_-]*\d*\b", re.I)
KNOWN_TOOL_FILE_RE = re.compile(r"lss_character_queue_v\d+.*\.(?:py|cmd|bat|ps1|md|json|txt)$", re.I)

FAST_SCAN_MAX_FILES = 35
FAST_SCAN_MAX_LOGS = 12
FAST_SCAN_MAX_DEPTH = 3
FAST_SCAN_NAME_RE = re.compile(
    r"(lssbot|lss-bot|log|setting|settings|config|configs|task|tasks|queue|queues|account|accounts|emulator|adb)",
    re.I,
)

FAST_SCAN_SKIP_RE = re.compile(
    r"(?:^|[\\/])(?:runtime|lib|jre|jdk|java|cache|tmp|temp|__pycache__|screenshots|backup|backups)(?:[\\/]|$)"
    r"|psfontj2d\.properties$"
    r"|.*\.runtimeconfig\.json$"
    r"|.*\.deps\.json$"
    r"|.*\.dll\.config$"
    r"|fontconfig.*\.properties$"
    r"|logging\.properties$"
    r"|net\.properties$"
    r"|sound\.properties$"
    r"|awt\.properties$",
    re.I,
)

FAST_SCAN_KEEP_RE = re.compile(
    r"(?:log|logs|setting|settings|config|configs|task|tasks|queue|queues|account|accounts|emulator|adb)",
    re.I,
)


def is_fast_scan_candidate(path: Path, root: Path) -> bool:
    """Keep only LSS-Bot-relevant user/config/log files, never Java runtime/lib files."""
    full = str(path)
    if FAST_SCAN_SKIP_RE.search(full):
        return False

    try:
        rel = str(path.relative_to(root))
    except ValueError:
        rel = path.name

    # Important: do not match the root folder name "lssbot".
    # Matching the full path caused false positives like runtime/lib/psfontj2d.properties.
    return bool(FAST_SCAN_KEEP_RE.search(rel) or FAST_SCAN_KEEP_RE.search(path.name))

LSSBOT_PROFILE_RE = re.compile(
    r"(?P<name>(?:LDPlayer|LD Player|BlueStacks|Nox|MEmu|MuMu|GameLoop)"
    r"[0-9]?"
    r"(?:[ \t_-]*\([^)]+\))?)"
    r"[ \t]*(?:\([ \t]*ID[ \t]*[:=][ \t]*(?P<id>\d+)[ \t]*\))",
    re.I,
)


def serial_to_probable_lssbot_id(serial: Optional[str]) -> Optional[str]:
    """Infer common emulator index from Android serials like emulator-5554."""
    if not serial:
        return None
    m = re.fullmatch(r"emulator-(\d{4,5})", serial.strip(), re.I)
    if not m:
        return None
    port = int(m.group(1))
    if port >= 5554 and (port - 5554) % 2 == 0:
        return str((port - 5554) // 2)
    return None


def clean_lssbot_profile_name(name: str, profile_id: Optional[str] = None) -> str:
    name = re.sub(r"\s+", " ", name.strip())
    if profile_id is not None and not re.search(r"\(\s*ID\s*[:=]", name, re.I):
        name = f"{name} (ID: {profile_id})"
    return name


def extract_lssbot_profiles(text: str) -> Dict[str, str]:
    """
    Extract emulator profile labels such as:
      LDPlayer9-(Farmen) (ID: 0)
      LDPlayer-(Mains) (ID: 1)

    The script keeps this generic, so different user naming schemes are supported
    as long as LSS-Bot logs/configs contain a name with an ID.
    """
    profiles: Dict[str, str] = {}
    for m in LSSBOT_PROFILE_RE.finditer(text):
        profile_id = m.group("id")
        name = clean_lssbot_profile_name(m.group("name"), profile_id)
        profiles[profile_id] = name
    return profiles


def resolve_emulator_profile_from_context(text: str, serial: str, global_profiles: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve a friendly LSS-Bot profile name for one ADB serial.
    Priority:
      1. Name + ID near the serial in the same log/config context.
      2. Common emulator port -> ID mapping, e.g. emulator-5554 => ID 0.
    """
    # Same-context lookup around the serial.
    for m in re.finditer(re.escape(serial), text, re.I):
        start = max(0, m.start() - 1200)
        end = min(len(text), m.end() + 1200)
        context = text[start:end]
        local_profiles = extract_lssbot_profiles(context)
        if len(local_profiles) == 1:
            profile_id, name = next(iter(local_profiles.items()))
            return name, profile_id

        probable_id = serial_to_probable_lssbot_id(serial)
        if probable_id and probable_id in local_profiles:
            return local_profiles[probable_id], probable_id

    # Global fallback by common port-to-ID mapping.
    probable_id = serial_to_probable_lssbot_id(serial)
    if probable_id and probable_id in global_profiles:
        return global_profiles[probable_id], probable_id

    return None, probable_id


def is_lssbot_scan_file(path: Path) -> bool:
    name = path.name.lower()
    full = str(path).lower()
    if KNOWN_TOOL_FILE_RE.search(path.name):
        return False
    if "__pycache__" in full:
        return False
    if "lssbot" in full or "lss-bot" in full:
        return True
    return False



def iter_files_limited(root: Path, max_depth: int = FAST_SCAN_MAX_DEPTH) -> Iterable[Path]:
    """Small bounded tree walk. Avoids hanging on huge LSS-Bot runtime/log/config folders."""
    try:
        root = root.resolve()
    except OSError:
        root = root.absolute()
    base_depth = len(root.parts)
    try:
        for current, dirs, files in os.walk(root):
            cur = Path(current)
            depth = len(cur.parts) - base_depth

            # Never descend into Java/.NET runtime/lib/cache style folders.
            dirs[:] = [
                d for d in dirs
                if not FAST_SCAN_SKIP_RE.search(str(cur / d))
            ]

            if depth >= max_depth:
                dirs[:] = []

            for name in files:
                p = cur / name
                if p.suffix.lower() not in TEXT_EXTENSIONS:
                    continue
                if not is_lssbot_scan_file(p):
                    continue
                if FAST_SCAN_SKIP_RE.search(str(p)):
                    continue
                if not is_fast_scan_candidate(p, root):
                    continue
                try:
                    if p.stat().st_size > MAX_FILE_BYTES:
                        continue
                except OSError:
                    continue
                yield p
    except (OSError, PermissionError):
        return


def iter_lssbot_files_fast(roots: Sequence[Path], max_files: int = FAST_SCAN_MAX_FILES) -> List[Path]:
    """
    Fast default scan:
    - only current-user LSS-Bot roots
    - recent logs + likely config/settings/task files
    - bounded file count
    """
    logs: List[Path] = []
    others: List[Path] = []
    seen: set[str] = set()

    progress_step("scan LSS-Bot folders for recent logs/configs; runtime/lib is skipped")
    for root in roots:
        progress_step(f"walk root: {root}")
        before = len(seen)
        for p in iter_files_limited(root):
            key = str(p).lower()
            if key in seen:
                continue
            seen.add(key)
            if "log" in p.name.lower() or "logs" in str(p.parent).lower():
                logs.append(p)
            else:
                others.append(p)
        progress_ok(f"root checked: {root} ({len(seen) - before} candidate files)")

    def mtime_key(p: Path) -> float:
        try:
            return p.stat().st_mtime
        except OSError:
            return 0.0

    logs = sorted(logs, key=mtime_key, reverse=True)[:FAST_SCAN_MAX_LOGS]
    others = sorted(others, key=mtime_key, reverse=True)[:max(0, max_files - len(logs))]
    selected = logs + others
    progress_ok(f"selected {len(selected)} files for fast scan")
    for p in selected:
        progress_step(f"queued file: {p}")
    return selected


def run_probe_command(args: Sequence[str], timeout: int = 4) -> str:
    cmd_text = " ".join(str(x) for x in args)
    progress_step(f"run command: {cmd_text}")
    try:
        proc = subprocess.run(
            list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
        output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        progress_ok(f"command finished: {Path(str(args[0])).name}")
        return output
    except subprocess.TimeoutExpired:
        progress_warn(f"command timeout after {timeout}s: {cmd_text}")
        return ""
    except Exception as exc:
        progress_warn(f"command failed: {cmd_text} ({exc})")
        return ""


def existing_candidates(paths: Sequence[str]) -> List[Path]:
    out: List[Path] = []
    seen: set[str] = set()
    for raw in paths:
        if not raw:
            continue
        p = win_expand(raw)
        key = str(p).lower()
        if key in seen:
            continue
        seen.add(key)
        if p.exists():
            out.append(p)
    return out


def normalize_emulator_type(value: Optional[str]) -> str:
    value = (value or "auto").strip().lower()
    aliases = {
        "1": "ldplayer9",
        "2": "ldplayer5",
        "3": "ldplayer4",
        "4": "ldplayer14",
        "5": "memu",
        "6": "nox",
        "7": "auto",
        "ld9": "ldplayer9",
        "ld5": "ldplayer5",
        "ld4": "ldplayer4",
        "ld14": "ldplayer14",
        "ldplayer 9": "ldplayer9",
        "ldplayer 5": "ldplayer5",
        "ldplayer 4": "ldplayer4",
        "ldplayer 14": "ldplayer14",
        "ldplayer14beta": "ldplayer14",
        "ldplayer14-beta": "ldplayer14",
        "memuplay": "memu",
        "memu play": "memu",
        "noxplayer": "nox",
        "nox player": "nox",
        "unknown": "auto",
        "all": "auto",
        "automatic": "auto",
    }
    return aliases.get(value, value if value in {"auto", "ldplayer9", "ldplayer5", "ldplayer4", "ldplayer14", "memu", "nox"} else "auto")


def emulator_type_label(value: Optional[str]) -> str:
    labels = {
        "auto": {
            "english": "Auto / unknown",
            "german": "Automatisch / unbekannt",
            "french": "Auto / inconnu",
            "espanol": "Auto / desconocido",
            "polski": "Auto / nieznany",
            "russian": "Avto / neizvestno",
        },
        "ldplayer9": "LDPlayer9",
        "ldplayer5": "LDPlayer5",
        "ldplayer4": "LDPlayer4",
        "ldplayer14": "LDPlayer 14 beta",
        "memu": "MEmu Play",
        "nox": "Nox Player",
    }
    normalized = normalize_emulator_type(value)
    label = labels.get(normalized, labels["auto"])
    if isinstance(label, dict):
        return label.get(ACTIVE_LANG, label["english"])
    return label


def emulator_cli_candidates(preferred: str = "auto") -> Dict[str, List[Path]]:
    """Find selected emulator management CLI without recursive all-disk scanning."""
    preferred = normalize_emulator_type(preferred)
    pf = os.environ.get("PROGRAMFILES", r"C:\Program Files")
    pfx86 = os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
    local = os.environ.get("LOCALAPPDATA", "")

    ld_paths_by_version = {
        "ldplayer9": [
            r"C:\LDPlayer\LDPlayer9\dnconsole.exe",
            r"C:\LDPlayer\LDPlayer9\ldconsole.exe",
            r"C:\ChangZhi\LDPlayer9\dnconsole.exe",
            r"C:\ChangZhi\LDPlayer9\ldconsole.exe",
            str(Path(pf) / "LDPlayer9" / "dnconsole.exe"),
            str(Path(pf) / "LDPlayer9" / "ldconsole.exe"),
            str(Path(pfx86) / "LDPlayer9" / "dnconsole.exe"),
            str(Path(pfx86) / "LDPlayer9" / "ldconsole.exe"),
            str(Path(local) / "LDPlayer9" / "dnconsole.exe"),
            str(Path(local) / "LDPlayer9" / "ldconsole.exe"),
        ],
        "ldplayer5": [
            r"C:\LDPlayer\LDPlayer5\dnconsole.exe",
            r"C:\LDPlayer\LDPlayer5\ldconsole.exe",
            r"C:\ChangZhi\LDPlayer5\dnconsole.exe",
            r"C:\ChangZhi\LDPlayer5\ldconsole.exe",
            str(Path(pf) / "LDPlayer5" / "dnconsole.exe"),
            str(Path(pf) / "LDPlayer5" / "ldconsole.exe"),
            str(Path(pfx86) / "LDPlayer5" / "dnconsole.exe"),
            str(Path(pfx86) / "LDPlayer5" / "ldconsole.exe"),
            str(Path(local) / "LDPlayer5" / "dnconsole.exe"),
            str(Path(local) / "LDPlayer5" / "ldconsole.exe"),
        ],
        "ldplayer4": [
            r"C:\LDPlayer\LDPlayer4\dnconsole.exe",
            r"C:\LDPlayer\LDPlayer4\ldconsole.exe",
            r"C:\ChangZhi\LDPlayer4\dnconsole.exe",
            r"C:\ChangZhi\LDPlayer4\ldconsole.exe",
            str(Path(pf) / "LDPlayer4" / "dnconsole.exe"),
            str(Path(pf) / "LDPlayer4" / "ldconsole.exe"),
            str(Path(pfx86) / "LDPlayer4" / "dnconsole.exe"),
            str(Path(pfx86) / "LDPlayer4" / "ldconsole.exe"),
            str(Path(local) / "LDPlayer4" / "dnconsole.exe"),
            str(Path(local) / "LDPlayer4" / "ldconsole.exe"),
        ],
        "ldplayer14": [
            r"C:\LDPlayer\LDPlayer14\dnconsole.exe",
            r"C:\LDPlayer\LDPlayer14\ldconsole.exe",
            r"C:\ChangZhi\LDPlayer14\dnconsole.exe",
            r"C:\ChangZhi\LDPlayer14\ldconsole.exe",
            str(Path(pf) / "LDPlayer14" / "dnconsole.exe"),
            str(Path(pf) / "LDPlayer14" / "ldconsole.exe"),
            str(Path(pfx86) / "LDPlayer14" / "dnconsole.exe"),
            str(Path(pfx86) / "LDPlayer14" / "ldconsole.exe"),
            str(Path(local) / "LDPlayer14" / "dnconsole.exe"),
            str(Path(local) / "LDPlayer14" / "ldconsole.exe"),
        ],
    }

    generic_ld = [
        r"C:\LDPlayer\dnconsole.exe",
        r"C:\LDPlayer\ldconsole.exe",
        r"C:\ChangZhi\LDPlayer\dnconsole.exe",
        r"C:\ChangZhi\LDPlayer\ldconsole.exe",
        str(Path(pf) / "LDPlayer" / "dnconsole.exe"),
        str(Path(pf) / "LDPlayer" / "ldconsole.exe"),
        str(Path(pfx86) / "LDPlayer" / "dnconsole.exe"),
        str(Path(pfx86) / "LDPlayer" / "ldconsole.exe"),
        str(Path(local) / "LDPlayer" / "dnconsole.exe"),
        str(Path(local) / "LDPlayer" / "ldconsole.exe"),
    ]

    memu_paths = [
        str(Path(pf) / "Microvirt" / "MEmu" / "memuc.exe"),
        str(Path(pfx86) / "Microvirt" / "MEmu" / "memuc.exe"),
        str(Path(local) / "Microvirt" / "MEmu" / "memuc.exe"),
        r"C:\Program Files\Microvirt\MEmu\memuc.exe",
        r"C:\Program Files (x86)\Microvirt\MEmu\memuc.exe",
    ]

    nox_paths = [
        str(Path(pf) / "Nox" / "bin" / "NoxConsole.exe"),
        str(Path(pfx86) / "Nox" / "bin" / "NoxConsole.exe"),
        str(Path(local) / "Nox" / "bin" / "NoxConsole.exe"),
        r"C:\Program Files\Nox\bin\NoxConsole.exe",
        r"C:\Program Files (x86)\Nox\bin\NoxConsole.exe",
    ]

    candidates: Dict[str, List[str]] = {"ldplayer": [], "memu": [], "nox": []}

    if preferred in {"ldplayer9", "ldplayer5", "ldplayer4", "ldplayer14"}:
        candidates["ldplayer"].extend(ld_paths_by_version[preferred])
        candidates["ldplayer"].extend(generic_ld)
    elif preferred == "memu":
        candidates["memu"].extend(memu_paths)
    elif preferred == "nox":
        candidates["nox"].extend(nox_paths)
    else:
        for paths in ld_paths_by_version.values():
            candidates["ldplayer"].extend(paths)
        candidates["ldplayer"].extend(generic_ld)
        candidates["memu"].extend(memu_paths)
        candidates["nox"].extend(nox_paths)

    if preferred in {"auto", "ldplayer9", "ldplayer5", "ldplayer4", "ldplayer14"}:
        for exe in ("dnconsole.exe", "ldconsole.exe"):
            found = shutil.which(exe)
            if found:
                candidates["ldplayer"].append(found)
    if preferred in {"auto", "memu"}:
        found = shutil.which("memuc.exe")
        if found:
            candidates["memu"].append(found)
    if preferred in {"auto", "nox"}:
        found = shutil.which("NoxConsole.exe")
        if found:
            candidates["nox"].append(found)

    return {k: existing_candidates(v) for k, v in candidates.items()}


def parse_csv_like_line(line: str) -> List[str]:
    return [x.strip().strip('"') for x in line.strip().split(",")]


def scan_emulators_cli(preferred: str = "auto") -> List[Emulator]:
    """
    Fast emulator identification via vendor CLI:
      LDPlayer: dnconsole/ldconsole list2
      MEmu: memuc listvms --running, fallback listvms
      Nox: NoxConsole list
    """
    progress_step(f"search vendor CLI for emulator type: {emulator_type_label(preferred)}")
    out: List[Emulator] = []
    seen_keys: set[str] = set()
    tools = emulator_cli_candidates(preferred)
    total_tools = sum(len(v) for v in tools.values())
    progress_ok(f"vendor CLI candidates found: {total_tools}")

    # LDPlayer: dnconsole.exe and ldconsole.exe usually return the same list.
    # Use the first CLI that returns instances, then stop to avoid duplicate entries.
    for exe in tools.get("ldplayer", []):
        progress_step(f"probe LDPlayer instances via list2: {exe}")
        data = run_probe_command([str(exe), "list2"])
        found_here = 0
        for line in data.splitlines():
            parts = parse_csv_like_line(line)
            if len(parts) >= 2 and parts[0].isdigit():
                idx = int(parts[0])
                name = parts[1] or f"LDPlayer {idx}"
                serial = f"emulator-{5554 + idx * 2}"
                label = f"{name} (ID: {idx})"
                key = f"ldplayer:{idx}:{serial}".lower()
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                found_here += 1
                progress_ok(f"LDPlayer list2 found: ID {idx} | title={name} | expected ADB={serial}")
                out.append(Emulator(
                    f"cli{len(out)+1:02d}",
                    label,
                    serial,
                    f"ldconsole-list2:{exe}",
                    line,
                    label,
                    str(idx),
                    "ldplayer-cli",
                ))
        if found_here:
            progress_ok(f"LDPlayer source accepted: {exe}")
            break

    for exe in tools.get("memu", []):
        progress_step(f"probe MEmu instances via listvms: {exe}")
        data = run_probe_command([str(exe), "listvms", "--running"]) or run_probe_command([str(exe), "listvms"])
        for line in data.splitlines():
            parts = parse_csv_like_line(line)
            if len(parts) >= 2 and parts[0].isdigit():
                idx = int(parts[0])
                name = parts[1] or f"MEmu {idx}"
                label = f"{name} (ID: {idx})"
                key = f"memu:{idx}:{name}".lower()
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                progress_ok(f"MEmu listvms found: ID {idx} | title={name}")
                out.append(Emulator(
                    f"cli{len(out)+1:02d}",
                    label,
                    None,
                    f"memuc-listvms:{exe}",
                    line,
                    label,
                    str(idx),
                    "memu-cli",
                ))

    for exe in tools.get("nox", []):
        progress_step(f"probe Nox instances via list: {exe}")
        data = run_probe_command([str(exe), "list"])
        for index, line in enumerate([x for x in data.splitlines() if x.strip()]):
            parts = parse_csv_like_line(line)
            if len(parts) >= 2:
                internal = parts[0]
                title = parts[1] or internal or f"Nox {index}"
                label = f"{title} (ID: {index})"
                key = f"nox:{index}:{title}".lower()
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                progress_ok(f"Nox list found: ID {index} | title={title}")
                out.append(Emulator(
                    f"cli{len(out)+1:02d}",
                    label,
                    None,
                    f"noxconsole-list:{exe}",
                    line,
                    label,
                    str(index),
                    "nox-cli",
                ))

    progress_ok(f"vendor CLI scan found {len(out)} unique instance(s)")
    return out



def find_adb(roots: Sequence[Path]) -> Optional[Path]:
    env = os.environ.get("ADB")
    if env and Path(env).exists():
        return Path(env)
    for root in roots:
        for rel in ("adb.exe", "adb", "tools/adb.exe", "tools/adb", "platform-tools/adb.exe", "platform-tools/adb"):
            p = root / rel
            if p.exists():
                return p
    found = shutil.which("adb")
    return Path(found) if found else None


def scan_emulators_adb(roots: Sequence[Path]) -> List[Emulator]:
    progress_step("search ADB executable")
    adb = find_adb(roots)
    if not adb:
        progress_warn("ADB executable not found")
        return []
    progress_step(f"run ADB devices: {adb}")
    try:
        proc = subprocess.run([str(adb), "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=8, check=False)
        progress_ok("ADB devices command finished")
    except subprocess.TimeoutExpired:
        progress_warn("ADB devices timeout after 8s")
        return []
    except Exception as exc:
        progress_warn(f"ADB devices failed: {exc}")
        return []
    out: List[Emulator] = []
    weak_tcp: List[Emulator] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("list of devices"):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1].lower() == "device":
            serial = parts[0]
            if ADB_SERIAL_RE.fullmatch(serial):
                out.append(Emulator(f"emu{len(out)+1:02d}", f"Emulator {len(out)+1} ({serial})", serial, f"adb:{adb}", line))
            elif TCP_ADB_SERIAL_RE.fullmatch(serial):
                weak_tcp.append(Emulator(f"tcp{len(weak_tcp)+1:02d}", f"TCP ADB ({serial})", serial, f"adb-weak:{adb}", line))
    progress_ok(f"ADB scan found {len(out or weak_tcp)} device(s)")
    return out or weak_tcp


def scan_emulators_files(roots: Sequence[Path]) -> List[Emulator]:
    progress_step("scan recent LSS-Bot logs/configs for emulator names")
    found: Dict[str, Emulator] = {}
    weak: Dict[str, Emulator] = {}
    profiles_by_id: Dict[str, str] = {}

    # First pass: collect profile names with IDs globally from current-user LSS-Bot files.
    file_texts: List[Tuple[Path, str]] = []
    for f in iter_lssbot_files_fast(roots):
        progress_step(f"read emulator context: {f}")
        text = read_text(f)
        if not text:
            continue
        file_texts.append((f, text))
        profiles_by_id.update(extract_lssbot_profiles(text))

    # Second pass: collect emulator serials and attach resolved profile names.
    for f, text in file_texts:
        for m in ADB_SERIAL_RE.finditer(text):
            raw = m.group(0)
            key = "adb:" + raw.lower()
            profile_name, profile_id = resolve_emulator_profile_from_context(text, raw, profiles_by_id)
            if key not in found:
                label = profile_name if profile_name else f"Emulator {len(found)+1} ({raw})"
                found[key] = Emulator(
                    f"emu{len(found)+1:02d}",
                    label,
                    raw,
                    f"lssbot-log:{f}",
                    raw,
                    profile_name,
                    profile_id,
                    "lssbot-profile" if profile_name else "adb-serial",
                )
            else:
                old = found[key]
                if profile_name and not old.lssbot_name:
                    old.lssbot_name = profile_name
                    old.lssbot_id = profile_id
                    old.resolved_from = "lssbot-profile"
                    old.label = profile_name

        # Keep weak hints only as fallback when no real emulator-* serial exists.
        for m in TCP_ADB_SERIAL_RE.finditer(text):
            raw = m.group(0)
            key = "tcp:" + raw.lower()
            if key not in weak:
                weak[key] = Emulator(f"tcp{len(weak)+1:02d}", f"TCP ADB ({raw})", raw, f"lssbot-log-weak:{f}", raw)
        for m in EMU_LABEL_RE.finditer(text):
            raw = re.sub(r"[ \t]+", " ", m.group(0).strip())
            if not raw:
                continue
            key = "label:" + raw.lower()
            if key not in weak:
                weak[key] = Emulator(f"label{len(weak)+1:02d}", f"Emulator hint ({raw})", None, f"lssbot-log-weak:{f}", raw)

    result = list(found.values()) or list(weak.values())
    progress_ok(f"LSS-Bot log/config emulator scan found {len(result)} candidate(s)")
    return result


def merge_emulators(a: Sequence[Emulator], b: Sequence[Emulator]) -> List[Emulator]:
    merged: Dict[str, Emulator] = {}
    suppressed: List[Emulator] = []

    def key_for(e: Emulator) -> str:
        if e.adb_serial and ADB_SERIAL_RE.fullmatch(e.adb_serial):
            return "adb:" + e.adb_serial.lower()
        if e.adb_serial and TCP_ADB_SERIAL_RE.fullmatch(e.adb_serial):
            return "tcp:" + e.adb_serial.lower()
        return "label:" + (e.raw or e.label).lower()

    for e in list(a) + list(b):
        key = key_for(e)
        if key.startswith("adb:"):
            if key not in merged:
                merged[key] = e
            else:
                old = merged[key]
                # Prefer lssbot-log source so it is marked as connected to LSS-Bot.
                if old.source.startswith("adb:") and e.source.startswith("lssbot-log:"):
                    e.raw = f"{e.raw}; live {old.source}"
                    merged[key] = e
                elif old.source.startswith("lssbot-log:") and e.source.startswith("adb:"):
                    old.raw = f"{old.raw}; live {e.source}"
            continue
        suppressed.append(e)

    # Strong rule: if emulator-5554/emulator-5556 were found, show only those unique serials.
    out = list(merged.values())
    if not out:
        # Fallback only when no real emulator-* serial exists.
        weak_merged: Dict[str, Emulator] = {}
        for e in suppressed:
            key = key_for(e)
            if key not in weak_merged:
                weak_merged[key] = e
        out = list(weak_merged.values())

    out.sort(key=lambda e: int(re.search(r"(\d+)$", e.adb_serial or "999999").group(1)) if re.search(r"(\d+)$", e.adb_serial or "") else 999999)
    for idx, e in enumerate(out, 1):
        e.id = f"emu{idx:02d}"
        if e.lssbot_name:
            e.label = e.lssbot_name
        elif e.adb_serial:
            probable_id = serial_to_probable_lssbot_id(e.adb_serial)
            if probable_id is not None:
                e.lssbot_id = e.lssbot_id or probable_id
            e.label = f"Emulator {idx} ({e.adb_serial})"
        elif not e.label.lower().startswith("emulator"):
            e.label = f"Emulator {idx} ({e.label})"
        if e.source.startswith("lssbot-log:") and "LSS-Bot connected" not in e.source:
            e.source = e.source + " | LSS-Bot connected"
    return out


def scan_tasks(roots: Sequence[Path], tasks: List[TaskDefinition]) -> List[TaskDefinition]:
    progress_step("compile known task signatures")
    compiled: List[Tuple[TaskDefinition, List[re.Pattern[str]]]] = []
    for t in tasks:
        pats = [re.compile(re.escape(alias), re.I) for alias in t.aliases if len(alias.strip()) >= 3]
        compiled.append((t, pats))
    progress_ok(f"compiled {len(compiled)} task definitions")
    progress_step("scan recent LSS-Bot files for known tasks")
    for f in iter_lssbot_files_fast(roots):
        progress_step(f"read task context: {f}")
        text = read_text(f)
        if not text:
            continue
        for task, pats in compiled:
            if any(p.search(text) for p in pats):
                s = str(f)
                if s not in task.scan_hits:
                    task.scan_hits.append(s)
    hit_count = sum(1 for task in tasks if task.scan_hits)
    progress_ok(f"task scan finished: {hit_count} known task group(s) matched")
    return tasks


def header(text: str) -> None:
    banner([text])


def banner(lines: Sequence[str]) -> None:
    # Exact visible width:
    # top/bottom border length == widest visible middle line.
    normalized = [str(line) for line in lines]
    inner_width = max(terminal_width(line) for line in normalized)
    width = inner_width + 6
    print()
    print(color_hash_line(width))
    for line in normalized:
        pad = " " * max(0, inner_width - terminal_width(line))
        print(bold_white(f"## {line}{pad} ##"))
    print(color_hash_line(width))


def program_banner() -> None:
    banner([
        "LSS Character Queue v5.0 FINAL",
        " [JLA]  -  Justice Lover Authority ",
        "by  neo",
    ])


def ask_int(prompt: str, lang: str, minimum: int = 1, maximum: Optional[int] = None, default: Optional[int] = None) -> int:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(format_prompt(f"{prompt}{suffix}: ")).strip()
        if not raw and default is not None:
            return default
        try:
            val = int(raw)
        except ValueError:
            print(tr("invalid_number", lang))
            continue
        if val < minimum:
            print(f"{tr('minimum', lang)} {minimum}.")
            continue
        if maximum is not None and val > maximum:
            print(f"{tr('maximum', lang)} {maximum}.")
            continue
        return val


def ask_text(prompt: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default else ""
    raw = input(format_prompt(f"{prompt}{suffix}: ")).strip()
    return raw if raw else (default or "")


def parse_select(raw: str, max_index: int, lang: str) -> List[int]:
    raw = raw.strip().lower()
    if raw in {"all", "alle", "beide", "both", "ambos", "lesdeux", "les-deux", "oba", "обa", "оба", "todo", "todos", "wszystko", "все", "*"}:
        return list(range(1, max_index + 1))
    result: List[int] = []
    for token in re.split(r"[,+;\s]+", raw):
        if not token:
            continue
        if "-" in token:
            try:
                a, b = [int(x) for x in token.split("-", 1)]
            except ValueError:
                raise ValueError(f"{tr('invalid_select', lang)}: {token}")
            if a > b:
                a, b = b, a
            for n in range(a, b + 1):
                if 1 <= n <= max_index and n not in result:
                    result.append(n)
            continue
        try:
            n = int(token)
        except ValueError:
            raise ValueError(f"{tr('invalid_select', lang)}: {token}")
        if not 1 <= n <= max_index:
            raise ValueError(f"{tr('invalid_select', lang)}: {n}")
        if n not in result:
            result.append(n)
    if not result:
        raise ValueError(tr("empty_select", lang))
    return result


def ask_select(prompt: str, max_index: int, lang: str) -> List[int]:
    while True:
        raw = input(format_prompt(f"{prompt} ({tr('select_hint', lang)}): ")).strip()
        try:
            return parse_select(raw, max_index, lang)
        except ValueError as exc:
            print(exc)


def choose_emulators(detected: List[Emulator], lang: str) -> List[Emulator]:
    header(tr("emulator_scan", lang))
    if detected:
        print(gray(tr("detected_emulators", lang) + ":"))
        for idx, e in enumerate(detected, 1):
            serial = f" | ADB={e.adb_serial}" if e.adb_serial else ""
            connected = f" | {tr('connected', lang)}" if "lssbot-log" in e.source.lower() else ""
            number = bold_gray(f"{idx:2d}.")
            label = gray(f" {e.label}")
            adb = gray(serial)
            conn = green(connected) if connected else ""
            print(f"{number}{label}{adb}{conn}")
            print(gray(f"    {tr('source', lang)}: ") + color_source(e.source))

        # Direct menu: emulator1 / emulator2 / both. This avoids the confusing
        # old two-step question where the user first entered a count and then indexes.
        prompt = tr("emu_menu", lang) if len(detected) <= 2 else tr("which_emulators", lang)
        idxs = ask_select(prompt, len(detected), lang)
        return [detected[i - 1] for i in idxs]

    print(gray(tr("no_emulators", lang)))
    count = ask_int(tr("manual_emulators", lang), lang, 1, None, 1)
    out: List[Emulator] = []
    for i in range(1, count + 1):
        label = ask_text(f"{tr('emulator_name', lang)} {i}", f"Emulator {i}")
        serial = ask_text(f"{tr('adb_serial', lang)} {i}", "")
        out.append(Emulator(f"emu{i:02d}", label, serial or None, "manual"))
    return out

def choose_characters(emulators: Sequence[Emulator], lang: str) -> List[Character]:
    header(tr("characters_header", lang))
    out: List[Character] = []
    for e in emulators:
        count = ask_int(f"{tr('how_many_chars', lang)} {e.label}", lang, 1, None, 2)
        for i in range(1, count + 1):
            label = ask_text(f"{tr('char_name', lang)} {i}", f"Charakter {i}")
            out.append(Character(f"{e.id}_char{i:02d}", label, e.id))
    return out


def choose_mode(lang: str) -> str:
    header(tr("mode_header", lang))

    explanations = {
        "german": {
            "intro": "Wähle nur, wie die Reihenfolge sortiert werden soll.",
            "m1": "1. Emulator nacheinander",
            "m1_lines": [
                "Erst wird Emulator 1 komplett abgearbeitet.",
                "Danach kommt Emulator 2.",
                "Gut, wenn ein Emulator erst fertig sein soll, bevor der nächste dran ist.",
            ],
            "m2": "2. Gleiche Queue zuerst überall",
            "m2_lines": [
                "Erst läuft Queue 1 auf allen gewählten Emulatoren/Charakteren.",
                "Danach läuft Queue 2 auf allen gewählten Emulatoren/Charakteren.",
                "Gut, wenn beide Emulatoren denselben Task-Block zusammen machen sollen.",
            ],
            "example": "Beispiel",
            "recommend": "Empfehlung: Für 2 Emulatoren meistens 2 wählen.",
        },
        "english": {
            "intro": "Choose only how the order should be sorted.",
            "m1": "1. One emulator after another",
            "m1_lines": [
                "Finish Emulator 1 completely first.",
                "Then continue with Emulator 2.",
                "Good if one emulator should be done before the next starts.",
            ],
            "m2": "2. Same queue everywhere first",
            "m2_lines": [
                "Run Queue 1 on all selected emulators/characters first.",
                "Then run Queue 2 on all selected emulators/characters.",
                "Good if both emulators should do the same task block together.",
            ],
            "example": "Example",
            "recommend": "Recommendation: For 2 emulators, usually choose 2.",
        },
        "french": {
            "intro": "Choisis seulement comment trier l’ordre.",
            "m1": "1. Un émulateur après l’autre",
            "m1_lines": [
                "Termine d’abord complètement l’émulateur 1.",
                "Ensuite passe à l’émulateur 2.",
                "Bien si un émulateur doit finir avant le suivant.",
            ],
            "m2": "2. Même queue partout d’abord",
            "m2_lines": [
                "Queue 1 tourne d’abord sur tous les émulateurs/personnages choisis.",
                "Puis Queue 2 tourne sur tous les émulateurs/personnages choisis.",
                "Bien si les deux émulateurs doivent faire le même bloc de tâches.",
            ],
            "example": "Exemple",
            "recommend": "Recommandation : pour 2 émulateurs, choisir 2 en général.",
        },
        "espanol": {
            "intro": "Elige solo cómo se ordena el trabajo.",
            "m1": "1. Un emulador tras otro",
            "m1_lines": [
                "Primero termina completamente el emulador 1.",
                "Luego continúa con el emulador 2.",
                "Útil si un emulador debe terminar antes de empezar el siguiente.",
            ],
            "m2": "2. La misma queue primero en todos",
            "m2_lines": [
                "Queue 1 se ejecuta primero en todos los emuladores/personajes elegidos.",
                "Después Queue 2 se ejecuta en todos los emuladores/personajes elegidos.",
                "Útil si ambos emuladores deben hacer el mismo bloque de tareas.",
            ],
            "example": "Ejemplo",
            "recommend": "Recomendación: con 2 emuladores, normalmente elige 2.",
        },
        "polski": {
            "intro": "Wybierz tylko sposób sortowania kolejności.",
            "m1": "1. Jeden emulator po drugim",
            "m1_lines": [
                "Najpierw cały Emulator 1.",
                "Potem Emulator 2.",
                "Dobre, gdy jeden emulator ma skończyć przed następnym.",
            ],
            "m2": "2. Ta sama kolejka najpierw wszędzie",
            "m2_lines": [
                "Najpierw Queue 1 na wszystkich wybranych emulatorach/postaciach.",
                "Potem Queue 2 na wszystkich wybranych emulatorach/postaciach.",
                "Dobre, gdy oba emulatory mają robić ten sam blok zadań razem.",
            ],
            "example": "Przykład",
            "recommend": "Rekomendacja: dla 2 emulatorów zwykle wybierz 2.",
        },
        "russian": {
            "intro": "Выбери только порядок сортировки работы.",
            "m1": "1. Один эмулятор за другим",
            "m1_lines": [
                "Сначала полностью Эмулятор 1.",
                "Потом Эмулятор 2.",
                "Хорошо, если один эмулятор должен закончить до следующего.",
            ],
            "m2": "2. Одна очередь сначала везде",
            "m2_lines": [
                "Сначала Queue 1 на всех выбранных эмуляторах/персонажах.",
                "Потом Queue 2 на всех выбранных эмуляторах/персонажах.",
                "Хорошо, если оба эмулятора делают один и тот же блок задач.",
            ],
            "example": "Пример",
            "recommend": "Рекомендация: для 2 эмуляторов обычно выбирай 2.",
        },
    }

    e = explanations.get(lang, explanations["english"])
    print(gray(e["intro"]))
    print()

    print(bold_gray(e["m1"]))
    for line in e["m1_lines"]:
        print(gray("   " + line))
    print(gray("   " + e["example"] + ":"))
    print(gray("     E1 C1 Q1 -> E1 C2 Q1 -> E1 C1 Q2 -> E1 C2 Q2 -> E2 ..."))
    print()

    print(bold_gray(e["m2"]))
    for line in e["m2_lines"]:
        print(gray("   " + line))
    print(gray("   " + e["example"] + ":"))
    print(gray("     E1 C1 Q1 -> E1 C2 Q1 -> E2 C1 Q1 -> E2 C2 Q1 -> Q2 ..."))
    print()

    print(bold_white(e["recommend"]))
    print()

    choice = ask_int(tr("choose_mode", lang), lang, 1, 2, 2)
    return "emulator_local_queue_cycle" if choice == 1 else "multi_emulator_parallel_queue"


def print_tasks(tasks: Sequence[TaskDefinition], lang: str) -> None:
    group = None
    for idx, t in enumerate(tasks, 1):
        if t.group != group:
            group = t.group
            print("\n" + bold_white(f"[{group}]"))
        status = tr("found", lang) if t.scan_hits else tr("canonical", lang)
        print(bold_gray(f"{idx:2d}.") + gray(f" {t.label} ({status})"))


def queue_wrapper_tasks() -> List[str]:
    return ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts']

def unique_task_ids(items: Sequence[str]) -> List[str]:
    out: List[str] = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def queue_preset_layout(count: int) -> List[Tuple[str, List[str]]]:
    presets_by_count: Dict[int, List[Tuple[str, List[str]]]] = {
        4: [
            ('Queue1 Alliance + Gathering Core', ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts', 'alliance_gathering', 'gathering_boost', 'resource_gathering', 'pit_gather']),
            ('Queue2 Base + Military Maintenance', ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts', 'shield', 'hq_upgrading', 'building_upgrading', 'research', 'wall_repair', 'trap_crafting', 'troop_training', 'troop_healing', 'tavern_recruitment', 'skills']),
            ('Queue3 Economy + Inventory Utility', ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts', 'game_gifts', 'bag_items', 'supply_depot', 'bank_investment', 'ruins']),
            ('Queue4 Final Rewards + Puzzle + Zombies', ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts', 'campaign_puzzle_auto', 'campaign_puzzle_general', 'dynamic_base_puzzles', 'duel_survival', 'pit_attack', 'zombies_40', 'quest_rewards']),
        ],
        5: [
            ('Queue1 Alliance', ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts', 'alliance_gathering', 'gathering_boost', 'resource_gathering']),
            ('Queue2 Base Maintenance', ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts', 'shield', 'hq_upgrading', 'building_upgrading', 'research', 'wall_repair', 'trap_crafting']),
            ('Queue3 Military', ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts', 'troop_training', 'troop_healing', 'tavern_recruitment', 'skills']),
            ('Queue4 Rewards Inventory Economy', ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts', 'game_gifts', 'bag_items', 'supply_depot', 'bank_investment', 'ruins', 'pit_gather']),
            ('Queue5 Final Quest Rewards + Puzzle/Zombies', ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts', 'campaign_puzzle_auto', 'campaign_puzzle_general', 'dynamic_base_puzzles', 'duel_survival', 'pit_attack', 'zombies_40', 'quest_rewards']),
        ],
        6: [
            ('Queue1 Alliance Research + Gifts + Gathering', ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts', 'alliance_gathering', 'gathering_boost', 'resource_gathering']),
            ('Queue2 Base Maintenance', ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts', 'shield', 'hq_upgrading', 'building_upgrading', 'research', 'wall_repair', 'trap_crafting']),
            ('Queue3 Military', ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts', 'troop_training', 'troop_healing', 'tavern_recruitment', 'skills']),
            ('Queue4 Resources / Economy', ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts', 'resource_gathering', 'gathering_boost', 'alliance_gathering', 'supply_depot', 'bank_investment', 'pit_gather']),
            ('Queue5 Rewards / Inventory / Puzzle', ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts', 'game_gifts', 'bag_items', 'ruins', 'campaign_puzzle_auto', 'campaign_puzzle_general', 'dynamic_base_puzzles', 'duel_survival', 'pit_attack']),
            ('Queue6 Final Quest Rewards + Zombies 40', ['speedup_help', 'nova_daily_praise', 'nova_research', 'noah_tavern', 'radio_quiz', 'collect_base_resources', 'alliance_research', 'alliance_gifts', 'zombies_40', 'quest_rewards']),
        ],
    }
    if count <= 4:
        return presets_by_count[4][:count]
    if count == 5:
        return presets_by_count[5]
    return presets_by_count[6][:min(count, 6)]
def print_queue_recommendations(lang: str) -> None:
    messages = {
        "german": [
            "Empfehlung: 4-6 Queues. Direkt-Eingabe ist jetzt möglich: Q1, Q2, Q3 ...",
            "",
            "Wrapper in jedem Queue-Block:",
            "  Speedup Help + Nova Daily > Praise + Nova Research + Noah Tavern + Radio Quiz",
            "  Collect Base Resources: Serum/Food/Wood/Steel/Gas + Antiserum-Limit bestätigen",
            "  Alliance > Research + Alliance > Gifts",
            "",
            "Buff-Regeln:",
            "  Shield: Buff > Shield > 2hr + shield_on_everyday + Gathering Search Menu",
            "  Gather Speedup: Buff > Gather Speedup + Gathering Search Menu + Alliance Gathering",
            "",
            "4 Queues = kompakt:",
            "  Q1 Alliance + Gathering Wrapper",
            "  Q2 Base + Military Maintenance Wrapper",
            "  Q3 Economy + Inventory Utility Wrapper",
            "  Q4 Final Rewards + Puzzle + Zombies",
            "",
            "5 Queues = besser:",
            "  Q1 Alliance Wrapper",
            "  Q2 Base Maintenance Wrapper",
            "  Q3 Military Wrapper",
            "  Q4 Rewards Inventory Economy Wrapper",
            "  Q5 Final Quest Rewards + Puzzle/Zombies",
            "",
            "6 Queues = sauber/profi:",
            "  Q1 Alliance Research + Gifts + Gathering",
            "  Q2 Base Maintenance",
            "  Q3 Military",
            "  Q4 Resources / Economy",
            "  Q5 Rewards / Inventory / Puzzle",
            "  Q6 Final Quest Rewards + Zombies 40",
            "",
            "Regel: Collect Quest Rewards wird nur in die letzte Queue eingefügt.",
            "Zombies: max Level 40. Zombies 39-59 wurde entfernt; korrekt ist 39-40 oder Zombies 40.",
        ],
        "english": [
            "Recommendation: 4-6 queues. Direct input is supported: Q1, Q2, Q3 ...",
            "Repeatable wrapper is added to each preset queue.",
            "Collect Quest Rewards is only inserted into the final queue.",
            "Zombies max level is 40.",
        ],
    }
    for line in messages.get(lang, messages["english"]):
        if not line:
            print()
        elif line.endswith(":") or line.startswith(("Empfehlung", "Recommendation", "Regel", "Zombies")):
            print(bold_white(line))
        else:
            print(gray(line))


def task_ids_to_indexes(task_ids: Sequence[str], tasks: Sequence[TaskDefinition]) -> List[int]:
    pos = {t.id: idx + 1 for idx, t in enumerate(tasks)}
    out: List[int] = []
    for tid in task_ids:
        if tid in pos and pos[tid] not in out:
            out.append(pos[tid])
    return out


def ask_queue_selection(prompt: str, q_number: int, count: int, tasks: Sequence[TaskDefinition], lang: str) -> Tuple[str, List[int]]:
    presets = queue_preset_layout(count)
    preset_map: Dict[str, Tuple[str, List[str]]] = {}
    for idx, preset in enumerate(presets, 1):
        preset_map[f"q{idx}"] = preset
        preset_map[f"queue{idx}"] = preset
        preset_map[str(idx) if False else f"preset{idx}"] = preset

    while True:
        hint = tr("select_hint", lang) + ", Q1/Q2/auto"
        raw = input(format_prompt(f"{prompt} ({hint}): ")).strip()
        key = raw.strip().lower()

        if key in {"", "auto", "preset", "standard", "default"}:
            key = f"q{q_number}"

        if key in preset_map:
            label, ids = preset_map[key]
            indexes = task_ids_to_indexes(ids, tasks)
            if indexes:
                print(green(f"Preset {key.upper()} übernommen: {label}"))
                return label, indexes
            print(f"{tr('invalid_select', lang)}: {raw}")
            continue

        try:
            return f"Queue{q_number}", parse_select(raw, len(tasks), lang)
        except ValueError as exc:
            print(exc)


def choose_queues(tasks: Sequence[TaskDefinition], lang: str) -> List[QueueDefinition]:
    header(tr("tasks_header", lang))
    print_tasks(tasks, lang)
    print()
    print_queue_recommendations(lang)
    count = ask_int("\n" + tr("queues_count", lang), lang, 1, None, 4)
    queues: List[QueueDefinition] = []
    for q in range(1, count + 1):
        label, selected = ask_queue_selection(tr("queue_tasks", lang, n=q), q, count, tasks, lang)
        queues.append(QueueDefinition(f"queue{q}", label, [tasks[i - 1].id for i in selected]))
    return queues


def build_assignments(emulators: Sequence[Emulator], chars: Sequence[Character], queues: Sequence[QueueDefinition], mode: str) -> List[Assignment]:
    by_emu: Dict[str, List[Character]] = {e.id: [] for e in emulators}
    for c in chars:
        by_emu.setdefault(c.emulator_id, []).append(c)
    out: List[Assignment] = []
    order = 1
    if mode == "emulator_local_queue_cycle":
        for e in emulators:
            for q in queues:
                for c in by_emu.get(e.id, []):
                    out.append(Assignment(order, e.id, c.id, q.id, mode)); order += 1
    else:
        for q in queues:
            for e in emulators:
                for c in by_emu.get(e.id, []):
                    out.append(Assignment(order, e.id, c.id, q.id, mode)); order += 1
    return out


def build_config(roots: Sequence[Path], detected: Sequence[Emulator], selected: Sequence[Emulator], chars: Sequence[Character], tasks: Sequence[TaskDefinition], queues: Sequence[QueueDefinition], assignments: Sequence[Assignment], mode: str, lang: str) -> Dict[str, Any]:
    return {
        "version": VERSION,
        "created_at": now_iso(),
        "language": lang,
        "lssbot_roots": [str(p) for p in roots],
        "scheduling_mode": mode,
        "emulators": {"detected": [asdict(e) for e in detected], "selected": [asdict(e) for e in selected]},
        "characters": [asdict(c) for c in chars],
        "queues": [asdict(q) for q in queues],
        "assignments": [asdict(a) for a in assignments],
        "tasks": {t.id: {"id": t.id, "label": t.label, "group": t.group, "aliases": t.aliases, "settings": t.settings, "scan_hits": t.scan_hits, "scan_status": "found_in_lssbot_files" if t.scan_hits else "canonical_default_not_found_in_scan"} for t in tasks},
        "task_split_rules": {
            "Alliance": ["alliance_research", "alliance_gifts", "alliance_gathering", "alliance_activities_generic"],
            "Pit": ["pit_gather", "pit_attack"],
            "Campaign Puzzle": ["campaign_puzzle_auto", "campaign_puzzle_general", "dynamic_base_puzzles", "duel_survival"],
            "Resources": ["resource_gathering", "gathering_boost", "supply_depot"],
            "Base": ["building_upgrading", "hq_upgrading", "research", "wall_repair", "trap_crafting", "shield"],
            "Military": ["troop_training", "troop_healing", "tavern_recruitment", "skills"],
            "Rewards": ["quest_rewards", "game_gifts", "bag_items", "bank_investment", "radio_quiz", "ruins"],
            "Zombies": "20-40 through 39-40 plus 40 alone; max level 40",
        },
        "task_resolution_version": "wulfpack_0.0.8_full_subtask_catalog",
        "queue_preset_policy": "4/5/6 queue templates; Q1/Q2 direct input; Quest Rewards only in final queue",
        "official_task_catalog_source": "LSS-Bot Puzzles & Survival feature list",
        "mapping_note": "split_confirmed tasks have concrete rules; official_generic tasks are catalog-mapped pending exact local LSS-Bot field metadata.",
        "safety": {"patches_lssbot_files": False, "requires_backup_before_real_patch": True},
    }


def plan_text(config: Dict[str, Any]) -> str:
    emu = {e["id"]: e for e in config["emulators"]["selected"]}
    chars = {c["id"]: c for c in config["characters"]}
    queues = {q["id"]: q for q in config["queues"]}
    tasks = config["tasks"]
    lines = [f"LSS Character Queue v{config['version']} FINAL", f"Created: {config['created_at']}", f"Language: {config['language']}", f"Mode: {config['scheduling_mode']}", ""]
    lines.append("Selected emulators:")
    for e in config["emulators"]["selected"]:
        serial = f" | ADB={e.get('adb_serial')}" if e.get("adb_serial") else ""
        lines.append(f"- {e['id']}: {e['label']}{serial}")
    lines.append("\nQueues:")
    for q in config["queues"]:
        lines.append(f"- {q['label']}:")
        for tid in q["tasks"]:
            task = tasks[tid]
            lines.append(f"  - {task['label']}")
            subtasks = task.get("settings", {}).get("expanded_subtasks", [])
            for sub in subtasks[:8]:
                lines.append(f"      · {sub}")
            opts = task.get("settings", {}).get("options", {})
            if opts:
                lines.append(f"      options: {json.dumps(opts, ensure_ascii=False)}")
    lines.append("\nExecution order:")
    for a in config["assignments"]:
        lines.append(f"{a['order']:03d}. {emu[a['emulator_id']]['label']} | {chars[a['character_id']]['label']} | {queues[a['queue_id']]['label']}")
    lines.append("\nSplit-task defaults:")
    for tid in ["alliance_research", "alliance_gifts", "alliance_gathering", "pit_gather", "pit_attack", "campaign_puzzle_auto", "campaign_puzzle_general", "zombies_20_40", "zombies_39_40", "zombies_40"]:
        if tid in tasks:
            lines.append(f"- {tasks[tid]['label']}: {json.dumps(tasks[tid]['settings'], ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def write_outputs(config: Dict[str, Any], outdir: Path) -> Tuple[Path, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    jp = outdir / CONFIG_BASENAME
    pp = outdir / PLAN_BASENAME
    jp.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    pp.write_text(plan_text(config), encoding="utf-8")
    return jp, pp


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LSS Character Queue v5.0 FINAL multilingual generator")
    p.add_argument("--lang", default="german", help="english,german,french,espanol,polski,russian or comma-list menu")
    p.add_argument("--emulator-type", default="auto", help="auto, ldplayer9, ldplayer5, ldplayer4, ldplayer14, memu, nox")
    p.add_argument("--lssbot-root", action="append", default=[], help="Additional LSS-Bot root folder to scan")
    p.add_argument("--scan-current-dir", action="store_true", help="Also scan current folder; disabled by default to avoid self-scan false positives")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    p.add_argument("--output-dir", default=str(Path.home() / "lss_character_queue_v5_final"), help="Output folder")
    p.add_argument("--non-interactive", action="store_true", help="Create default config without prompts")
    return p.parse_args(argv)


def noninteractive(detected: List[Emulator], tasks: List[TaskDefinition]) -> Tuple[List[Emulator], List[Character], str, List[QueueDefinition]]:
    selected = detected[:1] if detected else [Emulator("emu01", "Emulator 1", None, "manual")]
    chars = [Character(f"{selected[0].id}_char01", "Charakter 1", selected[0].id), Character(f"{selected[0].id}_char02", "Charakter 2", selected[0].id)]
    valid = {t.id for t in tasks}
    presets = queue_preset_layout(4)
    qs = []
    for idx, (label, ids) in enumerate(presets, 1):
        qs.append(QueueDefinition(f"queue{idx}", label, [x for x in ids if x in valid]))
    return selected, chars, "multi_emulator_parallel_queue", qs


def main(argv: Sequence[str]) -> int:
    global COLOR_ENABLED
    args = parse_args(argv)
    COLOR_ENABLED = not getattr(args, "no_color", False)
    enable_windows_ansi()
    lang = resolve_language(args.lang)
    set_active_lang(lang)
    install_cancel_handler(lang)
    program_banner()
    extra_roots = list(args.lssbot_root)
    if getattr(args, "scan_current_dir", False):
        extra_roots.append(".")
    roots = candidate_roots(extra_roots)
    print(gray(tr("scan_roots", lang) + ":"))
    for root in roots:
        print(gray("- ") + blue(str(root)))
    emulator_type = normalize_emulator_type(getattr(args, "emulator_type", "auto"))
    print(gray(ui_text("selected_emulator_type", lang, value=emulator_type_label(emulator_type))), flush=True)
    print(gray(ui_text("fast_scan", lang)), flush=True)
    progress_step("start live scan")

    # Important: detect emulator names first. This avoids looking stuck in task/log scan
    # before the user even sees the LDPlayer/LSS-Bot instance mapping.
    progress_step("phase 1/4: vendor CLI instance discovery")
    cli_emulators = scan_emulators_cli(emulator_type)

    progress_step("phase 2/4: ADB discovery")
    adb_emulators = scan_emulators_adb(roots)

    if cli_emulators:
        progress_ok("phase 3/4 skipped: vendor CLI already returned exact emulator instance names")
        file_emulators = []
    else:
        progress_step("phase 3/4: LSS-Bot log/config emulator-name discovery")
        file_emulators = scan_emulators_files(roots)

    progress_step("merge emulator results")
    detected = merge_emulators(adb_emulators + cli_emulators, file_emulators)
    progress_ok(f"emulator live scan finished: {len(detected)} emulator candidate(s)")

    progress_step("phase 4/4: task discovery")
    tasks = scan_tasks(roots, build_tasks())
    progress_ok("full live scan finished")
    if args.non_interactive:
        selected, chars, mode, queues = noninteractive(detected, tasks)
    else:
        selected = choose_emulators(detected, lang)
        chars = choose_characters(selected, lang)
        mode = choose_mode(lang)
        queues = choose_queues(tasks, lang)
    assignments = build_assignments(selected, chars, queues, mode)
    config = build_config(roots, detected, selected, chars, tasks, queues, assignments, mode, lang)
    jp, pp = write_outputs(config, Path(args.output_dir).expanduser().resolve())
    header(tr("done", lang))
    print(gray(f"{tr('json_written', lang)}: ") + blue(str(jp)))
    print(gray(f"{tr('plan_written', lang)}: ") + blue(str(pp)))
    print("\n" + bold_gray(tr("next_step", lang) + ":"))
    print(gray(tr("next_step_text", lang)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
