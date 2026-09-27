"""
Mictlán keçidi — SUBQRAF.

Astek inancına görə ruh evə çatmazdan əvvəl ölülər diyarının maneələrindən
keçir. Bunu əsas qrafın içinə 4 ayrı node kimi yazmaq olardı — amma onda
əsas qraf oxunmaz hala düşərdi.

Ona görə keçid **öz qrafıdır** və əsas qrafa **bir node kimi** qoşulur.
Diqqət ediləsi iki şey:

1. Subqrafın öz state sxemi var (`CrossingState`) — əsas state-in yalnız
   ehtiyacı olan sahələrini paylaşır, üstəlik özünə məxsus `strength` və
   `rests` sahələri var. Ortaq adlı sahələr avtomatik ötürülür; qalanları
   yalnız subqrafın içində yaşayır və valideyn state-ə çıxmır.

2. Subqraf valideynin `journey` sahəsinə YAZMIR — öz `crossing_steps`
   sahəsinə yazır. Səbəb incə və vacibdir: subqraf bitəndə valideynə
   state-in TAM dəyəri qaytarılır, yalnız dəyişiklik yox. Əgər subqraf
   `journey`-ə yazsaydı, valideynin mövcud jurnalı ona qayıdıb reducer-lə
   ikinci dəfə əlavə olunardı — bütün sətirlər cütləşərdi.
   Qayda: **valideyndə toplayan (accumulating) sahəyə subqrafdan yazma;
   subqrafa öz sahəsini ver.**
"""

from __future__ import annotations

from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from .state import gather


class CrossingState(TypedDict, total=False):
    # --- valideynlə paylaşılan sahələr -----------------------------------
    ofrenda: list[str]
    kind: str
    crossing_report: str
    crossing_steps: Annotated[list[str], gather]
    # --- yalnız subqrafın daxili sahələri --------------------------------
    strength: int
    rests: int


def _strength(state: CrossingState) -> int:
    return state.get("strength", 3)


def itzcuintlan(state: CrossingState) -> dict:
    """Birinci səviyyə: Apanohuacalhuia çayı.

    Xoloitzcuintle iti ruhu çaydan keçirir. Altarda su varsa, keçid asandır;
    yoxsa it ruhu daşıyır və güc itir.
    """
    has_water = "su" in state.get("ofrenda", [])
    if has_water:
        return {"strength": _strength(state), "crossing_steps": ["Itzcuintlan — çay sakit keçildi"]}
    return {
        "strength": _strength(state) - 1,
        "crossing_steps": ["Itzcuintlan — su yox idi, it ruhu daşıdı"],
    }


def tepeme_monamictlan(state: CrossingState) -> dict:
    """İkinci səviyyə: bir-birinə çırpılan dağlar. Güc tələb edir."""
    fed = "pan de muerto" in state.get("ofrenda", []) or "tamales" in state.get("ofrenda", [])
    return {
        "strength": _strength(state) + (1 if fed else -1),
        "crossing_steps": [
            "Tepeme Monamictlan — çörək gücü çatdı"
            if fed
            else "Tepeme Monamictlan — ac keçdi, dağlar ağır idi"
        ],
    }


def itzehecayan(state: CrossingState) -> dict:
    """Üçüncü səviyyə: obsidian küləkləri. Copal tüstüsü yolu göstərir."""
    smoke = "copal" in state.get("ofrenda", [])
    return {
        "strength": _strength(state) + (1 if smoke else -2),
        "crossing_steps": [
            "Itzehecayan — copal tüstüsü küləyi yardı"
            if smoke
            else "Itzehecayan — küləkdə yön itdi"
        ],
    }


def rest(state: CrossingState) -> dict:
    """Ruh dayanıb gücünü toplayır. Subqrafın öz daxili loop-u."""
    return {
        "strength": _strength(state) + 2,
        "rests": state.get("rests", 0) + 1,
        "crossing_steps": ["ruh bir an dayandı"],
    }


def crossed(state: CrossingState) -> Literal["rest", "report"]:
    """Subqrafın çıxış şərti: güc sıfıra düşübsə, dincəlmək lazımdır.

    İki həddi var — gücün bərpası (`strength`) və cəhd sayı (`rests`).
    Yalnız gücə baxsaydıq, copalsız ruh hər dövrədə 2 itirib 2 qazanaraq
    sonsuza qədər fırlanardı. Loop-un ikinci, "sərt" həddi həmişə lazımdır.
    """
    if _strength(state) > 0 or state.get("rests", 0) >= 2:
        return "report"
    return "rest"


def report(state: CrossingState) -> dict:
    """Keçidin nəticəsi — valideyn state-ə qayıdan yeganə xülasə."""
    s = _strength(state)
    verdict = "rahat" if s >= 3 else "çətin" if s >= 1 else "güclə"
    return {"crossing_report": f"Mictlán {verdict} keçildi (güc: {s})"}


def build_crossing():
    """Subqrafı qurub kompilyasiya edir. Checkpointer VERİLMİR —
    subqraf valideynin checkpointer-ini avtomatik miras alır."""
    g = StateGraph(CrossingState)
    g.add_node("itzcuintlan", itzcuintlan)
    g.add_node("tepeme_monamictlan", tepeme_monamictlan)
    g.add_node("itzehecayan", itzehecayan)
    g.add_node("rest", rest)
    g.add_node("report", report)

    g.add_edge(START, "itzcuintlan")
    g.add_edge("itzcuintlan", "tepeme_monamictlan")
    g.add_edge("tepeme_monamictlan", "itzehecayan")
    g.add_conditional_edges("itzehecayan", crossed, {"rest": "rest", "report": "report"})
    g.add_edge("rest", "itzehecayan")
    g.add_edge("report", END)
    return g.compile()
