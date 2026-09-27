"""
El Regreso — runner. Checkpointing burada yaşayır.

Bir ruhun bütün həyatı bir `thread_id`-dir. Hər il proqram tam bağlanır,
gələn il yenidən açılır və ruh keçən dəfə dayandığı yerdən davam edir.

    python -m solution.run_year --soul abuela --year 2021
    python -m solution.run_year --soul abuela --year 2024 --gift cempasúchil
    python -m solution.run_year --soul abuela --resume
    python -m solution.run_year --soul abuela --history
    python -m solution.run_year --soul abuela --fork <checkpoint_id> --gift şəkil
    python -m solution.run_year --soul abuela --state
    python -m solution.run_year --soul abuela --forget
"""

from __future__ import annotations

# PyCharm-da bu fayla ▶ basanda Python onu paketin bir hissəsi kimi
# görmür və nisbi importlar (`from .state import ...`) işləmir.
# Aşağıdakı üç sətir layihə kökünü sys.path-ə əlavə edir və faylı
# paketin içinə qaytarır — `python -m solution.<fayl>` ilə eyni olur.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
    __package__ = "solution"

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


# --------------------------------------------------------------------------
def load_soul_file(name: str) -> dict:
    path = ALTAR_DIR / f"{name}.json"
    if not path.exists():
        ui.warn(f"altar/{name}.json tapılmadı")
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def _summary(update: dict) -> str:
    """Node update-inin bir sətirlik xülasəsi."""
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


# --------------------------------------------------------------------------
def stream_run(graph, payload, config, gifts: list[str], interactive: bool) -> str:
    """Qrafı işlədir; interrupt-a düşəndə hədiyyə ilə davam edir.

    Qaytarır: 'done' | 'paused'
    'paused' — insan cavabı yoxdur, icra checkpoint-də dayandı. Proqram
    bağlana bilər; `--resume` ilə sabah davam edər.
    """
    while True:
        interrupted = False
        for chunk in graph.stream(payload, config, stream_mode="updates"):
            if "__interrupt__" in chunk:
                payload_value = chunk["__interrupt__"][0].value
                ui.question(payload_value["question"], payload_value["hint"])
                ui.note(f"altarda: {', '.join(payload_value['altar']) or 'boş'}", ui.SMOKE)
                if gifts:
                    gift = gifts.pop(0)
                    ui.note(f"→ {gift}", ui.MARIGOLD)
                elif interactive:
                    try:
                        gift = input(f"  {ui.VIOLET}› {ui.OFF}").strip()
                    except (EOFError, KeyboardInterrupt):
                        gift = ""
                    if not gift:
                        return "paused"
                else:
                    return "paused"
                payload = Command(resume=gift)
                interrupted = True
                break
            for node, update in chunk.items():
                # `__metadata__` kimi daxili açarlar node deyil — bərpa
                # zamanı LangGraph-ın özü göndərir.
                if node.startswith("__"):
                    continue
                ui.step(node, _summary(update))
        if not interrupted:
            return "done"


def show_year(values: dict) -> None:
    ui.note("")
    ui.trail(values.get("journey", []))
    if values.get("crossing_steps"):
        ui.note("")
        ui.note(f"  {values.get('crossing_report', 'Mictlán')}", ui.VIOLET)
        ui.trail(values["crossing_steps"])
    judgement = values.get("judgement") or {}
    if judgement:
        ui.note("")
        ui.note(
            f"  altarın istiliyi: {judgement.get('warmth', '?')}/100 · "
            f"{judgement.get('verdict', '')}",
            ui.JADE,
        )
        if judgement.get("longing"):
            ui.note(f"  ən çox darıxdığı: {judgement['longing']}", ui.SMOKE)
    if values.get("words"):
        ui.words(values.get("display") or values.get("name", "ruh"), values["words"])
    if values.get("calaverita"):
        ui.note("")
        ui.note("  calaverita", ui.CLAY)
        for line in values["calaverita"].splitlines():
            if line.strip():
                ui.note(f"    {line.strip()}", ui.BONE)
    ui.note("")
    ui.meter(values.get("remembrance", 0))
    if values.get("voices"):
        ui.note(f"  səslər: {' · '.join(values['voices'])}", ui.SMOKE)
    visits = values.get("visits", [])
    if visits:
        years = ", ".join(str(v["year"]) for v in visits)
        ui.note(f"  {len(visits)} ziyarət: {years}", ui.ASH)


