# Buradan başla

Tapşırığın şərtləri və rubrika: [`../TAPSIRIQ.md`](../TAPSIRIQ.md)

## Sıra

```bash
grep -rn "TODO" .        # bütün boşluqlar
```

`TODO`-lar nömrələnib, ardıcıllıqla get:

| Sıra | Fayl | Nə yazırsan |
|---|---|---|
| 1.1 – 1.5 | `state.py` | üç reducer + state sxemi |
| 2.1 – 2.12 | `nodes.py` | node-lar (5 fərqli növ) |
| 3.1 – 3.6 | `crossing.py` | subqraf |
| 3.7 | `graph.py` | node-lar və keçidlər |
| 4.1 – 4.11 | `run_year.py` | checkpointing |

## Hazır verilənlər

`ui.py` (terminal görüntüsü), `voice.py` (LLM qatı + offline şablon),
`chaos.py` (prosesi öldürüb bərpa edən test), `read_altar` tool-u və
`altar/*.json` faylları. Bunlara toxunmaq lazım deyil — dərsin mövzusu
deyillər.

## Yoxlama

PyCharm-da istənilən faylı açıb ▶ basa bilərsən — faylların başındakı üç
sətir nisbi importları işlək saxlayır. Terminaldan:

```bash
python -m starter.graph --png          # qraf çəkilirmi?
python -m starter.run_year --soul abuela --year 2021
python -m starter.run_year --soul abuela --year 2022   # AYRI proses
python -m starter.chaos                # öldür və bərpa et
```

İlk həftə `build_graph()`-ı checkpointer-siz təhvil verirsən: hər işə salma
sıfırdan başlayacaq. Bu, qəsdəndir — ikinci həftədə bir arqument əlavə
edəcəksən və fərqi özün görəcəksən.
