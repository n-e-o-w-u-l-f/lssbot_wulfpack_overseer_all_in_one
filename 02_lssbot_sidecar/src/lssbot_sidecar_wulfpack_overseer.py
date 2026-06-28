#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LSSBot Sidecar Wulfpack Overseer v0.0.8

Lokaler Begleitprozess für LSS Bot:
- schreibt zz_TASK_CHAIN_ACTIVE.json
- startet/stoppt LSS Bot.exe
- überwacht LSS-Logs
- HARD-STOPPT LSS sofort, wenn Account Switcher den letzten Account meldet
- erkennt Cooldown-/Account-ID-0-Endlosloop nach dem letzten Account
- kann vorhandene Profil-Warte-/Delay-Felder auf Mindestwerte erhöhen
- sendet deutsche IRC/ZNC-Meldungen

Keine Binary-/JAR-Patches, kein ZNC-Setup.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import glob
import hashlib
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import time
from pathlib import Path
from typing import Any, Dict

VERSION = "0.0.8"


def ts() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def ep(s: str) -> Path:
    return Path(os.path.expandvars(s)).expanduser()


def expanded_log_globs(cfg: Dict[str, Any]) -> list[str]:
    """Config-schonender Logpfad-Fallback.

    Der Nutzer darf die Config unverändert lassen. Zusätzlich zu cfg["log_globs"]
    werden die LSS-Pfade aus den geprüften ZIPs / realen Windows-Pfaden immer
    intern ergänzt. Dadurch verpasst der Sidecar die Logs nicht, wenn LSS sie
    unter AppData\\Local\\lssbot statt Roaming schreibt.
    """
    raw = list(cfg.get("log_globs", []) or [])
    defaults = [
        r"%LOCALAPPDATA%\lssbot\*.log",
        r"%LOCALAPPDATA%\lssbot\logs\*.log",
        r"%LOCALAPPDATA%\lssbot\**\*.log",
        r"%APPDATA%\lssbot_5\logs\*.log",
        r"%APPDATA%\lssbot_5\instances\*\logs\*.log",
        r"%APPDATA%\lssbot_5\*.log",
        r"%APPDATA%\lssbot_5\**\*.log",
        r"%USERPROFILE%\lssbot_5\*.log",
        r"%USERPROFILE%\lssbot_5\logs\*.log",
        r"%USERPROFILE%\lssbot_5\**\*.log",
    ]
    seen = set()
    out = []
    for g in raw + defaults:
        k = str(g).lower()
        if k not in seen:
            seen.add(k)
            out.append(str(g))
    return out


def merged_process_patterns(cfg: Dict[str, Any]) -> None:
    """Ergänzt Stop-/Kill-Muster ohne Config-Dateien zu ändern."""
    pc = cfg.setdefault("process_control", {})
    names = list(pc.get("process_names", ["LSS Bot.exe"]))
    for n in ["LSS Bot.exe"]:
        if n not in names:
            names.append(n)
    pc["process_names"] = names

    target_names = list(pc.get("targeted_process_names", ["java.exe", "javaw.exe", "LSS Bot.exe"]))
    for n in ["java.exe", "javaw.exe", "LSS Bot.exe"]:
        if n not in target_names:
            target_names.append(n)
    pc["targeted_process_names"] = target_names

    pats = list(pc.get("targeted_commandline_patterns", []))
    for p in [
        "lssbot",
        "LSS Bot",
        "lssbot_5",
        "lssbot5.jar",
        "lssbot-client.jar",
        r"\lssbot_5\\",
        "/lssbot_5/",
    ]:
        if p not in pats:
            pats.append(p)
    pc["targeted_commandline_patterns"] = pats


