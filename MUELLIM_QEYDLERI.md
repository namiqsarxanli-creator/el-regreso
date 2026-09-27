# Müəllim qeydləri

## Dərsin məntiqi

Dörd anlayış bərabər çəkiyə malikdir, ona görə tapşırıq dörd bloka bölünüb
və heç bir blok təkbaşına 100 bal qazandırmır. Ən çox unudulan iki şeyi
tapşırıq **məcburi** edir:

1. **Reducer seçimi** — tələbələr adətən hər şeyi `add_messages` ilə həll
   etməyə çalışır. Burada üç fərqli davranış tələb olunur, biri də öz
   yazdıqları olmalıdır.
2. **Uzun fasilədən sonra davam** — checkpointing-in əsl mənası budur.
   Bir prosesdə `for year in years:` yazmaq bunu nümayiş etdirmir, ona görə
   rubrikada «ayrıca proses» şərti var.

## Ən qısa yol: bir düymə

PyCharm-da **El Regreso** konfiqurasiyasını seç və ▶ bas — server qalxır,
brauzer açılır, baza boşdursa demo məlumatı özü qurulur. Auditoriya
qarşısında əmr yazmaq lazım deyil.

Terminal demosu üçün **El Regreso — 5 illik demo** (`python main.py --demo`):
beş ili ardıcıl işlədir, hər birini **ayrıca proses** kimi — interrupt və
davam da daxil.

## 90 saniyəlik demo ssenarisi

Terminalı böyüdün, `--slow 0.4` istifadə edin ki, node-lar görünsün.

```bash
rm altar.db

# 1) üç il, üç ayrı proses
python -m solution.run_year --soul abuela --year 2021 --slow 0.4
python -m solution.run_year --soul abuela --year 2022
python -m solution.run_year --soul abuela --year 2023

# 2) 2024 — cempasúchil yoxdur, qraf DAYANIR
python -m solution.run_year --soul abuela --year 2024 --no-input
#    burada terminalı bağlayın, auditoriyaya baxın, sonra açın:
python -m solution.run_year --soul abuela --resume --gift cempasúchil

# 3) beşinci il — layihənin zirvəsi
python -m solution.run_year --soul abuela --year 2025
#    → «3 ildir şəkil gətirmirsən»

# 4) ölümsüzlük
python -m solution.chaos

# 5) paralel kainat
python -m solution.run_year --soul abuela --history
python -m solution.run_year --soul abuela --fork 12 --gift şəkil --gift copal

# 6) üçüncü ölüm — TƏBİİ yolla (Tío Beto-nu artıq az adam xatırlayır)
python -m solution.run_year --soul tio --year 2025     # 19
python -m solution.run_year --soul tio --year 2026     # 5
python -m solution.run_year --soul tio --year 2027     # 0 → thread silinir
python -m solution.run_year --soul tio --state         # «thread boşdur»

# və ya dərhal, əl ilə:
python -m solution.run_year --soul abuela --forget
```

**Dörd ruh var:** `abuela` (beş illik əsas demo), `mateo` (angelito — başqa
marşrut və başqa dadlar), `donchuy` (chaos testi üçün, əsas demo pozulmasın
deyə), `tio` (üçüncü ölüm demosu, başlanğıc xatırlanması 25).

> Windows qeydi: `web/server.py` işləyərkən `altar.db` faylını silmək olmur
> (SQLite bağlantısı açıqdır). Əvvəlcə serveri dayandır.

**Vizual variant:** `python -m uvicorn web.server:app --port 8020` —
proyektorda daha yaxşı oturur. Checkpoint xəttindən bir nöqtəyə klikləyib
budaq yaratmaq ən çox təsir bağışlayan andır.

## AI hissəsi — nə deyilməli

Qrafda **dörd LLM node-u** var və hər biri fərqli bir texnikanı nümayiş edir:

| Node | Texnika | Dərsdəki mənası |
|---|---|---|
| `azdı` (lost) | sərbəst generasiya | ruh ailədən nə istədiyini **özü** yazır |
| `qiymət` | `with_structured_output(Judgement)` | model JSON sxemi qaytarır, parse lazım deyil |
| `calaverita` | generasiya + yaddaş | keçən ilin şeiri prompt-dadır, model təkrar etmir |
| `söz` | sərbəst generasiya | faktları cümləyə çevirir |

Üç vurğu:

1. **«Faktlar modeldən gəlmir.»** `3 ildir şəkil gətirmirsən` rəqəmi
   `visits` siyahısından hesablanır. Model onu yalnız cümləyə çevirir.
   Açarı silib yenidən işə salsan, eyni rəqəm deyiləcək — bunu canlı göstər.
2. **«Structured output sərbəst mətndən nə ilə fərqlənir?»** `qiymət`
   node-unun nəticəsi sonrakı node tərəfindən istifadə olunur. Sərbəst
   mətnə etibar etmək olmazdı.
3. **«Interrupt node-unda model çağırmaq olmaz.»** O node davam ediləndə
   başdan işləyir — hər resume-da yeni cavab, yeni xərc. Ona görə xahişi
   `azdı` node-u yaradır. Bu, tələbələrin ən çox düşdüyü tələdir.

**Provayder növbəsi:** Groq bitəndə avtomatik Gemini-yə keçir, ikisi də
bitəndə offline şablona. Terminalda bir sətir görünür:
`[voice] … sıradan çıxdı (limit/kvota) — növbəti provayderə keçilir`.
Auditoriyada bunu qəsdən göstərmək üçün `.env`-dəki Groq açarını pozub
işə salmaq kifayətdir.

## LangGraph jurnalı — mexanizmi göstərən panel

Jurnal hər node üçün nömrələnmiş kart yazır — **node-ların bir-birinə necə
bağlandığı** burada görünür:

