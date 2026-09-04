"""Text normalization: NFKC, lowercasing, ё→е, leet/homoglyph mapping."""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "SEPARATORS",
    "LEET_MAP",
    "HOMOGLYPH_MAP",
    "SKELETON_MAP",
    "HYBRID_MAP",
    "collapse_repeats",
    "normalize_char",
    "normalize_text",
    "hybrid_to_cyrillic",
]

SEPARATORS: set[str] = {
    " ",
    "\t",
    "\n",
    "\r",
    "\v",
    "\f",
    "\x85",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    "　",
    ".",
    ",",
    "!",
    "?",
    ":",
    ";",
    "-",
    "_",
    "*",
    "|",
    "/",
    "\\",
    "·",
    "•",
    "∙",
    "⋅",
    "‐",
    "‑",
    "‒",
    "–",
    "—",
    "―",
    "¦",
    "‖",
    "(",
    ")",
    "[",
    "]",
    "{",
    "}",
    "<",
    ">",
    "\"",
    "'",
    "`",
    "´",
    "′",
    "″",
    "~",
    "^",
    "+",
    "=",
    "&",
    "%",
    "#",
    "​",
    "‌",
    "‍",
    "﻿",
    "­",
    "⁠",
    "‎",
    "‏",
    "‪",
    "‫",
    "‬",
    "‭",
    "‮",
    "⁦",
    "⁧",
    "⁨",
    "⁩",
    "͏",
    "؜",
    "᠎",
    "ㅤ",
    "⠀",
    "ᅟ",
    "ᅠ",
}

LEET_MAP: dict[str, str] = {
    "0": "о",
    "3": "з",
    "4": "а",
    "5": "s",
    "@": "а",
    "$": "с",
    "＄": "с",
    "€": "е",
}

HOMOGLYPH_MAP: dict[str, str] = {
    "a": "а",
    "e": "е",
    "o": "о",
    "p": "р",
    "c": "с",
    "x": "х",
    "y": "у",
    "h": "н",
    "k": "к",
    "m": "м",
    "A": "а",
    "E": "е",
    "O": "о",
    "P": "р",
    "C": "с",
    "X": "х",
    "Y": "у",
    "H": "Н",
    "K": "К",
    "M": "М",
}

SKELETON_MAP: dict[str, str] = {**HOMOGLYPH_MAP, **LEET_MAP}

HYBRID_MAP: dict[str, str] = {
    "a": "а", "b": "б", "c": "ц", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "х",
    "i": "и", "j": "й", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о", "p": "п",
    "q": "к", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в", "w": "в", "x": "х",
    "y": "у", "z": "з",
    "A": "А", "B": "Б", "C": "Ц", "D": "Д", "E": "Е", "F": "Ф", "G": "Г", "H": "Х",
    "I": "И", "J": "Й", "K": "К", "L": "Л", "M": "М", "N": "Н", "O": "О", "P": "П",
    "Q": "К", "R": "Р", "S": "С", "T": "Т", "U": "У", "V": "В", "W": "В", "X": "Х",
    "Y": "У", "Z": "З",
}

_RE_REPEATS: re.Pattern[str] = re.compile(r"(.)\1{2,}")


def collapse_repeats(text: str) -> str:
    """Collapse 3+ repeated characters to 2."""
    return _RE_REPEATS.sub(r"\1\1", text)


def normalize_char(c: str) -> str:
    """Normalize a single character or string via skeleton mapping."""
    if not c:
        return c
    out: list[str] = []
    for ch in c:
        lower = ch.lower()
        if lower == "ё":
            out.append("е")
            continue
        if ch in SKELETON_MAP:
            out.append(SKELETON_MAP[ch])
        elif lower in SKELETON_MAP:
            out.append(SKELETON_MAP[lower])
        else:
            out.append(lower)
    return "".join(out) if len(out) > 1 else out[0] if out else ""


def normalize_text(text: str) -> str:
    """Normalize text: NFKC, strip diacritics, lower, ё→е, skeleton mapping."""
    if not text:
        return text
    text = unicodedata.normalize("NFKC", text)
    nfkd = unicodedata.normalize("NFKD", text)
    cleaned: list[str] = []
    for ch in nfkd:
        cat = unicodedata.category(ch)
        if cat in ("Mn", "Me"):
            # combining breve after и/И → й/Й
            if ch == "̆" and cleaned and cleaned[-1] in ("и", "И"):
                last = cleaned.pop()
                cleaned.append("й" if last == "и" else "Й")
                continue
            if ch in ("̀", "́", "̂", "̃", "̇", "̈", "̄", "̉", "̣", "̧", "̨"):
                continue
            continue
        cleaned.append(ch)
    text = "".join(cleaned)
    text = text.lower()
    text = text.replace("ё", "е")
    return "".join(SKELETON_MAP.get(ch, ch) for ch in text)


def hybrid_to_cyrillic(text: str) -> str:
    """Placeholder for hybrid latin→cyrillic conversion."""
    return text