def load_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def write_json(p: Path, data: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(p)


class Audit:
    def __init__(self, path: Path):
        self.path = path

    def __call__(self, msg: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = f"{ts()} {msg}"
        print(line, flush=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


class Redactor:
    def __init__(self, cfg: Dict[str, Any]):
        self.enabled = cfg.get("enabled", True)
        self.rules = [(re.compile(x["regex"]), x["replace"]) for x in cfg.get("patterns", [])]

    def __call__(self, s: str) -> str:
        if not self.enabled:
            return s
        for rx, repl in self.rules:
            s = rx.sub(repl, s)
        return s


class Translator:
    def __init__(self, cfg: Dict[str, Any]):
        self.rules = [(re.compile(x["regex"]), x["message"]) for x in cfg.get("rules", [])]

    def translate(self, s: str):
        for rx, tpl in self.rules:
            m = rx.search(s)
            if m:
                out = tpl
                for i, g in enumerate(m.groups(), 1):
                    out = out.replace("{%d}" % i, g)
                return out
        return None


class IRC:
    def __init__(self, cfg: Dict[str, Any], dry: bool, audit: Audit):
        self.cfg = cfg
        self.dry = dry
        self.audit = audit
        self.sock = None
        self.sent = []

    def pw(self) -> str:
        return os.environ.get(self.cfg.get("password_env", "LSS_IRC_PASSWORD")) or self.cfg.get("password", "")

    def connect(self) -> None:
        if self.dry or self.sock:
            return
        raw = socket.create_connection(
            (self.cfg["server"], int(self.cfg["port"])),
            timeout=int(self.cfg.get("connect_timeout_sec", 15)),
        )
        if self.cfg.get("use_tls"):
            if self.cfg.get("tls_verify", False):
                ctx = ssl.create_default_context()
            else:
                ctx = ssl._create_unverified_context()
                self.audit("[IRC][WARN] TLS-Zertifikatsprüfung deaktiviert; für private/self-signed IRC-Server.")
            self.sock = ctx.wrap_socket(raw, server_hostname=self.cfg["server"])
        else:
            self.sock = raw
        self.sock.settimeout(2)
        if self.pw():
            self.raw("PASS " + self.pw())
        self.raw("NICK " + self.cfg.get("nick", "LSS-Bot"))
        self.raw(
            "USER %s 0 * :%s"
            % (self.cfg.get("username", "lssbot"), self.cfg.get("realname", "LSS Bot Log Relay"))
        )
        time.sleep(1)
        for c in self.cfg.get("channels", []):
            self.raw("JOIN " + c)
        self.audit("[IRC] verbunden")

    def raw(self, line: str) -> None:
        if self.sock:
            self.sock.sendall((line + "\r\n").encode(self.cfg.get("encoding", "utf-8"), errors="replace"))

    def send(self, msg: str) -> None:
        now = time.time()
        self.sent = [x for x in self.sent if now - x < 60]
        if len(self.sent) >= int(self.cfg.get("rate_limit_messages_per_minute", 90)):
            return
        msg = msg[: int(self.cfg.get("message_max_len", 390))]
        if self.dry:
            self.audit("[DRY-RUN][IRC] " + msg)
            return
        try:
            self.connect()
            for c in self.cfg.get("channels", []):
                self.raw("PRIVMSG %s :%s" % (c, msg))
            self.sent.append(now)
        except Exception as e:
            self.audit("[IRC][ERROR] " + str(e))
            try:
                if self.sock:
                    self.sock.close()
            except Exception:
                pass
            self.sock = None


def install(root: Path, force: bool = False) -> None:
    for src, dst in [
        ("sidecar_config.example.json", "sidecar_config.json"),
        ("task_chain.example.json", "task_chain.json"),
        ("irc_config.example.json", "irc_config.json"),
        ("redaction_policy.example.json", "redaction_policy.json"),
        ("translation_de.example.json", "translation_de.json"),
        ("wait_policy.example.json", "wait_policy.json"),
    ]:
        s = root / "config" / src
        d = root / "config" / dst
        if not s.exists():
            continue
        if force or not d.exists():
            shutil.copy2(s, d)
            print("created", d)
        else:
            print("kept", d)


INSTANCE_RX = re.compile(r"^\s*(\d\d:\d\d:\d\d)\s+\[([A-Z]+)\]\s+\(([^)-]+)\s*-\s*([^)]+)\)\s*(.*)$")
NOINST_RX = re.compile(r"^\s*(\d\d:\d\d:\d\d)\s+\[([A-Z]+)\]\s+(.*)$")


def parse_line(line: str):
    s = line.rstrip("\r\n")
    m = INSTANCE_RX.match(s)
    if m:
        t, lvl, inst, emu, rest = m.groups()
        return inst.strip(), f"{t} [{lvl}] {rest}", s
    m = NOINST_RX.match(s)
    if m:
        t, lvl, rest = m.groups()
        return "LSS", f"{t} [{lvl}] {rest}", s
    return "LSS", s, s


class Tailer:
    """
    Robuster LSS-Log-Tailer.

    Fix gegenüber Wulfpack:
    - neue Logdateien nach Taskstart werden ab Byte 0 gelesen, nicht erst ab den letzten 8 KB
    - kritische Zeilen werden zusätzlich aus einem Recent-Scan der letzten 256 KB gelesen
    - alte Zeilen vor mark_end()/Taskstart werden anhand der HH:MM:SS-Zeit ignoriert
    - dadurch wird "Account Switcher ... -5 (Switched to the last account)" auch dann erkannt,
      wenn LSS während des Tasks in eine neue Logdatei rotiert oder der normale Tailer die Zeile
      wegen Dateiauswahl/Position verpasst.
    """
    CRITICAL_RX = re.compile(
        r'Account Switcher".*(?:-5 \(Switched to the last account\)|-2 \(Failed\))'
        r'|Starting from account ID 0'
        r'|Skipped - on cooldown'
        r'|Snapshot error|DISCONNECTED|Timeout getting a response from the device|unable to get the image',
        re.I,
    )

    def __init__(self, globs_, audit: Audit):
        self.globs = globs_
        self.pos = {}
        self.baseline_pos = {}
        self.task_start_epoch = None
        self.audit = audit
        self.marked = False
        self.task_start_sec = None
        self.seen_recent = set()
        self.max_files = 100
        self.recent_bytes = 262144

    def files(self):
        fs = []
        for g in self.globs:
            fs += [Path(x) for x in glob.glob(os.path.expandvars(g), recursive=True)]
        fs = [x for x in fs if x.is_file()]
        fs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return fs[: self.max_files]

    @staticmethod
    def _line_seconds(line: str):
        m = re.match(r"^(\d{2}):(\d{2}):(\d{2})\s+\[", line)
        if not m:
            return None
        h, mi, s = map(int, m.groups())
        return h * 3600 + mi * 60 + s

    def _line_is_after_task_start(self, line: str) -> bool:
        """Ignoriert alte Logzeilen vor Taskstart. Robust genug für gleiche Tages-Logs; mit Mitternachts-Wrap tolerant."""
        if self.task_start_sec is None:
            return True
        ls = self._line_seconds(line)
        if ls is None:
            return True
        start = int(self.task_start_sec)
        # Normalfall gleicher Tag.
        if ls >= start - 2:
            return True
        # Mitternachts-Wrap: Taskstart kurz vor Mitternacht, neue Logzeilen kurz danach.
        if start > 22 * 3600 and ls < 2 * 3600:
            return True
        return False

    @staticmethod
    def _fingerprint(p: Path, line: str) -> str:
        return str(p) + "|" + hashlib.sha1(line.encode("utf-8", "replace")).hexdigest()

    def _normal_read(self):
        out = []
        for p in self.files():
            k = str(p)
            try:
                size = p.stat().st_size
                if k not in self.pos:
                    # Vor mark_end() alter Fallback: nur Ende lesen.
                    # Nach mark_end()/Taskstart: neue Logs komplett ab Anfang lesen,
                    # damit frühe kritische Start-/Last-Account-Zeilen nicht verloren gehen.
                    self.pos[k] = 0 if self.marked else max(0, size - 8192)
                if size < self.pos[k]:
                    self.pos[k] = 0
                with p.open("r", encoding="utf-8", errors="replace") as f:
                    f.seek(self.pos[k])
                    lines = f.readlines()
                    self.pos[k] = f.tell()
                for line in lines:
                    if line.strip() and self._line_is_after_task_start(line):
                        out.append((p,) + parse_line(line))
            except Exception as e:
                self.audit("[LOG][WARN] %s: %s" % (p, e))
        return out

    def _recent_critical_scan(self):
        """Scannt nur den seit mark_end()/Taskstart neu entstandenen Logbereich.

        Wichtig: Frühere Versionen scannten die letzten 256 KB kompletter Logdateien.
        Dadurch wurden alte -2/-5/Cooldown-Zeilen aus vorherigen Runs als aktueller
        Task interpretiert. Diese Version nutzt Byte-Baselines je Datei:
        - existierende Dateien: nur Bytes nach mark_end()
        - neue Dateien nach Taskstart: ab Byte 0
        - alte Dateien ohne Baseline werden ignoriert
        """
        out = []
        for p in self.files():
            try:
                k = str(p)
                st = p.stat()
                size = st.st_size

                if k in self.baseline_pos:
                    start = self.baseline_pos[k]
                    if size < start:
                        # Datei rotiert/trunkiert. Nur als neue Datei akzeptieren, wenn sie wirklich
                        # nach Taskstart geändert wurde.
                        if self.task_start_epoch is None or st.st_mtime < self.task_start_epoch - 2:
                            continue
                        start = 0
                else:
                    # Datei existierte beim Taskstart nicht. Akzeptiere sie nur, wenn sie neu ist.
                    if self.task_start_epoch is None or st.st_mtime < self.task_start_epoch - 2:
                        continue
                    start = 0

                if start >= size:
                    continue

                # Bei sehr großem Zuwachs begrenzen, aber nie vor die Task-Baseline gehen.
                seek_from = max(start, size - self.recent_bytes)
                with p.open("rb") as f:
                    f.seek(seek_from)
                    chunk = f.read().decode("utf-8", errors="replace")

                for line in chunk.splitlines():
                    if not line.strip():
                        continue
                    # Recent-Scan ist nur für echte LSS-Zeilen. Keine Sidecar-/Audit-/IRC-Zeilen.
                    if not re.match(r"^\d{2}:\d{2}:\d{2}\s+\[[A-Z]+\]", line):
                        continue
                    if not self.CRITICAL_RX.search(line):
                        continue
                    if not self._line_is_after_task_start(line):
                        continue
                    fp = self._fingerprint(p, line)
                    if fp in self.seen_recent:
                        continue
                    self.seen_recent.add(fp)
                    out.append((p,) + parse_line(line))
            except Exception as e:
                self.audit("[LOG][WARN] recent-scan %s: %s" % (p, e))
        return out

    def read(self):
        normal = self._normal_read()
        recent = self._recent_critical_scan()
        if recent:
            self.audit("[LOG][RECENT_SCAN] kritische Zeilen nachgezogen: %d" % len(recent))
        return normal + recent

    def mark_end(self) -> None:
        """Setzt vorhandene Logdateien auf EOF und merkt Taskstart für sichere Recent-Scans."""
        now = datetime.datetime.now()
        self.task_start_epoch = time.time()
        self.task_start_sec = now.hour * 3600 + now.minute * 60 + now.second
        self.marked = True
        self.seen_recent.clear()
        self.baseline_pos.clear()
        for p in self.files():
            try:
                size = p.stat().st_size
                self.pos[str(p)] = size
                self.baseline_pos[str(p)] = size
            except Exception as e:
                self.audit("[LOG][WARN] mark_end %s: %s" % (p, e))


ACTIVE_KEYS = ("active", "enabled", "isActive", "selected", "checked")
POS_KEYS = ("position", "order", "index", "priority", "sort", "queuePosition")
NAME_KEYS = (
    "name", "scriptName", "script", "title", "label",
    "displayName", "scriptDisplayName", "executorName", "moduleName",
    "key", "id", "type"
)


def low(xs):
    return {x.strip().lower() for x in xs if isinstance(x, str) and x.strip()}



def script_name(o):
    if not isinstance(o, dict):
        return None
    for k in NAME_KEYS:
        if isinstance(o.get(k), str) and o[k].strip():
            return o[k].strip()
    for k, v in o.items():
        if isinstance(v, str) and 2 <= len(v.strip()) <= 80:
            if any(word in v.lower() for word in (
                "leaderboard","login","gift","supply","alliance","quiz","quest",
                "recruit","nova","gear","depot","bag","research","building",
                "troop","ruins","arena","campaign","gather","zombie","switcher",
                "rally","event"
            )):
                return v.strip()
    return None


def obj_looks_like_script(o):
    if not isinstance(o, dict):
        return False
    keys = {str(k).lower() for k in o.keys()}
    return bool(
        keys.intersection({k.lower() for k in ACTIVE_KEYS + POS_KEYS + NAME_KEYS})
        or keys.intersection({"cooldown","enabled","script","scriptid","executor","settings"})
    )


def _norm_name(s):
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())


def _name_matches(n, wanted_set):
    nl = str(n).strip().lower()
    if nl in wanted_set:
        return True
    nn = _norm_name(nl)
    return any(nn == _norm_name(w) for w in wanted_set)


def mutate_scripts(node, wanted, switchers, writer_cfg=None):
    """
    Aktiviert genau den gewünschten Task + Account Switcher.

    Unterstützte LSS-Formate:
    1) generisch/liste:
       {"scripts":[{"name":"Commend Leaderboard","active":false,"position":99}, ...]}

    2) echtes LSS-Settings-Profil aus der JAR/UI:
       {
         "Commend Leaderboard": {"active": false, "position": 99, "scriptRules": {...}},
         "Account Switcher": {"active": false, "position": 99, "scriptRules": {...}}
       }

    Das zweite Format war der Grund für matched=0/touched=1:
    der Scriptname steht dort als JSON-Key, nicht innerhalb des Objekts.
    """
    writer_cfg = writer_cfg or {}
    add_missing_active = bool(writer_cfg.get("add_missing_active_key", True))
    map_boolean_keys = bool(writer_cfg.get("map_boolean_script_keys", True))
    disable_non_selected = bool(writer_cfg.get("disable_non_selected_scripts", True))

    matched = 0
    touched = 0
    wanted_all = set(wanted) | set(switchers)
    script_words = (
        "leaderboard","login","gift","supply","alliance","quiz","quest","recruit",
        "nova","gear","depot","bag","research","building","troop","ruins","arena",
        "campaign","gather","zombie","switcher","rally","event"
    )

    def key_looks_like_script_name(k: str) -> bool:
        kl = str(k).strip().lower()
        if _name_matches(kl, wanted_all):
            return True
        return any(w in kl for w in script_words)

    def value_looks_like_lss_script_obj(v) -> bool:
        if not isinstance(v, dict):
            return False
        keys = {str(k).lower() for k in v.keys()}
        return bool(
            "active" in keys
            or "position" in keys
            or "scriptrules" in keys
            or keys.intersection({k.lower() for k in ACTIVE_KEYS + POS_KEYS + NAME_KEYS})
        )

    def set_active_fields(x, should):
        nonlocal touched
        has_active = any(k in x for k in ACTIVE_KEYS)
        if has_active:
            for k in ACTIVE_KEYS:
                if k in x:
                    if x[k] != bool(should):
                        touched += 1
                    x[k] = bool(should)
        elif add_missing_active:
            x["active"] = bool(should)
            touched += 1

    def set_position_fields(x, pos):
        nonlocal touched
        for k in POS_KEYS:
            if k in x and isinstance(x[k], int):
                if x[k] != pos:
                    touched += 1
                x[k] = pos

    def apply_script_object_by_name(name, obj, order):
        """Mutiert ein Scriptobjekt, dessen Name aus Key oder Feld bekannt ist."""
        nonlocal matched
        should = _name_matches(name, wanted_all)
        if should or disable_non_selected:
            set_active_fields(obj, should)
            if should:
                if _name_matches(name, wanted):
                    matched += 1
                set_position_fields(obj, order[0])
                order[0] += 1
            return True
        return False

    def rec(x, order):
        nonlocal matched, touched
        if isinstance(x, dict):
            # Echtes LSS-Settings-Format: Scriptname ist der JSON-Key.
            for k, v in list(x.items()):
                if isinstance(k, str) and isinstance(v, dict) and value_looks_like_lss_script_obj(v):
                    if key_looks_like_script_name(k):
                        apply_script_object_by_name(k, v, order)

            # Alternatives flaches Boolean-Format.
            if map_boolean_keys:
                for k in list(x.keys()):
                    kl = str(k).strip().lower()
                    if _name_matches(kl, wanted_all) and isinstance(x[k], bool):
                        if x[k] is not True:
                            touched += 1
                        x[k] = True
                        if _name_matches(kl, wanted):
                            matched += 1
                    elif disable_non_selected and isinstance(x[k], bool) and any(w in kl for w in script_words):
                        if x[k] is not False:
                            touched += 1
                        x[k] = False

            # Generisches Listen-/Objektformat: Scriptname steht im Objekt selbst.
            n = script_name(x)
            if n and obj_looks_like_script(x):
                apply_script_object_by_name(n, x, order)

            for v in x.values():
                rec(v, order)
        elif isinstance(x, list):
            for v in x:
                rec(v, order)

    rec(node, [1])
    return matched, touched



def contains_sidecar_marker(data):
    return isinstance(data, dict) and isinstance(data.get("_lss_sidecar_v4"), dict)


def score_profile_candidate(path: Path, task_names):
    try:
        raw = path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return -1, []
    raw_low = raw.lower()
    hits = []
    for name in task_names:
        if name and name.lower() in raw_low:
            hits.append(name)
    score = len(set(hits)) * 10
    if path.name.lower() in ("farms.json", "mains.json", "default.json"):
        score += 5
    if path.name.lower().startswith("zz_task_chain_active"):
        score -= 100
    if "_lss_sidecar_v4" in raw_low:
        score -= 50
    return score, sorted(set(hits))


def find_base(settings: Path, prefs, cfg=None, chain=None, audit=None):
    cfg = cfg or {}
    active_name = cfg.get("active_profile_name", "zz_TASK_CHAIN_ACTIVE.json").lower()
    excludes = {active_name}
    excludes.update(str(x).lower() for x in cfg.get("base_profile_exclude_names", []))

    for n in prefs:
        if str(n).lower() in excludes:
            continue
        p = settings / n
        if p.exists():
            try:
                if contains_sidecar_marker(load_json(p)):
                    continue
            except Exception:
                pass
            return p

    task_names = []
    if chain:
        for t in chain.get("tasks", []):
            task_names += t.get("script_names", []) + [t.get("name", "")]
        task_names += chain.get("account_switcher", {}).get("script_names", ["Account Switcher"])

    candidates = []
    for p in settings.glob("*.json"):
        if p.name.lower() in excludes or "state" in p.name.lower():
            continue
        score, hits = score_profile_candidate(p, task_names)
        if score > 0:
            candidates.append((score, p, hits))
    candidates.sort(key=lambda x: x[0], reverse=True)
    if candidates:
        if audit:
            audit("[PROFILE][BASE] Auto-Discovery nutzt %s hits=%s" % (candidates[0][1], ",".join(candidates[0][2][:8])))
        return candidates[0][1]

    for p in settings.glob("*.json"):
        if p.name.lower() in excludes or "state" in p.name.lower():
            continue
        try:
            if contains_sidecar_marker(load_json(p)):
                continue
        except Exception:
            pass
        return p
    return None


def scan_profiles(root, cfg_path):
    cfg = load_json(cfg_path)
    chain_path = root / "config/task_chain.json"
    chain = load_json(chain_path) if chain_path.exists() else {"tasks": [], "account_switcher": {}}
    settings = ep(cfg["settings_dir"])
    task_names = []
    for t in chain.get("tasks", []):
        task_names += t.get("script_names", []) + [t.get("name", "")]
    task_names += chain.get("account_switcher", {}).get("script_names", ["Account Switcher"])
    print("LSS SettingsDir:", settings)
    print("Aktives Chain-Profil wird als Basis ausgeschlossen:", cfg.get("active_profile_name", "zz_TASK_CHAIN_ACTIVE.json"))
    rows = []
    for p in sorted(settings.glob("*.json")) if settings.exists() else []:
        score, hits = score_profile_candidate(p, task_names)
        marker = ""
        try:
            if contains_sidecar_marker(load_json(p)):
                marker = "MANAGED_SIDECAR"
        except Exception:
            marker = "JSON_ERROR"
        rows.append((score, p.name, marker, hits[:12]))
    if not rows:
        print("Keine JSON-Profile gefunden.")
        return 2
    rows.sort(reverse=True, key=lambda r: r[0])
    for score, name, marker, hits in rows:
        print(f"{score:4d}  {name:45s} {marker:16s} hits={', '.join(hits)}")
    best = next((r for r in rows if r[0] > 0 and not r[2]), None)
    if best:
        print("\\nEmpfohlenes Basisprofil:", best[1])
        print("Trage es in config/sidecar_config.json unter base_profile_preference ganz vorne ein.")
        return 0
    print("\\nKein Profil mit bekannten Scriptnamen gefunden. In LSS ein echtes Profil mit sichtbarer Scriptliste speichern.")
    return 1


def mutate_waits(node, wait_cfg):
    """Best effort: vorhandene numerische Wait/Delay-Felder im LSS-Profil auf Mindestwerte erhöhen."""
    if not wait_cfg.get("enabled", True):
        return 0
    rules = []
    for r in wait_cfg.get("numeric_key_overrides", []):
        rules.append((re.compile(r["key_regex"], re.I), int(r["min_value"])))
    touched = 0

    def rec(x, path=""):
        nonlocal touched
        if isinstance(x, dict):
            for k, v in list(x.items()):
                keypath = (path + "." + k).strip(".")
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    for rx, minv in rules:
                        if rx.search(k) or rx.search(keypath):
                            if v < minv:
                                x[k] = minv
                                touched += 1
                            break
                else:
                    rec(v, keypath)
        elif isinstance(x, list):
            for i, v in enumerate(x):
                rec(v, f"{path}[{i}]")

    rec(node)
    return touched


def mutate_instance_settings(node, overrides):
    """
    Best effort: Felder aus LSSBotInstanceSettings setzen, wenn sie in einem exportierten/profilbasierten JSON vorkommen.
    Diese Feldnamen wurden aus lssbot5.jar per Bytecode-Inspektion abgeleitet.
    """
    if not overrides or not overrides.get("enabled", True):
        return 0
    values = overrides.get("values", {})
    touched = 0

    def rec(x):
        nonlocal touched
        if isinstance(x, dict):
            for k in list(x.keys()):
                if k in values:
                    if x[k] != values[k]:
                        x[k] = values[k]
                        touched += 1
            for v in x.values():
                rec(v)
        elif isinstance(x, list):
            for v in x:
                rec(v)
    rec(node)
    return touched


def enforce_sidecar_safe_instance_values(node):
    """Code-seitige Sicherheitskorrektur ohne Config-Datei-Änderung.

    Aus den echten Läufen ist ersichtlich, dass LSS den Prozess beenden kann,
    bevor der Sidecar den Taskwechsel sauber steuert, wenn ein Profil/Export
    stopInstanceAfterLoop=true enthält. Der Taskwechsel soll ausschließlich vom
    Sidecar über das Logsignal "Account Switcher ... -5 (Switched to the last account)"
    gesteuert werden. Deshalb erzwingen wir in der geschriebenen aktiven Profilkopie
    immer stopInstanceAfterLoop=false, selbst wenn die Config noch den alten Wert enthält.

    Das ändert keine Config-Datei und hält VERSION unverändert.
    """
    touched = 0

    def rec(x):
        nonlocal touched
        if isinstance(x, dict):
            for k in list(x.keys()):
                if str(k) == "stopInstanceAfterLoop":
                    if x[k] is not False:
                        x[k] = False
                        touched += 1
            for v in x.values():
                rec(v)
        elif isinstance(x, list):
            for v in x:
                rec(v)
    rec(node)
    return touched



def apply_profile(cfg, chain, task, dry, audit, root: Path):
    settings = ep(cfg["settings_dir"])
    settings.mkdir(parents=True, exist_ok=True)
    active = settings / cfg.get("active_profile_name", "zz_TASK_CHAIN_ACTIVE.json")
    base = find_base(settings, cfg.get("base_profile_preference", []), cfg=cfg, chain=chain, audit=audit)
    if not base:
        raise RuntimeError("Kein LSS-Basisprofil in %s gefunden" % settings)

    data = copy.deepcopy(load_json(base))
    matched, touched = mutate_scripts(
        data,
        low(task.get("script_names", []) + [task.get("name", "")]),
        low(chain["account_switcher"].get("script_names", ["Account Switcher"])),
        cfg.get("profile_writer", {}),
    )

    wait_touched = 0
    wait_file = root / cfg.get("wait_policy", {}).get("config_file", "config/wait_policy.json")
    if wait_file.exists():
        wait_touched = mutate_waits(data, load_json(wait_file))

    instance_touched = mutate_instance_settings(data, cfg.get("lss_instance_settings_overrides", {}))
    safe_instance_touched = enforce_sidecar_safe_instance_values(data)

    data["_lss_sidecar_v4"] = {
        "managed": True,
        "version": VERSION,
        "task_id": task["id"],
        "task_name": task["name"],
        "written_at": ts(),
        "base_profile": str(base),
        "matched_scripts": matched,
        "touched_script_fields": touched,
        "touched_wait_fields": wait_touched,
        "touched_instance_fields": instance_touched,
        "touched_safe_instance_fields": safe_instance_touched,
    }

    if dry:
        audit(
            "[DRY-RUN][PROFILE] würde %s schreiben: Task %02d %s matched=%d touched=%d wait_touched=%d instance_touched=%d safe_instance_touched=%d"
            % (active, task["id"], task["name"], matched, touched, wait_touched, instance_touched, safe_instance_touched)
        )
        return matched, touched, wait_touched

    if active.exists():
        b = settings / "_sidecar_backups"
        b.mkdir(exist_ok=True)
        shutil.copy2(active, b / (active.name + "." + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".bak"))
    write_json(active, data)
    audit(
        "[PROFILE] geschrieben: %s Task %02d %s matched=%d touched=%d wait_touched=%d instance_touched=%d safe_instance_touched=%d"
        % (active, task["id"], task["name"], matched, touched, wait_touched, instance_touched, safe_instance_touched)
    )
    return matched, touched, wait_touched


def freeze_active_profile(cfg, audit, reason=""):
    """Sicherheitsbremse: aktives Profil so schreiben, dass keine Task-Scripts aktiv bleiben.

    Das ersetzt NICHT den Prozess-Stop, verhindert aber nach einem Neustart/Restloop,
    dass erneut Task 1 aus dem alten aktiven Profil losläuft. Config bleibt unverändert.
    """
    try:
        settings = ep(cfg["settings_dir"])
        active = settings / cfg.get("active_profile_name", "zz_TASK_CHAIN_ACTIVE.json")
        if not active.exists():
            return
        data = load_json(active)
        # Alle Script-Objekte deaktivieren; Account Switcher ebenfalls.
        def rec(x):
            if isinstance(x, dict):
                # LSS-Root-Key Format und generische Objekte.
                if obj_looks_like_script(x) or any(str(k).lower() in ("active","enabled","position","scriptrules") for k in x.keys()):
                    for k in ACTIVE_KEYS:
                        if k in x:
                            x[k] = False
                for v in x.values():
                    rec(v)
            elif isinstance(x, list):
                for v in x:
                    rec(v)
        rec(data)
        data.setdefault("_lss_sidecar_v4", {})
        data["_lss_sidecar_v4"]["frozen_at"] = ts()
        data["_lss_sidecar_v4"]["freeze_reason"] = reason
        write_json(active, data)
        audit("[PROFILE][FREEZE] aktives Profil deaktiviert reason=%s" % reason)
    except Exception as e:
        audit("[PROFILE][FREEZE][WARN] %s" % e)


class Proc:
    def __init__(self, cfg, dry, audit):
        self.cfg = cfg
        self.dry = dry
        self.audit = audit

    def start(self):
        exe = ep(self.cfg["lss_exe_path"])
        if self.dry:
            self.audit("[DRY-RUN][PROCESS] würde starten: " + str(exe))
            return
        if not exe.exists():
            raise RuntimeError("LSS exe fehlt: " + str(exe))
        self.audit("[PROCESS] starte LSS")
        subprocess.Popen([str(exe)], cwd=str(exe.parent))
        time.sleep(float(self.cfg["process_control"].get("start_wait_sec", 12)))

    def _run(self, args, timeout=15):
        try:
            return subprocess.run(args, capture_output=True, text=True, timeout=timeout, shell=False)
        except Exception as e:
            self.audit("[PROCESS][WARN] %s" % (e,))
            return None

    def stop(self, hard=False, reason=""):
        pc = self.cfg["process_control"]
        names = list(pc.get("process_names", ["LSS Bot.exe"]))
        if hard:
            names += list(pc.get("hard_stop_extra_image_names", []))
        seen = set()
        names = [n for n in names if not (n.lower() in seen or seen.add(n.lower()))]

        if self.dry:
            mode = "HARD" if hard else "NORMAL"
            self.audit("[DRY-RUN][PROCESS][%s] würde stoppen: %s reason=%s" % (mode, ", ".join(names), reason))
            return

        mode = "HARD" if hard else "NORMAL"
        self.audit("[PROCESS][%s] stoppe LSS reason=%s" % (mode, reason))

        for n in names:
            args = ["taskkill"]
            if hard or pc.get("force_kill_after_timeout", True):
                args.append("/F")
            args += ["/IM", n, "/T"]
            self._run(args, timeout=10)

        if pc.get("targeted_commandline_kill", True):
            pats = pc.get("targeted_commandline_patterns", ["lssbot", "LSS Bot", "lssbot_5"])
            proc_names = pc.get("targeted_process_names", ["java.exe", "javaw.exe", "LSS Bot.exe"])
            ps_patterns = ",".join("'" + p.replace("'", "''") + "'" for p in pats)
            ps_names = ",".join("'" + p.replace("'", "''") + "'" for p in proc_names)
            ps = f"""
$patterns = @({ps_patterns})
$names = @({ps_names})
Get-CimInstance Win32_Process | ForEach-Object {{
  $cmd = [string]$_.CommandLine
  $name = [string]$_.Name
  $matchName = $false
  foreach($n in $names){{ if($name -ieq $n){{ $matchName = $true }} }}
  if(-not $matchName){{ return }}
  foreach($p in $patterns){{
    if($cmd -like "*$p*"){{
      try {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }} catch {{}}
      return
    }}
  }}
}}
"""
            self._run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], timeout=15)

        if not hard:
            time.sleep(float(pc.get("graceful_stop_timeout_sec", 8)))
            if pc.get("force_kill_after_timeout", True):
                for n in names:
                    self._run(["taskkill", "/F", "/IM", n, "/T"], timeout=10)
        time.sleep(float(pc.get("hard_stop_post_wait_sec", 2) if hard else pc.get("post_stop_wait_sec", 4)))
        self.audit("[PROCESS][%s] Stop-Befehl fertig" % mode)




