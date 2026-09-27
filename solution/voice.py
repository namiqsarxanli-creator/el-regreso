"""
Ruhun səsi — LLM qatı.

Üç prinsip:

1. **Faktlar state-dən gəlir, modeldən yox.** «3 ildir şəkil gətirmirsən»
   cümləsindəki rəqəm `visits` sahəsindən hesablanır. Model yalnız o
   faktları cümləyə çevirir. Səbəbi pedaqojidir: yaddaşı nümayiş etdiririk,
   modelin xəyalını yox.

2. **Provayderlər növbə ilə.** Biri bitəndə (kvota, limit, şəbəkə) avtomatik
   növbətisinə keçilir: Groq → Gemini → OpenAI → Anthropic. Sıranı
   `EL_REGRESO_MODELS` ilə dəyişmək olar.

3. **Açar yoxdursa, proqram çökmür.** Offline şablona düşür və eyni faktları
   deyir. Dərsdə internet olmaya bilər.
"""

from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent

# .env faylını yükləyirik — açarları ora yazmaq kifayətdir.
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT.parent / ".env", override=False)  # ümumi açarlar
except ImportError:
    pass


# --------------------------------------------------------------------------
# Provayder növbəsi
# --------------------------------------------------------------------------
DEFAULT_CHAIN = [
    # Groq: iki model — böyüyü bitəndə kiçiyinə keçir (eyni açar).
    ("GROQ_API_KEY", os.getenv("EL_REGRESO_GROQ_MODEL", "groq:openai/gpt-oss-120b")),
    ("GROQ_API_KEY", "groq:openai/gpt-oss-20b"),
    # Gemini: Groq-un hər iki modeli bitəndə növbə buna gəlir.
    ("GOOGLE_API_KEY", os.getenv("EL_REGRESO_GEMINI_MODEL", "google_genai:gemini-2.0-flash")),
    ("OPENAI_API_KEY", "openai:gpt-4o-mini"),
    ("ANTHROPIC_API_KEY", "anthropic:claude-sonnet-5"),
]

# Bu proses ərzində sıradan çıxmış provayderlər: {model: səbəb}
_dead: dict[str, str] = {}
_cache: dict[str, Any] = {}


def chain() -> list[str]:
    """Açarı olan və hələ sıradan çıxmamış modellərin sırası."""
    order = os.getenv("EL_REGRESO_MODELS")
    if order:
        wanted = [m.strip() for m in order.split(",") if m.strip()]
        return [m for m in wanted if m not in _dead]
    return [model for env_key, model in DEFAULT_CHAIN if os.getenv(env_key) and model not in _dead]


def status() -> dict:
    """UI üçün: kim hazırdır, kim sıradan çıxıb."""
    return {"available": chain(), "dead": dict(_dead), "offline": not chain()}


def _load(model_id: str):
    if model_id not in _cache:
        from langchain.chat_models import init_chat_model

        _cache[model_id] = init_chat_model(model_id, temperature=0.75)
    return _cache[model_id]


def _mark_dead(model_id: str, exc: Exception) -> None:
    name = type(exc).__name__
    text = str(exc).lower()
    if "rate" in text or "quota" in text or "429" in text:
        reason = "limit/kvota"
    elif "auth" in text or "api key" in text or "401" in text or "403" in text:
        reason = "açar problemi"
    elif "not found" in text or "404" in text or "model" in text and "decommission" in text:
        reason = "model tapılmadı"
    else:
        reason = name
    _dead[model_id] = reason
    print(f"  [voice] {model_id} sıradan çıxdı ({reason}) — növbəti provayderə keçilir")


def ask(system: str, user: str, schema: type[BaseModel] | None = None) -> tuple[Any, str]:
    """Növbədəki modellərə sıra ilə müraciət edir.

    Qaytarır: (cavab, mənbə). Cavab `schema` verilibsə pydantic obyekti,
    yoxsa mətndir. Heç biri işləməsə (None, "offline").
    """
    for model_id in chain():
        try:
            model = _load(model_id)
            if schema is not None:
                result = model.with_structured_output(schema).invoke(
                    [{"role": "system", "content": system}, {"role": "user", "content": user}]
                )
                return result, model_id
            response = model.invoke(
                [{"role": "system", "content": system}, {"role": "user", "content": user}]
            )
            content = response.content
            text = content if isinstance(content, str) else str(content)
            return text.strip(), model_id
        except Exception as exc:  # kvota bitdi, açar səhvdir, şəbəkə yoxdur...
            _mark_dead(model_id, exc)
    return None, "offline"


