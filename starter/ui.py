"""
Terminal görüntüsü.

Ayrıca fayldır ki, `run_year.py` yalnız checkpointing məntiqindən ibarət
olsun. Rənglər ANSI 256 paletindən seçilib: cempasúchil narıncısı, sümük
ağı, kül boz, obsidian bənövşəyi.
"""

from __future__ import annotations

import os
import sys

# Windows konsolunda ANSI-ni oyadan məlum hiylə.
if sys.platform == "win32":
    os.system("")

# Çıxış boruya (pipe) yönələndə Windows kodlaşdırmanı cp1252 edir və
# «ə», «❋» kimi simvollarda proses çökür: UnicodeEncodeError. PyCharm-ın
# Run pəncərəsi, chaos testi və web server — hamısı boru ilə işləyir.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def _c(code: int) -> str:
    return f"\033[38;5;{code}m"


MARIGOLD = _c(214)
EMBER = _c(208)
CLAY = _c(130)
BONE = _c(230)
ASH = _c(245)
SMOKE = _c(240)
BLOOD = _c(167)
JADE = _c(72)
VIOLET = _c(140)
DIM = "\033[2m"
BOLD = "\033[1m"
OFF = "\033[0m"

W = 66


def rule(char: str = "─", color: str = SMOKE) -> str:
    return f"{color}{char * W}{OFF}"


def banner(title: str, subtitle: str = "") -> None:
    """Papel picado — kəsilmiş kağız bayraqcıqları."""
    flags = "▼ " * ((W - 2) // 2)
    print()
    print(f"{MARIGOLD}{flags}{OFF}")
    print(f"{BOLD}{BONE}  {title}{OFF}")
    if subtitle:
        print(f"{ASH}  {subtitle}{OFF}")
    print(f"{MARIGOLD}{flags}{OFF}")


def step(node: str, detail: str = "") -> None:
    """Bir node işlədi."""
    dot = f"{MARIGOLD}❋{OFF}"
    name = f"{BONE}{node:<20}{OFF}"
    print(f"  {dot} {name} {SMOKE}{detail}{OFF}")


def trail(lines: list[str]) -> None:
    for line in lines:
        print(f"    {CLAY}·{OFF} {ASH}{line}{OFF}")


def question(text: str, hint: str = "") -> None:
    print()
    print(f"  {VIOLET}⟡ {BOLD}{text}{OFF}")
    if hint:
        print(f"    {SMOKE}{hint}{OFF}")


def words(name: str, text: str) -> None:
    print()
    print(f"  {EMBER}❝{OFF} {BOLD}{BONE}{name}{OFF}")
    for line in _wrap(text, W - 6):
        print(f"    {BONE}{line}{OFF}")


def meter(value: int, label: str = "xatırlanma") -> None:
    """Xatırlanma göstəricisi — şam kimi yanıb sönür."""
    filled = round(value / 100 * 28)
    color = JADE if value > 60 else MARIGOLD if value > 25 else BLOOD
    bar = f"{color}{'█' * filled}{SMOKE}{'░' * (28 - filled)}{OFF}"
    print(f"  {ASH}{label:<12}{OFF} {bar} {color}{value}{OFF}")


def note(text: str, color: str = ASH) -> None:
    print(f"  {color}{text}{OFF}")


def warn(text: str) -> None:
    print(f"  {BLOOD}⚠ {text}{OFF}")


def good(text: str) -> None:
    print(f"  {JADE}✓ {text}{OFF}")


def _wrap(text: str, width: int) -> list[str]:
    out: list[str] = []
    for paragraph in text.splitlines():
        line = ""
        for word in paragraph.split():
            if len(line) + len(word) + 1 > width:
                out.append(line)
                line = word
            else:
                line = f"{line} {word}".strip()
        out.append(line)
    return out