# ---------------------------------------------------------------------------
# Wulfpack Queue Import
# ---------------------------------------------------------------------------

QUEUE_SEARCH_CANDIDATES = [
    r"%LSS_QUEUE_JSON%",
    r"%USERPROFILE%\lss_character_queue_v5_final\lss_character_queue_v5_final.generated.json",
    r"%USERPROFILE%\lss_character_queue_v1_337a\lss_character_queue_v1_337a.generated.json",
    r"%USERPROFILE%\Desktop\lss_character_queue_v5_final_multilang\lss_character_queue_v5_final.generated.json",
    r"%USERPROFILE%\Desktop\lss_character_queue_v5_final_multilang\lss_character_queue_v1_337a.generated.json",
]

QUEUE_TO_LSS_ALIASES = {
    "alliance_research": ["Alliance Donate", "Alliance Tech", "Alliance Research"],
    "alliance_gifts": ["Alliance Gifts", "Alliance Gift"],
    "alliance_gathering": ["Alliance Gathering", "Alliance Gather", "Gather", "Gather Resources"],
    "alliance_activities_generic": ["Alliance Help", "Alliance Activities", "Alliance"],

    "pit_gather": ["Pit", "Arena", "Pit Arena", "Pit Gather"],
    "pit_attack": ["Pit", "Arena", "Pit Arena", "Pit Attack"],

    "campaign_puzzle_auto": ["Campaign Puzzle", "Campaign", "Campaign Puzzle Auto"],
    "campaign_puzzle_general": ["Campaign Puzzle", "Campaign", "Campaign Puzzle General"],
    "dynamic_base_puzzles": ["Dynamic Base Puzzles", "Base Puzzles", "Campaign Puzzle", "Campaign"],
    "duel_survival": ["Duel Survival", "Duel"],

    "resource_gathering": ["Gather", "Gather Resources", "Resource Gathering", "Collect Resources"],
    "gathering_boost": ["Buffs", "Skills", "Dispatch", "Gathering Boost"],
    "supply_depot": ["Supply Depot"],

    "building_upgrading": ["Building Upgrade", "Upgrade Building", "Building Upgrading"],
    "hq_upgrading": ["HQ Upgrade", "Headquarters Upgrade", "Building Upgrade"],
    "research": ["Research"],
    "wall_repair": ["Trap", "Wall Repair"],
    "trap_crafting": ["Trap", "Wall Trap Repair"],
    "shield": ["Shield"],

    "troop_training": ["Troop Training", "Train Troops"],
    "troop_healing": ["Heal", "Infirmary", "Troop Healing"],
    "tavern_recruitment": ["Recruit Free", "Noah's Tavern", "Noahs Tavern", "Tavern Recruitment"],
    "skills": ["Buffs", "Skills", "Dispatch"],

    "quest_rewards": ["Quest Rewards", "Quest Reward"],
    "game_gifts": ["Game Gifts", "Game Gift"],
    "bag_items": ["Bag Cleanup", "Use Items", "Bag Items"],
    "bank_investment": ["Bank Investment", "Bank"],
    "radio_quiz": ["Radio Quiz"],
    "ruins": ["Clearing the Ruins", "Ruins"],

    "speedup_help": ["Speedup Help", "Alliance Help", "Help Speedups"],
    "nova_daily_praise": ["Nova Daily", "Praise", "Nova Daily Praise"],
    "nova_research": ["Nova Research", "Nova"],
    "noah_tavern": ["Noah's Tavern", "Noahs Tavern", "Noah Tavern", "Tavern Recruitment"],
    "collect_base_resources": ["Collect Base Resources", "Base Resources", "Collect Resources", "Antiserum Storage"],
}


