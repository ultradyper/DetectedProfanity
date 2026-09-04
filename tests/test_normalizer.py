"""Tests for normalizer."""

from __future__ import annotations

import unicodedata

from detected_profanity.normalizer import (
    HOMOGLYPH_MAP,
    LEET_MAP,
    SEPARATORS,
    SKELETON_MAP,
    collapse_repeats,
    normalize_char,
    normalize_text,
)


class TestNFKC:
    def test_nfkc_fullwidth_latin_to_ascii_then_homoglyph(self):
        assert normalize_text("Ａ") == "а"

    def test_nfkc_fullwidth_hello(self):
        raw = "ｈｅｌｌｏ"
        assert unicodedata.normalize("NFKC", raw) == "hello"
        result = normalize_text(raw)
        assert "ｈ" not in result
        assert "ｅ" not in result

    def test_nfkc_ligature_fi(self):
        assert unicodedata.normalize("NFKC", "ﬁ") == "fi"
        assert normalize_text("ﬁ") == "fi"

    def test_nfkc_fullwidth_dollar(self):
        assert normalize_text("＄") == "с"

    def test_nfkc_circled_digit(self):
        assert normalize_text("①") == "1"


class TestLower:
    def test_lower_cyrillic(self):
        assert normalize_text("ПРИВЕТ") == "привет"

    def test_lower_latin_homoglyph_chain(self):
        assert normalize_text("HELLO") == "неllо"

    def test_lower_mixed_case(self):
        assert normalize_text("ПрИвЕт") == "привет"


class TestYo:
    def test_yo_lower(self):
        assert normalize_text("ё") == "е"

    def test_yo_upper(self):
        assert normalize_text("Ё") == "е"

    def test_yo_in_word(self):
        assert normalize_text("мёд") == "мед"
        assert normalize_text("МЁД") == "мед"

    def test_normalize_char_yo(self):
        assert normalize_char("ё") == "е"
        assert normalize_char("Ё") == "е"


class TestLeet:
    def test_leet_0_to_cyrillic_o(self):
        assert normalize_text("0") == "о"
        assert LEET_MAP["0"] == "о"
        assert ord(normalize_text("0")) == 0x043E

    def test_leet_3_to_cyrillic_ze(self):
        assert normalize_text("3") == "з"
        assert ord(normalize_text("3")) == 0x0437

    def test_leet_at_to_cyrillic_a(self):
        assert normalize_text("@") == "а"
        assert ord(normalize_text("@")) == 0x0430

    def test_leet_4_to_cyrillic_a(self):
        assert normalize_text("4") == "а"

    def test_leet_dollar_to_cyrillic_es(self):
        assert normalize_text("$") == "с"

    def test_leet_5_to_s(self):
        assert normalize_text("5") == "s"

    def test_leet_euro_to_e(self):
        assert normalize_text("€") == "е"

    def test_leet_in_word(self):
        assert normalize_text("h3llo") == "нзllо"
        assert normalize_text("4@0") == "аао"


class TestHomoglyph:
    def test_homoglyph_a_to_cyrillic_a(self):
        assert normalize_text("a") == "а"
        assert HOMOGLYPH_MAP["a"] == "а"

    def test_homoglyph_o_to_cyrillic_o(self):
        assert normalize_text("o") == "о"
        assert HOMOGLYPH_MAP["o"] == "о"

    def test_homoglyph_p_to_cyrillic_er(self):
        assert normalize_text("p") == "р"
        assert HOMOGLYPH_MAP["p"] == "р"

    def test_homoglyph_c_to_cyrillic_es(self):
        assert normalize_text("c") == "с"

    def test_homoglyph_x_to_cyrillic_kha(self):
        assert normalize_text("x") == "х"

    def test_homoglyph_upper_H(self):
        assert normalize_char("H") == "Н"
        assert normalize_text("H") == "н"

    def test_homoglyph_word(self):
        assert normalize_text("pope") == "роре"


class TestCollapseRepeats:
    def test_aaa_to_aa(self):
        assert collapse_repeats("aaa") == "aa"

    def test_blyaya_to_blya(self):
        assert collapse_repeats("бляяя") == "бляя"

    def test_two_unchanged(self):
        assert collapse_repeats("aa") == "aa"
        assert collapse_repeats("бля") == "бля"

    def test_four_to_two(self):
        assert collapse_repeats("aaaa") == "aa"
        assert collapse_repeats("яяяя") == "яя"

    def test_oooochen_many_to_two(self):
        assert collapse_repeats("оооочень") == "оочень"
        assert collapse_repeats("оооочень") == "о" * 2 + "чень"

    def test_mixed_repeats(self):
        assert collapse_repeats("привеееет") == "привеет"
        assert collapse_repeats("ааа ббб ввв") == "аа бб вв"

    def test_single_char(self):
        assert collapse_repeats("a") == "a"
        assert collapse_repeats("") == ""

    def test_no_repeats(self):
        assert collapse_repeats("привет") == "привет"

    def test_collapse_after_normalize(self):
        assert normalize_text("ааа") == "ааа"
        assert collapse_repeats(normalize_text("ааа")) == "аа"

    def test_collapse_repeats_three_edge(self):
        assert collapse_repeats("бляя") == "бляя"
        assert collapse_repeats("бляяя") == "бляя"


class TestNormalizeText:
    def test_empty(self):
        assert normalize_text("") == ""

    def test_combined_pipeline(self):
        assert normalize_text("Ё0@") == "еоа"

    def test_normalize_text_with_fullwidth_and_leet(self):
        assert normalize_text("Ｈ3ＬＬ0") == "нзllо"

    def test_normalize_text_preserves_cyrillic(self):
        assert normalize_text("привет мир") == "привет мир"

    def test_normalize_char_multi(self):
        assert normalize_char("aB") == "аb"
        assert normalize_char("aB") == "а" + "b"

    def test_normalize_text_does_not_strip_separators(self):
        assert normalize_text("п.р,и!вет") == "п.р,и!вет"

    def test_normalize_text_full_obfuscation(self):
        assert normalize_text("р0з@") == "роз" + "а"
        assert normalize_text("р0з@") == "р" + "о" + "з" + "а"


class TestSeparators:
    def test_is_set(self):
        assert isinstance(SEPARATORS, set)

    def test_contains_common_separators(self):
        for ch in [" ", ".", ",", "!", "?", "-", "_", "*", "|", "/", "\\"]:
            assert ch in SEPARATORS, f"{ch!r} should be in SEPARATORS"

    def test_contains_unicode_dashes(self):
        assert "—" in SEPARATORS
        assert "–" in SEPARATORS
        assert "·" in SEPARATORS
        assert "•" in SEPARATORS

    def test_contains_zero_width(self):
        assert "​" in SEPARATORS
        assert "‌" in SEPARATORS
        assert "‍" in SEPARATORS
        assert "﻿" in SEPARATORS
        assert "­" in SEPARATORS

    def test_contains_brackets_and_quotes(self):
        for ch in ["(", ")", "[", "]", "{", "}", "<", ">", '"', "'", "`"]:
            assert ch in SEPARATORS

    def test_non_separator_not_in(self):
        assert "а" not in SEPARATORS
        assert "o" not in SEPARATORS
        assert "1" not in SEPARATORS

    def test_size_reasonable(self):
        assert len(SEPARATORS) >= 40
