"""
El Regreso — canlı qraf (FastAPI + WebSocket).

    python -m web.server        →  http://127.0.0.1:8000

Server qrafı işlədir və hər node icra olunanda brauzerə hadisə göndərir.
Vizualizasiya *əlavə qat*dır: bütün məntiq `solution/` içindədir, burada
yalnız ötürücü var.

Diqqət: `graph.stream(...)` sinxron generatordur. Onu birbaşa async
funksiyada dövr etsək, event loop bloklanar və WebSocket donar. Ona görə
qraf ayrıca thread-də işləyir, hadisələr isə asyncio növbəsi ilə gəlir.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
import threading
import uuid
from pathlib import Path

# Layihə kökü sys.path-də olmasa, `from solution...` idxalı işləmir.
# Bu, serverin hansı qovluqdan işə salındığından asılı olmamasını təmin edir.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from solution.graph import build_graph
from solution.state import new_soul
from web import narration

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
import os
DB_PATH = Path(os.getenv("EL_REGRESO_DB", str(ROOT / "altar.db")))
ALTAR_DIR = ROOT / "altar"

import os

# Vizualizasiya üçün node-lar bir az yavaş işləsin — əks halda bütün gecə
# göz qırpımında bitir və heç nə görünmür. Xaricdən təyin edilibsə, ona
# toxunmuruq.
os.environ.setdefault("EL_REGRESO_SLOW", "0.45")

app = FastAPI(title="El Regreso")
app.mount("/static", StaticFiles(directory=str(WEB / "static")), name="static")

# check_same_thread=False — qraf ayrı thread-də işləyir.
_conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
CHECKPOINTER = SqliteSaver(_conn)
GRAPH = build_graph(CHECKPOINTER)
RUN_LOCK = asyncio.Lock()
with _conn:
    _conn.execute("CREATE TABLE IF NOT EXISTS story_branches (id TEXT PRIMARY KEY, soul TEXT NOT NULL, baseline TEXT NOT NULL, year INTEGER, created TEXT DEFAULT CURRENT_TIMESTAMP)")

PROFILES = {
    "abuela": {"bio": "Remedios ailəni süfrə ətrafında birləşdirən nənədir. Onun hekayəsində hər çiçək və hər şəkil bir görüşü yaşadır.", "favorites": ["şəkil", "tamales", "qəhvə"], "portrait": 0},
    "donchuy": {"bio": "Don Chuy ailənin sakit, söhbətcil babasıdır. Bir fincan qəhvə və tanış süfrə onun evə qayıdışını tamamlayır.", "favorites": ["qəhvə", "mezcal", "tamales"], "portrait": 1},
    "mateo": {"bio": "Kiçik qardaş Mateíto 1 noyabrda qayıdır. Oyuncaqları, şokoladı və uşaqlıq xatirələri onun altarına rəng qatır.", "favorites": ["oyuncaq", "şokolad", "süd"], "portrait": 2},
    "tio": {"bio": "Beto ailənin getdikcə daha az xatırlanan əmisidir. Kiçik bir hədiyyə belə onun hekayəsində yeni bir iz qoya bilər.", "favorites": ["mezcal", "şəkil", "şam"], "portrait": 3},
}

def soul_data(soul):
    if soul not in {p.stem for p in ALTAR_DIR.glob("*.json")}:
        raise ValueError("Ruh tapılmadı")
    return json.loads((ALTAR_DIR / f"{soul}.json").read_text(encoding="utf-8"))

def gift_list(value):
    if not isinstance(value, list) or len(value) > 30 or any(not isinstance(x, str) or not x.strip() or len(x) > 80 for x in value):
        raise ValueError("Altar ən çox 30 qısa əşya adından ibarət olmalıdır")
    return list(dict.fromkeys(x.strip() for x in value))

def branch_config(soul, branch_id=None):
    soul_data(soul)
    if branch_id and not _conn.execute("SELECT 1 FROM story_branches WHERE id=? AND soul=?", (branch_id, soul)).fetchone():
        raise ValueError("Budaq tapılmadı")
    return {"configurable": {"thread_id": branch_id or soul}}

def branches(soul):
    return [{"id": row[0], "baseline": json.loads(row[1]), "year": row[2], "created": row[3],
             "values": _clean(GRAPH.get_state(branch_config(soul, row[0])).values),
             "complete": not bool(GRAPH.get_state(branch_config(soul, row[0])).next)}
            for row in _conn.execute("SELECT id,baseline,year,created FROM story_branches WHERE soul=? ORDER BY created DESC, rowid DESC", (soul,)).fetchall()]


def souls() -> list[dict]:
    out = []
    for path in sorted(ALTAR_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        out.append(
            {
                "name": data["name"],
                "display": data.get("display", data["name"]),
                "kind": data["kind"],
                "relation": data.get("relation", ""),
                "years": sorted(data.get("years", {}), key=int),
                "offerings": data.get("years", {}),
                **PROFILES.get(data["name"], {}),
            }
        )
    return out


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(WEB / "static" / "index.html"))


@app.get("/api/souls")
def api_souls() -> list[dict]:
    return souls()


@app.get("/api/state/{soul}")
def api_state(soul: str, branch_id: str | None = None) -> dict:
    try:
        config = branch_config(soul, branch_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    snapshot = GRAPH.get_state(config)
    return {
        "values": _clean(snapshot.values),
        "waiting": list(snapshot.next) or [t.name for t in snapshot.tasks],
        "history": _history(config),
        "branches": branches(soul),
        "interrupt": next((i.value for task in snapshot.tasks for i in task.interrupts), None),
    }


@app.get('/api/narration/{soul}')
async def api_narration(soul: str, branch_id: str | None = None) -> Response:
    try:
        config = branch_config(soul, branch_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    values = GRAPH.get_state(config).values
    words = values.get('words', '')
    if not words:
        raise HTTPException(404, 'Bu ruhun hələ danışdığı söz yoxdur.')
    try:
        audio = await narration.generate(soul, words)
    except narration.NarrationError as exc:
        raise HTTPException(503, str(exc)) from exc
    # Never play a stale result if the story was forgotten or changed mid-request.
    if GRAPH.get_state(config).values.get('words') != words:
        raise HTTPException(409, 'Hekayə dəyişib. Yenidən dinlə.')
    return Response(audio, media_type='audio/wav', headers={'Cache-Control': 'no-store'})


# --------------------------------------------------------------------------
# Hər node üçün onu yaradan LangGraph çağırışı.
# Məqsəd pedaqojidir: ekranda hekayə yox, MEXANİZM görünsün.
# --------------------------------------------------------------------------
API_LINES = {
    "dusk_angelitos": 'return {"journey": [RESET, "1 noyabr…"]}   # trail reducer',
    "dusk_difuntos": 'return {"journey": [RESET, "2 noyabr…"]}   # trail reducer',
    "read_ofrenda": 'read_altar.invoke({"name": …, "year": …})   # tool node',
    "lost": "voice.plea(...)  →  state[\"plea\"]   # interrupt mətnini model yazır",
    "wait_for_family": "interrupt({...})   ⏸  icra dayandı, checkpoint yazıldı",
    "mictlan_crossing": "subgraph.invoke(...)  →  crossing_report   # subqraf node",
    "taste_food": "superstep: 3 node paralel  →  gather reducer",
    "smell_copal": "superstep: 3 node paralel  →  gather reducer",
    "see_photos": "superstep: 3 node paralel  →  gather reducer",
    "reunion": "fan-in: visits[] üzərindən missing_since hesablanır",
    "judge_ofrenda": "model.with_structured_output(Judgement).invoke(...)",
    "write_calaverita": "model.invoke(...)  →  calaverita   # keçən ilinki prompt-dadır",
    "speak_to_family": "model.invoke(...)  →  words",
    "farewell": 'return {"visits": [visit]}   # operator.add — illər yığılır',
    "third_death": "forgotten = True   → runner: checkpointer.delete_thread()",
}


def api_line(node: str, update: dict) -> str:
    """Node üçün çağırış sətri; bəzi sətirlər dinamik doldurulur."""
    if node == "follow_petals":
        goto = "mictlan_crossing" if update.get("petal_path") else "lost"
        return f'Command(goto="{goto}", update={{"petal_path": {update.get("petal_path")}}})'
    return API_LINES.get(node, f'node "{node}" → state update')


# --------------------------------------------------------------------------
# Node-un insan dilində izahı: nə etdi, state-ə nə yazdı, kimə ötürür.
# Jurnalın məqsədi yalnız API göstərmək deyil — node-ların bir-birinə
# necə bağlandığını göstərməkdir.
# --------------------------------------------------------------------------
# Hər ruh üçün addım sayğacı (jurnaldakı nömrələr).
STEP: dict[str, int] = {}

ROLES = {
    "dusk_angelitos": "saf funksiya",
    "dusk_difuntos": "saf funksiya",
    "read_ofrenda": "tool node",
    "follow_petals": "Command ilə marşrut",
    "lost": "LLM + loop sayğacı",
    "wait_for_family": "interrupt",
    "mictlan_crossing": "subqraf",
    "taste_food": "paralel ‖",
    "smell_copal": "paralel ‖",
    "see_photos": "paralel ‖",
    "reunion": "fan-in",
    "judge_ofrenda": "LLM · structured output ‖",
    "write_calaverita": "LLM ‖",
    "speak_to_family": "LLM",
    "farewell": "saf funksiya",
    "third_death": "son",
}

LABELS = {
    "dusk_angelitos": "qürub · 1 noyabr",
    "dusk_difuntos": "qürub · 2 noyabr",
    "read_ofrenda": "altarı oxu",
    "follow_petals": "ləçək yolu",
    "lost": "azdı",
    "wait_for_family": "ailəni gözlə",
    "mictlan_crossing": "Mictlán keçidi",
    "taste_food": "dad",
    "smell_copal": "copal",
    "see_photos": "şəkil",
    "reunion": "görüş",
    "judge_ofrenda": "qiymət",
    "write_calaverita": "calaverita",
    "speak_to_family": "söz",
    "farewell": "vida",
    "third_death": "üçüncü ölüm",
}


def describe(node: str, update: dict, soul: str) -> dict:
    """Bir node icrasının izahı: did / wrote / next / note."""
    journey = update.get("journey") or []
    last = str(journey[-1]) if journey and journey[-1] != "__RESET__" else ""

    if node in ("dusk_angelitos", "dusk_difuntos"):
        return {
            "did": "yeni gecə başladı — keçən ilin izləri silindi",
            "wrote": "senses · tasted · crossing_steps · voices sıfırlandı",
            "note": "visits və calaveritas SİLİNMİR — bütün yaddaş onlardadır",
            "next": "altarı oxu — bu ilin ofrendasını diskdən gətirəcək",
        }
    if node == "read_ofrenda":
        items = update.get("ofrenda") or []
        return {
            "did": f"altar/{soul}.json oxundu → {len(items)} əşya",
            "wrote": f"ofrenda ← {', '.join(items) or 'boş'}",
            "next": "ləçək yolu — altarda cempasúchil olub-olmadığına baxacaq",
        }
    if node == "follow_petals":
        found = bool(update.get("petal_path"))
        return {
            "did": "cempasúchil tapıldı — yol açıqdır"
            if found
            else "cempasúchil yoxdur — ruh qaranlıqda qaldı",
            "wrote": f"petal_path ← {str(found).lower()}",
            "note": "marşrutu node özü seçdi (şərti keçid deyil)",
            "next": "Mictlán keçidi — subqraf işə düşəcək"
            if found
            else "azdı — cəhd sayğacı artacaq",
        }
    if node == "lost":
        attempts = update.get("attempts", 1)
        return {
            "did": f"axtarış {attempts}/3 · model ruhun xahişini yazdı",
            "wrote": "attempts · plea (modelin cümləsi) · voices",
            "note": "model BURADA çağırılır, interrupt node-unda yox — "
            "o node davam ediləndə başdan işləyir",
            "next": "ailəni gözlə — icra dayanacaq"
            if attempts < 3
            else "vida — 3 cəhd bitdi, ruh evi tapmadan dönür",
        }
    if node == "wait_for_family":
        return {
            "did": last or "ailə altara yeni bir şey qoydu",
            "wrote": "ofrenda ← yeni əşya əlavə olundu",
            "note": "insanın cavabı Command(resume=…) ilə gəldi",
            "next": "ləçək yolu — dövrə: yol yenidən yoxlanılır",
        }
    if node == "mictlan_crossing":
        return {
            "did": update.get("crossing_report") or "Mictlán keçildi",
            "wrote": "crossing_report · crossing_steps",
            "note": "subqrafın 5 node-u içəridə işlədi, valideynə yalnız xülasə qayıtdı",
            "next": "dad · copal · şəkil — üçü PARALEL işə düşəcək",
        }
    if node in ("taste_food", "smell_copal", "see_photos"):
        senses = update.get("senses") or []
        return {
            "did": str(senses[-1]) if senses else "hiss qeyd olundu",
            "wrote": "senses ← (gather reducer birləşdirir)"
            + (" · tasted" if node == "taste_food" else ""),
            "note": "üç node eyni superstep-də; reducer olmasa LangGraph xəta verərdi",
            "next": "görüş — hər üçü bitənə qədər gözləyir",
        }
    if node == "reunion":
        missing = update.get("missing") or []
        since = update.get("missing_since") or {}
        detail = ", ".join(f"{k} ({v} il)" for k, v in since.items())
        return {
            "did": f"keçmişlə müqayisə: {detail}" if missing else "altarda hər şey yerindədir",
            "wrote": "missing · missing_since · arrived",
            "note": "bu hesablama visits[] üzərindədir — checkpointer olmasa siyahı boş olardı",
            "next": "qiymət və calaverita — iki LLM node-u paralel",
        }
    if node == "judge_ofrenda":
        j = update.get("judgement") or {}
        return {
            "did": f"model altarı qiymətləndirdi: {j.get('warmth', '?')}/100",
            "wrote": "judgement ← {warmth, verdict, longing}",
            "note": "sxem üzrə cavab — mətn parse etmək lazım deyil",
            "next": "söz — bu rəy ruhun cümləsinə daxil olacaq",
        }
    if node == "write_calaverita":
        return {
            "did": "dördmisralı zarafat epitafiya yazıldı",
            "wrote": "calaverita",
            "note": "keçən ilin şeiri prompt-da idi — model təkrar etmir",
            "next": "söz",
        }
    if node == "speak_to_family":
        return {
            "did": "ruh ailəyə müraciət etdi",
            "wrote": "words · messages",
            "note": "rəqəmlər state-dən gəldi, model yalnız cümləyə çevirdi",
            "next": "vida — il bağlanacaq",
        }
    if node == "farewell":
        rem = update.get("remembrance", "?")
        return {
            "did": f"xatırlanma yeniləndi → {rem}",
            "wrote": "visits ← bu ilin qeydi (operator.add) · calaveritas",
            "note": "bu gecə buradan sonra tarixə çevrilir",
            "next": "son" if isinstance(rem, int) and rem > 0 else "üçüncü ölüm",
        }
    if node == "third_death":
        return {
            "did": "xatırlanma sıfıra düşdü",
            "wrote": "forgotten ← True",
            "note": "qraf öz checkpoint-ini silə bilməz — bu, runner-in işidir",
            "next": "checkpointer.delete_thread()",
        }
    return {"did": last, "wrote": ", ".join(update.keys()), "next": ""}


def _clean(values: dict) -> dict:
    """Mesajlar JSON-a çevrilmir — vizualizasiyaya lazım da deyil."""
    return {k: v for k, v in values.items() if k != "messages"}


def _history(config: dict, limit: int = 200) -> list[dict]:
    rows = []
    for index, snap in enumerate(GRAPH.get_state_history(config)):
        if index >= limit:
            break
        rows.append(
            {
                "id": snap.config["configurable"]["checkpoint_id"],
                "index": index,
                "year": snap.values.get("year") if isinstance(snap.values, dict) else None,
                "next": list(snap.next),
                "can_fork": list(snap.next) == ["follow_petals"],
                "remembrance": snap.values.get("remembrance")
                if isinstance(snap.values, dict)
                else None,
            }
        )
    return rows


# --------------------------------------------------------------------------
async def pump(ws: WebSocket, payload, config, thread_config=None) -> None:
    """Qrafı thread-də işlədir, hadisələri WebSocket-ə ötürür.

    `thread_config` budaqlanma (fork) üçündür: `config` konkret bir
    checkpoint-ə bağlı olanda yekun vəziyyəti ondan oxumaq olmaz — thread
    səviyyəsindəki config lazımdır.
    """
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    soul = config["configurable"]["thread_id"]
    # Addım sayğacı: interrupt-dan sonra davam edəndə nömrələr sıfırlanmasın.
    step = [STEP.get(soul, 0)]
    failed = False

    def worker() -> None:
        try:
            for chunk in GRAPH.stream(payload, config, stream_mode="updates"):
                loop.call_soon_threadsafe(queue.put_nowait, chunk)
        except Exception as exc:  # brauzerə də göstərək
            loop.call_soon_threadsafe(queue.put_nowait, {"__error__": str(exc)})
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    threading.Thread(target=worker, daemon=True).start()

    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        if "__error__" in chunk:
            failed = True
            await ws.send_json({"type": "error", "message": chunk["__error__"]})
            continue
        if "__interrupt__" in chunk:
            STEP[soul] = step[0]
            await ws.send_json({"type": "api", "line": API_LINES["wait_for_family"], "kind": "pause"})
            await ws.send_json({"type": "interrupt", "payload": chunk["__interrupt__"][0].value})
            return
        for node, update in chunk.items():
            if node.startswith("__"):
                continue
            update = _clean(update or {})
            step[0] += 1
            await ws.send_json(
                {
                    "type": "flow",
                    "step": step[0],
                    "node": node,
                    "label": LABELS.get(node, node),
                    "role": ROLES.get(node, ""),
                    "api": api_line(node, update),
                    **describe(node, update, soul),
                }
            )
            await ws.send_json({"type": "node", "node": node, "update": update})

    STEP[soul] = step[0]
    if failed:
        return
    final = thread_config or config
    snapshot = GRAPH.get_state(final)
    await ws.send_json(
        {
            "type": "api",
            "kind": "call",
            "line": f"get_state(config).values  →  {len(snapshot.values.get('visits', []))} ziyarət, "
            f"xatırlanma {snapshot.values.get('remembrance', '?')}",
        }
    )
    await ws.send_json(
        {
            "type": "done",
            "values": _clean(snapshot.values),
            "history": _history(final),
        }
    )


async def process_message(ws, message):
    soul = message.get("soul", "abuela")
    data = soul_data(soul)
    config = branch_config(soul, message.get("branch_id"))
    action = message.get("action")
    if action == "run":
        if message.get("branch_id"):
            raise ValueError("Yeni gecə üçün əsas hekayəyə qayıdın")
        if GRAPH.get_state(config).next:
            raise ValueError("Əvvəl yarımçıq gecəni davam etdirin")
        year = int(message["year"])
        if str(year) not in data.get("years", {}):
            raise ValueError("Bu il üçün altar yoxdur")
        payload = {"year": year, "prepared_ofrenda": gift_list(message["gifts"]) if "gifts" in message else None}
        if not GRAPH.get_state(config).values.get("name"):
            payload |= new_soul(data["name"], data["kind"], data.get("relation", ""), data.get("display", ""))
            payload["remembrance"] = data.get("remembrance", 100)
        STEP[soul] = 0
        await ws.send_json({"type": "start", "year": year})
        await pump(ws, payload, config)
    elif action == "resume":
        snapshot = GRAPH.get_state(config)
        if not snapshot.next:
            raise ValueError("Davam etdiriləcək gecə yoxdur")
        gift = message.get("gift", "").strip()
        if not gift or len(gift) > 80:
            raise ValueError("Qısa bir əşya adı daxil edin")
        await pump(ws, Command(resume=gift), config)
    elif action == "fork":
        if message.get("branch_id"):
            raise ValueError("Müqayisə üçün əsas hekayədən bir an seçin")
        target = next((snap for snap in GRAPH.get_state_history(config)
                       if snap.config["configurable"]["checkpoint_id"] == message.get("checkpoint")), None)
        if target is None or list(target.next) != ["follow_petals"]:
            raise ValueError("Altarın oxunduğu, çiçək ilə işarələnən bir an seçin")
        gifts = gift_list(message.get("gifts", []))
        ofrenda = list(dict.fromkeys(list(target.values.get("ofrenda", [])) + gifts))
        # The baseline is immutable. Replay lives in a separate thread so the
        # main history and its visit reducer never accumulate alternative years.
        baseline = next((snap.values for snap in GRAPH.get_state_history(config)
                         if snap.values.get("year") == target.values.get("year") and not snap.next), None)
        if baseline is None:
            raise ValueError("Bu ilin əsas gecəsi bitdikdən sonra müqayisə edə bilərsiniz")
        branch_id = "branch-" + uuid.uuid4().hex
        branch = {"configurable": {"thread_id": branch_id}}
        cloned = dict(target.values)
        cloned["ofrenda"] = ofrenda
        cloned["prepared_ofrenda"] = None
        branch = GRAPH.update_state(branch, cloned, as_node="read_ofrenda")
        with _conn:
            _conn.execute("INSERT INTO story_branches(id,soul,baseline,year) VALUES(?,?,?,?)",
                          (branch_id, soul, json.dumps(_clean(baseline), ensure_ascii=False), target.values.get("year")))
        await ws.send_json({"type": "fork", "branch_id": branch_id, "ofrenda": ofrenda})
        await pump(ws, None, branch, thread_config={"configurable": {"thread_id": branch_id}})
    elif action == "forget":
        narration.forget(soul)
        # The user chose immediate forgetting; remove associated alternatives too.
        for row in _conn.execute("SELECT id FROM story_branches WHERE soul=?", (soul,)).fetchall():
            CHECKPOINTER.delete_thread(row[0])
        with _conn:
            _conn.execute("DELETE FROM story_branches WHERE soul=?", (soul,))
        CHECKPOINTER.delete_thread(soul)
        await ws.send_json({"type": "forgotten", "soul": soul})
    else:
        raise ValueError("Naməlum əməliyyat")


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    try:
        while True:
            message = await ws.receive_json()
            try:
                if RUN_LOCK.locked():
                    raise ValueError("Başqa gecə işləyir. Bir az sonra yenidən yoxlayın")
                async with RUN_LOCK:
                    await process_message(ws, message)
            except (ValueError, KeyError, TypeError) as exc:
                await ws.send_json({"type": "error", "message": str(exc)})
            except Exception:
                await ws.send_json({"type": "error", "message": "Gecə tamamlanmadı. Səhifəni yeniləyib yaddaşdan davam edin."})
    except WebSocketDisconnect:
        return


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
