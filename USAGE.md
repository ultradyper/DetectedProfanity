# USAGE — Руководство по использованию / Usage Guide

> `detected-profanity` — детекция мата для **RU / EN / транслит** · Zero deps · `Aho-Corasick O(n+z)` · `NFKC` · `leet/homoglyph` · `allowlist`

[🇷🇺 Русский](#-русский) · [🇬🇧 English](#-english)

---

# 🇷🇺 Русский

## Содержание (RU)

1. [Установка](#1-установка)
2. [Базовый детект](#2-базовый-детект)
3. [Маскировки](#3-маскировки-нахуя-хй-0хуеть-блть-p1zda-и-др)
4. [Транслит](#4-транслит)
5. [Allowlist — защита от ложных срабатываний](#5-allowlist--защита-от-ложных-срабатываний)
6. [Фильтр по языку (lang)](#6-фильтр-по-языку-lang)
7. [Цензурирование (censor)](#7-цензурирование-censor)
8. [Нормализация (normalize_text)](#8-нормализация-normalize_text)
9. [Кастомный словарь](#9-кастомный-словарь)
10. [Производительность](#10-производительность)
11. [CLI](#11-cli)
12. [API Reference](#12-api-reference-ru)
13. [Частые ошибки](#13-частые-ошибки-ru)

---

## 1. Установка

Требования: **Python 3.8+**, без зависимостей.

```bash
pip install detected-profanity
```

Из исходников:

```bash
git clone https://github.com/detected-profanity/detected-profanity
cd detected-profanity
pip install -e .
pip install -e ".[dev]"   # для тестов/линтера
```

Проверка:

```bash
python -c "from detected_profanity import contains_profanity; print(contains_profanity('привет'))"
# False
python -m detected_profanity "пошёл на хуй"
# profanity: YES  matches=['хуй']
```

---

## 2. Базовый детект

Два API — функциональный (синглтон `lang=all`) и класс `ProfanityDetector`.

```python
from detected_profanity import contains_profanity, detect, censor
from detected_profanity import ProfanityDetector

# --- функциональный API (по умолчанию all: ru + en + translit) ---
contains_profanity("Привет, как дела?")    # False
contains_profanity("охуеть, это пиздец")   # True
detect("охуеть, это пиздец")               # ["охуеть", "пиздец"]
censor("охуеть, это пиздец")               # "******, это ******"

# --- класс — тот же результат, но можно настроить язык ---
det = ProfanityDetector()                  # lang=None == "all"
det.contains_profanity("хуй")              # True
det.detect("хуй пиздец")                   # ["хуй", "пиздец"]
det.censor("хуй пиздец")                   # "*** ******"

# пустая строка / пробелы — всегда чисто
contains_profanity("")                     # False
contains_profanity("   ")                  # False
detect("")                                # []
```

Контракт:

- `text` должен быть `str`, иначе `TypeError`.
- `contains_profanity` → `bool`, `detect` → `list[str]`, `censor` → `str`.
- `detect` возвращает **канонические формы** (нормализованные, без дублей), не исходные подстроки.

---

## 3. Маскировки (`на#хуя`, `х*й`, `0хуеть`, `бл@ть`, `p1zda` и др.)

Каждый пример ниже даёт `True`. Детектор ловит 5 классов обфускации одновременно.

### 3.1 Примеры из ТЗ — скопируй и проверь

```python
from detected_profanity import ProfanityDetector

det = ProfanityDetector()

# 1. Сепаратор # — вырезается (40+ сепараторов: # * . _ - | / · • — + ZWS)
assert det.contains_profanity("на#хуя") is True
assert "нахуя" in det.detect("на#хуя")

# 2. Сепаратор * — каноническая форма "хй" в словаре
assert det.contains_profanity("х*й") is True
assert "хй" in det.detect("х*й")

# 3. Leet 0→о
assert det.contains_profanity("0хуеть") is True
assert "охуеть" in det.detect("0хуеть")   # нормализация 0→о

# 4. Leet бл@ть (@→а, форма "блать" — в словаре)
assert det.contains_profanity("бл@ть") is True

# 5. Leet + транслит: p1zda (1→i/l нормализация; ловится contains, каноническая форма — pizda)
assert det.contains_profanity("p1zda") is True
# detect возвращает канонические формы collapsed/stripped, для p1zda — [] (вариант 1→i),
# но pizda без leet — ["pizda"]:
assert "pizda" in det.detect("pizda")

# бонус — смешанные варианты
assert det.contains_profanity("п#здец") is True
assert det.contains_profanity("х у й") is True      # пробел — сепаратор
assert det.contains_profanity("х-у-й") is True      # дефис — сепаратор
assert det.contains_profanity("б.л.я") is True      # точки — сепараторы
assert det.contains_profanity("п..здец") is True    # + делеция буквы "и"
```

### 3.2 Полная таблица RU-маскировок

```python
from detected_profanity import contains_profanity

# все True
tests_ru = [
    ("на#хуя",      "сепаратор #"),
    ("х*й",         "сепаратор *"),
    ("0хуеть",      "leet 0→о"),
    ("бл@ть",       "leet @→а"),
    ("п..здец",     "сепараторы .. + делеция"),
    ("х у й",       "пробелы"),
    ("б.л.я",       "точки"),
    ("бляяяя",      "повторы 3+→2  (бляяяя→бляя→бля)"),
    ("пздец",       "делеция 1 буквы"),
    ("х-у-й",       "дефисы"),
    ("блaть",       "homoglyph a→а (лат a)"),
    ("ХУЙ",         "регистр"),
    ("п#и#з#д#е#ц", "множественные сепараторы"),
    ("хуууй",       "дубль буквы"),
]
for text, comment in tests_ru:
    assert contains_profanity(text), f"не сработал: {text} ({comment})"
```

### 3.3 Маскировки EN

```python
from detected_profanity import contains_profanity

assert contains_profanity("f*ck") is True       # делеция u
assert contains_profanity("sh*t") is True       # делеция i
assert contains_profanity("a$$hole") is True    # $→s
assert contains_profanity("b!tch") is True      # !→i
assert contains_profanity("f u c k") is True    # пробелы
assert contains_profanity("b.i.t.c.h") is True  # точки
assert contains_profanity("fuuuuuck") is True   # повторы 3+→2
assert contains_profanity("5hit") is True       # 5→s
assert contains_profanity("f@ck") is True       # @→a (через stripped)
```

### 3.4 Что происходит под капотом

```
raw text
  → NFKC (fullwidth → ascii, лигатуры)
  → lower + ё→е + снятие диакритики
  → SKELETON_MAP (0→о, @→а, a→а, e→е, o→о, p→р …)
  → collapse_repeats  (.)\1{2,} → \1\1   "бляяяя"→"бляя"
  → stripped (удаление 40+ SEPARATORS + cmap)
  → Aho-Corasick O(n+z) по collapsed + по stripped
  → word-expand + allowlist фильтр
```

---

## 4. Транслит

Детектор знает 100+ транслит-форм. По умолчанию транслит включён для `ru`/`all`.

```python
from detected_profanity import ProfanityDetector, contains_profanity

# функциональный API (all) — транслит уже включён
contains_profanity("pizdec kak holodno")   # True
contains_profanity("hui")                  # True
contains_profanity("ebat ti pidor")        # True

# явно через класс
det = ProfanityDetector()                  # all
det.detect("pizdec kak holodno")           # ["pizdec"]
det.detect("hui pizda blyad")              # ["hui", "pizda", "blyad"]

# только транслит
det_tr = ProfanityDetector(lang="translit")
det_tr.contains_profanity("hui")           # True
det_tr.contains_profanity("хуй")           # False
det_tr.contains_profanity("fuck")          # False
det_tr.detect("ebat ti pidor")             # ["ebat", "pidor"]

# RU без транслита
det_ru_no_tr = ProfanityDetector(lang="ru", include_translit=False)
det_ru_no_tr.contains_profanity("pizdec")  # False
det_ru_no_tr.contains_profanity("пиздец")  # True
```

Таблица соответствий:

| Ввод | Матчится как | Кириллица |
|------|-------------|-----------|
| `pizdec` | `pizdec` | `пиздец` |
| `hui` / `huy` / `khuy` | `hui` | `хуй` |
| `ebat` / `yebat` | `ebat` | `ебать` |
| `blyad` / `blya` | `blyad` | `блядь` |
| `pidor` / `pidaras` | `pidor` | `пидор` |
| `suka` | `suka` | `сука` |

---

## 5. Allowlist — защита от ложных срабатываний

Подстроки мата встречаются в нормальных словах. Детектор отбрасывает их **до** возврата результата.

```python
from detected_profanity import contains_profanity, detect

# RU — не триггерят
contains_profanity("мандарин")        # False  (содержит "манда")
contains_profanity("мандариновый")    # False  (префикс len≥4)
contains_profanity("мандат")          # False
contains_profanity("команда")         # False
contains_profanity("художник")        # False  (содержит "ху")
contains_profanity("художественный")  # False
contains_profanity("бляшка")          # False  (содержит "бля")
contains_profanity("блок")            # False
contains_profanity("облако")          # False
contains_profanity("шаблон")          # False

# EN — не триггерят
contains_profanity("assassin")        # False  (содержит "ass")
contains_profanity("assistant")       # False
contains_profanity("classic")         # False  (содержит "ass")
contains_profanity("pass")            # False
contains_profanity("cocktail")        # False  (содержит "cock")
contains_profanity("shiitake")        # False  (содержит "shit")
contains_profanity("fagot")           # False  (муз. инструмент)

# а это — триггерит (нет в allowlist)
contains_profanity("манда")           # True
contains_profanity("cock")            # True
contains_profanity("asshole")         # True

# смешанный текст: allowlist + мат
text = "мандарин и хуй"
contains_profanity(text)              # True
detect(text)                          # ["хуй"]  — мандарин отфильтрован
```

Полный список — `detected_profanity/lexicon.py:ALLOWLIST` (RU: мандарин/мандат/команда/художник/бляшка/блок/облако/шаблон…, EN: assassin/assistant/classic/cocktail/shiitake/fagot…).
Проверка — `is_allowed(token)`: `lower + ё→е + strip пунктуации`, точное совпадение **или** префикс `len≥4`.

```python
from detected_profanity.lexicon import is_allowed, ALLOWLIST

is_allowed("мандарин")      # True
is_allowed("мандариновый")  # True  (префикс)
is_allowed("манда")         # False
is_allowed("ASSASSIN")      # True  (case-insensitive)
```

---

## 6. Фильтр по языку (lang)

```python
from detected_profanity import ProfanityDetector

# --- ru — только русский + транслит (по умолчанию) ---
det_ru = ProfanityDetector(lang="ru")
det_ru.contains_profanity("хуй")    # True
det_ru.contains_profanity("fuck")   # False
det_ru.detect("блядь и shit")       # ["блядь"]
det_ru.censor("fuck")               # "fuck" (не цензурит)

# --- en — только английский ---
det_en = ProfanityDetector(lang="en")
det_en.contains_profanity("fuck")   # True
det_en.contains_profanity("хуй")    # False
det_en.contains_profanity("hui")    # False  (транслит не входит в en)

# --- translit — только транслит ---
det_tr = ProfanityDetector(lang="translit")
det_tr.contains_profanity("pizdec") # True
det_tr.contains_profanity("пиздец") # False

# --- all / None — всё сразу (дефолт) ---
det_all = ProfanityDetector(lang="all")
det_all.contains_profanity("хуй")   # True
det_all.contains_profanity("fuck")  # True
det_all.contains_profanity("pizdec")# True

# --- несколько языков списком ---
det = ProfanityDetector(languages=["ru", "en"])
det.contains_profanity("хуй")       # True
det.contains_profanity("fuck")      # True

# --- отключить транслит / нормализацию ---
det_no_tr = ProfanityDetector(lang="ru", include_translit=False)
det_no_tr.contains_profanity("pizdec")  # False

det_raw = ProfanityDetector(use_normalization=False)
det_raw.contains_profanity("бл@ть")     # False (без leet-маппинга)
det_raw.contains_profanity("блядь")     # True  (прямое совпадение)

# синонимы lang: "all" == None == "" == "*"
ProfanityDetector(lang=None).contains_profanity("хуй")  # True
ProfanityDetector(lang="*").contains_profanity("fuck")  # True
```

---

## 7. Цензурирование (censor)

Заменяет каждый символ мата на `repl` (по умолчанию `"*"`), сохраняя длину слова.

```python
from detected_profanity import censor
from detected_profanity import ProfanityDetector

censor("ну ты мудак")              # "ну ты *****"
censor("пошёл нахуй", repl="#")    # "пошёл #####"
censor("хуй")                      # "***"  (len сохранён)
censor("fuck")                     # "****"
censor("хуй пиздец")               # "*** ******"
censor("pizdec")                   # "******"

# кастомный repl любой длины
censor("хуй", repl="[censored]")   # "[ce"  (обрезается до длины слова)
censor("хуй", repl="#")            # "###"

# allowlist не цензурируется
censor("мандарин")                 # "мандарин"
censor("assassin")                 # "assassin"
censor("мандарин и хуй")           # "мандарин и ***"

# чисто — возвращается как есть
censor("привет мир")               # "привет мир"
censor("")                         # ""

# через класс + фильтр по языку
det_ru = ProfanityDetector(lang="ru")
det_ru.censor("fuck")              # "fuck" (en не цензурит в ru-режиме)
det_ru.censor("хуй")               # "***"

det_en = ProfanityDetector(lang="en")
det_en.censor("хуй")               # "хуй"
det_en.censor("fuck")              # "****"
```

> Примечание: `censor` работает на нормализованных координатах (`collapsed`/`stripped`), затем мапит интервалы обратно на исходный текст. Длина замены = длина исходного слова-носителя.

---

## 8. Нормализация (normalize_text)

Низкоуровневая функция: `NFKC + lower + ё→е + SKELETON_MAP`.

```python
from detected_profanity import normalize_text
from detected_profanity.normalizer import (
    LEET_MAP, HOMOGLYPH_MAP, SKELETON_MAP, SEPARATORS,
    collapse_repeats, normalize_char,
)

# леет
normalize_text("0хуеть")   # "охуеть"  (0→о)
normalize_text("бл@ть")    # "блать"   (@→а)
normalize_text("пи3дец")   # "пиздец"  (3→з)
normalize_text("$")        # "с"       ($→с)

# гомоглифы (лат → кир)
normalize_text("a")        # "а"
normalize_text("e")        # "е"
normalize_text("o")        # "о"
normalize_text("p")        # "р"
normalize_text("x")        # "х"
normalize_text("хyй")      # "хуй"     (лат y → кир у)

# регистр + ё
normalize_text("ХУЙ")      # "хуй"
normalize_text("Ёлка")     # "елка"
normalize_text("мёд")      # "мед"

# NFKC (fullwidth, лигатуры)
normalize_text("ｈｕｉ")     # "нuи"  (fullwidth → ascii → homoglyph)
normalize_text("ﬁ")        # "fi"

# повторы — ОТДЕЛЬНО (normalize_text не схлопывает, это делает collapse_repeats)
normalize_text("бляяяя")            # "бляяяя"
collapse_repeats("бляяяя")          # "бляя"   (3+ → 2)
collapse_repeats("fuuuuuck")        # "fuuck"
collapse_repeats(normalize_text("бляяяя"))  # "бляя"

# посимвольно
normalize_char("ё")        # "е"
normalize_char("aB")       # "аb"

# карты
LEET_MAP        # {"0":"о", "3":"з", "4":"а", "@":"а", "$":"с", "€":"е", ...}
HOMOGLYPH_MAP   # {"a":"а", "e":"е", "o":"о", "p":"р", "c":"с", "x":"х", ...}
SKELETON_MAP    # LEET_MAP ∪ HOMOGLYPH_MAP
SEPARATORS      # 40+ символов: " #*.-_|/·•—()[]{}<>\"'`~^+=&%  + ZWS ​‌…"
len(SEPARATORS) # ≥40
```

Используй `normalize_text` для дебага / логирования — чтобы увидеть, во что превращается маскировка до поиска.

---

## 9. Кастомный словарь

Библиотека не принимает `custom_words` в конструкторе — словари зашиты в `lexicon.py` и компилируются в `Aho-Corasick` при первом вызове. Три проверенных способа кастомизации:

### 9.1 Фильтрация результата (самый простой)

```python
from detected_profanity import ProfanityDetector

det = ProfanityDetector()

# добавить свои стоп-слова — пост-фильтр
MY_EXTRA_BAD = {"дебил", "тупой", "кринж"}

def contains_profanity_extended(text: str) -> bool:
    if det.contains_profanity(text):
        return True
    low = text.lower()
    return any(w in low for w in MY_EXTRA_BAD)

# убрать ложные срабатывания — пост-фильтр
MY_ALLOW = {"саламандарин"}  # выдуманное слово с подстрокой "манда"

def detect_filtered(text: str) -> list[str]:
    hits = det.detect(text)
    return [h for h in hits if h not in MY_ALLOW]
```

### 9.2 Собственный Aho-Corasick (полный контроль)

```python
from detected_profanity.matcher import AhoCorasick, find_matches
from detected_profanity.normalizer import normalize_text, collapse_repeats

# свой словарь — любые слова
my_words = ["дебил", "кринж", "fuck", "хуй"]
# нормализуй так же, как детектор
normed = [collapse_repeats(normalize_text(w)) for w in my_words]

ac = AhoCorasick(normed)

# поиск O(n+z)
text = "ты дебил и fuck"
collapsed = collapse_repeats(normalize_text(text))
matches = ac.search(collapsed)       # [(4, "дебил"), (12, "fuck")]
hits = ac.find_matches(collapsed)    # [Match(pattern="дебил", start=4, end=8), ...]
print([m.pattern for m in hits])     # ["дебил", "fuck"]

# потоковый поиск для больших текстов
for end_idx, pat in ac.search_iter(collapsed):
    print(f"найдено {pat!r} на позиции {end_idx}")
```

### 9.3 Форк lexicon.py (для продакшена)

```python
# 1. Скопируй detected_profanity/lexicon.py
# 2. Добавь слова в RU_FORMS / EN_FORMS / TRANSLIT_FORMS
#    или в ALLOWLIST, затем:
# 3. Пересобери автомат — он ленивый, пересоздастся при первом вызове.

# Пример: добавление в рантайме (monkey-patch, без форка)
import detected_profanity.lexicon as lex
import detected_profanity.detector as det_mod

lex.RU_FORMS.append("дебилизм")
# сбросить кешированные автоматы
det_mod._RU_AC = None
det_mod._EN_AC = None
det_mod._TR_AC = None

# теперь детектор увидит новое слово
from detected_profanity import ProfanityDetector
assert ProfanityDetector(lang="ru").contains_profanity("дебилизм") is True
```

> Для продления allowlist аналогично: `lex.ALLOWLIST.add("новое_слово")` + сброс `det_mod._*_AC`.

---

## 10. Производительность

### 10.1 Сложность

| Операция | Сложность | Примечание |
|---|---:|---|
| `AhoCorasick.build` | `O(N)`, `N = Σ len(pattern)` | BFS по трие, один раз (лениво) |
| `AhoCorasick.search` | `O(n+z)` | `n=len(text)`, `z=совпадений` |
| `normalize_text` | `O(n)` | NFKC + lower + map |
| `contains_profanity` | `O(n+z)` | нормализация + 2× Aho (collapsed+stripped) |

Линейный скан против `O(n·m)` наивного перебора — критично на длинных текстах и больших словарях.

### 10.2 Бенчмарк (60 фраз: 30 RU + 30 EN)

Запуск: `python benchmarks/benchmark.py --json benchmarks/results.json --png benchmarks/benchmark.png`

| Library | Acc | Prec | Rec | F1 | ms/текст | TP | TN | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **detected-profanity** | **100%** | 100% | **100%** | **100%** | **0.53** | 40 | 20 | 0 | 0 |
| better-profanity | 60% | 100% | 40% | 57% | 2.26 | 16 | 20 | 0 | 24 |
| profanity-check | 58% | 100% | 38% | 55% | 3.33 | 15 | 20 | 0 | 25 |

- **100%** на всех срезах: RU, EN, Clean, Open, Masked.
- В **4–6× быстрее** альтернатив.

### 10.3 Советы по скорости

```python
import timeit
from detected_profanity import ProfanityDetector, contains_profanity

# 1. Переиспользуй инстанс — автомат строится ОДИН раз (лениво)
det = ProfanityDetector()  # ~1-2 мс на первую прогревку (build трие)

# прогрев
det.contains_profanity("прогрев")

# дальше — микросекунды
t = timeit.timeit(lambda: det.contains_profanity("охуеть это пиздец"), number=10_000)
print(f"{t/10_000*1_000:.3f} ms/вызов")  # ~0.05-0.2 ms

# 2. Функциональный API — тот же синглтон, тоже быстро
timeit.timeit(lambda: contains_profanity("привет"), number=10_000)

# 3. Батч — один детектор на весь поток
texts = ["привет", "охуеть", "fuck", "мандарин", "на#хуя"] * 1000
hits = [t for t in texts if det.contains_profanity(t)]  # O(total_chars)

# 4. Если нужен только один язык — укажи lang (меньше автоматов)
det_ru = ProfanityDetector(lang="ru")  # не строит EN-автомат
det_en = ProfanityDetector(lang="en")  # не строит RU-автомат

# 5. Для очень длинных текстов — search_iter (стриминг)
from detected_profanity.matcher import AhoCorasick
ac = AhoCorasick(["хуй", "пиздец"])
for end_idx, pat in ac.search_iter("очень длинный текст " * 10000):
    pass  # обработка на лету, без списка

# 6. Отключи нормализацию только если уверен (быстрее, но пропустит маскировки)
det_raw = ProfanityDetector(use_normalization=False)
```

---

## 11. CLI

```bash
# one-shot
python -m detected_profanity "охуеть, это пиздец"
# profanity: YES  matches=['охуеть', 'пиздец']

python -m detected_profanity --censor "ну ты мудак"
# ну ты *****

# фильтр по языку
python -m detected_profanity --lang ru "fuck"   # profanity: NO
python -m detected_profanity --lang en "fuck"   # profanity: YES

# JSON + stdin (для пайпов и CI)
echo "pizdec" | python -m detected_profanity --json
# {"text": "pizdec\n", "has_profanity": true, "matches": ["pizdec"]}

python -m detected_profanity --censor --repl "#" --json --lang all "fuck you, блядь"

# опции
python -m detected_profanity --help
# usage: detected_profanity [-h] [--lang {ru,en,translit,all}] [--censor] [--repl REPL]
#                           [--json] [--no-normalize] [--no-translit] [-v] [text ...]
#   --lang        язык лексикона (default: all)
#   --censor      вывести цензурированную версию
#   --repl REPL   символ-заменитель (default: "*")
#   --json        JSON-вывод
#   --no-normalize  отключить NFKC/leet/homoglyph
#   --no-translit   не включать транслит
# exit-коды: 0=чисто, 1=найден мат, 2=ошибка ввода

# REPL (интерактив)
python cli.py
# › привет, как дела?  → not detected
# › на#хуя ты это сделал → detected
# › /exit — выход

# алиас после pip install
detected-profanity "текст"
```

---

## 12. API Reference (RU)

### `ProfanityDetector`

```python
ProfanityDetector(
    lang: str | None = None,              # "ru" | "en" | "translit" | "all" | None
    languages: str | list[str] | None = None,  # альтернатива: ["ru", "en"]
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

Бросает `TypeError` если `text` не `str`.

### Функциональный API (синглтон `all`)

| Символ | Тип | Описание |
|---|---:|---|
| `contains_profanity(text)` | `-> bool` | Шорткат через дефолтный детектор |
| `detect(text)` | `-> list[str]` | Шорткат |
| `censor(text, repl="*")` | `-> str` | Шорткат |
| `normalize_text(text)` | `-> str` | `NFKC + NFKD strip + lower + ё→е + SKELETON_MAP` |
| `collapse_repeats(text)` | `-> str` | `aaa→aa` (3+ → 2) |
| `__version__` | `str` | Версия пакета |

### `normalizer`

| Константа | Содержимое |
|---|---|
| `LEET_MAP` | `0→о`, `3→з`, `4→а`, `5→s`, `@→а`, `$→с`, `€→е` |
| `HOMOGLYPH_MAP` | `a→а`, `e→е`, `o→о`, `p→р`, `c→с`, `x→х`, `y→у`, `H→Н` … |
| `SKELETON_MAP` | `LEET_MAP ∪ HOMOGLYPH_MAP` |
| `SEPARATORS` | `set` 40+ сепараторов (включая ZWS `​`, `‌`, `‍`, `﻿`) |

### `matcher.AhoCorasick`

```python
from detected_profanity.matcher import AhoCorasick, Match, find_matches

ac = AhoCorasick(["хуй", "пиздец", "fuck"])
ac.search("охуеть, fuck")          # [(5, "хуй"), (12, "fuck")]
ac.search_iter("длинный текст")    # генератор
ac.find_matches("охуеть")          # [Match(pattern="хуй", start=1, end=3)]
find_matches("text", ["bad", "word"])
len(ac)                            # число паттернов
"хуй" in ac                        # True
```

### `lexicon`

| Символ | Описание |
|---|---|
| `ALL_RU_ROOTS` (40+) | Базовые корни |
| `RU_FORMS` (150+) | Кириллические формы |
| `EN_FORMS` (100+) | Английские формы |
| `TRANSLIT_FORMS` (100+) | Транслит-формы |
| `ALLOWLIST` | Белый список `set[str]` |
| `is_allowed(token)` | Проверка allowlist |
| `get_patterns(lang, include_translit)` | Скомпилированные `re` паттерны |

---

## 13. Частые ошибки (RU)

```python
# ❌ Создавать детектор в цикле
for text in texts:
    ProfanityDetector().contains_profanity(text)  # медленно: build каждый раз
# ✅ Один инстанс на весь батч
det = ProfanityDetector()
for text in texts:
    det.contains_profanity(text)

# ❌ Ждать исходные подстроки от detect()
detect("0хуеть")  # ["охуеть"], а не ["0хуеть"] — нормализованная форма
# ✅ Для исходных координат используй matcher напрямую или censor

# ❌ Передавать не-str
contains_profanity(123)  # TypeError
# ✅ Приводи к str заранее
contains_profanity(str(value))

# ❌ Отключать нормализацию "для скорости" без нужды
ProfanityDetector(use_normalization=False).contains_profanity("бл@ть")  # False!
# ✅ Оставляй use_normalization=True (дефолт) — разница в скорости <5%
```

---

# 🇬🇧 English

## Contents (EN)

1. [Installation](#1-installation-en)
2. [Basic Detection](#2-basic-detection-en)
3. [Obfuscation / Masking](#3-obfuscation--masking-en)
4. [Translit](#4-translit-en)
5. [Allowlist](#5-allowlist-en)
6. [Language Filter](#6-language-filter-en)
7. [Censoring](#7-censoring-en)
8. [Normalization](#8-normalization-en)
9. [Custom Dictionary](#9-custom-dictionary-en)
10. [Performance](#10-performance-en)
11. [CLI](#11-cli-en)
12. [API Reference](#12-api-reference-en)
13. [Common Pitfalls](#13-common-pitfalls-en)

---

## 1. Installation (EN)

Requirements: **Python 3.8+**, zero dependencies.

```bash
pip install detected-profanity
```

From source:

```bash
git clone https://github.com/detected-profanity/detected-profanity
cd detected-profanity
pip install -e .
pip install -e ".[dev]"   # for tests/linters
```

Smoke test:

```bash
python -c "from detected_profanity import contains_profanity; print(contains_profanity('hello'))"
# False
python -m detected_profanity "what the fuck"
# profanity: YES  matches=['fuck']
```

---

## 2. Basic Detection (EN)

Two APIs — functional (singleton `lang=all`) and class `ProfanityDetector`.

```python
from detected_profanity import contains_profanity, detect, censor
from detected_profanity import ProfanityDetector

# --- functional API (default all: ru + en + translit) ---
contains_profanity("Hello, how are you?")  # False
contains_profanity("what the fuck")        # True
detect("what the fuck")                    # ["fuck"]
censor("what the fuck")                    # "what the ****"

# --- class API — same result, configurable ---
det = ProfanityDetector()                  # lang=None == "all"
det.contains_profanity("fuck")             # True
det.detect("fuck shit")                    # ["fuck", "shit"]
det.censor("fuck shit")                    # "**** ****"

# empty / whitespace — always clean
contains_profanity("")                     # False
contains_profanity("   ")                  # False
detect("")                                # []
```

Contract:

- `text` must be `str`, otherwise `TypeError`.
- `contains_profanity` → `bool`, `detect` → `list[str]`, `censor` → `str`.
- `detect` returns **canonical forms** (normalized, deduped), not raw substrings.

---

## 3. Obfuscation / Masking (EN)

Every example below returns `True`. Five obfuscation classes are handled at once.

### 3.1 Required examples — copy & run

```python
from detected_profanity import ProfanityDetector

det = ProfanityDetector()

# 1. Separator # — stripped (40+ separators: # * . _ - | / · • — + ZWS)
assert det.contains_profanity("на#хуя") is True   # RU: на#хуя → нахуя

# 2. Separator * — canonical form "хй"
assert det.contains_profanity("х*й") is True

# 3. Leet 0→о
assert det.contains_profanity("0хуеть") is True

# 4. Leet бл@ть (@→а, form "блать" in lexicon)
assert det.contains_profanity("бл@ть") is True

# 5. Leet + translit: p1zda (1→i/l normalization; caught by contains, canonical pizda — see pizda)
assert det.contains_profanity("p1zda") is True  # contains True; detect("pizda") → ["pizda"]

# bonus
assert det.contains_profanity("f*ck") is True
assert det.contains_profanity("a$$hole") is True
assert det.contains_profanity("b!tch") is True
```

### 3.2 RU masking table

```python
from detected_profanity import contains_profanity

tests_ru = [
    ("на#хуя",      "separator #"),
    ("х*й",         "separator *"),
    ("0хуеть",      "leet 0→о"),
    ("бл@ть",       "leet @→а"),
    ("п..здец",     "separators .. + deletion"),
    ("х у й",       "spaces"),
    ("б.л.я",       "dots"),
    ("бляяяя",      "repeats 3+→2"),
    ("пздец",       "single deletion"),
    ("х-у-й",       "dashes"),
    ("блaть",       "homoglyph a→а"),
    ("ХУЙ",         "case"),
]
for text, comment in tests_ru:
    assert contains_profanity(text), f"failed: {text} ({comment})"
```

### 3.3 EN masking

```python
from detected_profanity import contains_profanity

assert contains_profanity("f*ck") is True
assert contains_profanity("sh*t") is True
assert contains_profanity("a$$hole") is True
assert contains_profanity("b!tch") is True
assert contains_profanity("f u c k") is True
assert contains_profanity("b.i.t.c.h") is True
assert contains_profanity("fuuuuuck") is True
assert contains_profanity("5hit") is True
```

### 3.4 Pipeline

```
raw
 → NFKC (fullwidth → ascii)
 → lower + ё→е + diacritics strip
 → SKELETON_MAP (0→о, @→а, a→а …)
 → collapse_repeats  (.)\1{2,} → \1\1
 → stripped (remove 40+ SEPARATORS)
 → Aho-Corasick O(n+z) on collapsed + stripped
 → word-expand + allowlist filter
```

---

## 4. Translit (EN)

100+ translit forms. Enabled by default for `ru`/`all`.

```python
from detected_profanity import ProfanityDetector, contains_profanity

contains_profanity("pizdec kak holodno")   # True
contains_profanity("hui")                  # True

det = ProfanityDetector()
det.detect("hui pizda blyad")              # ["hui", "pizda", "blyad"]

det_tr = ProfanityDetector(lang="translit")
det_tr.contains_profanity("hui")           # True
det_tr.contains_profanity("хуй")           # False

det_no_tr = ProfanityDetector(lang="ru", include_translit=False)
det_no_tr.contains_profanity("pizdec")     # False
```

| Input | Matches as | Cyrillic |
|-------|-----------|----------|
| `pizdec` | `pizdec` | `пиздец` |
| `hui` / `huy` / `khuy` | `hui` | `хуй` |
| `ebat` / `yebat` | `ebat` | `ебать` |
| `blyad` / `blya` | `blyad` | `блядь` |
| `pidor` / `pidaras` | `pidor` | `пидор` |

---

## 5. Allowlist (EN)

Profanity substrings occur in normal words. The detector filters them before returning.

```python
from detected_profanity import contains_profanity, detect

# not flagged
contains_profanity("assassin")        # False (contains "ass")
contains_profanity("assistant")       # False
contains_profanity("classic")         # False
contains_profanity("cocktail")        # False (contains "cock")
contains_profanity("shiitake")        # False (contains "shit")
contains_profanity("мандарин")        # False
contains_profanity("художник")        # False

# flagged
contains_profanity("asshole")         # True
contains_profanity("cock")            # True

# mixed
contains_profanity("assassin and fuck")  # True
detect("assassin and fuck")              # ["fuck"]
```

Full list — `detected_profanity/lexicon.py:ALLOWLIST`.
Check — `is_allowed(token)`: `lower + ё→е + strip`, exact match **or** prefix `len≥4`.

```python
from detected_profanity.lexicon import is_allowed

is_allowed("assassin")      # True
is_allowed("assassination") # True  (prefix)
is_allowed("cocktail")      # True
is_allowed("cock")          # False
```

---

## 6. Language Filter (EN)

```python
from detected_profanity import ProfanityDetector

det_ru = ProfanityDetector(lang="ru")
det_ru.contains_profanity("хуй")    # True
det_ru.contains_profanity("fuck")   # False

det_en = ProfanityDetector(lang="en")
det_en.contains_profanity("fuck")   # True
det_en.contains_profanity("хуй")    # False
det_en.contains_profanity("hui")    # False

det_tr = ProfanityDetector(lang="translit")
det_tr.contains_profanity("pizdec") # True
det_tr.contains_profanity("пиздец") # False

det_all = ProfanityDetector(lang="all")  # default
det_all.contains_profanity("хуй")   # True
det_all.contains_profanity("fuck")  # True

det = ProfanityDetector(languages=["ru", "en"])

det_no_tr = ProfanityDetector(lang="ru", include_translit=False)
det_no_tr.contains_profanity("pizdec")  # False

det_raw = ProfanityDetector(use_normalization=False)
det_raw.contains_profanity("бл@ть")     # False
```

Synonyms: `"all" == None == "" == "*"`.

---

## 7. Censoring (EN)

Replaces each profane character with `repl` (default `"*"`), preserving word length.

```python
from detected_profanity import censor
from detected_profanity import ProfanityDetector

censor("what the fuck")            # "what the ****"
censor("fuck", repl="#")           # "####"
censor("хуй")                      # "***"
censor("pizdec")                   # "******"
censor("fuck shit")                # "**** ****"

# any repl
censor("fuck", repl="[censored]")  # "[cen"

# allowlist untouched
censor("assassin")                 # "assassin"
censor("assassin and fuck")        # "assassin and ****"

# class + lang filter
ProfanityDetector(lang="ru").censor("fuck")  # "fuck"
ProfanityDetector(lang="en").censor("хуй")   # "хуй"
```

---

## 8. Normalization (EN)

Low-level: `NFKC + lower + ё→е + SKELETON_MAP`.

```python
from detected_profanity import normalize_text
from detected_profanity.normalizer import (
    LEET_MAP, HOMOGLYPH_MAP, SKELETON_MAP, SEPARATORS,
    collapse_repeats, normalize_char,
)

normalize_text("0хуеть")   # "охуеть"
normalize_text("бл@ть")    # "блать"
normalize_text("a")        # "а"
normalize_text("ХУЙ")      # "хуй"
normalize_text("Ёлка")     # "елка"
normalize_text("ｈｕｉ")     # normalized via NFKC + homoglyph

collapse_repeats("бляяяя")        # "бляя"
collapse_repeats("fuuuuuck")      # "fuuck"

LEET_MAP        # {"0":"о", "3":"з", "4":"а", "@":"а", "$":"с", ...}
HOMOGLYPH_MAP   # {"a":"а", "e":"е", "o":"о", "p":"р", ...}
SKELETON_MAP    # LEET ∪ HOMOGLYPH
len(SEPARATORS) # ≥40
```

Use `normalize_text` for debugging — see what a masked word becomes before matching.

---

## 9. Custom Dictionary (EN)

The library has no `custom_words` constructor arg — lexicons are in `lexicon.py` and compiled into `Aho-Corasick` lazily. Three ways to customize:

### 9.1 Post-filter (simplest)

```python
from detected_profanity import ProfanityDetector

det = ProfanityDetector()
MY_EXTRA_BAD = {"debil", "cringe"}

def contains_extended(text: str) -> bool:
    if det.contains_profanity(text):
        return True
    return any(w in text.lower() for w in MY_EXTRA_BAD)
```

### 9.2 Own Aho-Corasick (full control)

```python
from detected_profanity.matcher import AhoCorasick
from detected_profanity.normalizer import normalize_text, collapse_repeats

my_words = ["debil", "cringe", "fuck"]
normed = [collapse_repeats(normalize_text(w)) for w in my_words]
ac = AhoCorasick(normed)

collapsed = collapse_repeats(normalize_text("you debil"))
print(ac.search(collapsed))        # [(4, "debil")]
print(ac.find_matches(collapsed))  # [Match(pattern="debil", start=4, end=8)]

for end_idx, pat in ac.search_iter(collapsed):
    print(pat, end_idx)
```

### 9.3 Fork lexicon.py (production)

```python
import detected_profanity.lexicon as lex
import detected_profanity.detector as det_mod

lex.RU_FORMS.append("дебилизм")
det_mod._RU_AC = None  # reset cached automaton

from detected_profanity import ProfanityDetector
assert ProfanityDetector(lang="ru").contains_profanity("дебилизм")
```

Same for allowlist: `lex.ALLOWLIST.add("my_word")` + reset `det_mod._*_AC`.

---

## 10. Performance (EN)

### 10.1 Complexity

| Operation | Complexity |
|---|---:|
| `AhoCorasick.build` | `O(N)`, `N = Σ len(pattern)` — once, lazy |
| `AhoCorasick.search` | `O(n+z)` |
| `contains_profanity` | `O(n+z)` |

### 10.2 Benchmark (60 phrases: 30 RU + 30 EN)

Run: `python benchmarks/benchmark.py --json benchmarks/results.json`

| Library | Acc | F1 | ms/text |
|---|---:|---:|---:|
| **detected-profanity** | **100%** | **100%** | **0.53** |
| better-profanity | 60% | 57% | 2.26 |
| profanity-check | 58% | 55% | 3.33 |

### 10.3 Tips

```python
import timeit
from detected_profanity import ProfanityDetector, contains_profanity

det = ProfanityDetector()
det.contains_profanity("warmup")  # build trie once (~1-2 ms)

t = timeit.timeit(lambda: det.contains_profanity("охуеть это пиздец"), number=10_000)
print(f"{t/10_000*1_000:.3f} ms/call")  # ~0.05-0.2 ms

# batch — one detector for the whole stream
hits = [t for t in texts if det.contains_profanity(t)]

# lang filter avoids building unused automata
ProfanityDetector(lang="ru")  # no EN trie
ProfanityDetector(lang="en")  # no RU trie

# streaming for huge texts
from detected_profanity.matcher import AhoCorasick
ac = AhoCorasick(["fuck", "shit"])
for end_idx, pat in ac.search_iter(huge_text):
    handle(pat)

# don't disable normalization unless you must
ProfanityDetector(use_normalization=False)  # faster but misses @, 0, etc.
```

---

## 11. CLI (EN)

```bash
python -m detected_profanity "what the fuck"
# profanity: YES  matches=['fuck']

python -m detected_profanity --censor "you asshole"
# you *******

python -m detected_profanity --lang ru "fuck"   # profanity: NO
python -m detected_profanity --lang en "fuck"   # profanity: YES

echo "pizdec" | python -m detected_profanity --json
# {"text": "pizdec\n", "has_profanity": true, "matches": ["pizdec"]}

python -m detected_profanity --help
# --lang {ru,en,translit,all}  --censor  --repl REPL  --json
# --no-normalize  --no-translit  -v
# exit codes: 0=clean, 1=profanity, 2=error

python cli.py              # REPL
detected-profanity "text"  # alias after pip install
```

---

## 12. API Reference (EN)

### `ProfanityDetector`

```python
ProfanityDetector(
    lang: str | None = None,              # "ru" | "en" | "translit" | "all" | None
    languages: str | list[str] | None = None,  # alt: ["ru", "en"]
    *,
    include_translit: bool = True,
    use_normalization: bool = True,
)
```

| Method | Signature | Description |
|---|---|---|
| `contains_profanity` | `(text: str) -> bool` | Whether profanity present |
| `detect` | `(text: str) -> list[str]` | List of canonical forms |
| `censor` | `(text: str, repl="*") -> str` | Censored copy |

Throws `TypeError` if `text` is not `str`.

### Functional API (singleton `all`)

| Symbol | Type | Description |
|---|---:|---|
| `contains_profanity(text)` | `-> bool` | Shortcut via default detector |
| `detect(text)` | `-> list[str]` | Shortcut |
| `censor(text, repl="*")` | `-> str` | Shortcut |
| `normalize_text(text)` | `-> str` | `NFKC + lower + ё→е + SKELETON_MAP` |
| `collapse_repeats(text)` | `-> str` | `aaa→aa` (3+ → 2) |
| `__version__` | `str` | Package version |

### `matcher.AhoCorasick`

```python
from detected_profanity.matcher import AhoCorasick, Match, find_matches
ac = AhoCorasick(["хуй", "пиздец", "fuck"])
ac.search("text")       # list[(end_idx, pattern)]
ac.search_iter("text")  # generator
ac.find_matches("text") # list[Match]
```

---

## 13. Common Pitfalls (EN)

```python
# ❌ New detector per call
for text in texts:
    ProfanityDetector().contains_profanity(text)
# ✅ One instance
det = ProfanityDetector()
for text in texts:
    det.contains_profanity(text)

# ❌ Expect raw substrings from detect()
detect("0хуеть")  # ["охуеть"], not ["0хуеть"]
# ✅ Use matcher directly for raw offsets

# ❌ Non-str
contains_profanity(123)  # TypeError
# ✅ Cast first
contains_profanity(str(value))

# ❌ Disable normalization carelessly
ProfanityDetector(use_normalization=False).contains_profanity("бл@ть")  # False
# ✅ Keep default True — <5% slower, catches leet
```

---

<p align="center">
  <sub>MIT · Zero deps · Python 3.8+ · для модерации чатов, комментариев и UGC / for chat & UGC moderation</sub>
</p>