# --------------------------------------------------------------------------
def cmd_history(graph, config) -> None:
    ui.banner("Checkpoint tarixçəsi", "hər sətir bir andır — geri qayıda bilərsən")
    rows = list(graph.get_state_history(config))
    if not rows:
        ui.note("  tarixçə boşdur", ui.SMOKE)
        return
    for index, snap in enumerate(rows[:30]):
        cid = snap.config["configurable"]["checkpoint_id"]
        nxt = ", ".join(snap.next) or "—"
        year = snap.values.get("year", "—") if isinstance(snap.values, dict) else "—"
        rem = snap.values.get("remembrance", "—") if isinstance(snap.values, dict) else "—"
        print(
            f"  {ui.CLAY}[{index:>2}]{ui.OFF} {ui.SMOKE}…{cid[-8:]}{ui.OFF}  "
            f"{ui.ASH}il {year}{ui.OFF}  "
            f"{ui.BONE}növbəti: {nxt:<18}{ui.OFF} {ui.CLAY}xat. {rem}{ui.OFF}"
        )
    ui.note("")
    ui.note("  budaqlanmaq üçün:  --fork <nömrə> --gift <əşya>", ui.SMOKE)
    ui.note("  qeyd: checkpoint id-ləri vaxta görə sıralanır, ona görə", ui.SMOKE)
    ui.note("  əvvəlləri eynidir — sonuncu 8 simvol fərqlənir.", ui.SMOKE)


def resolve_checkpoint(graph, config, token: str):
    """`--fork` həm tarixçədəki nömrəni, həm də id parçasını qəbul edir.

    Snapshot-ın ÖZÜNÜ qaytarır: `snapshot.config` içində `checkpoint_ns`
    kimi sahələr də var və `update_state` onları tələb edir. Config-i əldə
    yığmaq tipik səhvdir (KeyError: 'checkpoint_ns').
    """
    rows = list(graph.get_state_history(config))
    if token.isdigit():
        index = int(token)
        return rows[index] if index < len(rows) else None
    for snap in rows:
        cid = snap.config["configurable"]["checkpoint_id"]
        if cid.endswith(token) or cid.startswith(token):
            return snap
    return None


def cmd_fork(graph, config, prefix: str, gifts: list[str], interactive: bool) -> None:
    """Zaman səyahəti: keçmiş bir checkpoint-ə qayıdıb altarı dəyişmək.

    `update_state` köhnə checkpoint-i dəyişmir — onun üstünə YENİ budaq
    yazır. Köhnə kainat yerində qalır, yenisi paralel olaraq davam edir.
    """
    snapshot = resolve_checkpoint(graph, config, prefix)
    if snapshot is None:
        ui.warn(f"checkpoint tapılmadı: {prefix}")
        return
    past = snapshot.config
    cid = past["configurable"]["checkpoint_id"]
    ofrenda = list(snapshot.values.get("ofrenda", [])) + list(gifts)

    ui.banner(
        "Paralel kainat",
        f"…{cid[-8:]} anına qayıdıldı · {snapshot.values.get('year', '?')} ili",
    )
    ui.note(f"  köhnə altar: {', '.join(snapshot.values.get('ofrenda', [])) or 'boş'}", ui.SMOKE)
    ui.note(f"  yeni altar : {', '.join(ofrenda)}", ui.MARIGOLD)

    # as_node="read_ofrenda" — qraf elə davam edir ki, sanki altarı məhz
    # o node oxumuşdu. Ondan sonrakı yol (follow_petals...) yenidən işləyir.
    branch = graph.update_state(past, {"ofrenda": ofrenda}, as_node="read_ofrenda")
    ui.note("")
    stream_run(graph, None, branch, gifts, interactive)
    # Diqqət: `branch` konkret bir checkpoint-ə bağlıdır. Yekun vəziyyəti
    # oxumaq üçün thread səviyyəsindəki config lazımdır.
    show_year(graph.get_state(config).values)


def cmd_state(graph, config) -> None:
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
        print(
            f"  {mark} {ui.BONE}{visit['year']}{ui.OFF}  "
            f"{ui.ASH}{', '.join(visit['ofrenda']) or 'boş altar'}{ui.OFF}"
        )


