# Detected Profanity

<p align="center">
  <a href="https://pypi.org/project/detected-profanity/"><img alt="PyPI" src="https://img.shields.io/pypi/v/detected-profanity?style=flat-square&logo=pypi&logoColor=white&label=PyPI&color=3775A9"></a>
  <a href="https://pypi.org/project/detected-profanity/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/detected-profanity?style=flat-square&logo=python&logoColor=white&label=Python&color=3775A9"></a>
  <a href="https://github.com/detected-profanity/detected-profanity/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square"></a>
  <img alt="Zero deps" src="https://img.shields.io/badge/dependencies-zero-brightgreen?style=flat-square">
  <img alt="Coverage" src="https://img.shields.io/badge/coverage-100%25-brightgreen?style=flat-square">
</p>

<p align="center">
  <b>Детектор мата для RU / EN / транслита. Без зависимостей.</b><br>
  <i>Profanity detection for Russian, English and translit. Zero dependencies, pure Python.</i>
</p>

<p align="center">
  <code>NFKC</code> · <code>ё→е</code> · <code>leet / homoglyph</code> · <code>сепараторы</code> · <code>повторы 3+→2</code> · <code>делеция / дубль</code> · <code>Aho-Corasick O(n+z)</code> · <code>allowlist</code>
</p>

---

## Оглавление

