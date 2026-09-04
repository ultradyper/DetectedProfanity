"""Profanity detection with Aho-Corasick and normalization."""

from __future__ import annotations

import re
import unicodedata
from typing import Final

from .lexicon import EN_FORMS, RU_FORMS, TRANSLIT_FORMS, is_allowed
from .matcher import AhoCorasick
from .normalizer import SEPARATORS, SKELETON_MAP, collapse_repeats, hybrid_to_cyrillic, normalize_text

__all__ = ["ProfanityDetector", "contains_profanity", "detect", "censor"]

_EN_LEET_MAP: Final[dict[str, str]] = {
    "0": "o",
    "1": "l",
    "3": "e",
    "4": "a",
    "5": "s",
    "6": "b",
    "7": "t",
    "8": "b",
    "9": "g",
    "@": "a",
    "$": "s",
    "€": "e",
    "£": "e",
    "!": "i",
    "|": "l",
    "(": "c",
    "＄": "s",
}

_RU_EXPANDED_LEET: Final[dict[str, str]] = {
    "1": "и",
    "2": "г",
    "6": "б",
    "7": "т",
    "8": "в",
    "9": "я",
    "!": "и",
    "|": "л",
    "(": "с",
    "£": "е",
}

_RU_EXPANDED_HOMO: Final[dict[str, str]] = {
    "b": "в", "d": "д", "f": "ф", "g": "г", "i": "и", "j": "й", "l": "л", "n": "н",
    "r": "р", "s": "с", "t": "т", "u": "у", "v": "в", "w": "в", "z": "з", "q": "к",
    "B": "В", "D": "Д", "F": "Ф", "G": "Г", "I": "И", "J": "Й", "L": "Л", "N": "Н",
    "R": "Р", "S": "С", "T": "Т", "U": "У", "V": "В", "W": "В", "Z": "З", "Q": "К",
}


def _en_normalize(text: str) -> str:
    if not text:
        return text
    text = unicodedata.normalize("NFKC", text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) not in ("Mn", "Me"))
    text = text.lower()
    return "".join(_EN_LEET_MAP.get(ch, ch) for ch in text)


def _ru_expanded_normalize(text: str) -> str:
    """Extended RU normalization: additional leet and homoglyph mappings."""
    if not text:
        return text
    text = unicodedata.normalize("NFKC", text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) not in ("Mn", "Me"))
    text = text.lower()
    text = text.replace("ё", "е")
    expanded_map = {**SKELETON_MAP, **_RU_EXPANDED_LEET, **_RU_EXPANDED_HOMO}
    return "".join(expanded_map.get(ch, ch) for ch in text)


def _ru_expanded_variants(text: str) -> list[str]:
    """Generate alternative normalizations for ambiguous mappings (e.g. u→у/и)."""
    base = _ru_expanded_normalize(text)
    variants = {base}
    if "u" in text.lower():
        tmp = unicodedata.normalize("NFKC", text)
        tmp = unicodedata.normalize("NFKD", tmp)
        tmp = "".join(ch for ch in tmp if unicodedata.category(ch) not in ("Mn", "Me"))
        tmp = tmp.lower().replace("ё", "е")
        alt_map: dict[str, str] = {**SKELETON_MAP, **_RU_EXPANDED_LEET}
        alt_map.update({
            "u": "и", "U": "И",
            "b": "в", "d": "д", "f": "ф", "g": "г", "i": "и", "j": "й",
            "l": "л", "n": "н", "r": "р", "s": "с", "t": "т", "v": "в",
            "w": "в", "z": "з", "q": "к",
        })
        alt = "".join(alt_map.get(ch, ch) for ch in tmp)
        variants.add(alt)
    return sorted(variants)


def _en_normalize_variants(text: str) -> list[str]:
    """Return variants for ambiguous leet (1→l/i, h→cyrillic)."""
    base = _en_normalize(text)
    variants = {base}
    if "1" in text:
        alt = unicodedata.normalize("NFKC", text)
        alt = unicodedata.normalize("NFKD", alt)
        alt = "".join(ch for ch in alt if unicodedata.category(ch) not in ("Mn", "Me"))
        alt = alt.lower().replace("1", "i")
        alt = "".join(_EN_LEET_MAP.get(ch, ch) if ch != "1" else "i" for ch in alt)
        variants.add(alt)
    if "h" in text.lower():
        tmp = unicodedata.normalize("NFKC", text)
        tmp = unicodedata.normalize("NFKD", tmp)
        tmp = "".join(ch for ch in tmp if unicodedata.category(ch) not in ("Mn", "Me"))
        tmp = tmp.lower()
        alt_map = {**_EN_LEET_MAP, "h": "х", "H": "Х"}
        variants.add("".join(alt_map.get(ch, ch) for ch in tmp))
    return sorted(variants)