# --------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="El Regreso — bir gecə, hər il.")
    parser.add_argument("--soul", default="abuela", help="altar/<ad>.json")
    parser.add_argument("--year", type=int, help="hansı il ziyarət olunur")
    parser.add_argument("--gift", action="append", default=[], help="interrupt cavabı")
    parser.add_argument("--resume", action="store_true", help="yarımçıq gecəni davam etdir")
    parser.add_argument("--history", action="store_true", help="checkpoint tarixçəsi")
    parser.add_argument("--fork", metavar="CHECKPOINT", help="keçmişə qayıt və budaq yarat")
    parser.add_argument("--state", action="store_true", help="cari yaddaş")
    parser.add_argument("--forget", action="store_true", help="thread-i sil (üçüncü ölüm)")
    parser.add_argument("--slow", type=float, default=0, help="node gecikməsi (demo üçün)")
    parser.add_argument("--no-input", action="store_true", help="interrupt-da soruşma, dayan")
    args = parser.parse_args()

    if args.slow:
        os.environ["EL_REGRESO_SLOW"] = str(args.slow)
    interactive = not args.no_input and sys.stdin is not None and sys.stdin.isatty()

    soul_file = load_soul_file(args.soul)
    config = {"configurable": {"thread_id": args.soul}}

    with SqliteSaver.from_conn_string(str(DB_PATH)) as checkpointer:
        graph = build_graph(checkpointer)

        if args.history:
            cmd_history(graph, config)
            return
        if args.state:
            cmd_state(graph, config)
            return
        if args.forget:
            checkpointer.delete_thread(args.soul)
            ui.banner("Üçüncü ölüm", f"«{args.soul}» thread-i silindi")
            ui.note("  Növbəti il proqram işə düşəcək — amma heç kim gəlməyəcək.", ui.SMOKE)
            return
        if args.fork:
            cmd_fork(graph, config, args.fork, args.gift, interactive)
            return

        snapshot = graph.get_state(config)
        # Yarımçıq gecənin iki əlaməti var:
        #   snapshot.next   — növbədə gözləyən node-lar
        #   snapshot.tasks  — icrası başlamış, amma checkpoint-ə yazılmamış
        # İkincisi vacibdir: proses node-un ortasında öldürüləndə `next`
        # boş qalır, `tasks` isə yarımçıq işi göstərir.
        waiting = list(snapshot.next) or [task.name for task in snapshot.tasks]
        pending = bool(waiting)

        if args.resume or (pending and not args.year):
            if not pending:
                ui.note("  yarımçıq gecə yoxdur", ui.SMOKE)
                return
            ui.banner(
                f"{soul_file['display']} — davam",
                f"qraf «{', '.join(waiting)}» node-unda dayanmışdı",
            )
            status = stream_run(graph, None, config, args.gift, interactive)
        else:
            year = args.year or max(int(y) for y in soul_file["years"])
            payload: dict = {"year": year}
            if not snapshot.values.get("name"):
                payload |= new_soul(
                    soul_file["name"],
                    soul_file["kind"],
                    soul_file.get("relation", ""),
                    soul_file.get("display", ""),
                )
                # Altar faylı istəsə, başlanğıc xatırlanmanı aşağı sala bilər
                # (artıq yarı unudulmuş ruhlar üçün — üçüncü ölüm demosu).
                if "remembrance" in soul_file:
                    payload["remembrance"] = int(soul_file["remembrance"])
            ui.banner(
                f"{soul_file['display']} — {year}",
                "1 noyabr, angelitos" if soul_file["kind"] == "angelito" else "2 noyabr, difuntos",
            )
            status = stream_run(graph, payload, config, args.gift, interactive)

        values = graph.get_state(config).values
        if status == "paused":
            ui.note("")
            ui.warn("gecə yarımçıq qaldı — ruh qapının ağzında dayandı")
            ui.note(f"  davam: python -m solution.run_year --soul {args.soul} --resume", ui.SMOKE)
            return

        show_year(values)

        if values.get("forgotten"):
            ui.note("")
            ui.warn("üçüncü ölüm: xatırlanma sıfıra düşdü")
            checkpointer.delete_thread(args.soul)
            ui.note("  thread silindi. Gələn il bu ad bir daha yüklənməyəcək.", ui.SMOKE)


if __name__ == "__main__":
    main()