def find_queue_json(explicit: str = "") -> Path:
    if explicit:
        p = ep(explicit)
        if p.exists():
            return p
        raise FileNotFoundError("Queue JSON nicht gefunden: " + str(p))
    for raw in QUEUE_SEARCH_CANDIDATES:
        p = ep(raw)
        if p.exists():
            return p
    raise FileNotFoundError(
        "Keine Queue JSON gefunden. Erwartet z.B.: "
        + str(ep(QUEUE_SEARCH_CANDIDATES[0]))
    )


def queue_task_to_lss_task(task_id: str, task_obj: Dict[str, Any], seq_id: int, queue_label: str) -> Dict[str, Any]:
    label = task_obj.get("label") or task_id
    aliases = []
    settings = task_obj.get("settings") or {}
    if settings.get("script_name"):
        aliases.append(settings.get("script_name"))
    if settings.get("display_name"):
        aliases.append(settings.get("display_name"))
    aliases.extend(QUEUE_TO_LSS_ALIASES.get(task_id, []))
    aliases.extend(task_obj.get("aliases") or [])
    aliases.append(label)

    # Zombie levels are split in the generator but LSS usually exposes one "Zombies/Zombie Lair" script.
    if str(task_id).startswith("zombies_") or str(label).lower().startswith("zombies"):
        aliases = ["Zombie Lair", "Zombies", "Zombie", label] + aliases

    # Preserve order and remove duplicates.
    seen = set()
    unique_aliases = []
    for a in aliases:
        s = str(a).strip()
        if not s:
            continue
        k = s.lower()
        if k not in seen:
            seen.add(k)
            unique_aliases.append(s)

    return {
        "id": seq_id,
        "name": f"{queue_label} / {label}",
        "script_names": unique_aliases,
        "enabled": True,
        "source_queue_task_id": task_id,
        "source_queue_label": queue_label,
    }