def _strip_with_map(text: str) -> tuple[str, list[int]]:
    """Remove separators and return (stripped, index_map)."""
    stripped_chars: list[str] = []
    cmap: list[int] = []
    for idx, ch in enumerate(text):
        if ch in SEPARATORS:
            continue
        if ch.isalnum():
            stripped_chars.append(ch)
            cmap.append(idx)
    return "".join(stripped_chars), cmap


def _expand_word(text: str, start: int, end: int) -> tuple[int, int, str]:
    ws = start
    while ws > 0 and text[ws - 1] not in SEPARATORS and text[ws - 1].isalnum():
        ws -= 1
    we = end
    while we + 1 < len(text) and text[we + 1] not in SEPARATORS and text[we + 1].isalnum():
        we += 1
    return ws, we, text[ws : we + 1]


def _is_allowed_word(word: str) -> bool:
    if not word:
        return False
    if is_allowed(word):
        return True
    stripped, _ = _strip_with_map(word.lower())
    if stripped and is_allowed(stripped):
        return True
    return False


def _gen_variants(patterns: list[str], min_keep: int = 3) -> list[str]:
    """Generate variants via single/double deletion and single duplication."""
    variants: set[str] = set(patterns)
    _DENY_DOUBLE = {"ела", "ело", "ели", "ель", "или", "ать", "ять", "ить"}
    for pat in patterns:
        if len(pat) >= 4:
            for i in range(len(pat)):
                v = pat[:i] + pat[i + 1 :]
                if len(v) >= min_keep and v not in variants:
                    variants.add(v)
        if len(pat) >= 5:
            for i in range(len(pat)):
                for j in range(i + 1, len(pat)):
                    v = pat[:i] + pat[i + 1 : j] + pat[j + 1 :]
                    if len(v) >= 3 and v not in variants and v not in _DENY_DOUBLE:
                        if len(v) == 3 and v in {"ела", "ело", "или"}:
                            continue
                        variants.add(v)
        if len(pat) >= 3:
            for i in range(len(pat)):
                v = pat[: i + 1] + pat[i] + pat[i + 1 :]
                if v not in variants:
                    variants.add(v)
    return sorted(variants)


def _build_ru_automaton() -> AhoCorasick:
    base = [normalize_text(p) for p in RU_FORMS]
    base = [collapse_repeats(p) for p in base]
    uniq = sorted({p for p in base if p})
    expanded = _gen_variants(uniq)
    # filter generic variant that causes false positives
    expanded = [p for p in expanded if p != "жный"]
    return AhoCorasick(expanded)


def _build_en_automaton() -> AhoCorasick:
    base = [_en_normalize(p) for p in EN_FORMS]
    base = [collapse_repeats(p) for p in base]
    uniq = sorted({p for p in base if p})
    expanded = _gen_variants(uniq)
    _DENY_EN = {
        "read", "aker", "eat", "her", "hert", "assa", "assas", "ssass",
        "was", "the", "are", "you", "and", "for", "not", "but", "had",
        "has", "were", "been", "have",
    }
    expanded = [p for p in expanded if p not in _DENY_EN]
    return AhoCorasick(expanded)


def _build_translit_automaton() -> AhoCorasick:
    base = [_en_normalize(p) for p in TRANSLIT_FORMS]
    base = [collapse_repeats(p) for p in base]
    plain = [collapse_repeats(p.lower()) for p in TRANSLIT_FORMS]
    uniq = sorted({p for p in base + plain if p})
    expanded = _gen_variants(uniq)
    _DENY_TR = {"eat", "her", "hert", "ret", "ati"}
    expanded = [p for p in expanded if p not in _DENY_TR]
    return AhoCorasick(expanded)


