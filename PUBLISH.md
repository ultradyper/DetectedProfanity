# PUBLISH — гайд по публикации `detected-profanity` на PyPI

Краткий чеклист: подготовка → сборка → проверка → заливка → установка → использование → интеграция → FAQ.

---

## 1. Подготовка

### 1.1 Bump version

Версия в **двух местах** — должны совпадать:

```bash
# pyproject.toml  [project] version = "0.1.0"
# detected_profanity/__init__.py  __version__ = "1.0.0"
```

Синхронизируй перед релизом (SemVer `MAJOR.MINOR.PATCH`):

```bash
# пример bump 0.1.0 → 0.2.0
sed -i 's/version = ".*"/version = "0.2.0"/' pyproject.toml
sed -i 's/__version__.*=.*/__version__: Final[str] = "0.2.0"/' detected_profanity/__init__.py
# или вручную

# проверка
grep -E 'version|__version__' pyproject.toml detected_profanity/__init__.py
python -c "import detected_profanity; print(detected_profanity.__version__)"
```

### 1.2 Changelog и проверки

```bash
# обнови CHANGELOG.md / секцию Unreleased в README (что изменилось, breaking changes)

# прогон качества — всё должно быть зелёным
pytest -q
python -m ruff check .
python -m mypy detected_profanity --strict

# (опц.) бенчмарк
python benchmarks/benchmark.py --no-plot
```

### 1.3 Git tag

```bash
git status                          # working tree clean
git add pyproject.toml detected_profanity/__init__.py CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"
git tag -a v0.2.0 -m "v0.2.0"
git push origin main
git push origin v0.2.0
```

> Тег `vX.Y.Z` — триггер для CI/релизов на GitHub. Если ошибся: `git tag -d v0.2.0 && git push origin :refs/tags/v0.2.0`.

---

## 2. Сборка

```bash
# зависимости сборки (один раз)
pip install --upgrade build twine

# очистка старых артефактов
rm -rf dist/ build/ *.egg-info detected_profanity.egg-info

# сборка (hatchling → wheel + sdist)
python -m build

# проверка результата
ls -lh dist/
# dist/detected_profanity-0.2.0-py3-none-any.whl
# dist/detected-profanity-0.2.0.tar.gz

tar tzf dist/detected-profanity-0.2.0.tar.gz | head -n 20
```

`pyproject.toml`: `build-system = hatchling`, `requires-python >=3.8`, `dependencies = []`.

---

## 3. Проверка

### 3.1 twine check

```bash
twine check dist/*
# PASSED — long_description, metadata OK
```

Если `FAILED` — проверь `readme = "README.md"` и `license` в `pyproject.toml`.

### 3.2 TestPyPI

```bash
# загрузка в тестовый индекс
twine upload --repository testpypi dist/*

# установка оттуда в чистом окружении
pip install --index-url https://test.pypi.org/simple/ --no-deps --extra-index-url https://pypi.org/simple/ detected-profanity

# smoke-test
python -c "from detected_profanity import contains_profanity; print(contains_profanity('хуй'))"  # True
python -m detected_profanity "охуеть, это пиздец"        # profanity: YES
python -m detected_profanity --version
```

Настройка `~/.pypirc`:

```ini
[distutils]
index-servers = pypi testpypi

[pypi]
username = __token__
password = pypi-...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-...
```

> Токены: https://pypi.org/manage/account/token/ и https://test.pypi.org/manage/account/token/ (scope = конкретный проект).

---

## 4. Заливка (PyPI)

```bash
# финальная проверка ещё раз
twine check dist/*

# загрузка в прод PyPI
twine upload dist/*

# или явно
# twine upload --repository pypi dist/*

# проверка
pip install --upgrade detected-profanity
pip show detected-profanity
python -m detected_profanity --version
open https://pypi.org/project/detected-profanity/
```

Если нужно перезалить ту же версию — нельзя (PyPI immutable). Делай `0.2.0.post1` / `0.2.1`.