def import_queue_into_task_chain(root: Path, queue_json: str = "", queue_ids: str = "", dry_run: bool = False) -> int:
    qpath = find_queue_json(queue_json)
    q = load_json(qpath)

    queues = q.get("queues") or []
    tasks = q.get("tasks") or {}
    selected_ids = [x.strip().lower() for x in str(queue_ids or "").replace("+", ",").replace(";", ",").split(",") if x.strip()]
    selected = []
    for item in queues:
        qid = str(item.get("id", "")).lower()
        qlabel = str(item.get("label", "")).lower()
        if not selected_ids or qid in selected_ids or qlabel in selected_ids:
            selected.append(item)

    if not selected:
        raise RuntimeError("Keine passende Queue in der Generator-JSON gefunden.")

    imported_tasks = []
    seq = 1
    for qitem in selected:
        qlabel = qitem.get("label") or qitem.get("id") or f"Queue{len(imported_tasks)+1}"
        for tid in qitem.get("tasks", []):
            tobj = tasks.get(tid)
            if not tobj:
                continue
            imported_tasks.append(queue_task_to_lss_task(tid, tobj, seq, str(qlabel)))
            seq += 1

    if not imported_tasks:
        raise RuntimeError("Die ausgewählten Queues enthalten keine importierbaren Tasks.")

    chain = {
        "version": "wulfpack-overseer-0.0.8",
        "generated_from": str(qpath),
        "generated_at": ts(),
        "active_profile_name": "zz_TASK_CHAIN_ACTIVE.json",
        "tasks": imported_tasks,
        "account_switcher": {
            "script_names": ["Account Switcher"],
            "must_remain_enabled": True,
            "last_account_success_regex": r"Stopping script \"Account Switcher\".*-5 \(Switched to the last account\)",
            "failed_regex": r"Stopping script \"Account Switcher\".*-2 \(Failed\)"
        },
        "scheduling_note": (
            "Imported from character queue JSON. LSS-Bot Account Switcher handles accounts; "
            "the sidecar runs the imported LSS task order and stops/starts LSS Bot.exe between tasks."
        ),
    }

    target = root / "config" / "task_chain.json"
    manifest = root / "config" / "queue_import_manifest.json"

    print("QUEUE_IMPORT source:", qpath)
    print("QUEUE_IMPORT target:", target)
    print("QUEUE_IMPORT tasks:", len(imported_tasks))
    for t in imported_tasks:
        print(" - %02d %s -> %s" % (t["id"], t["name"], ", ".join(t["script_names"][:5])))

    if dry_run:
        print("QUEUE_IMPORT dry-run: keine Datei geschrieben")
        return 0

    if target.exists():
        backup = root / "config" / "_backups" / ("task_chain.json." + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".bak")
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
        print("QUEUE_IMPORT backup:", backup)

    write_json(target, chain)
    write_json(manifest, {
        "imported_at": ts(),
        "source": str(qpath),
        "target": str(target),
        "queue_ids": selected_ids or "all",
        "task_count": len(imported_tasks),
        "tasks": imported_tasks,
    })
    print("QUEUE_IMPORT OK")
    return 0


