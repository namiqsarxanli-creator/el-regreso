"""
BLOK 1 — State (Ofrenda).

Altar bir siyahı deyil, quruluşdur: bəzi şeylər hər il yenidən qoyulur,
bəziləri illərlə yığılır, bəziləri bir dəfə dadılır. Bu fərqi reducer-lər
yaradır.

Bu faylda üç reducer yazacaqsan. Üçü də fərqli davranmalıdır — əks halda
blokdan bal getmir.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph.message import add_messages

# Toplayan reducer-in problemi: bir dəfə yığmağa başladısa, boşaltmaq
# mümkün deyil. Bizə isə hər il təmiz başlanğıc lazımdır. Həlli — reducer-in
# başa düşdüyü xüsusi işarə.
RESET = "__RESET__"


# ==========================================================================
# TODO 1.1 — ortaq giriş emalı
# ==========================================================================
def _prepare(old: list[str] | None, new: list[str] | str | None) -> tuple[list[str], list[str]]:
    """`new` dörd formada gələ bilər — hamısını normallaşdır:

        "su"                  → tək element
        ["su", "duz"]         → siyahı
        RESET                 → sahəni boşalt
        [RESET, "yeni addım"] → boşalt və dərhal yenisini yaz

    Qaytarır: (baza siyahısı, əlavə olunacaq elementlər)
    """
    raise NotImplementedError("TODO 1.1")


# ==========================================================================
# TODO 1.2 — paralel node-lardan gələni toplayan reducer
# ==========================================================================
def gather(old: list[str] | None, new: list[str] | str | None) -> list[str]:
    """Üç paralel node eyni sahəyə yazır; hamısı saxlanılmalıdır.

    Reducer olmasa nə baş verir? Sına və README-də bir cümlə ilə yaz.
    """
    raise NotImplementedError("TODO 1.2")


# ==========================================================================
# TODO 1.3 — təkrarı süzən reducer
# ==========================================================================
def taste_once(old: list[str] | None, new: list[str] | str | None) -> list[str]:
    """Ruh yeməyin mahiyyətini alır — eyni şey iki dəfə əlavə olunmamalıdır.

    Diqqət: `set()` istifadə etmə, sıra qorunmalıdır.
    """
    raise NotImplementedError("TODO 1.3")


# ==========================================================================
# TODO 1.4 — ardıcıl təkrarı süzən reducer (səyahət jurnalı)
# ==========================================================================
def trail(old: list[str] | None, new: list[str] | str | None) -> list[str]:
    """Loop-a düşən qraf jurnalı eyni sətirlə doldurmasın.

    YALNIZ ardıcıl təkrar süzülür: ruh eyni yerə iki dəfə qayıda bilər və
    bu, jurnalda görünməlidir. `taste_once`-dan fərqi budur.
    """
    raise NotImplementedError("TODO 1.4")


SoulKind = Literal["angelito", "difunto"]


class Visit(TypedDict):
    """Bir ilin ziyarət qeydi."""

    year: int
    ofrenda: list[str]
    tasted: list[str]
    arrived: bool
    remembrance: int
    note: str
    warmth: int  # modelin verdiyi qiymət (structured output)


class SoulState(TypedDict, total=False):
    """TODO 1.5 — sahələri reducer-lərlə tamamla.

    Hər sahə üçün özünə sual ver: bu dəyər yığılmalıdır, yoxsa üstünə
    yazılmalıdır? Cavabı README-də bir cümlə ilə əsaslandır.
    """

    # --- kimlik: ilk ildə yazılır, sonra dəyişmir --------------------------
    name: str
    display: str
    kind: SoulKind
    relation: str

    # --- bu ilin sessiyası: hər il üstünə yazılır (reducer YOXDUR) --------
    year: int
    ofrenda: list[str]
    petal_path: bool
    attempts: int
    arrived: bool
    crossing_report: str
    words: str
    missing: list[str]
    missing_since: dict[str, int]
    plea: str  # ruhun öz xahişi — modelin yazdığı interrupt mətni
    judgement: dict  # structured output: warmth / verdict / longing
    calaverita: str  # bu ilin zarafat epitafiyası

    # --- reducer-li sahələr -----------------------------------------------
    # TODO: `visits` illər boyu yığılmalıdır və HEÇ VAXT silinməməlidir
    visits: list[Visit]
    # TODO: `tasted` → taste_once
    tasted: list[str]
    # TODO: `senses` → gather (fan-in burada baş verir)
    senses: list[str]
    # TODO: `crossing_steps` → gather (subqrafdan gələn sətirlər)
    crossing_steps: list[str]
    # TODO: `journey` → trail
    journey: list[str]
    # TODO: `calaveritas` illər boyu yığılmalıdır (operator.add) — model
    #       keçən ilinkini görüb təkrar etməməlidir. Sıfırlanmır!
    calaveritas: list[str]
    # TODO: `voices` → gather (bu gecə hansı modellər danışdı; paralel
    #       node-lardan fan-in ilə gəlir)
    voices: list[str]
    messages: Annotated[list[Any], add_messages]

    # --- yaddaşın ölçüsü ---------------------------------------------------
    remembrance: int
    forgotten: bool


def new_soul(name: str, kind: SoulKind, relation: str = "", display: str = "") -> SoulState:
    """Bir ruhun ilk ili — yalnız thread boş olanda çağırılır. (Hazırdır.)"""
    return {
        "name": name,
        "display": display or name,
        "kind": kind,
        "relation": relation,
        "remembrance": 100,
        "forgotten": False,
        "attempts": 0,
        "visits": [],
        "journey": [],
        "tasted": [],
        "senses": [],
        "crossing_steps": [],
        "calaveritas": [],
        "voices": [],
        "messages": [],
    }
