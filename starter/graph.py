"""
BLOK 3 — Qrafın yığılması.

Bu faylda BİR SƏTİR də iş məntiqi olmamalıdır: yalnız node-lar və keçidlər.
Qrafı oxuyan adam node-un içinə baxmadan bütün marşrutları görməlidir.

Dörd keçid növü burada nümayiş olunur:

  1. Şərti keçid START-dan     → which_night (angelito / difunto)
  2. Command ilə marşrut       → follow_petals node-un İÇİNDƏN seçir
  3. Loop + hədd               → lost → wait_for_family → follow_petals
  4. Fan-out / fan-in          → üç hiss node-u → reunion
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
    """TODO 3.7 — qrafı qur.

    1-ci həftə: `checkpointer=None` ilə təhvil verilir (yaddaşsız).
    2-ci həftə: eyni funksiyaya checkpointer verilir — və layihə canlanır.
    """
    g = StateGraph(SoulState)

    # --- node-lar ---------------------------------------------------------
    # TODO: 16 node əlavə et. Subqraf da adi node kimi əlavə olunur:
    #       g.add_node("mictlan_crossing", build_crossing())

    # --- 1. şərti giriş ---------------------------------------------------
    # TODO: g.add_conditional_edges(START, which_night, {...})

    # --- 2. follow_petals üçün OX ÇƏKİLMİR --------------------------------
    # Marşrutu node özü qaytarır: Command(goto=...).

    # --- 3. loop və onun həddi --------------------------------------------
    # TODO: lost → (can_retry) → wait_for_family | farewell
    #       wait_for_family → follow_petals

    # --- 4. fan-out / fan-in ----------------------------------------------
    # TODO: mictlan_crossing → üç hiss node-u (paralel)
    #       hər üçü → reunion (LangGraph hamısını gözləyir)

    # --- 5. ikinci paralel qrup: iki LLM node-u ---------------------------
    # TODO: reunion → judge_ofrenda və reunion → write_calaverita
    #       ikisi də → speak_to_family
    #       (biri sxem üzrə qiymət verir, biri şeir yazır; eyni superstep)

    # --- son --------------------------------------------------------------
    # TODO: speak_to_family → farewell
    #       farewell → (is_forgotten) → third_death | END

    raise NotImplementedError("TODO 3.7")


if __name__ == "__main__":  # python -m starter.graph --png
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