def validate(root, cfg_path):
    cfg = load_json(cfg_path)
    probs = []
    warns = []
    if not ep(cfg["lss_exe_path"]).exists():
        probs.append("LSS exe fehlt: " + str(ep(cfg["lss_exe_path"])))
    if not ep(cfg["settings_dir"]).exists():
        warns.append("SettingsDir fehlt noch: " + str(ep(cfg["settings_dir"])))
    for f in ["task_chain.json", "irc_config.json", "redaction_policy.json", "translation_de.json"]:
        if not (root / "config" / f).exists():
            probs.append("Config fehlt: " + f)
    if warns:
        print("VALIDATION: WARN")
        print("\n".join(" - " + p for p in warns))
    if probs:
        print("VALIDATION: FAIL")
        print("\n".join(" - " + p for p in probs))
        return 1
    print("VALIDATION: OK")
    return 0


def run(root, cfg_path, dry_override=None):
    cfg = load_json(cfg_path)
    if dry_override is not None:
        cfg["dry_run"] = bool(dry_override)
    dry = bool(cfg.get("dry_run", True))
    audit = Audit(root / cfg["status_files"].get("audit_log", "logs/sidecar_audit.log"))
    chain = load_json(root / "config/task_chain.json")
    red = Redactor(load_json(root / cfg["redaction"].get("config_file", "config/redaction_policy.json")))
    tr = Translator(load_json(root / "config/translation_de.json"))
    irc = None
    if cfg.get("irc", {}).get("enabled"):
        irc = IRC(load_json(root / cfg["irc"].get("config_file", "config/irc_config.json")), dry, audit)

    merged_process_patterns(cfg)
    tail = Tailer(expanded_log_globs(cfg), audit)
    proc = Proc(cfg, dry, audit)
    runtime = cfg.get("task_runtime", {})
    loading_guard = cfg.get("loading_solver_guard", {})
    hard_stop_on_last = runtime.get("hard_stop_immediately_on_last_account", True)

    def emit(msg, inst="Sidecar"):
        audit("[%s] %s" % (inst, msg))
        if irc:
            irc.send("[%s] %s" % (inst, msg))

    def send_log(inst, payload, raw):
        if not irc:
            return
        if inst not in cfg.get("managed_instances", []) and inst != "LSS":
            return
        prefix = cfg["irc"].get("prefix_format", "[{instance}]").format(instance=inst)
        if cfg["irc"].get("send_raw_log", True):
            irc.send(prefix + " " + red(payload))
        if cfg["irc"].get("send_translated_events", True):
            m = tr.translate(raw) or tr.translate(payload)
            if m:
                irc.send(prefix + " " + m)

    def detect_event(inst, payload, raw, expected, state):
        send_log(inst, payload, raw)
        now = time.time()

        # Hard-stop Signal: dieses reale LSS-Logformat darf niemals verpasst werden.
        # Zusätzlich zum konfigurierten Regex gibt es einen festen Fallback.
        if (
            re.search(chain["account_switcher"]["last_account_success_regex"], raw)
            or re.search(r'Stopping script\s+"Account Switcher".*?-5\s*\(Switched to the last account\)', raw, re.I)
            or re.search(r"Account Switcher.*Switched to the last account", raw, re.I)
        ):
            state["last_account_seen_at"] = now
            state["last_account_raw"] = raw
            return "DONE_LAST_ACCOUNT"

        if state.get("last_account_seen_at"):
            guard = float(runtime.get("old_loop_guard_after_last_account_sec", 120))
            if now - state["last_account_seen_at"] <= guard:
                if "Starting from account ID 0" in raw:
                    return "OLD_LOOP_AFTER_LAST_ACCOUNT"
                if re.search(r"Skipped - on cooldown", raw, re.I):
                    return "COOLDOWN_AFTER_LAST_ACCOUNT"

        if re.search(chain["account_switcher"]["failed_regex"], raw):
            return "SWITCH_FAILED"

        if re.search(r"Snapshot error|DISCONNECTED|Timeout getting a response from the device|unable to get the image", raw, re.I):
            return "HARD_ERROR"

        if re.search(r"Checking for additional popups", raw, re.I):
            state["checking_popups_at"] = now
            return None

        if re.search(r"Stopping loading solver", raw, re.I):
            state["loading_stopped_at"] = now
            return "LOADING_SOLVER_STOPPED"

        mstart = re.search(r"Starting script\s+(.+?)\s+v", raw)
        if mstart and loading_guard.get("enabled", True):
            stopped = state.get("loading_stopped_at")
            min_grace = float(loading_guard.get("min_seconds_after_loading_solver_stop_before_script", 8))
            if stopped and (now - stopped) < min_grace:
                mode = loading_guard.get("premature_script_start_action", "warn")
                state["premature_start_count"] = state.get("premature_start_count", 0) + 1
                if mode == "retry":
                    return "PREMATURE_SCRIPT_AFTER_LOADING_SOLVER"
                return "WARN_PREMATURE_SCRIPT_AFTER_LOADING_SOLVER"

        m = re.search(r"Filtered the script queue.*?:\s*1\)\s*(.+)$", raw)
        if runtime.get("abort_on_wrong_active_script", True) and m:
            active = m.group(1).strip().lower()
            expected_low = low(expected)
            if active not in expected_low:
                return "WRONG_SCRIPT:" + active

        return None

    emit(f"LSSBot Sidecar Wulfpack Overseer v{VERSION} gestartet")
    if dry:
        emit("DRY-RUN aktiv: keine Prozess-/Profiländerungen")

    tasks = [t for t in chain["tasks"] if t.get("enabled", True)]
    for task in tasks:
        ok = False
        for attempt in range(1, int(runtime.get("max_retries_per_task", 5)) + 1):
            state = {"task_id": task["id"], "task_name": task["name"], "attempt": attempt}
            emit("Starte Task %02d %s Versuch %d" % (task["id"], task["name"], attempt), "TaskChain")

            if cfg.get("process_control", {}).get("stop_before_each_task", True):
                proc.stop(hard=True, reason="vor Taskstart alten LSS-Prozess bereinigen")

            matched, touched, wait_touched = apply_profile(cfg, chain, task, dry, audit, root)
            if matched == 0 and runtime.get("abort_if_profile_matched_zero", True):
                emit("Abbruch: Profilwriter hat keinen passenden Scriptnamen gefunden: %s" % task["name"], "TaskChain")
                emit("Hinweis: 05_SCAN_PROFILES.cmd ausführen und ein echtes LSS-Profil mit Scriptliste als Basis wählen.", "TaskChain")
                return 1

            if dry:
                emit("[DRY-RUN] Task %02d Profil-Mutation geprüft; kein LSS-Start und keine Warte-Schleife" % task["id"], "TaskChain")
                ok = True
                limit = int(runtime.get("dry_run_task_limit", 3))
                if limit > 0 and task["id"] >= limit:
                    emit("[DRY-RUN] Limit erreicht; setze task_runtime.dry_run_task_limit=0 für alle Tasks", "TaskChain")
                    return 0
                break

            tail.mark_end()
            proc.start()
            deadline = time.time() + float(runtime.get("max_task_runtime_sec", 1800))
            while time.time() < deadline:
                broke_for_retry = False
                for p, inst, payload, raw in tail.read():
                    ev = detect_event(inst, payload, raw, task.get("script_names", []) + [task["name"]], state)
                    if ev == "DONE_LAST_ACCOUNT":
                        emit("Task %02d fertig: letzter Charakter erreicht; LSS wird sofort gestoppt" % task["id"], inst)
                        freeze_active_profile(cfg, audit, reason="last account reached before process stop")
                        proc.stop(hard=hard_stop_on_last, reason="last account reached")
                        ok = True
                        break
                    elif ev in ("OLD_LOOP_AFTER_LAST_ACCOUNT", "COOLDOWN_AFTER_LAST_ACCOUNT"):
                        emit("Alter Loop nach letztem Account erkannt (%s); stoppe hart und gehe zum nächsten Task" % ev, inst)
                        freeze_active_profile(cfg, audit, reason=ev)
                        proc.stop(hard=True, reason=ev)
                        ok = True
                        break
                    elif ev == "LOADING_SOLVER_STOPPED":
                        emit("Loading Solver beendet; Popup-Grace-Guard aktiv", inst)
                    elif ev == "WARN_PREMATURE_SCRIPT_AFTER_LOADING_SOLVER":
                        emit("Warnung: Script startete kurz nach Loading Solver; Popup kann noch fehlen", inst)
                    elif ev == "PREMATURE_SCRIPT_AFTER_LOADING_SOLVER":
                        emit("Popup-/Loading-Guard: Script startete zu früh; Recovery gleicher Task", inst)
                        proc.stop(hard=True, reason=ev)
                        broke_for_retry = True
                        break
                    elif ev:
                        emit("Problem bei Task %02d: %s" % (task["id"], ev), inst)
                        proc.stop(hard=True if ev in ("HARD_ERROR", "SWITCH_FAILED") or ev.startswith("WRONG_SCRIPT") else False, reason=ev)
                        if attempt >= int(runtime.get("max_retries_per_task", 5)):
                            return 1
                        broke_for_retry = True
                        break
                if ok:
                    break
                if broke_for_retry:
                    break
                time.sleep(float(runtime.get("log_poll_interval_sec", 0.5)))

            if ok:
                break
            emit("Task %02d Zeitlimit/Fehler, nächster Versuch" % task["id"], "TaskChain")
        if not ok:
            if runtime.get("skip_after_max_retries", True):
                emit("Task %02d nach maximalen Versuchen übersprungen: %s" % (task["id"], task["name"]), "TaskChain")
                freeze_active_profile(cfg, audit, reason="skip_after_max_retries")
                proc.stop(hard=True, reason="skip_after_max_retries")
                continue
            emit("Kette abgebrochen bei Task %02d %s" % (task["id"], task["name"]), "TaskChain")
            return 1

    emit("Alle Tasks abgearbeitet", "TaskChain")
    return 0



