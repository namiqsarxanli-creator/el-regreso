# El Regreso

🇬🇧 [English](README.md)

> *Bir gecə, hər il.*
> Día de los Muertos üzərində qurulmuş LangGraph agenti —
> **stateful qraflar, nodes, edges və checkpointing**.

## Nə qurulur

Ruh 1–2 noyabr gecəsi evinə qayıdır: ləçək yolunu tapır, Mictlán-ın
maneələrindən keçir, altarı «dadır», ailə ilə görüşür və danışır. Sonra geri
dönür — **gələn ilə qədər**. Növbəti il eyni `thread_id` ilə qayıdanda keçən
illəri xatırlayır:

> *«Qapını tanıdım, Abuela Remedios. Süfrə boş idi, amma gəldiyim yol boş
> deyildi. **3 ildir şəkil gətirmirsən.** Soruşmuram, sadəcə deyirəm.
> 5 ildir səni görürəm. Bu, az şey deyil.»*

Bu cümlədəki «3 ildir» rəqəmi model tərəfindən uydurulmur — `visits`
sahəsindən, yəni **checkpointer-dən** hesablanır. Checkpointer olmasa, bu
cümlə mövcud deyil. Layihənin bütün ideyası bu bir sətirdədir.

![qraf](docs/graph.png)

---

## Qurulum

```bash
pip install -r requirements.txt
```

## PyCharm-da işə salmaq

`main.py` faylını aç və yaşıl ▶ düyməsini bas — hamısı budur.
Server qalxır, **brauzer özü açılır**, baza boşdursa demo məlumatı
(abuela 2021–2023, mateo 2021–2022) avtomatik qurulur ki, ilk ekran boş
olmasın. Port məşğuldursa, özü azad port tapır.

Yuxarıdakı konfiqurasiya siyahısında dörd hazır seçim var:

| Konfiqurasiya | Nə edir |
|---|---|
| **El Regreso** | web + brauzer (standart) |
| **El Regreso — bir gecə** | terminalda 2021-ci il, yavaş rejimdə |
| **El Regreso — 5 illik demo** | beş il, hər biri ayrıca proses, interrupt daxil |
| **El Regreso — chaos** | prosesi öldürüb bərpa edir |

`solution/` içindəki fayllara birbaşa ▶ basmaq da işləyir:
hər faylın başında layihə kökünü `sys.path`-ə əlavə edən üç sətir var,
ona görə «attempted relative import with no known parent package» xətası
çıxmır.

### Model

Açarları `.env` faylına yazmaq kifayətdir (`.env.example`-dan köçür).
Qrafda **dörd LLM node-u** var və hamısı eyni növbədən istifadə edir:

```
GROQ_API_KEY   → groq:openai/gpt-oss-120b
               → groq:openai/gpt-oss-20b     (böyüyü bitəndə)
GOOGLE_API_KEY → gemini-2.0-flash            (Groq bitəndə)
OPENAI_API_KEY → gpt-4o-mini
heç biri       → offline şablon              (proqram çökmür)
```

Biri kvota/limit verəndə növbəti avtomatik işə düşür və terminalda bir
sətir yazılır: `[voice] … sıradan çıxdı (limit/kvota) — növbəti provayderə
keçilir`. Sıranı `EL_REGRESO_MODELS` ilə əl ilə də vermək olar.

**Vacib prinsip:** faktlar state-dən gəlir, modeldən yox. «3 ildir şəkil
gətirmirsən» rəqəmi `visits` sahəsindən hesablanır — model yalnız onu
cümləyə çevirir. Ona görə açarsız demo da eyni həqiqəti deyir.

## Terminaldan işə salma

```bash
# hər şey bir əmrlə
python main.py                 # web + brauzer
python main.py --demo          # terminalda 5 illik demo
python main.py --fresh         # bazanı sil və yenidən qur
```

Ayrı-ayrı əmrlər:

```bash
# bir il — hər dəfə ayrıca proses olmalıdır
python -m solution.run_year --soul abuela --year 2021

# ruh azıb, qraf insanı gözləyir (interrupt)
python -m solution.run_year --soul abuela --year 2024
python -m solution.run_year --soul abuela --resume --gift cempasúchil

# checkpoint tarixçəsi və paralel kainat
python -m solution.run_year --soul abuela --history
python -m solution.run_year --soul abuela --fork 7 --gift şəkil

# cari yaddaş / üçüncü ölüm
python -m solution.run_year --soul abuela --state
python -m solution.run_year --soul abuela --forget

# prosesi ortada öldürüb bərpa edən test
python -m solution.chaos

# qrafın şəkli
python -m solution.graph --png
```

### Canlı vizualizasiya

```bash
python -m uvicorn web.server:app --port 8020
```

`http://127.0.0.1:8020` — altar, canlı qraf, **LangGraph jurnalı**,
altarın qiyməti, calaverita, xatırlanma şamı və checkpoint xətti.

### İnteraktiv hekayə imkanları

Veb interfeysində qraf vizualizasiyası ilə yanaşı hekayəni dəyişən beş bölmə var:

- **İnteraktiv altar:** ilin hazır ofrendasını dəyiş, əşyaları kliklə və ya
  altara sürüşdür, sonra gecəni həmin seçimlə başlat. Qaralama brauzerdə
  saxlanır və yalnız gecəni başladanda state-ə daxil olur.