```
08  görüş                                                 FAN-İN
    keçmişlə müqayisə: şam (3 il), copal (3 il), pan de muerto (3 il)
    STATE     missing · missing_since · arrived
    │ bu hesablama visits[] üzərindədir — checkpointer olmasa siyahı boş olardı
    NÖVBƏTİ   qiymət və calaverita — iki LLM node-u paralel
    fan-in: visits[] üzərindən missing_since hesablanır
```

Dörd sətrin hər biri bir sualın cavabıdır: *nə etdi · state-ə nə yazdı ·
niyə vacibdir · kimə ötürür.* Sonda həqiqi API çağırışı.

**Təqdimatda necə istifadə etməli:** gecəni başlat, sonra jurnalı yuxarıdan
aşağı oxu — 12 addım bütün dərsi ardıcıllıqla danışır. Xüsusilə üç kartda
dayan:

- **03 ləçək yolu** — «marşrutu node özü seçdi» (Command vs şərti keçid)
- **05–07 paralel üçlük** — «reducer olmasa LangGraph xəta verərdi»
- **08 görüş** — «checkpointer olmasa bu siyahı boş olardı»

Bu panel olmasa, demo «gözəl animasiya» kimi qalır.

### Demo zamanı deyiləsi üç cümlə

- *«Bu proqram ildə bir dəfə, üç dəqiqə işləyir. Aradakı bir ili SQLite
  faylı saxlayır.»*
- *«İndi prosesi öldürürəm — heç bir təmizləmə kodu işləməyəcək.»*
- *«Bu cümləni model uydurmadı. `visits` siyahısından hesabladı.»*

---

## Tələbələrin tipik səhvləri (yoxlama siyahısı)

| Səhv | Necə görünür | Nə soruşmalı |
|---|---|---|
| Reducer yoxdur, paralel node-lar eyni sahəyə yazır | `InvalidUpdateError: At key 'x'` | «İki node eyni anda bir sahəyə yazanda nə olur?» |
| Subqraf valideynin toplayan sahəsinə yazır | jurnal sətirləri cütləşir | «Subqraf valideynə nəyi qaytarır — dəyişikliyi, yoxsa bütün state-i?» |
| `MemorySaver` istifadə edilib | proqram bağlananda hər şey itir | «Sabah açsan, ruh harada olacaq?» |
| Loop-un həddi yoxdur | `GraphRecursionError` | «Bu dövrə nə vaxt dayanır?» |
| `thread_id` sabit («1») | bütün ruhlar bir-birinə qarışır | «İki ruhu eyni anda necə saxlayırsan?» |
| `update_state`-ə əl ilə yığılmış config verilib | `KeyError: 'checkpoint_ns'` | «Config-i haradan alırsan?» |
| `interrupt`-dan sonra `invoke(payload)` təkrar göndərilir | gecə əvvəldən başlayır | «Davam etmək üçün input nə olmalıdır?» |
| LLM açarı yoxdur, proqram çökür | `AuthenticationError` | «Açarsız kompüterdə necə işləyəcək?» |
| Model çağırışı `interrupt` node-unun içindədir | hər resume-da yeni cavab, ikiqat xərc | «Bu node davam ediləndə haradan başlayır?» |
| Modelin cavabı `json.loads()` ilə parse olunur | bəzən çökür, bəzən işləyir | «`with_structured_output` nə üçündür?» |
| `calaveritas` da sıfırlanır | model hər il eyni şeiri yazır | «Model keçən ilinkini haradan bilməlidir?» |

### Xüsusi diqqət: `next` boş ola bilər

Proses node-un **ortasında** öldürüləndə `snapshot.next` boş qalır, amma
`snapshot.tasks` yarımçıq işi göstərir. Yalnız `next`-ə baxan tələbə
«davam ediləsi bir şey yoxdur» nəticəsi çıxaracaq. Həllində belədir:

```python
waiting = list(snapshot.next) or [task.name for task in snapshot.tasks]
```

Bu, əla müzakirə mövzusudur: checkpoint node-ların **arasında** yazılır,
ona görə LangGraph «ən azı bir dəfə» (at-least-once) zəmanəti verir və
node-lar idempotent olmalıdır.

---

## Qiymətləndirməni sürətləndirən yoxlamalar

```bash
# 1. Checkpointer həqiqətən fayldadırmı?
ls -la *.db

# 2. Thread izolyasiyası
python -m solution.run_year --soul mateo --year 2021
python -m solution.run_year --soul abuela --state    # mateo görünməməlidir

# 3. Kill/resume həqiqətən işləyirmi (iki PID)
python -m solution.chaos

# 4. Zaman səyahəti köhnə budağı saxlayırmı?
python -m solution.run_year --soul abuela --history | head -20
# fork-dan sonra köhnə checkpoint-lər hələ də siyahıda olmalıdır
```

## Çətinlik tənzimi

- **Zəif qrup:** Blok 1–3 məcburi, Blok 4-dən yalnız `SqliteSaver` +
  restart tələb olunur; `interrupt`, fork və silmə bonusa keçir.
- **Güclü qrup:** əlavə şərt — `Send` API ilə map-reduce (hər əşya üçün
  ayrıca «dad» node-u), və ya ikinci bir checkpointer (Postgres) ilə eyni
  qrafın işlədilməsi.

## Vaxt büdcəsi (təxmini)

| İş | Saat |
|---|---|
| State + reducer-lər | 2–3 |
| Node-lar (5 növ) | 3–4 |
| Edges + subqraf | 2–3 |
| Checkpointing + CLI | 3–4 |
| README + demo | 1–2 |

Bonus vizualizasiya əlavə 4–6 saat — yalnız istəyənlər üçün.
