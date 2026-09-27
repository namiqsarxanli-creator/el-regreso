# El Regreso — Evə gedən yol

**Mövzu:** LangGraph — Stateful qraflar, Nodes, Edges, Checkpointing
**Müddət:** 2 həftə · **Təhvil:** fərdi · **Maksimal bal:** 100 (+10 bonus)

---

## Hekayə

Meksikada Día de los Muertos gecəsində ölülərin evə qayıtdığına inanılır.
Ailə altar (**ofrenda**) qurur, qapıdan məzara qədər cempasúchil — qadife
gülü — ləçəklərindən yol düzür ki, ruh evi tapa bilsin. 1 noyabr uşaq
ruhlarına (**angelitos**), 2 noyabr böyüklərə (**difuntos**) aiddir.

İnanca görə insan üç dəfə ölür: nəfəsi kəsiləndə, dəfn olunanda və **onu
xatırlayan son adam öləndə**.

Sən bu gecəni bir LangGraph qrafı kimi yazacaqsan. Qraf ildə bir dəfə, bir
neçə dəqiqə işləyir — və gələn il **keçən dəfə nə olduğunu xatırlayır**.

> **Layihənin bir cümləlik ideyası:**
> checkpointer = yaddaş = həyat. `thread_id`-ni silmək üçüncü ölümdür.

---

## Ritual ↔ texnologiya

Bu cədvəl README-də olmalıdır, hər sətir öz kodunla əsaslandırılmalıdır.

| Ritual | LangGraph |
|---|---|
| Ofrenda (altar) | `State` — `TypedDict` sxemi |
| Altara əşya əlavə etmək | `update_state()` / `Command(resume=...)` |
| Cempasúchil ləçək yolu | `edge` — node-lar arası marşrut |
| 1 vs 2 noyabr (angelitos / difuntos) | `add_conditional_edges(START, ...)` |
| Azmış ruh, copal tüstüsü | `interrupt()` + insan müdaxiləsi |
| Mictlán-ın səviyyələri | subqraf (`subgraph` bir node kimi) |
| İl boyu gözləyən ruh | `SqliteSaver` + `thread_id` |
| Keçmiş ziyarətləri xatırlamaq | `get_state_history()` |
| Üçüncü ölüm | checkpoint-in silinməsi (`delete_thread`) |

---

## Blok 1 — Stateful qraf (25 bal)

State bir `dict` deyil, **dizayn** məsələsidir. Ən azı **üç fərqli davranış**
göstərməlisən:

- [ ] `TypedDict` ilə state sxemi, hər sahənin nə üçün olduğu şərhdə yazılıb
- [ ] **Toplayan sahə** — `Annotated[list, operator.add]` (illər yığılır, silinmir)
- [ ] **Üstünə yazılan sahə** — reducer-siz (hər il yenidən qurulan altar)
- [ ] **Öz yazdığın reducer** — hazır olanlardan biri deyil; məsələn təkrarı
      süzən, ardıcıl eyni addımı yazmayan və ya xüsusi işarə ilə sıfırlanan
- [ ] Ən azı bir node **yalnız bir sahə** qaytarır (qismən update-in qalan
      sahələri silmədiyini göstərmək üçün)
- [ ] README-də: «hansı sahəyə niyə bu reducer» — 4 cümlə

> **Tələ:** toplayan sahəni sıfırlamaq lazım gələndə nə edəcəksən? Bu suala
> cavabın kodda görünməlidir.

## Blok 2 — Nodes (25 bal)

Node sayı yox, **növü** qiymətləndirilir. Ən azı beş fərqli tip:

- [ ] **Saf funksiya node** — LLM yoxdur, yalnız state hesablaması
- [ ] **Tool node** — xarici mənbədən oxuyur (fayl / API / DB)
- [ ] **LLM node** — model çağırır. Ən azı **üç** LLM node-u olmalıdır və
      hər biri fərqli iş görməlidir:
      · sərbəst mətn (ruhun sözləri)
      · **structured output** — `with_structured_output(Schema)` ilə sxem üzrə
        cavab; nəticə sonrakı node-lar tərəfindən istifadə olunur
      · generasiya + yaddaş — calaverita: model keçən ilinkini görür və
        təkrar etmir
- [ ] **Provayder növbəsi** — biri bitəndə (kvota, limit) avtomatik
      digərinə keçilir; açar heç yoxdursa offline şablona düşür və proqram
      **çökmür**
- [ ] **Subqraf** — ayrıca qurulmuş qraf, əsas qrafa **bir node kimi** qoşulur
- [ ] **Paralel qrup** — ən azı üç node eyni superstep-də işləyir
- [ ] Hər node-un docstring-i var: nə edir, hansı sahələri dəyişir

> **Tələ:** `interrupt()` olan node davam ediləndə **başdan yenidən işləyir**.
> Model çağırışını ora qoysan, hər resume-da yenidən pul gedəcək və ruh hər
> dəfə başqa şey istəyəcək. Model çağırışını haraya qoyduğunu README-də izah et.

## Blok 3 — Edges (25 bal)

Dörd fərqli marşrutlaşdırma növü:

- [ ] **Şərti keçid** — `add_conditional_edges`, ən azı biri `START`-dan
      (angelitos / difuntos ayrımı)
- [ ] **Loop + hədd** — geri qayıdan dövrə və onun çıxış şərti (sayğac).
      Sonsuz loop = avtomatik 0 bal bu bənddən
