"""
El Regreso — vahid giriş nöqtəsi.

PyCharm-da yaşıl ▶ düyməsi məhz bu faylı işə salır: server qalxır, brauzer
özü açılır, baza boşdursa demo məlumatı doldurulur. Heç bir əmr yazmaq
lazım deyil.

    python main.py                  # server + brauzer (standart)
    python main.py --port 8030      # başqa port
    python main.py --no-browser     # brauzeri açma
    python main.py --fresh          # bazanı silib demo-nu yenidən qur
    python main.py --demo           # web yox, terminalda 5 illik demo
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "altar.db"

# Windows-da çıxış boruya yönələndə (PyCharm Run pəncərəsi, dev server)
# kodlaşdırma cp1252 olur və Azərbaycan hərflərində proses çökür.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
if sys.platform == "win32":
    os.system("")  # ANSI rəngləri

# PyCharm faylı birbaşa işə salanda `solution` və `web` paketlərinin
# tapılması üçün layihə kökü sys.path-ə əlavə olunur.
sys.path.insert(0, str(ROOT))


# --------------------------------------------------------------------------
def pick_port(preferred: int) -> int:
    """İstənilən port məşğuldursa, azad birini tapır.

    Diqqət: bu, adətən əvvəlki işə salmanın hələ də işlədiyini bildirir.
    Səssizcə başqa porta keçmək təhlükəlidir — brauzerdə KÖHNƏ server
    açıq qalır və kodda etdiyin dəyişikliklər görünmür. Ona görə açıq
    xəbərdarlıq edirik.
    """
    for candidate in (preferred, preferred + 1, preferred + 2, 0):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", candidate))
                port = probe.getsockname()[1]
            except OSError:
                continue
        if port != preferred:
            print()
            print(f"  ⚠  {preferred} portu məşğuldur — əvvəlki işə salma hələ işləyir.")
            print(f"     Bu proses {port} portunda qalxacaq.")
            print("     Köhnəsini bağlamaq üçün PyCharm-da qırmızı ■ düyməsini bas")
            print("     və ya: taskkill /F /IM python.exe")
        return port
    return preferred


def open_when_ready(url: str, port: int, timeout: float = 90.0) -> None:
    """Brauzeri yalnız server HƏQİQƏTƏN cavab verəndə açır.

    Sabit gecikmə (məsələn `Timer(1.2, ...)`) işləmir: `langgraph` və
    `langchain` idxalı maşından asılı olaraq 3–15 saniyə çəkir və brauzer
    boş qapını döyür — ERR_CONNECTION_REFUSED. Ona görə portu qısa
    fasilələrlə yoxlayırıq.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.4):
                webbrowser.open(url)
                return
        except OSError:
            time.sleep(0.25)
    print("  server vaxtında qalxmadı — brauzeri əl ilə aç:", url)


def seed_demo() -> None:
    """Baza boşdursa, üç illik tarixçə qur ki, ilk ekran boş olmasın.

    Bu, demo rahatlığıdır: vizualizasiyanın əsl mənası yalnız keçmiş
    ziyarətlər olanda görünür.
    """
    from langgraph.checkpoint.sqlite import SqliteSaver

    from solution.graph import build_graph
    from solution.state import new_soul

    os.environ["EL_REGRESO_SLOW"] = "0"
    plan = [("abuela", [2021, 2022, 2023]), ("mateo", [2021, 2022])]

    import json

    with SqliteSaver.from_conn_string(str(DB_PATH)) as checkpointer:
        graph = build_graph(checkpointer)
        for soul, years in plan:
            data = json.loads((ROOT / "altar" / f"{soul}.json").read_text(encoding="utf-8"))
            config = {"configurable": {"thread_id": soul}}
            for year in years:
                values = graph.get_state(config).values
                # İdempotent: eyni il iki dəfə yazılmasın (proses təkrar
                # işə düşsə də ziyarətlər cütləşməsin).
                if year in {v["year"] for v in values.get("visits", [])}:
                    continue
                payload: dict = {"year": year}
                if not values.get("name"):
                    payload |= new_soul(
                        data["name"], data["kind"], data.get("relation", ""), data.get("display", "")
                    )
                graph.invoke(payload, config)
    print(f"  demo məlumatı quruldu: {DB_PATH.name}")


def run_cli_demo() -> None:
    """Terminal demosu — beş il, hər biri AYRICA proses.

    Ayrıca proses olması vacibdir: checkpointing-in bütün mənası budur.
    Bir dövrədə beş il işlətmək eyni şey deyil.
    """
    steps = [
        ["--soul", "abuela", "--year", "2021", "--slow", "0.35"],
        ["--soul", "abuela", "--year", "2022"],
        ["--soul", "abuela", "--year", "2023"],
        ["--soul", "abuela", "--year", "2024", "--no-input"],
        ["--soul", "abuela", "--resume", "--gift", "cempasúchil", "--no-input"],
        ["--soul", "abuela", "--year", "2025"],
    ]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    for args in steps:
        subprocess.run([sys.executable, "-u", "-m", "solution.run_year", *args], cwd=str(ROOT), env=env)
        time.sleep(0.3)


# --------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="El Regreso")
    parser.add_argument("--port", type=int, default=8020)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--fresh", action="store_true", help="bazanı sil və yenidən qur")
    parser.add_argument("--demo", action="store_true", help="web yox, terminal demosu")
    args = parser.parse_args()

    if args.fresh and DB_PATH.exists():
        DB_PATH.unlink()

    if args.demo:
        if not DB_PATH.exists():
            pass  # terminal demosu onsuz da sıfırdan başlayır
        run_cli_demo()
        return

    if not DB_PATH.exists():
        seed_demo()

    port = pick_port(args.port)
    url = f"http://127.0.0.1:{port}"

    print()
    print("  El Regreso — bir gecə, hər il")
    print(f"  {url}")
    print("  server qalxır (langgraph yüklənir, bir neçə saniyə çəkə bilər)…")
    print("  dayandırmaq: Ctrl+C")
    print()

    if not args.no_browser:
        threading.Thread(target=open_when_ready, args=(url, port), daemon=True).start()

    import uvicorn

    # Tətbiqi sətir kimi ("web.server:app") vermirik: onda modulu uvicorn
    # özü idxal edir və nəticə işlək qovluqdan asılı olur — PyCharm başqa
    # qovluqdan işə salanda «Could not import module web.server» verir.
    # Obyekti özümüz idxal edirik; ROOT artıq sys.path-dədir.
    from web.server import app

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  şam söndürüldü.")
