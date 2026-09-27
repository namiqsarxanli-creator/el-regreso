"""
Chaos testi — öldürülə bilməyən gecə.

Bu skript `run_year.py`-ı ayrıca proses kimi işə salır, təsadüfi anda onu
**sərt şəkildə öldürür** (SIGKILL / TerminateProcess — heç bir təmizləmə
kodu işləmir), sonra yenidən işə salır.

Gözlənilən nəticə: ikinci proses sıfırdan başlamır, öldüyü yerdən davam
edir və artıq icra olunmuş node-ları TƏKRAR ETMİR.

    python -m starter.chaos --soul abuela --year 2026

Bir node yenidən işləyə bilər — öldürülən anda yarımçıq qalan node.
Checkpoint node-ların ARASINDA yazılır, ona görə yarımçıq node-un nəticəsi
diskə düşməyib. Bu, səhv deyil: LangGraph "ən azı bir dəfə" (at-least-once)
zəmanəti verir, ona görə node-lar idempotent yazılmalıdır.
"""

from __future__ import annotations

# PyCharm-da bu fayla ▶ basanda Python onu paketin bir hissəsi kimi
# görmür və nisbi importlar (`from .state import ...`) işləmir.
# Aşağıdakı üç sətir layihə kökünü sys.path-ə əlavə edir və faylı
# paketin içinə qaytarır — `python -m starter.<fayl>` ilə eyni olur.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
    __package__ = "starter"

import argparse
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

from . import ui

ROOT = Path(__file__).resolve().parent.parent
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
NODE_RE = re.compile(r"❋\s+(\S+)")


def launch(args: list[str]) -> subprocess.Popen:
    # Windows-da boru (pipe) ilə işləyəndə uşaq prosesin çıxış kodlaşdırması
    # cp1252 olur və «❋», «ə» kimi simvollarda proses çökür. UTF-8 məcburi.
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.Popen(
        # -u: buferlənməmiş çıxış. Onsuz uşaq prosesin sətirləri 4KB blok
        # dolana qədər gözləyir və biz onu görməmiş öldürərik.
        [sys.executable, "-u", "-m", "starter.run_year", *args],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env,
    )


def drain(proc: subprocess.Popen, seconds: float | None) -> list[str]:
    """Prosesin çıxışını oxuyur; `seconds` verilibsə, o vaxtdan sonra öldürür."""
    nodes: list[str] = []
    deadline = time.time() + seconds if seconds else None
    assert proc.stdout is not None
    for line in proc.stdout:
        # Rəng kodları təmizlənməsə, node adı «\x1b[0m» ilə başlayır.
        match = NODE_RE.search(ANSI_RE.sub("", line))
        if match:
            nodes.append(match.group(1))
            ui.step(match.group(1), "")
        if deadline and time.time() > deadline:
            proc.kill()
            break
    proc.wait()
    return nodes


def main() -> None:
    parser = argparse.ArgumentParser(description="El Regreso — chaos testi")
    # Ayrıca ruh: beş illik demo thread-i pozulmasın deyə.
    parser.add_argument("--soul", default="donchuy")
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--slow", type=float, default=0.7)
    parser.add_argument("--kill-after", type=float, default=0)
    args = parser.parse_args()

    kill_after = args.kill_after or random.uniform(1.5, 3.2)
    common = ["--soul", args.soul, "--slow", str(args.slow), "--no-input"]

    ui.banner("Chaos testi", f"{kill_after:.1f} saniyə sonra proses öldürüləcək")
    first = launch([*common, "--year", str(args.year), "--gift", "cempasúchil"])
    ui.note(f"  PID {first.pid} işə düşdü", ui.SMOKE)
    ui.note("")
    before = drain(first, kill_after)
    ui.note("")
    ui.warn(f"PID {first.pid} öldürüldü (kod: {first.returncode})")
    ui.note(f"  icra olunmuş node-lar: {len(before)}", ui.SMOKE)

    time.sleep(0.5)

    ui.banner("Davam", "eyni thread_id, yeni proses")
    # Əgər proses ilk checkpoint yazılmamış öldürülübsə, davam ediləsi bir
    # şey yoxdur — onda ili yenidən başladırıq.
    resume_args = ["--resume"] if before else ["--year", str(args.year)]
    second = launch([*common, *resume_args, "--gift", "cempasúchil"])
    ui.note(f"  PID {second.pid} işə düşdü", ui.SMOKE)
    ui.note("")
    after = drain(second, None)

    ui.note("")
    print(ui.rule())
    repeated = [node for node in after if node in before]
    ui.note(f"  birinci proses : {', '.join(before) or '—'}", ui.ASH)
    ui.note(f"  ikinci proses  : {', '.join(after) or '—'}", ui.ASH)
    ui.note("")
    if not repeated:
        ui.good("heç bir node təkrar işləmədi — iş tam bərpa olundu")
    elif len(set(repeated)) == 1:
        ui.good(f"yalnız yarımçıq qalan node təkrar işlədi: {repeated[0]}")
        ui.note("  checkpoint node-ların arasında yazılır — bu, gözlənilən davranışdır.", ui.SMOKE)
    else:
        ui.warn(f"{len(set(repeated))} node təkrarlandı: {', '.join(set(repeated))}")
        ui.note("  bu qədər təkrar gözlənilmir — node-ların idempotentliyini yoxla.", ui.SMOKE)


if __name__ == "__main__":
    main()