# ==========================================================================
# 1. Ruhun sözləri
# ==========================================================================
_SPEAK_SYSTEM = (
    "Sən Día de los Muertos gecəsində evinə qayıtmış bir ruhsan. "
    "Ailənə ÜÇ-DÖRD QISA cümlə ilə, sakit və isti tonda müraciət et.\n"
    "Qaydalar:\n"
    "— verilən faktlardan kənara çıxma, yeni xatirə uydurma;\n"
    "— «neçə ildir» rəqəmlərini olduğu kimi işlət (məsələn «3 ildir şəkil "
    "gətirmirsən»);\n"
    "— «xatırlanma gücü» rəqəmini HEÇ VAXT dilə gətirmə, o daxili ölçüdür;\n"
    "— şeir yazma, uzun cümlə qurma, sadə danış;\n"
    "— Azərbaycan dilində."
)


def _facts_text(facts: dict) -> str:
    missing = facts.get("missing_since", {})
    return (
        f"Ruhun adı: {facts.get('name', '')}\n"
        f"Ailə ilə əlaqəsi: {facts.get('relation', '')}\n"
        f"Bu il dadılanlar: {', '.join(facts.get('tasted', [])) or 'heç nə'}\n"
        f"Neçə ildir xatırlanır: {facts.get('years_remembered', 1)}\n"
        f"Yoxa çıxan əşyalar: "
        f"{', '.join(f'{k} — {v} ildir yoxdur' for k, v in missing.items()) or 'yoxdur'}\n"
        f"Xatırlanma gücü (0-100): {facts.get('remembrance', 0)}\n"
        f"Altarın qiyməti: {facts.get('verdict', '')}\n"
        f"Keçən ilin kalaveritası: {facts.get('last_calaverita', 'yoxdur')}\n"
    )


def speak(facts: dict) -> tuple[str, str]:
    text, source = ask(_SPEAK_SYSTEM, _facts_text(facts))
    if text is None:
        return _offline_speak(facts), "offline"
    return text, source


def _offline_speak(facts: dict) -> str:
    """Açarsız rejim — məzmun tam olaraq state-dən gəlir."""
    name = facts.get("name") or "sən"
    tasted = facts.get("tasted", [])
    missing = facts.get("missing", [])
    years = facts.get("years_remembered", 1)
    lines = [
        random.choice(
            [f"Qapını tanıdım, {name}.", f"Bu il də yolu tapdım, {name}.", f"Işıq hələ də yanır, {name}."]
        )
    ]
    if tasted:
        lines.append("Süfrədə " + ", ".join(tasted[:3]) + " vardı — hamısının qoxusunu apardım.")
    else:
        lines.append("Süfrə boş idi, amma gəldiyim yol boş deyildi.")
    if missing:
        item = missing[0]
        gap = facts.get("missing_since", {}).get(item, 1)
        lines.append(
            f"{gap} ildir {item} gətirmirsən. Soruşmuram, sadəcə deyirəm."
            if gap >= 2
            else f"Keçən il {item} vardı, bu il yox idi."
        )
    if years >= 3:
        lines.append(f"{years} ildir səni görürəm. Bu, az şey deyil.")
    lines.append("Sabah səhər yenidən yola çıxıram. Şamı söndürməyi unutma.")
    return " ".join(lines)


# ==========================================================================
# 2. Altarın qiymətləndirilməsi — STRUCTURED OUTPUT
# ==========================================================================
class Judgement(BaseModel):
    """Modelin sərbəst mətn yox, SXEM üzrə cavab verməsi.

    `with_structured_output` modelə tool çağırışı kimi ötürülür və nəticə
    birbaşa bu sinfin obyektidir — parse etmək, JSON təmizləmək lazım deyil.
    Qrafın sonrakı node-ları bu sahələrə etibar edə bilər.
    """

    warmth: int = Field(description="Altarın istiliyi, 0-100 arası tam ədəd")
    verdict: str = Field(description="Altar haqqında bir qısa cümlə")
    longing: str = Field(description="Ruhun ən çox darıxdığı bir şey, 2-3 söz")