def self_test(root: Path) -> int:
    """Lokaler Smoke-Test ohne echte LSS-Installation.

    Testet zwei Profilformen:
    - generisches Listenformat
    - echtes LSS-Settings-Format, das aus der JAR/UI-Logik abgeleitet wurde:
      Root-Key = Scriptname, Value = Objekt mit active/position/scriptRules.
    """
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="lss_sidecar_selftest_"))
    try:
        settings = tmp / "settings"
        settings.mkdir()

        list_profile = {
            "scripts": [
                {"name": "Commend Leaderboard", "active": False, "position": 99, "clickDelay": 100},
                {"name": "Account Switcher", "active": False, "position": 99},
                {"name": "Radio Quiz", "active": True, "position": 1},
            ],
            "stopInstanceAfterLoop": False,
            "randomizeTaskOrder": True,
            "ignoreCooldowns": True,
            "sleepBaseEnterMills": 100,
            "sleepMapOpenMills": 100,
        }
        write_json(settings / "Farms.json", list_profile)

        cfg = load_json(root / "config/sidecar_config.json")
        cfg["settings_dir"] = str(settings)
        cfg["dry_run"] = True
        cfg["irc"]["enabled"] = False
        cfg["lss_instance_settings_overrides"] = {
            "enabled": True,
            "values": {
                "stopInstanceAfterLoop": True,
                "randomizeTaskOrder": False,
                "ignoreCooldowns": False,
                "sleepBaseEnterMills": 9000,
                "sleepMapOpenMills": 6000,
            },
        }
        chain = load_json(root / "config/task_chain.json")

        class A:
            def __call__(self, msg): print(msg)

        matched, touched, wait_touched = apply_profile(cfg, chain, chain["tasks"][0], True, A(), root)
        if matched < 1:
            print("SELFTEST FAIL: Listenformat matched < 1")
            return 1

        cfg["dry_run"] = False
        apply_profile(cfg, chain, chain["tasks"][0], False, A(), root)
        active = load_json(settings / cfg.get("active_profile_name", "zz_TASK_CHAIN_ACTIVE.json"))
        scripts = active["scripts"]
        checks = [
            scripts[0]["active"] is True,
            scripts[1]["active"] is True,
            scripts[2]["active"] is False,
            active["stopInstanceAfterLoop"] is False,
            active["randomizeTaskOrder"] is False,
            active["ignoreCooldowns"] is False,
        ]
        if not all(checks):
            print("SELFTEST FAIL: Listenformat output checks failed", checks)
            return 1

        # Echtes LSS-Saveformat: Scriptname ist JSON-Key, nicht ein Feld im Objekt.
        for p in settings.glob("*.json"):
            p.unlink()
        lss_profile = {
            "Commend Leaderboard": {"active": False, "position": 99, "scriptRules": {"cd": 0}},
            "Account Switcher": {"active": False, "position": 99, "scriptRules": {"cd": 0}},
            "Radio Quiz": {"active": True, "position": 1, "scriptRules": {"cd": 0}},
            "stopInstanceAfterLoop": False,
            "randomizeScriptOrder": True,
            "ignoreCooldowns": True,
            "sleepBaseEnterMills": 100,
            "sleepMapOpenMills": 100,
        }
        write_json(settings / "Farms.json", lss_profile)

        cfg["dry_run"] = True
        matched, touched, wait_touched = apply_profile(cfg, chain, chain["tasks"][0], True, A(), root)
        if matched < 1:
            print("SELFTEST FAIL: LSS-Keyformat matched < 1")
            return 1

        cfg["dry_run"] = False
        apply_profile(cfg, chain, chain["tasks"][0], False, A(), root)
        active = load_json(settings / cfg.get("active_profile_name", "zz_TASK_CHAIN_ACTIVE.json"))
        checks = [
            active["Commend Leaderboard"]["active"] is True,
            active["Account Switcher"]["active"] is True,
            active["Radio Quiz"]["active"] is False,
            active["Commend Leaderboard"]["position"] == 1,
            active["Account Switcher"]["position"] == 2,
            active["stopInstanceAfterLoop"] is False,
            active["ignoreCooldowns"] is False,
        ]
        if not all(checks):
            print("SELFTEST FAIL: LSS-Keyformat output checks failed", checks)
            return 1


        # Log-loop-Guard-Test: selbst wenn der normale Tailer die -5-Zeile verpasst,
        # muss der Recent-Scan sie lokal nachziehen. Das bildet den vom Nutzer gelieferten
        # Loop ab: nach -5 folgt sonst wieder account ID 0 und Cooldown.
        logdir = tmp / "logs"
        logdir.mkdir(exist_ok=True)
        lf = logdir / "lss.log"
        old_line = '19:59:41 [INFO] (Farms - emulator-5554) Timeout getting a response from the device, reconnecting\n'
        last_line = '09:10:07 [INFO] (Farms - emulator-5554) Stopping script "Account Switcher" v1.0 with exit code "-5 (Switched to the last account)". Script finished in 00:00:29\n'
        loop_line = '09:10:29 [INFO] (Farms - emulator-5554) Starting from account ID 0\n'
        cooldown_line = '09:10:27 [INFO] (Farms - emulator-5554) Stopping script "Commend Leaderboard" v0.0 with exit code "-8 (Skipped - on cooldown)". Script finished in 00:00:00\n'
        lf.write_text(old_line, encoding="utf-8")
        tail = Tailer([str(logdir / "*.log")], A())
        tail.mark_end()
        # Reproduziert den realen Fehlerfall: alte kritische Zeile liegt vor Task-Baseline,
        # die neue -5-Zeile wird nach Taskstart angehängt, normaler Tailer verpasst sie.
        tail.task_start_sec = 9 * 3600
        with lf.open("a", encoding="utf-8") as f:
            f.write(last_line + cooldown_line + loop_line)
        tail.pos[str(lf)] = lf.stat().st_size  # Simuliere: normaler Tailer hat die neue Zeile verpasst.
        got = tail.read()
        raws = [x[3] for x in got]
        if any('Timeout getting a response' in r for r in raws):
            print("SELFTEST FAIL: Recent-Scan zieht alte kritische Zeilen vor Taskstart nach")
            return 1
        if not any('Switched to the last account' in r for r in raws):
            print("SELFTEST FAIL: Recent-Scan erkennt last-account-Zeile nach Taskstart nicht")
            return 1
        if not re.search(chain["account_switcher"]["last_account_success_regex"], last_line):
            print("SELFTEST FAIL: last_account_success_regex passt nicht auf reales Logformat")
            return 1

        print("SELFTEST OK")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)