Откат: `yank` релиза на странице PyPI → Manage → Releases → Yank (не удаляет, скрывает от `pip`).

---

## 5. Установка

### Из PyPI (пользователь)

```bash
pip install detected-profanity
pip install --upgrade detected-profanity

# проверка
python -c "import detected_profanity; print(detected_profanity.__version__)"
detected-profanity --help          # console_scripts из pyproject.toml
python -m detected_profanity --help
```

### Из исходников (разработка)

```bash
git clone https://github.com/detected-profanity/detected-profanity
cd detected-profanity

pip install -e .                   # editable, без dev-зависимостей
pip install -e ".[dev]"            # + ruff/mypy/pytest/build/twine (если extras настроены)

# альтернатива без editable
pip install .
```

---

## 6. Использование

### 6.1 Python API

```python
from detected_profanity import ProfanityDetector, contains_profanity, detect, censor, normalize_text

# функциональный API (синглтон lang=all)
contains_profanity("Привет, как дела?")   # False
contains_profanity("охуеть, это пиздец")  # True
contains_profanity("бл@ть")               # True  (leet @→а раскрывается)
detect("охуеть, это пиздец")              # ["охуеть", "пиздец"]
censor("ну ты мудак")                     # "ну ты *****"
censor("пошёл нахуй", repl="#")           # "пошёл #####"
normalize_text("бл@ть, 0хуеть")           # "блать, охуеть"

# ProfanityDetector — фильтр по языку
det_ru = ProfanityDetector(lang="ru")
det_ru.contains_profanity("hello fuck")   # False
det_ru.detect("блядь и shit")             # ["блядь"]

det_en = ProfanityDetector(lang="en")
det_en.contains_profanity("fuck")         # True
det_en.contains_profanity("хуй")          # False

det = ProfanityDetector(languages=["ru", "en"])
det.contains_profanity("хуй")             # True
det.contains_profanity("fuck")            # True

# транслит
ProfanityDetector().contains_profanity("pizdec kak holodno")  # True
ProfanityDetector(lang="translit").detect("ebat ti pidor")    # ["ebat", "pidor"]

# опции
ProfanityDetector(use_normalization=False).contains_profanity("бл@ть")              # False
ProfanityDetector(lang="ru", include_translit=False).contains_profanity("pizdec")  # False

# allowlist — ложных срабатываний нет
contains_profanity("мандарин и assassin")  # False
contains_profanity("художник")             # False
```

Исключения: `TypeError` если `text` не `str`. Пустая строка → `False` / `[]`.

### 6.2 CLI

```bash
# one-shot через модуль
python -m detected_profanity "охуеть, это пиздец"
# profanity: YES  matches=['охуеть', 'пиздец']

python -m detected_profanity --censor "ну ты мудак"
# ну ты *****

python -m detected_profanity --lang ru "fuck"   # profanity: NO
python -m detected_profanity --lang en "fuck"   # profanity: YES

# JSON + stdin (CI/пайпы)
echo "pizdec" | python -m detected_profanity --json
# {"text": "pizdec\n", "has_profanity": true, "matches": ["pizdec"]}

python -m detected_profanity --censor --repl "#" --json --lang all "fuck you, блядь"
echo "hello" | python -m detected_profanity --censor --json

# флаги: --lang {ru,en,translit,all}  --censor  --repl "*"  --json  --no-normalize  --no-translit  -v/--version
# exit-коды: 0=чисто, 1=найден мат, 2=ошибка ввода

# console_scripts (после pip install)
detected-profanity "текст" --json --censor

# REPL (интерактивный)
python cli.py
# › привет          → not detected
# › на#хуя          → detected
# › /exit — выход

python cli.py "бля, это пиздец"   # one-shot → detected / not detected
echo "хуй" | python cli.py        # stdin
```

---

## 7. Интеграция

### 7.1 FastAPI middleware

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from detected_profanity import ProfanityDetector

