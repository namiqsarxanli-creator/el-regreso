"""
BLOK 2/3 — Mictlán keçidi: SUBQRAF.

Ruh evə çatmazdan əvvəl ölülər diyarının maneələrindən keçir. Bunu əsas
qrafın içinə 5 node kimi yazmaq olardı — amma onda əsas qraf oxunmaz hala
düşərdi. Ona görə keçid öz qrafıdır və əsas qrafa BİR NODE kimi qoşulur.

İki incə məqam var, ikisi də qiymətləndirilir:

1. Subqrafın öz state sxemi var. Valideynlə ortaq adlı sahələr avtomatik
   ötürülür; yalnız burada elan olunanlar (məsələn `strength`) subqrafın
   içində qalır və valideynə çıxmır.

2. Subqraf valideynin TOPLAYAN sahəsinə yazmamalıdır. Səbəbini özün tap:
   subqraf bitəndə valideynə nə qaytarılır — yalnız dəyişiklik, yoxsa
   state-in tam dəyəri? Səhv etsən, jurnal sətirləri cütləşəcək.
"""

from __future__ import annotations

from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from .state import gather


class CrossingState(TypedDict, total=False):
    """TODO 3.1 — sxemi tamamla.

    Valideynlə paylaşılan: ofrenda, kind, crossing_report, crossing_steps
    Yalnız daxili: strength, rests
    """

    ofrenda: list[str]
    kind: str
    crossing_report: str
    crossing_steps: Annotated[list[str], gather]
    strength: int
    rests: int


def _strength(state: CrossingState) -> int:
    return state.get("strength", 3)


# ==========================================================================
# TODO 3.2 — üç səviyyə
# ==========================================================================
def itzcuintlan(state: CrossingState) -> dict:
    """Apanohuacalhuia çayı. Altarda «su» varsa keçid asandır; yoxsa
    xoloitzcuintle iti ruhu daşıyır və güc azalır."""
    raise NotImplementedError("TODO 3.2")


def tepeme_monamictlan(state: CrossingState) -> dict:
    """Bir-birinə çırpılan dağlar. «pan de muerto» və ya «tamales» güc verir."""
    raise NotImplementedError("TODO 3.2")


def itzehecayan(state: CrossingState) -> dict:
    """Obsidian küləkləri. «copal» tüstüsü yolu göstərir, yoxsa güc itir."""
    raise NotImplementedError("TODO 3.2")


def rest(state: CrossingState) -> dict:
    """TODO 3.3 — subqrafın daxili loop-u. Gücü artır və cəhd sayğacını da."""
    raise NotImplementedError("TODO 3.3")


def crossed(state: CrossingState) -> Literal["rest", "report"]:
    """TODO 3.4 — çıxış şərti.

    Diqqət: yalnız gücə baxsan, copalsız ruh hər dövrədə eyni qədər itirib
    eyni qədər qazanaraq sonsuza qədər fırlana bilər. Loop-un İKİNCİ, sərt
    həddi də olmalıdır.
    """
    raise NotImplementedError("TODO 3.4")


def report(state: CrossingState) -> dict:
    """TODO 3.5 — valideynə qayıdan xülasə (`crossing_report`)."""
    raise NotImplementedError("TODO 3.5")


def build_crossing():
    """TODO 3.6 — subqrafı qur və kompilyasiya et.

    Checkpointer VERMƏ: subqraf valideynin checkpointer-ini miras alır.

    Marşrut:
        START → itzcuintlan → tepeme_monamictlan → itzehecayan
        itzehecayan → (şərti) rest | report
        rest → itzehecayan
        report → END
    """
    raise NotImplementedError("TODO 3.6")
