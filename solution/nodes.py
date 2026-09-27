"""
El Regreso — Node-lar.

Tapşırığın 2-ci bloku: node-lar eyni cinsdən olmamalıdır. Burada beş fərqli
növ var və hər birinin başlığında hansı növ olduğu yazılıb:

  [saf funksiya]  LLM yoxdur, yalnız state hesablaması
  [tool]          xarici mənbədən (fayl) oxuyur
  [interrupt]     icranı dayandırıb insandan cavab gözləyir
  [paralel]       eyni superstep-də digərləri ilə birlikdə işləyir
  [LLM]           modelə müraciət edir (açar yoxdursa offline şablon)

Subqraf (`mictlan_crossing`) ayrıca fayldadır: crossing.py
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
from .voice import calaverita, judge, plea, speak

ALTAR_DIR = Path(__file__).resolve().parent.parent / "altar"

# Cempasúchil — qadife gülü. Ləçəklərindən çəkilən yol ruhu evə aparır.
PETAL = "cempasúchil"

# Hansı ruh nəyi dadır. Angelitos (uşaq ruhları) 1 noyabrda gəlir və
# onlara spirtli içki qoyulmur — bu, bayramın öz qaydasıdır, bizim
# şərti keçidimizin (conditional edge) də səbəbidir.
TASTE = {
    "angelito": {"süd", "şokolad", "oyuncaq", "şəkər kəllə", "pan de muerto", "meyvə"},
    "difunto": {"mezcal", "tamales", "pan de muerto", "qəhvə", "siqaret", "duz", "meyvə"},
}


def _breathe() -> None:
    """Demo üçün nəfəs: EL_REGRESO_SLOW=0.8 qoyanda node-lar görünən sürətlə
    işləyir. Chaos testində prosesi ortada öldürmək üçün də lazımdır.

    Dəyər hər çağırışda oxunur ki, `--slow` bayrağı import-dan sonra da
    təsir edə bilsin."""
    delay = float(os.getenv("EL_REGRESO_SLOW", "0") or 0)
    if delay:
        time.sleep(delay)


# ==========================================================================
# 1. Giriş — hansı gecə?
# ==========================================================================
def which_night(state: SoulState) -> Literal["dusk_angelitos", "dusk_difuntos"]:
    """[router] START-dan çıxan şərti keçid.

    1 noyabr — angelitos (uşaq ruhları), 2 noyabr — difuntos (böyüklər).
    Eyni qraf, iki fərqli marşrut. Bu funksiya node deyil: heç nə qaytarmır,
    yalnız növbəti node-un adını seçir.
    """
    return "dusk_angelitos" if state.get("kind") == "angelito" else "dusk_difuntos"


def _dusk(state: SoulState, night: str) -> dict:
    _breathe()
    return {
        # RESET — keçən ilin qoxuları, dadları və izi silinir.
        # `visits` isə silinmir: yaddaş odur.
        "senses": RESET,
        "tasted": RESET,
        "crossing_steps": RESET,
        "voices": RESET,
        # `calaveritas` SIFIRLANMIR — model keçən ilinkini görməlidir.
        "calaverita": "",
        "judgement": {},
        "plea": "",
        # [RESET, addım] — eyni update-də həm boşalt, həm yeni ili başlat.
        "journey": [RESET, f"{night} — {state.get('year')} ili, qürub"],
        "attempts": 0,
        "arrived": False,
        "words": "",
        "missing": [],
        "crossing_report": "",
    }


def dusk_angelitos(state: SoulState) -> dict:
    """[saf funksiya] 1 noyabr, uşaq ruhları yola çıxır."""
    return _dusk(state, "1 noyabr")


def dusk_difuntos(state: SoulState) -> dict:
    """[saf funksiya] 2 noyabr, böyük ruhlar yola çıxır."""
    return _dusk(state, "2 noyabr")


# ==========================================================================
# 2. Altarı oxumaq — tool node
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
    """[tool] Altarda bu il nə var?

    State-in içindən deyil, xaricdən — diskdən oxuyur. Node-un işi xarici
    dünyanı state-ə gətirməkdir; qərar vermək başqa node-ların işidir.
    """
    _breathe()
    items = read_altar.invoke({"name": state["name"], "year": state["year"]})
    if state.get("prepared_ofrenda") is not None:
        items = list(state["prepared_ofrenda"])
    return {
        "ofrenda": items,
        "prepared_ofrenda": None,
        "journey": [f"altar oxundu: {len(items)} əşya"],
    }


# ==========================================================================
# 3. Ləçək yolu — Command ilə marşrutlaşdırma
# ==========================================================================
def follow_petals(state: SoulState) -> Command[Literal["mictlan_crossing", "lost"]]:
    """[saf funksiya] Cempasúchil yolu varmı?

    Bu node həm state-i yeniləyir, həm də özü növbəti node-u seçir —
    `Command(goto=..., update=...)`. Şərti keçiddən (conditional edge) fərqi:
    orada qərarı ayrıca router funksiyası verir, burada node-un özü.
    Qrafda ayrıca ox çəkilmir, marşrut node-un içindədir.
    """
    _breathe()
    has_path = PETAL in state.get("ofrenda", [])
    if has_path:
        return Command(
            goto="mictlan_crossing",
            update={
                "petal_path": True,
                "journey": ["cempasúchil yolu tapıldı — ruh evə tərəf dönür"],
            },
        )
    return Command(
        goto="lost",
        update={
            "petal_path": False,
            "journey": ["yol yoxdur — qaranlıqda"],
        },
    )


# ==========================================================================
# 4. Azmaq — loop və onun həddi
# ==========================================================================
def lost(state: SoulState) -> dict:
    """[LLM] Ruh yolu itirdi və ailədən nə istədiyini ÖZÜ yazır.

    Diqqət — xahiş məhz burada, `wait_for_family`-dən ƏVVƏL yaradılır.
    Səbəbi checkpointing ilə bağlıdır: `interrupt()` olan node davam
    ediləndə BAŞDAN yenidən işləyir. Model çağırışını ora qoysaydıq, hər
    resume-da pul və vaxt gedərdi və ruh hər dəfə başqa şey istəyərdi.
    Qayda: **interrupt node-unu ucuz və determinik saxla.**
    """
    _breathe()
    attempts = state.get("attempts", 0) + 1
    text, source = plea(
        {
            "name": state.get("display") or state.get("name", "Ruh"),
            "ofrenda": state.get("ofrenda", []),
            "attempt": attempts,
        }
    )
    return {
        "attempts": attempts,
        "plea": text,
        "voices": [f"xahiş ← {source}"],
        "journey": [f"axtarış {attempts}/3"],
    }


def can_retry(state: SoulState) -> Literal["wait_for_family", "farewell"]:
    """[router] Loop-un çıxış şərti.

    Bu şərt olmasaydı, qraf `follow_petals → lost → wait_for_family →
    follow_petals` dövrəsində sonsuza qədər fırlanardı. Hər loop-un
    sayğacı və həddi olmalıdır — bu, qrafın ən çox unudulan qaydasıdır.
    """
    return "wait_for_family" if state.get("attempts", 0) < 3 else "farewell"


# ==========================================================================
# 5. Ailəni gözləmək — interrupt (human-in-the-loop)
# ==========================================================================
def wait_for_family(state: SoulState) -> dict:
    """[interrupt] İcra dayanır və insandan cavab gözlənir.

    `interrupt()` çağırılan anda qraf state-i checkpoint-ə yazır və icra
    tam olaraq dayanır. Proqramı bağlaya, sabah aça bilərsən — ruh həmin
    qapının ağzında dayanmış olacaq. Davam üçün:
        graph.invoke(Command(resume="cempasúchil"), config)
    """
    answer = interrupt(
        {
            # Sual mətnini model yazıb (`lost` node-unda), burada yalnız
            # state-dən oxuyuruq — bu node heç bir model çağırmır.
            "question": state.get("plea")
            or f"{state.get('display') or state['name']} yolu tapa bilmir. "
            f"Altara nə əlavə edirsən?",
            "hint": f"'{PETAL}' yolu açır. Digərləri gücü artırır.",
            "altar": state.get("ofrenda", []),
            "attempt": state.get("attempts", 0),
        }
    )
    gift = str(answer).strip().lower()
    return {
        # ofrenda reducer-siz sahədir: yeni siyahı köhnəsinin üstünə yazılır.
        "ofrenda": list(state.get("ofrenda", [])) + [gift],
        "journey": [f"ailə altara «{gift}» qoydu"],
    }


# ==========================================================================
# 6. Üç hiss — paralel node-lar (fan-out)
# ==========================================================================
def taste_food(state: SoulState) -> dict:
    """[paralel] Ruh yeməyin mahiyyətini alır, özünü yox."""
    _breathe()
    allowed = TASTE[state.get("kind", "difunto")]
    tasted = [item for item in state.get("ofrenda", []) if item in allowed]
    return {"tasted": tasted, "senses": [f"dad: {', '.join(tasted) or 'yoxdur'}"]}


def smell_copal(state: SoulState) -> dict:
    """[paralel] Copal tüstüsü duanı yuxarı aparır."""
    _breathe()
    has = "copal" in state.get("ofrenda", [])
    return {"senses": ["tüstü: copal" if has else "tüstü: yoxdur"]}


def see_photos(state: SoulState) -> dict:
    """[paralel] Şəkil olmasa, ruh kimin üçün gəldiyini görmür."""
    _breathe()
    has = "şəkil" in state.get("ofrenda", [])
    return {"senses": ["görüntü: şəkil" if has else "görüntü: qaranlıq"]}


# ==========================================================================
# 7. Görüş — fan-in
# ==========================================================================
def reunion(state: SoulState) -> dict:
    """[saf funksiya] Üç paralel node burada birləşir.

    Bu node layihənin yaddaş nüvəsidir: `visits` sahəsindəki keçmiş illərə
    baxıb, əvvəllər müntəzəm qoyulan, amma bu il olmayan əşyaları tapır.
    Məhz bu siyahı sonda ruhun ən kəskin cümləsinə çevrilir — və o siyahı
    yalnız checkpointer işləyəndə mövcud olur.
    """
    _breathe()
    history = state.get("visits", [])[-5:]
    current = set(state.get("ofrenda", []))

    missing_since: dict[str, int] = {}
    for item in {i for v in history for i in v.get("ofrenda", [])}:
        if item in current:
            continue
        # Əvvəllər ən azı iki dəfə qoyulmuşdusa, yoxluğu təsadüf deyil.
        if sum(1 for v in history if item in v.get("ofrenda", [])) < 2:
            continue
        streak = 1  # bu il
        for visit in reversed(history):
            if item in visit.get("ofrenda", []):
                break
            streak += 1
        missing_since[item] = streak

    # Sıralama determinikdir: əvvəlcə ən çoxdan yoxa çıxan, sonra əlifba.
    missing = sorted(missing_since, key=lambda i: (-missing_since[i], i))

    return {
        "arrived": True,
        "missing": missing,
        "missing_since": missing_since,
        "journey": ["ailə ilə görüş"],
        "senses": [f"{len(state.get('visits', [])) + 1}-ci ziyarət"],
    }


# ==========================================================================
# 8a. Altarın qiyməti — STRUCTURED OUTPUT node-u [paralel]
# ==========================================================================
def judge_ofrenda(state: SoulState) -> dict:
    """[LLM · structured output] Model sərbəst mətn yox, SXEM qaytarır.

    `with_structured_output(Judgement)` sayəsində nəticə birbaşa
    `{"warmth": int, "verdict": str, "longing": str}` olur — JSON parse
    etmək, mətni təmizləmək lazım deyil. Qrafın sonrakı node-ları bu
    sahələrə etibar edə bilər; sərbəst mətnə edə bilməzdi.

    `write_calaverita` ilə eyni superstep-də, paralel işləyir.
    """
    _breathe()
    data, source = judge(_facts(state))
    return {
        "judgement": data,
        "voices": [f"qiymət ← {source}"],
        "journey": [f"altar qiymətləndirildi: {data.get('warmth')}/100"],
    }


# ==========================================================================
# 8b. Calaverita literaria — generasiya + illər arası yaddaş [paralel]
# ==========================================================================
def write_calaverita(state: SoulState) -> dict:
    """[LLM] Bayramın öz janrı: DİRİLƏR üçün zarafat epitafiya.

    Modelə keçən ilin kalaveritası göstərilir və təkrar etməməsi tapşırılır
    — yəni checkpointer-dəki yaddaş birbaşa generasiyaya təsir edir.
    """
    _breathe()
    text, source = calaverita(_facts(state))
    return {
        "calaverita": text,
        "voices": [f"calaverita ← {source}"],
        "journey": ["calaverita yazıldı"],
    }


# ==========================================================================
# 8c. Danışmaq — LLM node
# ==========================================================================
def _facts(state: SoulState) -> dict:
    """Bütün LLM node-larının istifadə etdiyi fakt dəsti.

    Hamısı state-dən gəlir — model heç nə uydurmur, yalnız ifadə edir.
    """
    calaveritas = state.get("calaveritas", [])
    return {
        "name": state.get("display") or state.get("name", ""),
        "relation": state.get("relation", ""),
        "ofrenda": state.get("ofrenda", []),
        "tasted": state.get("tasted", []),
        "missing": state.get("missing", []),
        "missing_since": state.get("missing_since", {}),
        "years_remembered": len(state.get("visits", [])) + 1,
        "remembrance": state.get("remembrance", 0),
        "verdict": (state.get("judgement") or {}).get("verdict", ""),
        "last_calaverita": calaveritas[-1] if calaveritas else "yoxdur",
    }


def speak_to_family(state: SoulState) -> dict:
    """[LLM] Faktlar state-dən, cümlə modeldən.

    Bu node paralel iki node-dan (`judge_ofrenda`, `write_calaverita`)
    SONRA işləyir və onların nəticəsini də faktlara daxil edir.
    """
    _breathe()
    words, source = speak(_facts(state))
    return {
        "words": words,
        "messages": [{"role": "assistant", "content": words}],
        "voices": [f"söz ← {source}"],
        "journey": [f"ruh danışdı ({source})"],
    }


# ==========================================================================
# 9. Vida — ilin bağlanması
# ==========================================================================
def farewell(state: SoulState) -> dict:
    """[saf funksiya] Ziyarət qeydə alınır, xatırlanma gücü yenilənir.

    Düstur qəsdən acımasızdır:

        yeni = köhnə − 30 + 4·(altardakı əşya) + (görüş: +12 / uğursuz: −20)

    Yəni zəngin altar (7-8 əşya) ruhu 100-də saxlayır, orta altar (4-5)
    yavaş-yavaş sönür, boş altar isə üç ilə öldürür. Yaddaş boş yerdən
    qorunmur — hər il nəyinsə edilməsi lazımdır.
    """
    _breathe()
    arrived = state.get("arrived", False)
    ofrenda = state.get("ofrenda", [])
    score = state.get("remembrance", 100) - 30 + len(ofrenda) * 4 + (12 if arrived else -20)
    score = max(0, min(100, score))

    visit: Visit = {
        "year": state.get("year", 0),
        "ofrenda": list(ofrenda),
        "tasted": list(state.get("tasted", [])),
        "arrived": arrived,
        "remembrance": score,
        "note": state.get("words", "")[:160],
        "words": state.get("words", ""),
        "calaverita": state.get("calaverita", ""),
        "warmth": (state.get("judgement") or {}).get("warmth", 0),
    }
    update = {
        "remembrance": score,
        "visits": [visit],  # operator.add — illər yığılır
        "journey": ["vida" if arrived else "ruh evi tapa bilmədi, geri döndü"],
    }
    # Bu ilin kalaveritası tarixçəyə qoşulur ki, gələn il model onu görsün.
    if state.get("calaverita"):
        update["calaveritas"] = [state["calaverita"]]
    return update


def is_forgotten(state: SoulState) -> Literal["third_death", "__end__"]:
    """[router] Üçüncü ölümün astanası."""
    return "third_death" if state.get("remembrance", 0) <= 0 else "__end__"


def third_death(state: SoulState) -> dict:
    """[saf funksiya] Üçüncü ölüm.

    Diqqət: bu node checkpoint-i SİLMİR — qraf öz yaddaşını icra zamanı
    silə bilməz (sildiyi anda icra qeydi də itərdi). Node yalnız işarə
    qoyur; faylı silmək runner-in işidir:
        checkpointer.delete_thread(thread_id)
    Bax: run_year.py → `_maybe_forget`.
    """
    return {
        "forgotten": True,
        "journey": ["üçüncü ölüm — onu xatırlayan qalmadı"],
    }