_RU_AC: AhoCorasick | None = None
_EN_AC: AhoCorasick | None = None
_TR_AC: AhoCorasick | None = None


def _get_ru_ac() -> AhoCorasick:
    global _RU_AC
    if _RU_AC is None:
        _RU_AC = _build_ru_automaton()
    return _RU_AC


def _get_en_ac() -> AhoCorasick:
    global _EN_AC
    if _EN_AC is None:
        _EN_AC = _build_en_automaton()
    return _EN_AC


def _get_tr_ac() -> AhoCorasick:
    global _TR_AC
    if _TR_AC is None:
        _TR_AC = _build_translit_automaton()
    return _TR_AC


def _check_collapsed(collapsed: str, ac: AhoCorasick) -> bool:
    if not collapsed or not ac:
        return False
    for end_idx, pat in ac.search(collapsed):
        start_idx = end_idx - len(pat) + 1
        if start_idx < 0:
            continue
        if len(pat) == 2:
            ws, we, word = _expand_word(collapsed, start_idx, end_idx)
            word_stripped, _ = _strip_with_map(word.lower())
            if len(word_stripped) != len(pat):
                continue
            if _is_allowed_word(word):
                continue
        elif len(pat) == 3:
            ws, we, word = _expand_word(collapsed, start_idx, end_idx)
            word_stripped, _ = _strip_with_map(word.lower())
            if len(word_stripped) != len(pat):
                continue
            if _is_allowed_word(word):
                continue
        else:
            ws, we, word = _expand_word(collapsed, start_idx, end_idx)
            word_stripped, _ = _strip_with_map(word.lower())
            if len(word_stripped) > len(pat) + 3:
                continue
            if _is_allowed_word(word):
                continue
        if _is_allowed_word(pat):
            continue
        return True
    return False


def _check_stripped(collapsed: str, stripped: str, cmap: list[int], ac: AhoCorasick) -> bool:
    if not stripped or not ac:
        return False
    for end_idx, pat in ac.search(stripped):
        start_idx = end_idx - len(pat) + 1
        if start_idx < 0 or start_idx >= len(cmap) or end_idx >= len(cmap):
            continue
        orig_start = cmap[start_idx]
        orig_end = cmap[end_idx]
        ws, we, word = _expand_word(collapsed, orig_start, orig_end)
        if len(pat) == 2:
            word_stripped, _ = _strip_with_map(word.lower())
            if len(word_stripped) != len(pat):
                continue
        elif len(pat) == 3:
            word_stripped, _ = _strip_with_map(word.lower())
            if len(word_stripped) != len(pat):
                continue
        if _is_allowed_word(word):
            continue
        return True
    return False


def _find_collapsed_matches(collapsed: str, ac: AhoCorasick) -> list[tuple[int, int, str, str]]:
    results: list[tuple[int, int, str, str]] = []
    seen: set[tuple[int, int]] = set()
    for end_idx, pat in ac.search(collapsed):
        start_idx = end_idx - len(pat) + 1
        if start_idx < 0:
            continue
        if (start_idx, end_idx) in seen:
            continue
        ws, we, word = _expand_word(collapsed, start_idx, end_idx)
        if len(pat) == 2:
            word_stripped, _ = _strip_with_map(word.lower())
            if len(word_stripped) != len(pat):
                continue
        elif len(pat) == 3:
            word_stripped, _ = _strip_with_map(word.lower())
            if len(word_stripped) != len(pat):
                continue
        if _is_allowed_word(word) or _is_allowed_word(pat):
            continue
        seen.add((start_idx, end_idx))
        results.append((start_idx, end_idx, pat, word))
    results.sort(key=lambda x: (x[0], x[1]))
    return results


def _find_stripped_matches(collapsed: str, stripped: str, cmap: list[int], ac: AhoCorasick) -> list[tuple[int, int, str, str]]:
    results: list[tuple[int, int, str, str]] = []
    seen: set[tuple[int, int]] = set()
    for end_idx, pat in ac.search(stripped):
        start_idx = end_idx - len(pat) + 1
        if start_idx < 0 or start_idx >= len(cmap) or end_idx >= len(cmap):
            continue
        orig_start = cmap[start_idx]
        orig_end = cmap[end_idx]
        if (orig_start, orig_end) in seen:
            continue
        ws, we, word = _expand_word(collapsed, orig_start, orig_end)
        if len(pat) == 2:
            word_stripped, _ = _strip_with_map(word.lower())
            if len(word_stripped) != len(pat):
                continue
        elif len(pat) == 3:
            word_stripped, _ = _strip_with_map(word.lower())
            if len(word_stripped) != len(pat):
                continue
        if _is_allowed_word(word):
            continue
        seen.add((orig_start, orig_end))
        results.append((orig_start, orig_end, pat, word))
    results.sort(key=lambda x: (x[0], x[1]))
    return results