app = FastAPI()
det = ProfanityDetector(lang="all")  # или ru/en/translit

@app.middleware("http")
async def profanity_middleware(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            body = await request.body()
            if body and det.contains_profanity(body.decode(errors="ignore")):
                return JSONResponse({"detail": "profanity detected"}, status_code=400)
        except Exception:
            pass
    return await call_next(request)

# точечная проверка поля
@app.post("/comments")
async def create_comment(text: str):
    if det.contains_profanity(text):
        raise HTTPException(400, f"profanity: {det.detect(text)}")
    # ... сохранить
    return {"censored": det.censor(text)}

# цензура ответа
@app.post("/censor")
async def censor_text(text: str, repl: str = "*"):
    return {"censored": det.censor(text, repl=repl)}
```

Зависимости: `pip install fastapi uvicorn detected-profanity`.

### 7.2 Telegram bot (aiogram 3 / python-telegram-bot)

```python
# aiogram 3
import asyncio, logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from detected_profanity import ProfanityDetector

det = ProfanityDetector(lang="ru")  # ru + translit по умолчанию
bot = Bot(token="BOT_TOKEN")
dp = Dispatcher()

@dp.message(F.text)
async def check(msg: Message):
    text = msg.text or ""
    if det.contains_profanity(text):
        await msg.reply(f"Мат: {det.detect(text)}")
        # или цензура: await msg.reply(det.censor(text))
        # или удаление: await msg.delete()
    else:
        await msg.reply("Чисто")

asyncio.run(dp.start_polling(bot))
```

```python
# python-telegram-bot v20+
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from detected_profanity import ProfanityDetector

det = ProfanityDetector(lang="all")

async def check(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    if det.contains_profanity(text):
        await update.message.reply_text(f"Найден мат: {det.detect(text)}")

app = Application.builder().token("BOT_TOKEN").build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check))
app.run_polling()
```

Советы:
- Создавай `ProfanityDetector` один раз (ленивый Aho-Corasick, thread-safe `search`).
- Для групп — `lang="ru"` + `include_translit=True` покрывает `pizdec/hui`.
- Не блокируй event loop — детектор `O(n+z)`, ~0.5 ms/текст, доп. тред не нужен.

---

## 8. FAQ

**Версии в `pyproject.toml` и `__init__.py` разъехались?**
Синхронизируй: `__version__` — источник для `python -m detected_profanity --version`, `pyproject.toml` — для PyPI. Держи одинаковыми.

**`twine upload` — 400 Invalid distribution?**
Версия уже существует (PyPI immutable). Подними `PATCH`: `0.1.0 → 0.1.1`. Проверь `twine check dist/*` и `long_description` (README.md).

**`pip install` ставит старую версию?**
`pip cache purge && pip install --no-cache-dir --upgrade detected-profanity`. CDN PyPI обновляется ~1–2 мин.

**Поддерживается Python 3.7?**
Нет, `requires-python >=3.8`. На 3.7 — `ERROR: Package requires a different Python`.

**Зависимости?**
Zero deps, только stdlib (`unicodedata`, `re`). Ставится везде.

**Ложные срабатывания (`мандарин`, `assassin`, `художник`)?**
Покрыты `ALLOWLIST` + `word-expand`. Если нашёл новое — заведи issue / PR в `lexicon.py`.

**Как добавить слово в словарь?**
Форк → правка `lexicon.py` (`RU_FORMS` / `EN_FORMS` / `TRANSLIT_FORMS`) → `pytest -q` → PR (<200 строк, `ruff` + `mypy --strict` зелёные).

**CLI vs `python -m` — в чём разница?**
`python -m detected_profanity` — всегда доступен. `detected-profanity` — алиас из `[project.scripts]` после `pip install`. `python cli.py` — цветной REPL (не устанавливается как entry point).

**Где CI/автопубликация?**
Добавь `.github/workflows/publish.yml` на `push tag v*`: `python -m build && twine upload` с `PYPI_API_TOKEN` в Secrets.

---
