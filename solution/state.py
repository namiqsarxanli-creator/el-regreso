"""
El Regreso — State (Ofrenda).

Día de los Muertos-da altar (ofrenda) bir siyahı deyil, bir *quruluşdur*:
bəzi şeylər hər il yenidən qoyulur (üstünə yazılır), bəziləri illər boyu
yığılır (heç vaxt silinmir), bəziləri isə bir dəfə dadılır və təkrarlanmır.

LangGraph-da bu fərqi `reducer`-lər yaradır. Aşağıdakı dörd sahə qəsdən
dörd fərqli davranışa malikdir — tapşırığın 1-ci bloku budur.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph.message import add_messages

# --------------------------------------------------------------------------
# Sentinel
# --------------------------------------------------------------------------
# Toplayan (accumulating) reducer-in problemi budur: bir dəfə yığmağa
# başladısa, onu boşaltmaq mümkün deyil — çünki hər update əlavə olunur.
# Bizə isə hər il təmiz başlanğıc lazımdır: keçən ilin qoxuları bu ilin
# ruhuna keçməməlidir. Həlli — reducer-in başa düşdüyü xüsusi işarə.
RESET = "__RESET__"


def _prepare(old: list[str] | None, new: list[str] | str | None) -> tuple[list[str], list[str]]:
    """Hər üç reducer üçün ortaq giriş emalı.

    `new` üç formada gələ bilər:
      "su"                  → tək element
      ["su", "duz"]         → siyahı
      RESET                 → sahəni boşalt
      [RESET, "yeni addım"] → boşalt və dərhal yenisini yaz (dusk node-u
                              məhz bunu edir: köhnə il silinir, yeni il
                              eyni update-də başlayır)
    """
    base = list(old or [])
    if new is None:
        return base, []
    if isinstance(new, str):
        new = [new]
    new = list(new)
    if RESET in new:
        base = []
        new = new[new.index(RESET) + 1 :]
    return base, new


# --------------------------------------------------------------------------
# Reducer 1 — toplayan, amma sıfırlana bilən
# --------------------------------------------------------------------------
def gather(old: list[str] | None, new: list[str] | str | None) -> list[str]:
    """Paralel node-lardan gələn hissləri toplayır; RESET gələndə boşaldır.

    `taste_food`, `smell_copal` və `see_photos` eyni superstep-də işləyir və
    hər biri `senses` sahəsinə yazır. Reducer olmasaydı, LangGraph eyni
    sahəyə iki paralel yazışı birləşdirə bilməyib xəta verərdi
    (InvalidUpdateError). Fan-in məhz burada baş verir.
    """
    base, new = _prepare(old, new)
    return base + new


# --------------------------------------------------------------------------
# Reducer 2 — bir dəfə dadılır
# --------------------------------------------------------------------------
def taste_once(old: list[str] | None, new: list[str] | str | None) -> list[str]:
    """Ruh yeməyin mahiyyətini alır — ikinci dəfə dadmağın mənası yoxdur.

    Sıranı qoruyur (set istifadə etmirik: altarın ardıcıllığı da yaddaşdır).
    """
    result, new = _prepare(old, new)
    for item in new:
        if item not in result:
            result.append(item)
    return result


# --------------------------------------------------------------------------
# Reducer 3 — yolun izi
# --------------------------------------------------------------------------
def trail(old: list[str] | None, new: list[str] | str | None) -> list[str]:
    """Səyahət jurnalı: eyni addım ardıcıl iki dəfə yazılmır.

    Loop-a düşən qraf (`follow_petals` → `lost` → `wait_for_family` →
    `follow_petals`) jurnalı eyni sətirlə doldurmasın deyə. Diqqət: burada
    *ardıcıl* təkrar filtrlənir, uzaqdakı təkrar yox — ruh eyni yerə iki
    dəfə qayıda bilər və bu, jurnalda görünməlidir.
    """
    result, new = _prepare(old, new)
    for step in new:
        if not result or result[-1] != step:
            result.append(step)
    return result


# --------------------------------------------------------------------------
# State
# --------------------------------------------------------------------------
SoulKind = Literal["angelito", "difunto"]


class Visit(TypedDict):
    """Bir ilin ziyarət qeydi. `visits` sahəsində illərlə yığılır."""

    year: int
    ofrenda: list[str]
    tasted: list[str]
    arrived: bool
    remembrance: int
    note: str
    warmth: int  # modelin verdiyi qiymət (structured output)
    words: str
    calaverita: str


class SoulState(TypedDict, total=False):
    """Bir ruhun bütün varlığı. Checkpointer bunu diskdə saxlayır.

    Sahələrin reducer davranışı (README-dəki cədvəlin kod qarşılığı):

    | sahə          | davranış            | səbəb                                  |
    |---------------|---------------------|----------------------------------------|
    | `visits`      | operator.add        | illər yığılır, heç vaxt silinmir       |
    | `ofrenda`     | overwrite (reducersiz) | hər il altar yenidən qurulur        |
    | `tasted`      | taste_once          | təkrar dadılmır                        |
    | `senses`      | gather              | paralel node-lardan fan-in             |
    | `journey`     | trail               | ardıcıl təkrarsız iz                   |
    | `remembrance` | overwrite           | tək bir cari dəyər                     |
    """

    # --- kimlik: ilk ildə yazılır, sonra dəyişmir --------------------------
    name: str  # altar/<name>.json — thread_id ilə eynidir
    display: str  # görünən ad: "Abuela Remedios"
    kind: SoulKind
    relation: str

    # --- bu ilin sessiyası: hər il üstünə yazılır -------------------------
    year: int
    ofrenda: list[str]
    prepared_ofrenda: list[str] | None
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

    # --- reducer-li sahələr ------------------------------------------------
    visits: Annotated[list[Visit], operator.add]
    tasted: Annotated[list[str], taste_once]
    senses: Annotated[list[str], gather]
    crossing_steps: Annotated[list[str], gather]  # subqrafdan gələn sətirlər
    # İllər boyu yığılan kalaveritalar: model keçən ilkini görür və
    # təkrar etmir — yəni yaddaş generasiyaya təsir edir.
    calaveritas: Annotated[list[str], operator.add]
    # Bu gecə hansı modellər danışdı (paralel node-lardan fan-in ilə gəlir).
    voices: Annotated[list[str], gather]
    journey: Annotated[list[str], trail]
    messages: Annotated[list[Any], add_messages]

    # --- yaddaşın ölçüsü ---------------------------------------------------
    remembrance: int
    forgotten: bool


def new_soul(name: str, kind: SoulKind, relation: str = "", display: str = "") -> SoulState:
    """Bir ruhun ilk ili — yalnız thread boş olanda çağırılır."""
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