- **Ruh kartları:** hər ruhun bədii portreti, ailədəki yeri, qısa hekayəsi
  və sevdiyi hədiyyələr göstərilir.
- **Xatirə albomu:** bitmiş ziyarətlərin ili, altar əşyaları, xatırlanma,
  istilik, ruhun tam sözləri və calaveritası kartlarda qalır. Köhnə baza
  qeydlərində yalnız qısa `note` varsa, interfeys bunu ayrıca bildirir.
- **Alternativ hekayə:** checkpoint xəttində çiçəklə işarələnən
  `read_ofrenda → follow_petals` anından yeni hədiyyə ilə ayrıca budaq açılır.
  Əsas gecə dəyişmir; iki nəticənin xatırlanma və istilik fərqi yanaşı görünür.
- **Personaj səsləri:** ekrandakı mətn azərbaycanca qalır; dinləmə düyməsi onu
  ispancaya tərcümə edib Gemini ilə personajın təbii səsini yaradır. Remedios
  üçün Gacrux (nənə), Don Chuy üçün Algenib (baba), Mateíto üçün Puck (uşaq
  interpretasiyası), Beto üçün Charon (əmi) avtomatik seçilir. Səs/dil menyusu
  yoxdur. `.env` daxilində `GEMINI_API_KEY` və ya `GOOGLE_API_KEY` lazımdır;
  tərcümədə mövcud Groq açarı, alınmasa Gemini istifadə olunur. Təkrar dinləmə
  üçün səs server yaddaşında müvəqqəti saxlanır. Keyfiyyət modelin
  interpretasiyasından asılıdır; uğursuzluqda robot brauzer səsinə keçilmir.
- **Vida:** `unut` düyməsi əlavə təsdiq olmadan ruhun yaddaşını və alternativ
  budaqlarını silir. Server uğuru təsdiqlədikdə portret cempasúchil ləçəklərinə
  çevrilir və dramatik musiqi çalır. Səhnəni bağlamaq silinməni geri qaytarmır.

Alternativ budaqlar `altar.db` daxilində ayrıca thread kimi saxlanır və
`story_branches` cədvəlində əsas nəticə ilə əlaqələndirilir. `unut` əməliyyatı
ruh ilə birlikdə ona aid alternativ budaqları da silir.

Jurnal panelində hər hadisənin arxasındakı həqiqi çağırış görünür:

```
› graph.stream({"year": 2024}, {"configurable": {"thread_id": "abuela"}}, …)
› Command(goto="lost", update={"petal_path": False})
› voice.plea(...)  →  state["plea"]   # interrupt mətnini model yazır
› interrupt({...})   ⏸  icra dayandı, checkpoint yazıldı
› model.with_structured_output(Judgement).invoke(...)
› update_state(config{checkpoint_id="…4b2d"}, …)   ⑂ yeni budaq
› checkpointer.delete_thread("abuela")   ✖ üçüncü ölüm
```

Yəni ekranda yalnız hekayə yox, **mexanizm** görünür. Xəttdəki hər nöqtə bir andır: üstünə klikləyib altara nəsə əlavə edib
**oradan yeni budaq** aça bilərsən. Köhnə budaq yerində qalır.

---

## Qovluq quruluşu

```
main.py         vahid giriş nöqtəsi — PyCharm ▶ bunu işə salır
solution/
  state.py      state sxemi + üç fərqli reducer
  nodes.py      beş növ node (saf funksiya, tool, interrupt, paralel, LLM)
  crossing.py   Mictlán keçidi — subqraf
  graph.py      yalnız node/edge — bir sətir də iş məntiqi yoxdur
  voice.py      LLM qatı (offline fallback ilə)
  run_year.py   CLI + bütün checkpointing əməliyyatları
  chaos.py      kill / resume testi
  ui.py         terminal görüntüsü
web/
  server.py     FastAPI + WebSocket ötürücüsü
  static/       hand-made vizualizasiya (kitabxanasız)
altar/          ruhların illik ofrenda faylları
                abuela  — beş illik əsas demo
                mateo   — angelito, 1 noyabr marşrutu
                donchuy — chaos testi üçün
                tio     — üçüncü ölüm demosu
docs/           qrafın şəkli və mermaid mənbəyi
altar.db        checkpoint bazası — silinə bilər, sıfırdan yaranır
```

## Ritual ↔ texnologiya

| Ritual | LangGraph |
|---|---|
| Ofrenda (altar) | `State` — `TypedDict` |
| Altara əşya qoymaq | `update_state()` / `Command(resume=...)` |
| Cempasúchil ləçək yolu | `edge` |
| 1 vs 2 noyabr | `add_conditional_edges(START, ...)` |
| Azmış ruh | `interrupt()` |
| Mictlán səviyyələri | subqraf |
| İl boyu gözləyən ruh | `SqliteSaver` + `thread_id` |
| Keçmiş ziyarətlər | `get_state_history()` |
| Üçüncü ölüm | `delete_thread()` |

## Sıfırdan başlamaq

```bash
rm altar.db     # bütün ruhlar unudulur
```
