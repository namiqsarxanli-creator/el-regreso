"""
BLOK 4 — Runner. Checkpointing burada yaşayır.

Bir ruhun bütün həyatı bir `thread_id`-dir. Hər il proqram tam bağlanır,
gələn il yenidən açılır və ruh keçən dəfə dayandığı yerdən davam edir.

    python -m starter.run_year --soul abuela --year 2021
    python -m starter.run_year --soul abuela --resume --gift cempasúchil
    python -m starter.run_year --soul abuela --history
    python -m starter.run_year --soul abuela --fork 7 --gift şəkil
    python -m starter.run_year --soul abuela --state
    python -m starter.run_year --soul abuela --forget

CLI-nin «darıxdırıcı» hissəsi hazır verilib: argparse, çap, fayl oxuma.
Sənin işin `TODO 4.x` ilə işarələnmiş checkpointing hissələridir.
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
import json
import os
import sys
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from . import ui
from .graph import build_graph
from .state import RESET, new_soul

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "altar.db"
ALTAR_DIR = ROOT / "altar"


def load_soul_file(name: str) -> dict:
    path = ALTAR_DIR / f"{name}.json"
    if not path.exists():
        ui.warn(f"altar/{name}.json tapılmadı")
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def _summary(update: dict) -> str:
    """Node update-inin bir sətirlik xülasəsi. (Hazırdır.)"""
    if not isinstance(update, dict):
        return ""
    journey = update.get("journey")
    if isinstance(journey, list) and journey and journey[-1] != RESET:
        return str(journey[-1])[:44]
    for key in ("missing", "crossing_report", "words", "senses"):
        value = update.get(key)
        if not value or value == RESET:
            continue
        text = ", ".join(str(v) for v in value) if isinstance(value, list) else str(value)
        return text[:44].replace("\n", " ")
    return ""


def stream_run(graph, payload, config, gifts: list[str], interactive: bool) -> str:
    """TODO 4.1 — qrafı işlət və interrupt-ı idarə et.

    Qaytarır: 'done' | 'paused'

    Addımlar:
      1. `graph.stream(payload, config, stream_mode="updates")` üzərində dövr
      2. Gələn chunk-da `"__interrupt__"` açarı varsa:
           - sualı göstər: chunk["__interrupt__"][0].value
           - cavabı `gifts` siyahısından və ya `input()`-dan al
           - cavab yoxdursa 'paused' qaytar (proqram bağlana bilər)
           - varsa: payload = Command(resume=cavab) və dövrəni yenidən başlat
      3. Adi node update-ləri: ui.step(node, _summary(update))
         `__` ilə başlayan açarları ötür — onlar node deyil.
    """
    raise NotImplementedError("TODO 4.1")


def show_year(values: dict) -> None:
    """İlin yekunu. (Hazırdır.)"""
    ui.note("")
    ui.trail(values.get("journey", []))
    if values.get("crossing_steps"):
        ui.note("")
        ui.note(f"  {values.get('crossing_report', 'Mictlán')}", ui.VIOLET)
        ui.trail(values["crossing_steps"])
    if values.get("words"):
        ui.words(values.get("display") or values.get("name", "ruh"), values["words"])
    ui.note("")
    ui.meter(values.get("remembrance", 0))
    visits = values.get("visits", [])
    if visits:
        ui.note(f"  {len(visits)} ziyarət: {', '.join(str(v['year']) for v in visits)}", ui.ASH)


def cmd_history(graph, config) -> None:
    """TODO 4.2 — checkpoint tarixçəsi.

    `graph.get_state_history(config)` StateSnapshot-lar qaytarır.
    Hər sətirdə göstər: sıra nömrəsi, checkpoint_id-nin son 8 simvolu,
    il, `snap.next` (növbəti node-lar), xatırlanma.

    Qeyd: checkpoint id-ləri vaxta görə sıralanır — İLK simvolları eyni
    olur. Ona görə sonuncu simvolları göstər.
    """
    raise NotImplementedError("TODO 4.2")


def resolve_checkpoint(graph, config, token: str):
    """TODO 4.3 — tarixçədən snapshot tap (nömrə və ya id parçası ilə).

    DİQQƏT: snapshot-ın ÖZÜNÜ qaytar, id-ni yox. `update_state` üçün
    `snapshot.config` lazımdır — orada `checkpoint_ns` kimi sahələr var.
    Config-i əl ilə yığmaq tipik səhvdir: KeyError: 'checkpoint_ns'.
    """
    raise NotImplementedError("TODO 4.3")


def cmd_fork(graph, config, token: str, gifts: list[str], interactive: bool) -> None:
    """TODO 4.4 — zaman səyahəti və budaqlanma.

    1. Keçmiş snapshot-ı tap
    2. Altarı dəyiş: köhnə ofrenda + gifts
    3. `graph.update_state(snapshot.config, {...}, as_node="read_ofrenda")`
       → bu, köhnə checkpoint-i DƏYİŞMİR, üstünə YENİ budaq yazır
       → qaytardığı config yeni budağın başlanğıcıdır
    4. `stream_run(graph, None, branch, ...)` ilə davam et
    5. Yekunu oxuyanda diqqət: `branch` konkret checkpoint-ə bağlıdır.
       Son vəziyyəti THREAD səviyyəsindəki config-dən oxu.
    """
    raise NotImplementedError("TODO 4.4")


def cmd_state(graph, config) -> None:
    """Cari yaddaş. (Hazırdır.)"""
    values = graph.get_state(config).values
    if not values:
        ui.note("  thread boşdur — bu ruh hələ heç vaxt gəlməyib", ui.SMOKE)
        return
    ui.banner(
        values.get("display") or values.get("name", "?"),
        f"{len(values.get('visits', []))} ziyarət · xatırlanma {values.get('remembrance', 0)}",
    )
    ui.meter(values.get("remembrance", 0))
    for visit in values.get("visits", []):
        mark = f"{ui.JADE}●{ui.OFF}" if visit["arrived"] else f"{ui.BLOOD}○{ui.OFF}"
        print(f"  {mark} {ui.BONE}{visit['year']}{ui.OFF}  "
              f"{ui.ASH}{', '.join(visit['ofrenda']) or 'boş altar'}{ui.OFF}")


def main() -> None:
    parser = argparse.ArgumentParser(description="El Regreso — bir gecə, hər il.")
    parser.add_argument("--soul", default="abuela")
    parser.add_argument("--year", type=int)
    parser.add_argument("--gift", action="append", default=[])
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--fork", metavar="CHECKPOINT")
    parser.add_argument("--state", action="store_true")
    parser.add_argument("--forget", action="store_true")
    parser.add_argument("--slow", type=float, default=0)
    parser.add_argument("--no-input", action="store_true")
    args = parser.parse_args()

    if args.slow:
        os.environ["EL_REGRESO_SLOW"] = str(args.slow)
    interactive = not args.no_input and sys.stdin is not None and sys.stdin.isatty()

    soul_file = load_soul_file(args.soul)

    # TODO 4.5 — thread konfiqurasiyası
    # Hər ruh öz thread-ində yaşamalıdır. Sabit "1" yazsan, bütün ruhlar
    # bir-birinə qarışacaq.
    config = {"configurable": {"thread_id": ...}}  # TODO

    # TODO 4.6 — checkpointer
    # `SqliteSaver.from_conn_string(...)` context manager-dir.
    # MemorySaver İSTİFADƏ ETMƏ: proqram bağlananda hər şey itər.
    with SqliteSaver.from_conn_string(str(DB_PATH)) as checkpointer:
        graph = build_graph(checkpointer)

        if args.history:
            cmd_history(graph, config)
            return
        if args.state:
            cmd_state(graph, config)
            return
        if args.forget:
            # TODO 4.7 — üçüncü ölüm: thread-i tamamilə sil
            raise NotImplementedError("TODO 4.7")
        if args.fork:
            cmd_fork(graph, config, args.fork, args.gift, interactive)
            return

        snapshot = graph.get_state(config)

        # TODO 4.8 — yarımçıq gecənin AŞKARLANMASI
        # İki əlamət var:
        #   snapshot.next   — növbədə gözləyən node-lar
        #   snapshot.tasks  — başlamış, amma checkpoint-ə yazılmamış iş
        # İkincisi vacibdir: proses node-un ORTASINDA öldürüləndə `next`
        # boş qalır. Yalnız `next`-ə baxsan, chaos testin uğursuz olacaq.
        waiting = []  # TODO
        pending = bool(waiting)

        if args.resume or (pending and not args.year):
            if not pending:
                ui.note("  yarımçıq gecə yoxdur", ui.SMOKE)
                return
            ui.banner(f"{soul_file['display']} — davam",
                      f"qraf «{', '.join(waiting)}» node-unda dayanmışdı")
            # TODO 4.9 — davam etmək üçün input nə olmalıdır?
            # (İpucu: yeni state göndərmək gecəni əvvəldən başladar.)
            status = stream_run(graph, ..., config, args.gift, interactive)  # TODO
        else:
            year = args.year or max(int(y) for y in soul_file["years"])
            payload: dict = {"year": year}
            # TODO 4.10 — ruh ilk dəfə gəlirsə, kimliyini yarat.
            # Şərt: thread BOŞ olanda. İkinci ildə bunu təkrar etsən,
            # bütün yaddaş sıfırlanacaq — layihənin ən pis səhvi budur.
            ui.banner(
                f"{soul_file['display']} — {year}",
                "1 noyabr, angelitos" if soul_file["kind"] == "angelito" else "2 noyabr, difuntos",
            )
            status = stream_run(graph, payload, config, args.gift, interactive)

        values = graph.get_state(config).values
        if status == "paused":
            ui.note("")
            ui.warn("gecə yarımçıq qaldı — ruh qapının ağzında dayandı")
            ui.note(f"  davam: python -m starter.run_year --soul {args.soul} --resume", ui.SMOKE)
            return

        show_year(values)

        if values.get("forgotten"):
            # TODO 4.11 — burada da thread silinməlidir
            ui.warn("üçüncü ölüm: xatırlanma sıfıra düşdü")


if __name__ == "__main__":
    main()