class ProfanityDetector:
    """Detector for RU/EN/translit profanity with masking bypass."""

    def __init__(
        self,
        lang: str | None = None,
        languages: str | list[str] | None = None,
        *,
        include_translit: bool = True,
        use_normalization: bool = True,
    ) -> None:
        raw_lang: str | list[str] | None = languages if languages is not None else lang
        if isinstance(raw_lang, (list, tuple, set)):
            parts = [str(p).strip().lower() for p in raw_lang if str(p).strip()]
            if not parts:
                self.lang: str | None = None
                self._active_langs: set[str] | None = None
            elif len(parts) == 1:
                v = parts[0]
                self.lang = None if v in ("", "all", "*") else v
                self._active_langs = None
            else:
                self.lang = None
                self._active_langs = set(parts)
                self.include_translit = include_translit
                self.use_normalization = use_normalization
                return
        elif isinstance(raw_lang, str):
            v = raw_lang.strip().lower()
            self.lang = None if v in ("", "all", "*") else v
        else:
            self.lang = None
        self._active_langs: set[str] | None = None
        self.include_translit = include_translit
        self.use_normalization = use_normalization

    def _prepare_text(self, text: str) -> tuple[str, str]:
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__!r}")
        if self.use_normalization:
            normalized = normalize_text(text)
        else:
            normalized = text.lower()
        collapsed = collapse_repeats(normalized)
        stripped = "".join(ch for ch in collapsed if ch not in SEPARATORS)
        return collapsed, stripped

    def _prepare_plain(self, text: str) -> tuple[str, str, list[int]]:
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__!r}")
        if self.use_normalization:
            collapsed = collapse_repeats(_en_normalize(text))
        else:
            collapsed = collapse_repeats(text.lower())
        stripped, cmap = _strip_with_map(collapsed)
        return collapsed, stripped, cmap

    def _prepare_translit_plain(self, text: str) -> tuple[str, str, list[int]]:
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__!r}")
        lower = unicodedata.normalize("NFKC", text.lower())
        lower = unicodedata.normalize("NFKD", lower)
        lower = "".join(ch for ch in lower if unicodedata.category(ch) not in ("Mn", "Me"))
        collapsed = collapse_repeats(lower)
        stripped, cmap = _strip_with_map(collapsed)
        return collapsed, stripped, cmap

    def _prepare_plain_variants(self, text: str) -> list[tuple[str, str, list[int]]]:
        variants = _en_normalize_variants(text)
        out = []
        for v in variants:
            collapsed = collapse_repeats(v)
            stripped, cmap = _strip_with_map(collapsed)
            out.append((collapsed, stripped, cmap))
        return out

    def _check_ru(self, text: str) -> bool:
        collapsed, _ = self._prepare_text(text)
        stripped, cmap = _strip_with_map(collapsed)
        if _check_collapsed(collapsed, _get_ru_ac()):
            return True
        if _check_stripped(collapsed, stripped, cmap, _get_ru_ac()):
            return True
        has_cyrillic = any(0x0400 <= ord(ch) <= 0x04FF or 0x0500 <= ord(ch) <= 0x052F for ch in text)
        if has_cyrillic:
            try:
                for exp_collapsed in _ru_expanded_variants(text):
                    exp_collapsed = collapse_repeats(exp_collapsed)
                    if exp_collapsed == collapsed:
                        continue
                    e_stripped, e_cmap = _strip_with_map(exp_collapsed)
                    if _check_collapsed(exp_collapsed, _get_ru_ac()):
                        return True
                    if _check_stripped(exp_collapsed, e_stripped, e_cmap, _get_ru_ac()):
                        return True
            except Exception:
                pass
            hybrid = hybrid_to_cyrillic(collapsed)
            if hybrid != collapsed:
                h_stripped, h_cmap = _strip_with_map(hybrid)
                if _check_collapsed(hybrid, _get_ru_ac()):
                    return True
                if _check_stripped(hybrid, h_stripped, h_cmap, _get_ru_ac()):
                    return True
            try:
                for exp in _ru_expanded_variants(text):
                    exp_c = collapse_repeats(exp)
                    exp_hybrid = hybrid_to_cyrillic(exp_c)
                    if exp_hybrid not in (collapsed, locals().get("hybrid", "")):
                        eh_stripped, eh_cmap = _strip_with_map(exp_hybrid)
                        if _check_collapsed(exp_hybrid, _get_ru_ac()):
                            return True
                        if _check_stripped(exp_hybrid, eh_stripped, eh_cmap, _get_ru_ac()):
                            return True
            except Exception:
                pass
        return False

    def _check_en(self, text: str) -> bool:
        for collapsed, stripped, cmap in self._prepare_plain_variants(text):
            if _check_collapsed(collapsed, _get_en_ac()):
                return True
            if _check_stripped(collapsed, stripped, cmap, _get_en_ac()):
                return True
        return False

    def _check_translit(self, text: str) -> bool:
        collapsed, stripped, cmap = self._prepare_translit_plain(text)
        if _check_collapsed(collapsed, _get_tr_ac()):
            return True
        if _check_stripped(collapsed, stripped, cmap, _get_tr_ac()):
            return True
        for collapsed_en, stripped_en, cmap_en in self._prepare_plain_variants(text):
            if _check_collapsed(collapsed_en, _get_tr_ac()):
                return True
            if _check_stripped(collapsed_en, stripped_en, cmap_en, _get_tr_ac()):
                return True
        return False

    def _find_ru(self, text: str) -> list[tuple[int, int, str, str]]:
        collapsed, _ = self._prepare_text(text)
        stripped, cmap = _strip_with_map(collapsed)
        res: list[tuple[int, int, str, str]] = []
        res.extend(_find_collapsed_matches(collapsed, _get_ru_ac()))
        res.extend(_find_stripped_matches(collapsed, stripped, cmap, _get_ru_ac()))
        has_cyrillic = any(0x0400 <= ord(ch) <= 0x04FF or 0x0500 <= ord(ch) <= 0x052F for ch in text)
        if has_cyrillic:
            try:
                for exp_collapsed in _ru_expanded_variants(text):
                    exp_collapsed = collapse_repeats(exp_collapsed)
                    if exp_collapsed == collapsed:
                        continue
                    e_stripped, e_cmap = _strip_with_map(exp_collapsed)
                    res.extend(_find_collapsed_matches(exp_collapsed, _get_ru_ac()))
                    res.extend(_find_stripped_matches(exp_collapsed, e_stripped, e_cmap, _get_ru_ac()))
                    exp_hybrid = hybrid_to_cyrillic(exp_collapsed)
                    if exp_hybrid not in (collapsed, exp_collapsed):
                        eh_stripped, eh_cmap = _strip_with_map(exp_hybrid)
                        res.extend(_find_collapsed_matches(exp_hybrid, _get_ru_ac()))
                        res.extend(_find_stripped_matches(exp_hybrid, eh_stripped, eh_cmap, _get_ru_ac()))
            except Exception:
                pass
            hybrid = hybrid_to_cyrillic(collapsed)
            if hybrid != collapsed:
                h_stripped, h_cmap = _strip_with_map(hybrid)
                res.extend(_find_collapsed_matches(hybrid, _get_ru_ac()))
                res.extend(_find_stripped_matches(hybrid, h_stripped, h_cmap, _get_ru_ac()))
        res.sort(key=lambda x: (x[0], -len(x[2])))
        seen: set[tuple[int, int]] = set()
        word_best: dict[str, int] = {}
        uniq: list[tuple[int, int, str, str]] = []
        for item in res:
            span = (item[0], item[1])
            if span in seen:
                continue
            w = item[3].lower()
            if w in word_best and len(item[2]) <= word_best[w]:
                continue
            seen.add(span)
            existing = [u for u in uniq if u[3].lower() == w]
            if existing and len(item[2]) <= max(len(e[2]) for e in existing):
                continue
            uniq = [u for u in uniq if u[3].lower() != w or len(item[2]) > len(u[2])]
            word_best[w] = len(item[2])
            uniq.append(item)
        uniq.sort(key=lambda x: (x[0], x[1]))
        return uniq

    def _find_en(self, text: str) -> list[tuple[int, int, str, str]]:
        collapsed, stripped, cmap = self._prepare_plain(text)
        res: list[tuple[int, int, str, str]] = []
        res.extend(_find_collapsed_matches(collapsed, _get_en_ac()))
        res.extend(_find_stripped_matches(collapsed, stripped, cmap, _get_en_ac()))
        res.sort(key=lambda x: (x[0], -len(x[2])))
        seen: set[tuple[int, int]] = set()
        word_best: dict[str, int] = {}
        uniq: list[tuple[int, int, str, str]] = []
        for item in res:
            span = (item[0], item[1])
            if span in seen:
                continue
            w = item[3].lower()
            if w in word_best and len(item[2]) <= word_best[w]:
                continue
            seen.add(span)
            existing = [u for u in uniq if u[3].lower() == w]
            if existing and len(item[2]) <= max(len(e[2]) for e in existing):
                continue
            uniq = [u for u in uniq if u[3].lower() != w or len(item[2]) > len(u[2])]
            word_best[w] = len(item[2])
            uniq.append(item)
        uniq.sort(key=lambda x: (x[0], x[1]))
        return uniq

    def _find_tr(self, text: str) -> list[tuple[int, int, str, str]]:
        collapsed, stripped, cmap = self._prepare_translit_plain(text)
        collapsed_en, stripped_en, cmap_en = self._prepare_plain(text)
        res: list[tuple[int, int, str, str]] = []
        res.extend(_find_collapsed_matches(collapsed, _get_tr_ac()))
        res.extend(_find_stripped_matches(collapsed, stripped, cmap, _get_tr_ac()))
        res.extend(_find_collapsed_matches(collapsed_en, _get_tr_ac()))
        res.extend(_find_stripped_matches(collapsed_en, stripped_en, cmap_en, _get_tr_ac()))
        res.sort(key=lambda x: (x[0], -len(x[2])))
        seen: set[tuple[int, int]] = set()
        word_best: dict[str, int] = {}
        uniq: list[tuple[int, int, str, str]] = []
        for item in res:
            span = (item[0], item[1])
            if span in seen:
                continue
            w = item[3].lower()
            if w in word_best and len(item[2]) <= word_best[w]:
                continue
            seen.add(span)
            existing = [u for u in uniq if u[3].lower() == w]
            if existing and len(item[2]) <= max(len(e[2]) for e in existing):
                continue
            uniq = [u for u in uniq if u[3].lower() != w or len(item[2]) > len(u[2])]
            word_best[w] = len(item[2])
            uniq.append(item)
        uniq.sort(key=lambda x: (x[0], x[1]))
        return uniq

    def contains_profanity(self, text: str) -> bool:
        """Return True if text contains profanity."""
        if not text:
            return False
        if self._active_langs is not None:
            if "ru" in self._active_langs and self._check_ru(text):
                return True
            if "en" in self._active_langs and self._check_en(text):
                return True
            if "translit" in self._active_langs and self._check_translit(text):
                return True
            if self.include_translit and "ru" in self._active_langs and self._check_translit(text):
                return True
            return False
        lang = self.lang
        if lang is None:
            if self._check_ru(text):
                return True
            if self._check_en(text):
                return True
            if self.include_translit and self._check_translit(text):
                return True
            return False
        if lang == "ru":
            if self._check_ru(text):
                return True
            if self.include_translit and self._check_translit(text):
                return True
            return False
        if lang == "en":
            return self._check_en(text)
        if lang == "translit":
            return self._check_translit(text)
        return self._check_ru(text) or self._check_en(text) or self._check_translit(text)

    def detect(self, text: str) -> list[str]:
        """Return list of matched profanity forms."""
        if not text:
            return []
        results: list[tuple[int, int, str]] = []
        if self._active_langs is not None:
            if "ru" in self._active_langs:
                for s, e, pat, _w in self._find_ru(text):
                    results.append((s, e, pat))
            if "en" in self._active_langs:
                for s, e, pat, _w in self._find_en(text):
                    results.append((s, e, pat))
            if "translit" in self._active_langs:
                for s, e, pat, _w in self._find_tr(text):
                    results.append((s, e, pat))
            elif self.include_translit and "ru" in self._active_langs:
                for s, e, pat, _w in self._find_tr(text):
                    results.append((s, e, pat))
        elif self.lang is None:
            for s, e, pat, _w in self._find_ru(text):
                results.append((s, e, pat))
            for s, e, pat, _w in self._find_en(text):
                results.append((s, e, pat))
            if self.include_translit:
                for s, e, pat, _w in self._find_tr(text):
                    results.append((s, e, pat))
        elif self.lang == "ru":
            for s, e, pat, _w in self._find_ru(text):
                results.append((s, e, pat))
            if self.include_translit:
                for s, e, pat, _w in self._find_tr(text):
                    results.append((s, e, pat))
        elif self.lang == "en":
            for s, e, pat, _w in self._find_en(text):
                results.append((s, e, pat))
        elif self.lang == "translit":
            for s, e, pat, _w in self._find_tr(text):
                results.append((s, e, pat))
        else:
            for s, e, pat, _w in self._find_ru(text):
                results.append((s, e, pat))
            for s, e, pat, _w in self._find_en(text):
                results.append((s, e, pat))
        results.sort(key=lambda x: (x[0], x[1]))
        seen: set[tuple[int, int]] = set()
        out: list[str] = []
        for s, e, pat in results:
            if (s, e) not in seen:
                seen.add((s, e))
                canonical = re.sub(r"(.)\1+", r"\1", pat)
                out.append(canonical)
        return out

    def censor(self, text: str, repl: str = "*") -> str:
        """Return censored copy of text."""
        if not text:
            return text
        intervals: list[tuple[int, int]] = []
        if self._active_langs is not None:
            finders = []
            if "ru" in self._active_langs:
                finders.append(self._find_ru)
            if "en" in self._active_langs:
                finders.append(self._find_en)
            if "translit" in self._active_langs:
                finders.append(self._find_tr)
            elif self.include_translit and "ru" in self._active_langs:
                finders.append(self._find_tr)
        elif self.lang is None:
            finders = [self._find_ru, self._find_en]
            if self.include_translit:
                finders.append(self._find_tr)
        elif self.lang == "ru":
            finders = [self._find_ru]
            if self.include_translit:
                finders.append(self._find_tr)
        elif self.lang == "en":
            finders = [self._find_en]
        elif self.lang == "translit":
            finders = [self._find_tr]
        else:
            finders = [self._find_ru, self._find_en]
        for finder in finders:
            for s, e, _pat, word in finder(text):
                intervals.append((s, e))
        if not intervals:
            return text
        intervals.sort()
        merged: list[tuple[int, int]] = []
        cs, ce = intervals[0]
        for s, e in intervals[1:]:
            if s <= ce + 1:
                ce = max(ce, e)
            else:
                merged.append((cs, ce))
                cs, ce = s, e
        merged.append((cs, ce))
        try:
            ref_collapsed = collapse_repeats(normalize_text(text)) if self.use_normalization else collapse_repeats(text.lower())
            if len(ref_collapsed) == len(text):
                chars = list(text)
                for s, e in reversed(merged):
                    if s < 0 or e >= len(chars):
                        continue
                    length = e - s + 1
                    fill = repl * length if len(repl) == 1 else (repl * ((length // len(repl)) + 1))[:length]
                    chars[s : e + 1] = list(fill)
                return "".join(chars)
            else:
                chars = list(ref_collapsed)
                for s, e in reversed(merged):
                    if s < 0 or e >= len(chars):
                        continue
                    length = e - s + 1
                    fill = repl * length if len(repl) == 1 else (repl * ((length // len(repl)) + 1))[:length]
                    chars[s : e + 1] = list(fill)
                return "".join(chars)
        except Exception:
            return text


_default_detector: ProfanityDetector = ProfanityDetector()


def contains_profanity(text: str) -> bool:
    """Return True if text contains profanity."""
    return _default_detector.contains_profanity(text)


def detect(text: str) -> list[str]:
    """Return list of matched profanity forms."""
    return _default_detector.detect(text)


def censor(text: str, repl: str = "*") -> str:
    """Return censored copy of text."""
    return _default_detector.censor(text, repl=repl)