def judge(facts: dict) -> tuple[dict, str]:
    system = (
        "Sən Día de los Muertos altarını qiymətləndirən bir ruhsan. "
        "Verilən məlumata əsaslanaraq sxemi doldur. Azərbaycan dilində, qısa."
    )
    result, source = ask(system, _facts_text(facts), schema=Judgement)
    if result is None:
        # Offline: eyni sahələr, sadə hesablama ilə
        items = len(facts.get("ofrenda", []))
        warmth = max(0, min(100, items * 12))
        return (
            {
                "warmth": warmth,
                "verdict": "Altar zəngindir." if items >= 6 else "Altar kasıbdır.",
                "longing": (facts.get("missing") or ["sükut"])[0],
            },
            "offline",
        )
    return result.model_dump(), source


# ==========================================================================
# 3. Ruhun öz xahişi — interrupt mətnini model yazır
# ==========================================================================
def plea(facts: dict) -> tuple[str, str]:
    """Ruh azanda ailədən nə istədiyini ÖZÜ deyir.

    Əvvəl bu mətn sabit idi. İndi modelin işidir: altara baxıb nəyin
    çatışmadığını özü seçir. Nəticə `interrupt()`-a ötürülür.
    """
    system = (
        "Sən qaranlıqda yolunu itirmiş bir ruhsan. Ailəndən altara qoymaq "
        "üçün BİR KONKRET əşya istə.\n"
        "Qaydalar:\n"
        "— cavabın yalnız BİR cümlə olsun;\n"
        "— həmin əşyanın adı cümlədə mütləq keçsin;\n"
        "— yalnız bu siyahıdan seç: cempasúchil, su, copal, şam, şəkil, "
        "pan de muerto, duz, mezcal;\n"
        "— altarda artıq olan bir şeyi istəmə;\n"
        "— yalvarma, sakit danış; Azərbaycan dilində."
    )
    user = (
        f"Altarda artıq olanlar: {', '.join(facts.get('ofrenda', [])) or 'heç nə'}\n"
        f"Cəhd: {facts.get('attempt', 1)}/3\n"
        f"Nə nəyə görədir: cempasúchil ləçəkləri evə gedən yolu açır, "
        f"su yol üçün güc verir, copal tüstüsü küləkdən qoruyur, "
        f"şəkil ruha kimin üçün gəldiyini göstərir.\n"
    )
    text, source = ask(system, user)
    if text is None:
        return f"{facts.get('name', 'Ruh')} yolu tapa bilmir. Altara nə əlavə edirsən?", "offline"
    return text, source


# ==========================================================================
# 4. Calaverita literaria — DİRİLƏR üçün zarafat epitafiya
# ==========================================================================
def calaverita(facts: dict) -> tuple[str, str]:
    """Bayramın öz janrı: diri insanlar üçün yazılan yumoristik epitafiya.

    State-də saxlanılır və gələn il modelə keçən ilin kalaveritası
    göstərilir — yəni yaddaş generasiyaya təsir edir.
    """
    system = (
        "Calaverita literaria yaz: DİRİ insanlar üçün yumoristik dördmisralı "
        "epitafiya. Ölümü yumşaq və zarafatla xatırladır, kobud olmur. "
        "Yalnız dörd misra yaz, başqa heç nə. Azərbaycan dilində, qafiyəli."
    )
    user = (
        f"Kim haqqında: {facts.get('relation', 'ailə')} — altarı quran ailə\n"
        f"Bu ilki altar: {', '.join(facts.get('ofrenda', [])) or 'boş'}\n"
        f"Keçən ilin kalaveritası: {facts.get('last_calaverita', 'yoxdur')}\n"
        f"Təkrar etmə, bu il yenisini yaz.\n"
    )
    text, source = ask(system, user)
    if text is None:
        items = facts.get("ofrenda", [])
        first = items[0] if items else "boş masa"
        return (
            f"Bu il altara {first} qoydun,\n"
            f"növbəti il mən gələcəyəm.\n"
            f"Qorxma, tələsmirəm heç,\n"
            f"sadəcə yerini görəcəyəm.",
            "offline",
        )
    return text, source