- [Features](#features)
- [Установка](#установка)
- [Быстрый старт](#быстрый-старт)
- [Маскировки](#маскировки)
- [Архитектура](#архитектура)
- [Производительность](#производительность)
- [Сравнение с альтернативами](#сравнение-с-альтернативами)
- [API Reference](#api-reference)
- [Allowlist](#allowlist)
- [Разработка и публикация](#разработка-и-публикация)
- [Лицензия](#лицензия)

---

## Features

| Возможность | Что делает |
|---|---|
| **3 языка** | `ru` / `en` / `translit` (`pizdec`, `hui`, `blyad`) + `all` (по умолчанию) |
| **Нормализация** | `NFKC` (fullwidth → ascii, лигатуры), `lower`, `ё→е`, снятие диакритики |
| **Leet / homoglyph** | RU: `0→о`, `3→з`, `4→а`, `@→а`, `$→с`, `a→а`, `e→е`, `o→о`, `p→р` · EN: `0→o`, `1→l`, `!→i`, `|→l`, `$→s`, `@→a` |
| **Сепараторы** | 40+ символов: `# * . _ - \| / · • —` + ZWS (`​`, `‌`, `‍`, `﻿` и др.) — вырезаются перед поиском |
| **Повторы** | `бляяяя → бляя`, `fuuuuuck → fuuck` — схлопывание `3+ → 2` |
| **Делеция / дубль** | `пздец` (пропуск), `хууй` (дубль) — варианты генерируются при сборке автомата |
| **Границы слова** | Проверка `word-expand` + allowlist — `мандарин` / `assassin` не триггерят |
| **Aho-Corasick** | `O(n+z)` поиск, ленивая сборка автоматов, thread-safe `search` |
| **Zero deps** | Только stdlib, Python 3.8+ |
| **Транслит** | Двойная проверка: `lower` + EN-leet нормализация |

---

## Установка

```bash
pip install detected-profanity
```

Требования: **Python 3.8+**, без зависимостей.

Из исходников:

```bash
git clone https://github.com/detected-profanity/detected-profanity
cd detected-profanity
pip install -e .
# с dev-зависимостями
pip install -e ".[dev]"
```

Проверка:

```bash
python -c "from detected_profanity import contains_profanity; print(contains_profanity('привет'))"
# False
python -m detected_profanity "пошёл на хуй"
# profanity: YES  matches=['хуй']
```

---

## Быстрый старт

### Python API

```python
from detected_profanity import ProfanityDetector, contains_profanity, detect, censor, normalize_text

# по умолчанию — все языки (ru + en + translit)
contains_profanity("Привет, как дела?")   # False
contains_profanity("охуеть, это пиздец")  # True
detect("охуеть, это пиздец")              # ["охуеть", "пиздец"]
censor("ну ты мудак")                     # "ну ты *****"
censor("пошёл нахуй", repl="#")           # "пошёл #####"

# нормализация раскрывает маскировку
normalize_text("бл@ть, 0хуеть")           # "блать, охуеть"  (@→а, 0→о)
contains_profanity("бл@ть")               # True

# фильтр по языку
det_ru = ProfanityDetector(lang="ru")
det_ru.contains_profanity("hello fuck")   # False  — только RU
det_ru.detect("блядь и shit")             # ["блядь"]

det_en = ProfanityDetector(lang="en")
det_en.contains_profanity("fuck")         # True
det_en.contains_profanity("хуй")          # False

# несколько языков
det = ProfanityDetector(languages=["ru", "en"])
det.contains_profanity("хуй")             # True
det.contains_profanity("fuck")            # True

# транслит
ProfanityDetector().contains_profanity("pizdec kak holodno")  # True
ProfanityDetector(lang="translit").detect("ebat ti pidor")    # ["ebat", "pidor"]

# без нормализации / без транслита
ProfanityDetector(use_normalization=False).contains_profanity("бл@ть")  # False
ProfanityDetector(lang="ru", include_translit=False).contains_profanity("pizdec")  # False

# allowlist — ложных срабатываний нет
contains_profanity("мандарин и assassin")  # False
contains_profanity("художник")             # False
```

### CLI

```bash
# one-shot
python -m detected_profanity "охуеть, это пиздец"
# profanity: YES  matches=['охуеть', 'пиздец']

python -m detected_profanity --censor "ну ты мудак"
# ну ты *****

# разные языки
python -m detected_profanity --lang ru "fuck"   # profanity: NO
python -m detected_profanity --lang en "fuck"   # profanity: YES

# JSON + stdin (для пайпов и CI)
echo "pizdec" | python -m detected_profanity --json
# {"text": "pizdec\n", "has_profanity": true, "matches": ["pizdec"]}

python -m detected_profanity --censor --repl "#" --json --lang all "fuck you, блядь"

# REPL
python cli.py
# › привет, как дела?  → not detected
# › на#хуя ты это сделал → detected
# › /exit — выход
```

`--help`:

```
usage: detected_profanity [-h] [--lang {ru,en,translit,all}] [--censor] [--repl REPL]
                          [--json] [--no-normalize] [--no-translit] [-v] [text ...]

  text                  Текст для проверки (если не указан — читается stdin)
  --lang                Язык лексикона (default: all)
  --censor              Вывести цензурированную версию
  --repl REPL           Символ-заменитель (default: "*")
  --json                JSON-вывод
  --no-normalize        Отключить NFKC/leet/homoglyph
  --no-translit         Не включать транслит
  -v, --version

exit-коды: 0 = чисто, 1 = найден мат, 2 = ошибка ввода
```

Консольная команда (после `pip install`): `detected-profanity "текст"` — алиас к `python -m detected_profanity`.

---

## Маскировки

Каждый пример ниже — `contains_profanity(...) is True`. Проверено на датасете 60 фраз (см. [Производительность](#производительность)).

### RU — 14 примеров

| # | Тип | Ввод | Нормализован | Матчится как | Комментарий |
|---|-----|------|-------------|-------------|-------------|
| 1 | Сепаратор `#` | `на#хуя` | `нахуя` | `нахуя` | `#` ∈ `SEPARATORS`, вырезается |
| 2 | Сепаратор `*` | `х*й` | `хй` | `хй` | каноническая форма для `х*й` |
| 3 | Leet `0→о` | `0хуеть` | `охуеть` | `охуеть` | `LEET_MAP: 0→о` |
| 4 | Leet `@→а` | `бл@ть` | `блать` | `блать` | `@→а`, форма `блать` в словаре |
| 5 | Сепараторы `..` | `п..здец` | `пздец` | `пздец` | `.` — сепаратор, `и` — делеция |
| 6 | Пробелы | `х у й` | `хуй` | `хуй` | пробел — сепаратор, поиск в `stripped` |
| 7 | Точки | `б.л.я` | `бля` | `бля` | каждая `.` — сепаратор |
| 8 | Повторы `3+→2` | `бляяяя` | `бляя` | `бля` | `collapse_repeats: (.)\1{2,}→\1\1` |
| 9 | Делеция | `пздец` | `пздец` | `пздец` | `_gen_variants` удаляет 1 букву при `len≥4` |
| 10 | Дефисы | `х-у-й` | `хуй` | `хуй` | `-` — сепаратор |
| 11 | Homoglyph `a→а` | `блaть` (лат. `a`) | `блать` | `блать` | `HOMOGLYPH_MAP: a→а` |
| 12 | Fullwidth | `ｂｌｙａｄ` | `blyad` → `бляд` | `бляд` | `NFKC` fullwidth → ascii → homoglyph |
| 13 | Смешанная | `п#здец` | `пздец` | `пздец` | `#` + делеция |
| 14 | Регистр | `ХУЙ` / `ХуЙ` | `хуй` | `хуй` | `lower` до маппинга |

### EN — 10 примеров

| # | Тип | Ввод | Нормализован | Матчится как |
|---|-----|------|-------------|-------------|
| 1 | Сепаратор `*` | `f*ck` | `fck` | `fuck` (вариант делеции `u`) |
| 2 | Сепаратор `*` | `sh*t` | `sht` | `shit` |
| 3 | Leet `$→s` | `a$$hole` | `asshole` | `asshole` |
| 4 | Leet `!→i` | `b!tch` | `bitch` | `bitch` |
| 5 | Leet `@→a` | `f@ck` | `fack` | `fuck` (через `stripped`) |
| 6 | Пробелы | `f u c k` | `fuck` | `fuck` |
| 7 | Точки | `b.i.t.c.h` | `bitch` | `bitch` |
| 8 | Повторы | `fuuuuuck` | `fuuck` | `fuck` (вариант дубля) |
| 9 | Делеция | `fck` | `fck` | `fuck` |
| 10 | Leet `5→s` | `5hit` | `shit` | `shit` |

### Транслит

| Ввод | Матчится как | Исходник |
|------|-------------|----------|
| `pizdec` | `pizdec` | `пиздец` |
| `hui` / `huy` / `khuy` | `hui` | `хуй` |
| `ebat` / `yebat` | `ebat` | `ебать` |
| `blyad` / `blya` | `blyad` | `блядь` |
| `pidor` / `pidaras` | `pidor` | `пидор` |
| `suka` | `suka` | `сука` |

> Карты: `detected_profanity/normalizer.py` — `LEET_MAP`, `HOMOGLYPH_MAP`, `SKELETON_MAP`, `SEPARATORS` (40+ символов включая ZWS `​`, `‌`, `‍`, `﻿`).

---

## Архитектура

```
                  ┌──────────────────────────────────────────────────┐
  raw text        │              ProfanityDetector                    │
  "бл@ть, 0хуеть!"│                                                   │
       │          │   ┌──────────────┐      ┌──────────────────┐     │
       ▼          │   │  RU branch   │      │  EN / translit   │     │
  ┌──────────┐    │   │ normalize_   │      │  _en_normalize   │     │
  │  NFKC    │────┼──►│ text (NFKC+  │      │  (NFKC+lower+    │     │
  │ normalize│    │   │ lower+ё→е+   │      │  EN leet)        │     │
  └────┬─────┘    │   │ skeleton)    │      │                  │     │
       │          │   └──────┬───────┘      └────────┬─────────┘     │
       ▼          │          │                       │               │
  ┌──────────┐    │          ▼                       ▼               │
  │  lower   │    │   collapse_repeats  (.)\1{2,} → \1\1             │
  └────┬─────┘    │   "бляяяя" → "бляя"  /  "fuuuuuck" → "fuuck"      │
       │          │          │                       │               │
       ▼          │          ▼                       ▼               │
  ┌──────────┐    │   ┌─────────────┐        ┌─────────────┐         │
  │  ё → е   │    │   │  collapsed  │        │  collapsed  │         │
  └────┬─────┘    │   │ "блать,     │        │ "fuck,      │         │
       │          │   │  охуеть"    │        │  shit"      │         │
       ▼          │   └──────┬──────┘        └──────┬──────┘         │
  ┌──────────────┐│          │  ┌───────────────────┘                │
  │ skeleton map ││          │  │  _strip_with_map(SEPARATORS)       │
  │ 0→о,@→а,a→а  ││      ┌───▼──▼───┐                                 │
  └──────┬───────┘│      │ stripped │  без сепараторов + cmap        │
         │        │      │ "блать   │  "fuckshit" + [pos map]        │
         ▼        │      │  охуеть" │                                 │
  ┌──────────────┐│      └────┬─────┘                                 │
  │  collapsed   ││           │                                       │
  │  3+ → 2      ││     ┌─────▼──────┐                                │
  └──────┬───────┘│     │ Aho-Corasick│  O(n+z) scan                  │
         │        │     │  build: O(N)│  N = Σ len(patterns)          │
         ▼        │     │ search: O(n+z)│ n=len(text), z=matches      │
  ┌──────────────┐│     └─────┬──────┘                                │
  │  stripped    ││           │  collapsed  +  stripped               │
  │  + cmap      ││           │  (два прохода)                        │
  └──────┬───────┘│           ▼                                       │
         │        │     ┌──────────┐  word-expand + allowlist         │
         ▼        │     │  filter  │  is_allowed(word)               │
     ┌────────┐   │     └────┬─────┘  len 2/3 → strict               │
     │ Aho AC │   │          │                                        │
     └────┬───┘   │          ▼                                        │
          │       │     contains → bool / detect → list / censor      │
          ▼       │                                                   │
     ┌─────────┐  │                                                   │
     │ filter  │  └──────────────────────────────────────────────────┘
     └─────────┘
```

### Шаги

| # | RU ветка | EN / translit ветка | Сложность |
|---|----------|---------------------|-----------|
| 1 | `unicodedata.normalize('NFKC', text)` | то же | `O(n)` |
| 2 | `lower()` + `ё→е` | `lower()` + `_EN_LEET_MAP` | `O(n)` |
| 3 | `SKELETON_MAP` (`0→о`, `@→а`, `a→а` …) | `_EN_LEET_MAP` (`0→o`, `@→a`, `!→i` …) | `O(n)` |
| 4 | `collapse_repeats` | то же | `O(n)` |
| 5 | `stripped` + `cmap` (без `SEPARATORS`) | то же | `O(n)` |
| 6 | `_gen_variants` при **сборке** (делеция `len≥4`, дубль `len≥3`) | то же | `O(P·L)` один раз |
| 7 | `AhoCorasick.search(collapsed)` + `search(stripped)` | то же | **`O(n+z)`** |
| 8 | `_expand_word` + `is_allowed` фильтрация | то же | `O(z·w)` |

Паттерны расширяются на этапе сборки, поиск остаётся линейным. Автоматы ленивые (`_get_ru_ac` / `_get_en_ac` / `_get_tr_ac`) — строятся при первом вызове. `search` thread-safe (только чтение).

---

## Производительность

### Сложность

| Операция | Сложность | Примечание |
|---|---:|---|
| `AhoCorasick.build` | `O(N)`, `N = Σ len(pattern)` | BFS по трие, один раз |
| `AhoCorasick.search` | **`O(n+z)`** | `n=len(text)`, `z=совпадений` |
| `AhoCorasick.search_iter` | `O(n+z)` streaming | ленивый генератор |
| `normalize_text` | `O(n)` | NFKC + lower + map |
| `contains_profanity` | `O(n+z)` | нормализация + 2× Aho |
| Память | `O(N)` trie | ~500 паттернов с вариантами |

Линейный скан против `O(n·m)` наивного перебора — критично на длинных текстах и больших словарях.

### Бенчмарк

Датасет: **60 фраз** — `30 RU (10 clean + 10 open + 10 masked)` + `30 EN (10 clean + 10 open + 10 masked)`. Запуск: `python benchmarks/benchmark.py`.

```
Benchmark: detected-profanity vs alternatives (60 фраз: 30 RU + 30 EN)
```

| Library | Status | Acc | Prec | Rec | F1 | Time(s) | ms/txt | TP | TN | FP | FN |
|---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **detected-profanity** | ok | **100.0%** | 100.0% | **100.0%** | **100.0%** | **0.0316** | **0.53** | 40 | 20 | 0 | 0 |
| better-profanity | ok | 60.0% | 100.0% | 40.0% | 57.1% | 0.1354 | 2.26 | 16 | 20 | 0 | 24 |
| profanity-check | ok | 58.3% | 100.0% | 37.5% | 54.5% | 0.2000 | 3.33 | 15 | 20 | 0 | 25 |
| censure | skipped | — | — | — | — | — | — | — | — | — | — |

Детализация (только `ok`):

| Library | RU (30) | EN (30) | Clean (20) | Open (20) | Masked (20) |
|---|---:|---:|---:|---:|---:|
| **detected-profanity** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| better-profanity | 33.3% | 86.7% | 100.0% | 50.0% | 30.0% |
| profanity-check | 33.3% | 83.3% | 100.0% | 50.0% | 25.0% |

Итог:

- **Best accuracy / F1 / recall / masked** — `detected-profanity` (100% на всех срезах)
- **Fastest** — `detected-profanity` (0.53 ms/текст, в 4–6× быстрее альтернатив)
- Альтернативы проваливают RU (33.3%) и маскировки (25–30%)

![Benchmark chart](benchmarks/benchmark.png)

Воспроизвести:

```bash
python benchmarks/benchmark.py --json benchmarks/results.json --png benchmarks/benchmark.png
python benchmarks/benchmark.py --no-plot
python benchmarks/benchmark.py --list-dataset
```

---

## Сравнение с альтернативами

Основано на `benchmarks/results.json` (60 фраз, см. выше).

| Критерий | **detected-profanity** | `better-profanity` | `profanity-check` | `censure` |
|---|:---:|---|---|---|
| **RU** | **Да** (150+ форм, 40+ корней) | Нет (EN only) | Нет | Нет |
| **Транслит** | **Да** (100+ форм) | Нет | Нет | Нет |
| **Leet / homoglyph** | **Да** | Частично | Нет | Нет |
| **Сепараторы (40+)** | **Да** | Нет | Нет | Нет |
| **Повторы 3+→2** | **Да** | Нет | Нет | Нет |
| **Делеция / дубль** | **Да** | Нет | Нет | Нет |
| **Allowlist** | **Да** | Нет | Нет | Нет |
| **Accuracy (60)** | **100%** | 60.0% | 58.3% | — |
| **Masked (20)** | **100%** | 30.0% | 25.0% | — |
| **RU accuracy (30)** | **100%** | 33.3% | 33.3% | — |
| **Алгоритм** | **Aho-Corasick O(n+z)** | Regex / list scan | ML (sklearn TF-IDF) | Regex |
| **Зависимости** | **zero** (stdlib) | zero | `scikit-learn` (~100 MB) | zero |
| **Скорость** | **0.53 ms/txt** | 2.26 ms/txt | 3.33 ms/txt | — |
| **Censor** | Да (`repl`) | Да | Нет | Да |
| **Лицензия** | MIT | MIT | MIT | MIT |

Вердикт: единственная из проверенных библиотек, проходящая RU + маскировки без регресса на EN. Единственный zero-deps вариант с `O(n+z)` и <1 ms на текст.

---

## API Reference

### `ProfanityDetector`

```python
ProfanityDetector(
    lang: str | None = None,              # "ru" | "en" | "translit" | "all" | None (all)
    languages: str | list[str] | None = None,  # альтернатива lang: ["ru", "en"]
    *,
    include_translit: bool = True,        # включать транслит при ru/all
    use_normalization: bool = True,       # NFKC+leet+homoglyph (False → только lower)
)
```

| Метод | Сигнатура | Описание |
|---|---|---|
| `contains_profanity` | `(text: str) -> bool` | Есть ли мат |
| `detect` | `(text: str) -> list[str]` | Список канонических форм |
| `censor` | `(text: str, repl="*") -> str` | Цензурированная копия |

Бросает `TypeError` если `text` не `str`. Пустая строка → `False` / `[]`.

### Функциональный API (синглтон `all`)

| Символ | Тип | Описание |
|---|---:|---|
| `contains_profanity(text)` | `-> bool` | Шорткат через дефолтный детектор |
| `detect(text)` | `-> list[str]` | Шорткат |
| `censor(text, repl="*")` | `-> str` | Шорткат |
| `normalize_text(text)` | `-> str` | `NFKC + NFKD strip + lower + ё→е + SKELETON_MAP` |
| `collapse_repeats(text)` | `-> str` | `aaa→aa` (3+ → 2) |
| `__version__` | `str` | Версия пакета |

### `normalizer` — карты

| Константа | Содержимое |
|---|---|
| `LEET_MAP` | `0→о`, `3→з`, `4→а`, `5→s`, `@→а`, `$→с`, `€→е` |
| `HOMOGLYPH_MAP` | `a→а`, `e→е`, `o→о`, `p→р`, `c→с`, `x→х`, `y→у`, `H→Н` … |
| `SKELETON_MAP` | `LEET_MAP ∪ HOMOGLYPH_MAP` |
| `SEPARATORS` | `set` из 40+ сепараторов (включая ZWS `​`, `‌`, `‍`, `﻿`) |

### `matcher.AhoCorasick`

```python
from detected_profanity.matcher import AhoCorasick, Match, find_matches

ac = AhoCorasick(["хуй", "пиздец", "fuck"])
ac.search("охуеть, fuck")          # [(5, "хуй"), (12, "fuck")]  — (end_idx, pattern)
ac.search_iter("длинный текст")    # генератор
ac.find_matches("охуеть")          # [Match(pattern="хуй", start=1, end=3)]
find_matches("text", ["bad", "word"])
len(ac)                            # число паттернов
"хуй" in ac                        # True
```

| Метод | Сложность |
|---|---|
| `add_pattern(p)` | `O(k)`, `k=len(p)` |
| `build()` | `O(N)` BFS, idempotent |
| `search(text)` | `O(n+z)` |
| `search_iter(text)` | `O(n+z)` streaming |
| `find_matches(text)` | `O(n+z)` → `list[Match]` |

### `lexicon`

| Символ | Описание |
|---|---|
| `ALL_RU_ROOTS` (40+) | Базовые корни |
| `RU_FORMS` (150+) | Кириллические формы |
| `EN_FORMS` (100+) | Английские формы |
| `TRANSLIT_FORMS` (100+) | Транслит-формы |
| `ALLOWLIST` | Белый список (`set[str]`) |
| `is_allowed(token)` | Проверка allowlist (нормализация + префикс `len≥4`) |
| `get_patterns(lang, include_translit)` | Скомпилированные `re` паттерны с `\b` |

---

## Allowlist

Подстроки профлексики встречаются в нормальных словах — детектор фильтрует их до проверки паттернов.

| Токен | Почему в allowlist | Без фильтра |
|---|---|---|
| `мандарин`, `мандат`, `команда` | содержат `манд` | FP на `манда` |
| `художник`, `художественный` | содержат `ху` | FP на `хуй` |
| `бляшка`, `блок`, `бланк`, `облако` | содержат `бля` / `бл` | FP на `блядь` |
| `страхование`, `подстраховать` | содержат `страх` | FP |
| `assassin`, `assistant`, `classic`, `pass` | содержат `ass` | FP на `ass` |
| `cocktail`, `cockpit`, `peacock` | содержат `cock` | FP на `cock` |
| `shiitake` | содержит `shit` | FP на `shit` |

Проверка — `is_allowed(token)`: `lower + ё→е + strip пунктуации`, точное совпадение или префикс `len≥4` (`мандариновый` → `мандарин`). Плюс `word-expand` в детекторе: совпадение отбрасывается, если слово-носитель целиком в allowlist.

Кастомизация — передайте свой allowlist через форк `lexicon.py` или фильтрацию результата `detect()`.

---

## Разработка и публикация

### Разработка

```bash
git clone https://github.com/detected-profanity/detected-profanity
cd detected-profanity
pip install -e ".[dev]"

pytest -q                          # все тесты
pytest tests/test_detector.py -v   # только детектор
python -m ruff check .             # линтер
python -m mypy detected_profanity  # типы (strict)
```

Бенчмарк:

```bash
python benchmarks/benchmark.py
python benchmarks/benchmark.py --list-dataset
python benchmarks/benchmark.py --no-plot
cat benchmarks/results.json | python -m json.tool | head -n 60
open benchmarks/benchmark.png
```

Структура:

```
detected_profanity/
  __init__.py      — публичный API, __version__
  detector.py      — ProfanityDetector + Aho-Corasick wiring
  normalizer.py    — NFKC, LEET_MAP, HOMOGLYPH_MAP, SEPARATORS, collapse_repeats
  matcher.py       — AhoCorasick, Match, find_matches (pure Python, O(n+z))
  lexicon.py       — ALL_RU_ROOTS, RU/EN/TRANSLIT_FORMS, ALLOWLIST, is_allowed
  __main__.py      — python -m detected_profanity (argparse)
cli.py             — интерактивный REPL
benchmarks/
  benchmark.py     — сравнение с better-profanity / profanity-check / censure
  dataset.py       — 60 фраз (RU/EN clean/profane/masked)
  results.json     — последний прогон
  benchmark.png    — график
tests/
  test_detector.py / test_normalizer.py / test_matcher.py / test_cli.py
```

Требования к PR:

- `python -m ruff check .` — 0 warnings
- `python -m mypy detected_profanity` — strict, без `any`
- `pytest -q` — зелёный
- PR <200 строк

### Публикация

```bash
# версия — в pyproject.toml и detected_profanity/__init__.py (__version__)
# 1. bump версии, changelog, git tag
# 2. сборка
python -m build                    # hatchling → dist/*.whl + *.tar.gz
twine check dist/*

# 3. проверка в TestPyPI (опционально)
twine upload --repository testpypi dist/*

# 4. релиз
twine upload dist/*
git tag v1.0.0 && git push --tags
```

`pyproject.toml`: `build-system = hatchling`, `requires-python >=3.8`, `dependencies = []`.

---

## Лицензия

MIT — см. [LICENSE](LICENSE).

---

<p align="center">
  <sub>Для модерации чатов, комментариев и UGC без ML и внешних API.</sub>
</p>
