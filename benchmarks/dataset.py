"""Dataset for benchmarks: RU/EN clean/profane/obfuscated."""

from __future__ import annotations

RU_CLEAN: list[str] = [
    "Привет, как дела?",
    "Погода сегодня солнечная и теплая.",
    "Я люблю читать книги вечером.",
    "Мы поехали на дачу в выходные.",
    "Кот спит на подоконнике.",
    "Завтра важный экзамен в университете.",
    "Мне нравится слушать музыку.",
    "Дети играют во дворе.",
    "Я купил свежий хлеб в магазине.",
    "Фильм был очень интересным.",
]

RU_PROFANE: list[str] = [
    "пошёл на хуй",
    "это полный пиздец",
    "заебал ты меня уже",
    "блядь, опять опоздал на работу",
    "сука, как же ты бесишь",
    "пидор ты конченый",
    "мудак ебаный, что ты натворил",
    "ебло закрой и слушай",
    "пиздюк малолетний, иди отсюда",
    "долбоеб, опять всё испортил",
]

RU_OBFUSCATED: list[str] = [
    "на#хуя ты это сделал",
    "х*й тебе а не повышение",
    "х у й знает что происходит",
    "б.л.я опять пробка на дороге",
    "бл@ть как же холодно сегодня",
    "0хуеть как круто получилось",
    "п..здец полный, что творится",
    "бляяяя как больно было",
    "пздец ты где был весь день",
    "хуи пинать будешь до вечера",
    "ебло завали, надоел уже",
    "пиздюк мелкий, иди учись",
    "сука где мои ключи от машины",
    "пидор ты редкостный",
    "мудак ты конченый, опять обманул",
    "п#здец какой день тяжёлый",
    "х-у-й тебе а не деньги",
    "бл@ть иди сюда быстро",
    "охуенно получилось, браво",
    "на х*й иди отсюда",
]

EN_CLEAN: list[str] = [
    "Hello world",
    "Beautiful day outside",
    "I love quiet evenings",
    "Weekend trip to countryside",
    "Small cat sleeps peacefully",
    "Important study session tomorrow",
    "Kids play in garden",
    "Fresh bread from bakery",
    "Interesting film tonight",
    "Sunny weather today",
]

EN_PROFANE: list[str] = [
    "fuck you",
    "shit happens",
    "you are a bitch",
    "what a dumb ass",
    "you fucking idiot",
    "that cunt is annoying",
    "suck my dick",
    "you bastard, leave me alone",
    "what the hell, damn it",
    "bullshit, I don't believe you",
]

EN_OBFUSCATED: list[str] = [
    "f*ck you buddy",
    "sh*t happens every day",
    "bullshit detector triggered",
    "f.u.c.k off now",
    "5hit happens again",
    "f**k this shit",
    "sh!t happens, sorry",
    "b!tch please stop",
    "a$$hole move",
    "motherf*cker you are",
]

ALL_EXPECTED: dict[str, bool] = {
    **{t: False for t in RU_CLEAN},
    **{t: True for t in RU_PROFANE},
    **{t: True for t in RU_OBFUSCATED},
    **{t: False for t in EN_CLEAN},
    **{t: True for t in EN_PROFANE},
    **{t: True for t in EN_OBFUSCATED},
}

__all__ = [
    "RU_CLEAN",
    "RU_PROFANE",
    "RU_OBFUSCATED",
    "EN_CLEAN",
    "EN_PROFANE",
    "EN_OBFUSCATED",
    "ALL_EXPECTED",
]

assert len(RU_CLEAN) == 10, f"RU_CLEAN={len(RU_CLEAN)} != 10"
assert len(RU_PROFANE) == 10, f"RU_PROFANE={len(RU_PROFANE)} != 10"
assert len(RU_OBFUSCATED) == 20, f"RU_OBFUSCATED={len(RU_OBFUSCATED)} != 20"
assert len(EN_CLEAN) == 10, f"EN_CLEAN={len(EN_CLEAN)} != 10"
assert len(EN_PROFANE) == 10, f"EN_PROFANE={len(EN_PROFANE)} != 10"
assert len(EN_OBFUSCATED) == 10, f"EN_OBFUSCATED={len(EN_OBFUSCATED)} != 10"
assert len(ALL_EXPECTED) == 70, f"ALL_EXPECTED={len(ALL_EXPECTED)} != 70"
for _needle in ["на#хуя", "х*й", "х у й", "б.л.я", "бл@ть", "0хуеть", "п..здец", "бляяяя", "пздец", "хуи", "ебло", "пиздюк", "сука", "пидор", "мудак"]:
    assert any(_needle in _t for _t in RU_OBFUSCATED), f"RU_OBFUSCATED missing {_needle!r}"
for _needle in ["f*ck", "sh*t", "bullshit", "f.u.c.k", "5hit"]:
    assert any(_needle in _t for _t in EN_OBFUSCATED), f"EN_OBFUSCATED missing {_needle!r}"