def replay_task10_test(root: Path, real_log_path: str | None = None) -> int:
    """Deterministischer lokaler Test bis Task 10 ohne echten LSS/LDPlayer.

    Simuliert 10 Task-Zyklen:
    - Profil für Task N schreiben
    - LSS-Log mit Account Switcher -5 erzeugen
    - Event-Detector muss DONE_LAST_ACCOUNT liefern
    - nächster Task muss geschrieben werden
    Zusätzlich wird das vom Nutzer gelieferte echte Loop-Log geprüft.
    """
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="lss_sidecar_task10_"))
    try:
        settings = tmp / "settings"
        logs = tmp / "logs"
        settings.mkdir()
        logs.mkdir()
        cfg = load_json(root / "config/sidecar_config.json")
        cfg["settings_dir"] = str(settings)
        cfg["dry_run"] = False
        cfg.setdefault("irc", {})["enabled"] = False
        cfg["log_globs"] = [str(logs / "*.log")]
        cfg["lss_exe_path"] = str(tmp / "fake_lss.exe")
        cfg["process_control"]["start_wait_sec"] = 0
        cfg["process_control"]["hard_stop_post_wait_sec"] = 0
        cfg["process_control"]["post_stop_wait_sec"] = 0
        cfg["process_control"]["graceful_stop_timeout_sec"] = 0
        (tmp / "fake_lss.exe").write_text("fake", encoding="utf-8")

        chain = load_json(root / "config/task_chain.json")
        task_names = []
        for t in chain["tasks"][:10]:
            task_names.extend(t.get("script_names", []) or [t["name"]])
        # Vollständiges LSS-Key-Profil für die ersten 10 Tasks + Switcher.
        prof = {name: {"active": False, "position": 99, "scriptRules": {}} for name in set(task_names)}
        prof["Account Switcher"] = {"active": False, "position": 99, "scriptRules": {}}
        prof["stopInstanceAfterLoop"] = False
        prof["randomizeScriptOrder"] = True
        write_json(settings / "Farms.json", prof)

        class A:
            def __init__(self): self.lines=[]
            def __call__(self, msg):
                self.lines.append(msg)
                print(msg)
        audit = A()

        def detect(raw, task, state):
            now = time.time()
            if (
                re.search(chain["account_switcher"]["last_account_success_regex"], raw)
                or re.search(r'Stopping script\s+"Account Switcher".*?-5\s*\(Switched to the last account\)', raw, re.I)
                or re.search(r"Account Switcher.*Switched to the last account", raw, re.I)
            ):
                state["last_account_seen_at"] = now
                return "DONE_LAST_ACCOUNT"
            if state.get("last_account_seen_at"):
                if "Starting from account ID 0" in raw:
                    return "OLD_LOOP_AFTER_LAST_ACCOUNT"
                if re.search(r"Skipped - on cooldown", raw, re.I):
                    return "COOLDOWN_AFTER_LAST_ACCOUNT"
            return None

        completed = []
        for task in chain["tasks"][:10]:
            matched, touched, wait_touched = apply_profile(cfg, chain, task, False, audit, root)
            if matched < 1:
                print("REPLAY FAIL: matched < 1 for Task", task["id"], task["name"])
                return 1
            active = load_json(settings / cfg.get("active_profile_name", "zz_TASK_CHAIN_ACTIVE.json"))
            # Mindestens ein Task-Script und Account Switcher aktiv.
            wanted = low(task.get("script_names", []) + [task["name"]])
            active_task = any(isinstance(v, dict) and any(str(k).lower() in ACTIVE_KEYS for k in v.keys()) and _name_matches(k, wanted) and v.get("active") for k, v in active.items())
            if not active_task or not active.get("Account Switcher", {}).get("active"):
                print("REPLAY FAIL: active profile not set for Task", task["id"], task["name"])
                return 1

            log = logs / "lss.log"
            hh = 9
            minute = 20 + task["id"]
            lines = [
                f"{hh:02d}:{minute:02d}:00 [INFO] (Farms - emulator-5554) Executing a total of 1 scripts\n",
                f"{hh:02d}:{minute:02d}:01 [INFO] (Farms - emulator-5554) Filtered the script queue, scripts that are currently on cooldown will appear in the bottom of the queue: 1) {task['script_names'][0] if task.get('script_names') else task['name']}\n",
                f"{hh:02d}:{minute:02d}:20 [INFO] (Farms - emulator-5554) Stopping script \"Account Switcher\" v1.0 with exit code \"-5 (Switched to the last account)\". Script finished in 00:00:30\n",
                f"{hh:02d}:{minute:02d}:25 [INFO] (Farms - emulator-5554) Stopping script \"{task['script_names'][0] if task.get('script_names') else task['name']}\" v0.0 with exit code \"-8 (Skipped - on cooldown)\". Script finished in 00:00:00\n",
                f"{hh:02d}:{minute:02d}:29 [INFO] (Farms - emulator-5554) Starting from account ID 0\n",
            ]
            state={}
            evs=[]
            for line in lines:
                ev=detect(line, task, state)
                if ev:
                    evs.append(ev)
                if ev == "DONE_LAST_ACCOUNT":
                    freeze_active_profile(cfg, audit, reason="replay last account")
                    completed.append(task["id"])
                    break
            if not evs or evs[0] != "DONE_LAST_ACCOUNT":
                print("REPLAY FAIL: last-account not first terminal event for Task", task["id"], evs)
                return 1
            # Nach Freeze darf Task nicht aktiv bleiben.
            frozen = load_json(settings / cfg.get("active_profile_name", "zz_TASK_CHAIN_ACTIVE.json"))
            if any(isinstance(v, dict) and v.get("active") is True for v in frozen.values()):
                print("REPLAY FAIL: freeze left active scripts for Task", task["id"])
                return 1

        if completed != list(range(1, 11)):
            print("REPLAY FAIL: completed", completed)
            return 1

        if real_log_path:
            rp = Path(real_log_path)
            content = rp.read_text(encoding="utf-8", errors="replace")
            if "Switched to the last account" not in content:
                print("REPLAY FAIL: real log has no -5 line")
                return 1
            # Prüfe: unser Terminal-Detector findet die reale -5-Zeile vor account-id-0/cooldown-Folgen.
            idx = content.find("Switched to the last account")
            window = content[max(0, idx-250):idx+500]
            if not re.search(r'Stopping script\s+"Account Switcher".*?-5\s*\(Switched to the last account\)', window, re.I):
                print("REPLAY FAIL: real log regex did not match")
                print(window)
                return 1
        print("TASK10_REPLAY_OK completed=1..10")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(root / "config/sidecar_config.json"))
    ap.add_argument("--install-config", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--scan-profiles", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--replay-task10-test", action="store_true")
    ap.add_argument("--real-log", default="")
    ap.add_argument("--import-queue", action="store_true")
    ap.add_argument("--queue-json", default="")
    ap.add_argument("--queue-ids", default="", help="Optional comma list like queue1,queue2; default imports all queues")
    ap.add_argument("--live", action="store_true", help="Run LSS Bot.exe live; overrides config dry_run=false")
    ap.add_argument("--dry-run", action="store_true", help="Force dry-run for import/run")
    a = ap.parse_args(argv)
    if a.install_config:
        install(root, a.force)
        return 0
    if a.validate:
        return validate(root, Path(a.config))
    if a.scan_profiles:
        return scan_profiles(root, Path(a.config))
    if a.self_test:
        return self_test(root)
    if a.replay_task10_test:
        return replay_task10_test(root, a.real_log or None)
    if a.import_queue:
        return import_queue_into_task_chain(root, a.queue_json, a.queue_ids, dry_run=bool(a.dry_run))
    dry_override = None
    if a.live:
        dry_override = False
    elif a.dry_run:
        dry_override = True
    return run(root, Path(a.config), dry_override=dry_override)


if __name__ == "__main__":
    raise SystemExit(main())