- [ ] **Fan-out / fan-in** — paralel budaqlar bir node-da birləşir; birləşmənin
      necə baş verdiyi README-də izah olunub (reducer ilə əlaqəsi).
      **İki ayrı paralel qrup** olmalıdır: biri ucuz saf funksiyalardan,
      biri iki LLM node-undan (eyni anda iki model çağırışı)
- [ ] **`Command` ilə marşrut** — ən azı bir node `Command(goto=..., update=...)`
      qaytarır; şərti keçiddən fərqi şərhdə yazılıb
- [ ] `draw_mermaid_png()` ilə çəkilmiş qraf şəkli təhvildə var

## Blok 4 — Checkpointing (25 bal)

- [ ] `SqliteSaver` (yaddaşda deyil, **faylda**)
- [ ] **Thread izolyasiyası** — ən azı 3 ruh, 3 `thread_id`, state-lər qarışmır
- [ ] **Kill → resume** — proses sərt şəkildə öldürülür, yenidən açılır və
      öldüyü yerdən davam edir. Logda **iki ayrı PID** görünməlidir
- [ ] **`interrupt()` + davam** — qraf insanı gözləyir; proqram bağlanıb
      yenidən açılandan sonra da eyni yerdən davam edir
- [ ] **Zaman səyahəti** — `get_state_history()` ilə keçmiş bir ana qayıt,
      `update_state()` ilə altarı dəyiş, **yeni budaq** yarat. Köhnə budaq
      yerində qalmalıdır
- [ ] **Üçüncü ölüm** — şərt ödənəndə `delete_thread()` çağırılır və növbəti
      işə salmada thread həqiqətən boş olur

> **`--year 2021`, `--year 2022` … ardıcıl çağırmaq kifayət deyil.**
> Hər il **ayrıca proses** olmalıdır: proqram tam bağlanır, sonra açılır.
> Bir `for` dövrəsində beş il işlətmək bu bənddən bal qazandırmır.

## Bonus (10 bal)

- [ ] Canlı vizualizasiya (WebSocket + qraf) — node-lar işıqlanır
- [ ] **LangGraph jurnalı** — ekranda hər hadisənin arxasındakı həqiqi
      çağırış görünür (`Command(goto=…)`, `interrupt(…)`, `update_state(…)`,
      `delete_thread(…)`). Təqdimatda ən çox faydası olan hissədir
- [ ] 60 saniyəlik demo videosu
- [ ] `Send` API ilə map-reduce: hər altar əşyası üçün ayrıca «dad» node-u

---

## Təhvil paketi

```
soyad_ad_elregreso/
├─ README.md            ritual↔texnologiya cədvəli, reducer izahı, işə salma
├─ state.py             sxem + reducer-lər
├─ nodes.py             node-lar
├─ crossing.py          subqraf
├─ graph.py             yalnız node/edge — iş məntiqi yoxdur
├─ run_year.py          CLI: --year, --resume, --history, --fork, --forget
├─ chaos.py             prosesi öldürüb bərpa edən test
├─ altar/*.json         ən azı 3 ruh, hər birində 4+ il
├─ docs/graph.png       qrafın şəkli
└─ docs/demo.md         ekran görüntüləri və ya video linki
```

## Qiymətləndirmə

| Blok | Bal |
|---|---:|
| 1 — Stateful qraf: sxem, 3 fərqli davranış, öz reducer-in | 25 |
| 2 — Nodes: 5 fərqli tip, 3 LLM node-u (biri structured output), subqraf, paralel qrup | 25 |
| 3 — Edges: şərti, loop+hədd, fan-out/fan-in, `Command` | 25 |
| 4 — Checkpointing: izolyasiya, kill-resume, interrupt, zaman səyahəti, silinmə | 25 |
| Bonus — vizualizasiya / video / calaverita | +10 |

**Avtomatik bal itkisi:**
– sonsuz loop (`recursion limit` xətası) → Blok 3-dən 10 bal
– `MemorySaver` (yaddaşda checkpointer) → Blok 4-dən 15 bal
– LLM açarı olmadan proqram çökürsə → Blok 2-dən 8 bal
– `interrupt` olan node-un içində model çağırışı varsa → Blok 2-dən 8 bal
– modelin cavabı `json.loads()` ilə əl ilə parse olunursa (structured output
  əvəzinə) → Blok 2-dən 5 bal
– bütün node-lar eyni tipdədirsə (hamısı LLM və ya hamısı saf funksiya) → Blok 2-dən 10 bal

## Mərhələli təhvil

**1-ci həftə (Blok 1 + 2 + 3):** qraf işləyir, checkpointer **yoxdur**.
Hər işə salma sıfırdan başlayır — bu, qəsdəndir. Yaddaşsız qrafın nə demək
olduğunu öz təcrübəndə görməlisən.

**2-ci həftə (Blok 4):** eyni qrafa `checkpointer=` əlavə olunur və layihə
canlanır. `graph.py`-da dəyişən sətir sayı çox az olacaq — bu da dərsin bir
hissəsidir.

## Demo ssenarisi (təqdimatda 90 saniyə)

1. `--year 2021` → gecə keçir, ruh danışır
2. `--year 2022`, `--year 2023` → **hər dəfə ayrı proses**
3. `--year 2024` → cempasúchil yoxdur, ruh azır, qraf **dayanır**
4. Terminalı bağla. Yenidən aç. `--resume` → ruh hələ də qapının ağzındadır
5. `--year 2025` → ruh deyir: «3 ildir şəkil gətirmirsən»
6. `chaos.py` → proses öldürülür, iş itmir
7. `--history` → keçmişə qayıt, altarı dəyiş, **paralel kainat**
8. `--forget` → thread silinir. Yenidən işə sal: heç kim gəlmir
