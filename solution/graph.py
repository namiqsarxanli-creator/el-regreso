"""
El Regreso — qrafın yığılması.

Burada bir sətir də iş məntiqi yoxdur: yalnız node-lar və keçidlər.
Bu ayrılıq şüurludur — qrafı oxuyan adam bir dəqiqədə bütün marşrutları
görməlidir, node-un içini oxumadan.

Keçidlərin dörd növü (tapşırığın 3-cü bloku):

  1. Şərti keçid START-dan          → which_night (angelito / difunto)
  2. Command ilə marşrut            → follow_petals node-un içindən seçir
  3. Loop + hədd                    → lost → wait_for_family → follow_petals
  4. Fan-out / fan-in               → üç hiss node-u → reunion
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

from langgraph.graph import END, START, StateGraph

from .crossing import build_crossing
from .nodes import (
    can_retry,
    dusk_angelitos,
    dusk_difuntos,
    farewell,
    follow_petals,
    is_forgotten,
    judge_ofrenda,
    lost,
    read_ofrenda,
    reunion,
    see_photos,
    smell_copal,
    speak_to_family,
    taste_food,
    third_death,
    wait_for_family,
    which_night,
    write_calaverita,
)
from .state import SoulState


def build_graph(checkpointer=None):
    """Qrafı qurur. `checkpointer=None` olanda qraf yaddaşsız işləyir —
    tapşırığın 1-ci həftəsi məhz belə təhvil verilir."""
    g = StateGraph(SoulState)

    # --- node-lar ---------------------------------------------------------
    g.add_node("dusk_angelitos", dusk_angelitos)
    g.add_node("dusk_difuntos", dusk_difuntos)
    g.add_node("read_ofrenda", read_ofrenda)
    g.add_node("follow_petals", follow_petals)
    g.add_node("lost", lost)
    g.add_node("wait_for_family", wait_for_family)
    # Subqraf bir node kimi qoşulur — içindəki 5 node buradan görünmür.
    g.add_node("mictlan_crossing", build_crossing())
    g.add_node("taste_food", taste_food)
    g.add_node("smell_copal", smell_copal)
    g.add_node("see_photos", see_photos)
    g.add_node("reunion", reunion)
    g.add_node("judge_ofrenda", judge_ofrenda)
    g.add_node("write_calaverita", write_calaverita)
    g.add_node("speak_to_family", speak_to_family)
    g.add_node("farewell", farewell)
    g.add_node("third_death", third_death)

    # --- 1. şərti giriş ---------------------------------------------------
    g.add_conditional_edges(
        START,
        which_night,
        {"dusk_angelitos": "dusk_angelitos", "dusk_difuntos": "dusk_difuntos"},
    )
    g.add_edge("dusk_angelitos", "read_ofrenda")
    g.add_edge("dusk_difuntos", "read_ofrenda")
    g.add_edge("read_ofrenda", "follow_petals")

    # --- 2. follow_petals üçün ox çəkilmir ---------------------------------
    # Marşrutu node özü qaytarır: Command(goto="mictlan_crossing" | "lost").

    # --- 3. loop və onun həddi --------------------------------------------
    g.add_conditional_edges(
        "lost",
        can_retry,
        {"wait_for_family": "wait_for_family", "farewell": "farewell"},
    )
    g.add_edge("wait_for_family", "follow_petals")

    # --- 4. fan-out / fan-in ----------------------------------------------
    # Üç node eyni superstep-də paralel işləyir...
    g.add_edge("mictlan_crossing", "taste_food")
    g.add_edge("mictlan_crossing", "smell_copal")
    g.add_edge("mictlan_crossing", "see_photos")
    # ...və `reunion` hər üçü bitənə qədər gözləyir.
    g.add_edge("taste_food", "reunion")
    g.add_edge("smell_copal", "reunion")
    g.add_edge("see_photos", "reunion")

    # İkinci paralel qrup — iki LLM node-u eyni superstep-də işləyir:
    # biri sxem üzrə qiymət verir, biri şeir yazır.
    g.add_edge("reunion", "judge_ofrenda")
    g.add_edge("reunion", "write_calaverita")
    g.add_edge("judge_ofrenda", "speak_to_family")
    g.add_edge("write_calaverita", "speak_to_family")
    g.add_edge("speak_to_family", "farewell")

    # --- son: unudulma astanası -------------------------------------------
    g.add_conditional_edges(
        "farewell",
        is_forgotten,
        {"third_death": "third_death", "__end__": END},
    )
    g.add_edge("third_death", END)

    return g.compile(checkpointer=checkpointer)


if __name__ == "__main__":  # python -m solution.graph
    import sys
    from pathlib import Path

    graph = build_graph()
    mermaid = graph.get_graph(xray=True).draw_mermaid()
    out = Path(__file__).resolve().parent.parent / "docs"
    out.mkdir(exist_ok=True)
    (out / "graph.mmd").write_text(mermaid, encoding="utf-8")
    print(mermaid)
    if "--png" in sys.argv:
        try:
            (out / "graph.png").write_bytes(graph.get_graph(xray=True).draw_mermaid_png())
            print("\ndocs/graph.png yazıldı")
        except Exception as exc:
            print(f"\nPNG alınmadı ({exc}); docs/graph.mmd faylını mermaid.live-da aç")
