"""
BLOK 2 — Node-lar.

Beş fərqli node növü yazacaqsan. Node sayı yox, növ müxtəlifliyi
qiymətləndirilir:

  [saf funksiya]  LLM yoxdur, yalnız state hesablaması
  [tool]          xarici mənbədən (fayl) oxuyur          → hazır verilib
  [interrupt]     icranı dayandırıb insandan cavab gözləyir
  [paralel]       eyni superstep-də digərləri ilə işləyir
  [LLM]           modelə müraciət edir                   → voice.py hazırdır

Qayda: node yalnız DƏYİŞƏN sahələri qaytarır, bütün state-i yox.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Literal

from langchain_core.tools import tool
from langgraph.types import Command, interrupt

from .state import RESET, SoulState, Visit
from .voice import speak

ALTAR_DIR = Path(__file__).resolve().parent.parent / "altar"

PETAL = "cempasúchil"  # qadife gülü — ləçək yolu

# Angelitos (uşaq ruhları) 1 noyabrda gəlir və onlara spirtli içki
# qoyulmur. Şərti keçidin (conditional edge) səbəbi budur.
TASTE = {
    "angelito": {"süd", "şokolad", "oyuncaq", "şəkər kəllə", "pan de muerto", "meyvə"},
    "difunto": {"mezcal", "tamales", "pan de muerto", "qəhvə", "siqaret", "duz", "meyvə"},
}


def _breathe() -> None:
    """Demo üçün nəfəs — EL_REGRESO_SLOW=0.5. (Hazırdır.)"""
    delay = float(os.getenv("EL_REGRESO_SLOW", "0") or 0)
    if delay:
        time.sleep(delay)


# ==========================================================================
# TODO 2.1 — giriş marşrutu (router funksiyası, node DEYİL)
# ==========================================================================
def which_night(state: SoulState) -> Literal["dusk_angelitos", "dusk_difuntos"]:
    """1 noyabr angelitos, 2 noyabr difuntos. State-in `kind` sahəsinə bax."""
    raise NotImplementedError("TODO 2.1")


# ==========================================================================
# TODO 2.2 — qürub node-ları [saf funksiya]
# ==========================================================================
def _dusk(state: SoulState, night: str) -> dict:
    """Yeni gecə başlayır.

    Keçən ilin izləri silinməlidir: `senses`, `tasted`, `crossing_steps`,
    `journey`, `voices`, həmçinin `plea`, `judgement`, `calaverita`.

    İKİSİ SİLİNMİR: `visits` (layihənin yaddaşı) və `calaveritas` (model
    keçən ilinkini görməlidir).

    İpucu: `journey` üçün eyni update-də həm sıfırlamaq, həm də ilk addımı
    yazmaq lazımdır. `_prepare` funksiyasını məhz bunun üçün yazmısan.
    """
    raise NotImplementedError("TODO 2.2")


def dusk_angelitos(state: SoulState) -> dict:
    return _dusk(state, "1 noyabr")


def dusk_difuntos(state: SoulState) -> dict:
    return _dusk(state, "2 noyabr")


# ==========================================================================
# Altarı oxumaq [tool] — HAZIRDIR, nümunə kimi oxu
# ==========================================================================
@tool
def read_altar(name: str, year: int) -> list[str]:
    """altar/<ad>.json faylından həmin ilin ofrenda siyahısını oxuyur."""
    path = ALTAR_DIR / f"{name}.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("years", {}).get(str(year), []))


def read_ofrenda(state: SoulState) -> dict:
    """[tool] Xarici dünyanı state-ə gətirir; qərar vermir. (Hazırdır.)"""
    _breathe()
    items = read_altar.invoke({"name": state["name"], "year": state["year"]})
    return {"ofrenda": items, "journey": [f"altar oxundu: {len(items)} əşya"]}


# ==========================================================================
# TODO 2.3 — ləçək yolu [Command ilə marşrut]  (BLOK 3-ə də aiddir)
# ==========================================================================
def follow_petals(state: SoulState) -> Command[Literal["mictlan_crossing", "lost"]]:
    """Altarda cempasúchil varsa → `mictlan_crossing`, yoxsa → `lost`.

    Bu node həm state-i yeniləyir, həm də özü növbəti node-u seçir:
        Command(goto=..., update={...})

    Şərti keçiddən fərqini README-də bir cümlə ilə yaz.
    """
    raise NotImplementedError("TODO 2.3")


# ==========================================================================
# TODO 2.4 — azmaq [loop sayğacı + LLM]
# ==========================================================================
def lost(state: SoulState) -> dict:
    """Cəhd sayını artır, jurnala yaz VƏ ruhun xahişini modelə yazdır.

    `voice.plea(facts)` hazırdır — sənə lazım olan faktlar: name, ofrenda,
    attempt. Nəticəni `state["plea"]`-ya yaz, mənbəni `voices`-a əlavə et.

    Sual: niyə model çağırışı burada, `wait_for_family`-də deyil?
    Cavabı tapmaq üçün `interrupt` olan node-un davam zamanı nə etdiyini
    düşün. Cavabı README-də bir cümlə ilə yaz.
    """
    raise NotImplementedError("TODO 2.4")


def can_retry(state: SoulState) -> Literal["wait_for_family", "farewell"]:
    """TODO 2.5 — loop-un çıxış şərti.

    3 cəhddən sonra ruh geri dönməlidir. Bu şərt olmasa qraf sonsuza qədər
    fırlanacaq (`GraphRecursionError`).
    """
    raise NotImplementedError("TODO 2.5")


# ==========================================================================
# TODO 2.6 — ailəni gözləmək [interrupt]
# ==========================================================================
def wait_for_family(state: SoulState) -> dict:
    """`interrupt()` çağırılan anda qraf state-i checkpoint-ə yazır və
    icra TAM DAYANIR. Proqramı bağlaya, sabah aça bilərsən.

    interrupt-a dict ver (sual, ipucu, cari altar), qayıdan dəyəri isə
    altara əlavə et. Sual mətni üçün `state["plea"]` istifadə et — onu
    `lost` node-u modelə yazdırıb. Bu node HEÇ BİR model çağırmamalıdır.

    Davam üçün runner belə çağıracaq:
        graph.invoke(Command(resume="cempasúchil"), config)
    """
    raise NotImplementedError("TODO 2.6")


# ==========================================================================
# TODO 2.7 — üç hiss [paralel node-lar]
# ==========================================================================
def taste_food(state: SoulState) -> dict:
    """Yalnız bu ruhun dada biləcəyi əşyalar (`TASTE` lüğətinə bax)."""
    raise NotImplementedError("TODO 2.7")


def smell_copal(state: SoulState) -> dict:
    """Copal tüstüsü altarda varmı?"""
    raise NotImplementedError("TODO 2.7")


def see_photos(state: SoulState) -> dict:
    """Şəkil olmasa, ruh kimin üçün gəldiyini görmür."""
    raise NotImplementedError("TODO 2.7")


# ==========================================================================
# TODO 2.8 — görüş [fan-in] — LAYİHƏNİN YADDAŞ NÜVƏSİ
# ==========================================================================
def reunion(state: SoulState) -> dict:
    """Üç paralel node burada birləşir.

    Əsas iş: `visits` sahəsindəki keçmiş illərə bax və bu il altarda
    OLMAYAN, amma əvvəllər müntəzəm qoyulan əşyaları tap.

    Qaytar:
        missing:       siyahı, ən çoxdan yoxa çıxan birinci
        missing_since: {əşya: neçə ildir yoxdur}

    Şərtlər:
      - əşya son 5 ildə ən azı 2 dəfə qoyulmuş olmalıdır (təsadüf olmasın)
      - sıralama determinik olmalıdır (eyni məlumat → eyni cavab)

    Bu siyahı olmasa, layihənin ən təsirli cümləsi mövcud deyil.
    """
    raise NotImplementedError("TODO 2.8")


# ==========================================================================
# TODO 2.9a — bütün LLM node-ları üçün ortaq fakt dəsti
# ==========================================================================
def _facts(state: SoulState) -> dict:
    """State-dən modelə veriləcək faktları yığ.

    Açarlar: name, relation, ofrenda, tasted, missing, missing_since,
             years_remembered, remembrance, verdict, last_calaverita

    `last_calaverita` — `calaveritas` siyahısının sonuncusu (yoxdursa
    "yoxdur"). Məhz bu sahə sayəsində model keçən ilinkini təkrar etmir.
    """
    raise NotImplementedError("TODO 2.9a")


# ==========================================================================
# TODO 2.9b — altarın qiyməti [LLM · STRUCTURED OUTPUT] (paralel)
# ==========================================================================
def judge_ofrenda(state: SoulState) -> dict:
    """`voice.judge(facts)` modeldən SƏRBƏST MƏTN yox, sxem qaytarır:
    `{"warmth": int, "verdict": str, "longing": str}`.

    Nəticəni `judgement` sahəsinə yaz, mənbəni `voices`-a əlavə et.

    `write_calaverita` ilə eyni superstep-də paralel işləyəcək — deməli
    ikisi də `voices` sahəsinə yazır və reducer-in olması vacibdir.
    """
    raise NotImplementedError("TODO 2.9b")


# ==========================================================================
# TODO 2.9c — calaverita literaria [LLM] (paralel)
# ==========================================================================
def write_calaverita(state: SoulState) -> dict:
    """`voice.calaverita(facts)` — dirilər üçün zarafat epitafiya.

    Nəticəni `calaverita` sahəsinə yaz. `farewell` onu `calaveritas`
    tarixçəsinə əlavə edəcək ki, gələn il model onu görsün.
    """
    raise NotImplementedError("TODO 2.9c")


# ==========================================================================
# TODO 2.9d — danışmaq [LLM node]
# ==========================================================================
def speak_to_family(state: SoulState) -> dict:
    """`voice.speak(facts)` hazırdır — sən yalnız faktları hazırla.

    Bu node yuxarıdakı iki paralel node-dan SONRA işləyir, ona görə
    faktlarda `verdict` sahəsi də dolu olacaq.

    Diqqət: faktlar STATE-dən gəlir, modeldən yox. Açar olmasa da eyni
    rəqəmlər deyiləcək.
    """
    raise NotImplementedError("TODO 2.9d")


# ==========================================================================
# TODO 2.10 — vida [ilin bağlanması]
# ==========================================================================
def farewell(state: SoulState) -> dict:
    """Ziyarəti `visits`-ə yaz və xatırlanma gücünü yenilə.

    Düstur (istəsən dəyiş, amma README-də əsaslandır):
        yeni = köhnə − 30 + 4·(əşya sayı) + (görüş: +12 / uğursuz: −20)
        nəticə 0..100 aralığına sıxılır

    Həmçinin: bu ilin `calaverita`-sını `calaveritas` tarixçəsinə əlavə et
    və `judgement["warmth"]` dəyərini ziyarət qeydinə yaz.

    Zəngin altar ruhu 100-də saxlayır, boş altar üç ilə öldürür.
    """
    raise NotImplementedError("TODO 2.10")


def is_forgotten(state: SoulState) -> Literal["third_death", "__end__"]:
    """TODO 2.11 — xatırlanma sıfıra düşübsə, üçüncü ölüm."""
    raise NotImplementedError("TODO 2.11")


def third_death(state: SoulState) -> dict:
    """TODO 2.12 — yalnız işarə qoy.

    Bu node checkpoint-i SİLMİR: qraf öz yaddaşını icra zamanı silə bilməz.
    Faylı silmək runner-in işidir (`delete_thread`). Niyə belə olduğunu
    README-də bir cümlə ilə izah et.
    """
    raise NotImplementedError("TODO 2.12")
