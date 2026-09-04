"""Tests for Aho-Corasick."""

from __future__ import annotations

import time

import pytest

from detected_profanity.matcher import AhoCorasick, Match, find_matches


def test_add_pattern_single():
    ac = AhoCorasick()
    ac.add_pattern("hello")
    assert "hello" in ac
    assert len(ac) == 1
    assert ac.patterns == ("hello",)
    assert ac.search("hello world") == [(4, "hello")]


def test_add_pattern_empty_ignored():
    ac = AhoCorasick()
    ac.add_pattern("")
    assert len(ac) == 0
    assert ac.patterns == ()
    ac2 = AhoCorasick(["", "a", ""])
    assert len(ac2) == 1
    assert ac2.patterns == ("a",)


def test_add_pattern_duplicate_ignored():
    ac = AhoCorasick()
    ac.add_pattern("bad")
    ac.add_pattern("bad")
    ac.add_pattern("bad")
    assert len(ac) == 1
    assert ac.patterns == ("bad",)
    result = ac.search("bad")
    assert result == [(2, "bad")]

    ac2 = AhoCorasick(["word", "word", "word", "bad", "word"])
    assert len(ac2) == 2
    assert set(ac2.patterns) == {"word", "bad"}
    assert ac2.search("word bad") == [(3, "word"), (7, "bad")]


def test_add_pattern_type_error():
    ac = AhoCorasick()
    with pytest.raises(TypeError):
        ac.add_pattern(123)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ac.add_pattern(None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ac.add_pattern(b"bytes")  # type: ignore[arg-type]


def test_add_pattern_invalidates_build():
    ac = AhoCorasick(["hello"])
    ac.build()
    assert ac._built is True
    ac.add_pattern("world")
    assert ac._built is False
    result = ac.search("hello world")
    assert (4, "hello") in result
    assert (10, "world") in result
    assert ac._built is True


def test_add_pattern_multiple_and_search():
    ac = AhoCorasick()
    for pat in ["he", "she", "his", "hers"]:
        ac.add_pattern(pat)
    ac.build()
    assert len(ac) == 4
    result = ac.search("ushers")
    assert (3, "she") in result
    assert (3, "he") in result
    assert (5, "hers") in result
    assert not any(p == "his" for _, p in result)


def test_build_idempotent():
    ac = AhoCorasick(["a", "ab", "bab"])
    ac.build()
    first_search = ac.search("abab")
    ac.build()
    ac.build()
    second_search = ac.search("abab")
    assert first_search == second_search
    assert ac._built is True


def test_build_empty_automaton():
    ac = AhoCorasick()
    ac.build()
    assert ac.search("anything") == []
    assert ac.search("") == []

    ac2 = AhoCorasick([])
    ac2.build()
    assert ac2.search("text") == []


def test_build_lazy_on_search():
    ac = AhoCorasick()
    ac.add_pattern("lazy")
    assert ac._built is False
    result = ac.search("lazy build")
    assert ac._built is True
    assert result == [(3, "lazy")]

    ac2 = AhoCorasick(["eager"])
    assert ac2._built is True


def test_search_basic_ascii():
    ac = AhoCorasick(["hello", "world"])
    result = ac.search("hello world, hello!")
    assert result == [(4, "hello"), (10, "world"), (17, "hello")]


def test_search_empty_text():
    ac = AhoCorasick(["a", "b"])
    assert ac.search("") == []


def test_search_empty_patterns():
    ac = AhoCorasick()
    assert ac.search("some text") == []
    ac2 = AhoCorasick([])
    assert ac2.search("some text") == []


def test_search_no_match():
    ac = AhoCorasick(["xyz", "abc"])
    assert ac.search("hello world") == []


def test_search_type_error():
    ac = AhoCorasick(["hello"])
    with pytest.raises(TypeError):
        ac.search(123)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ac.search(None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ac.search(b"bytes")  # type: ignore[arg-type]


def test_search_cyrillic_simple():
    ac = AhoCorasick(["привет", "мир"])
    result = ac.search("привет мир")
    assert result == [(5, "привет"), (9, "мир")]


def test_search_cyrillic_overlapping():
    ac = AhoCorasick(["мир", "ири", "привет"])
    result = ac.search("привет мир")
    assert (5, "привет") in result
    assert (9, "мир") in result


def test_search_cyrillic_case_sensitive():
    ac = AhoCorasick(["Привет"])
    assert ac.search("привет") == []
    assert ac.search("Привет") == [(5, "Привет")]


def test_search_cyrillic_mixed_with_latin():
    ac = AhoCorasick(["hello", "привет", "мир", "world"])
    text = "hello привет world мир"
    result = ac.search(text)
    assert (4, "hello") in result
    assert (11, "привет") in result
    assert (17, "world") in result
    assert (21, "мир") in result


def test_search_overlapping_classic():
    ac = AhoCorasick(["a", "ab", "bab", "bc", "bca", "c", "caa"])
    result = ac.search("abccab")
    assert (0, "a") in result
    assert (1, "ab") in result
    assert (2, "bc") in result
    assert (2, "c") in result
    assert (5, "ab") in result


def test_search_overlapping_prefix_chain():
    ac = AhoCorasick(["a", "aa", "aaa"])
    result = ac.search("aaaa")
    assert result == [
        (0, "a"),
        (1, "aa"), (1, "a"),
        (2, "aaa"), (2, "aa"), (2, "a"),
        (3, "aaa"), (3, "aa"), (3, "a"),
    ]


def test_search_overlapping_suffix_via_failure_links():
    ac = AhoCorasick(["he", "she", "hers", "his"])
    result = ac.search("ushers")
    assert result == [(3, "she"), (3, "he"), (5, "hers")]
    ac2 = AhoCorasick(["he", "she"])
    assert ac2.search("she") == [(2, "she"), (2, "he")]


def test_search_nested_patterns():
    ac = AhoCorasick(["abc", "bc", "c"])
    result = ac.search("abc")
    assert (2, "abc") in result
    assert (2, "bc") in result
    assert (2, "c") in result
    assert len(result) == 3


def test_search_unicode_emoji():
    ac = AhoCorasick(["😀", "😀😀", "🎉"])
    result = ac.search("hello 😀😀 world 🎉")
    assert any(p == "😀" for _, p in result)
    assert any(p == "😀😀" for _, p in result)
    assert any(p == "🎉" for _, p in result)
    ac2 = AhoCorasick(["😀", "😀😀"])
    assert ac2.search("😀😀") == [(0, "😀"), (1, "😀😀"), (1, "😀")]


def test_search_unicode_cjk():
    ac = AhoCorasick(["你好", "世界", "你好世界"])
    result = ac.search("你好世界")
    assert (1, "你好") in result
    assert (3, "世界") in result
    assert (3, "你好世界") in result


def test_search_unicode_mixed_scripts():
    ac = AhoCorasick(["привет", "hello", "😀", "你好"])
    text = "привет hello 😀 你好"
    result = ac.search(text)
    assert (5, "привет") in result
    assert (11, "hello") in result
    assert (13, "😀") in result
    assert (16, "你好") in result


def test_search_unicode_normalization_not_applied():
    ac = AhoCorasick(["café"])
    assert ac.search("café") == [(3, "café")]
    assert ac.search("café") == []

    ac2 = AhoCorasick(["café"])
    assert ac2.search("café") == [(4, "café")]
    assert ac2.search("café") == []


def test_search_complexity_linear():
    patterns = [f"pat{i:04d}" for i in range(500)]
    ac = AhoCorasick(patterns)
    ac.build()

    text_short = "x" * 10_000 + "pat0001" + "x" * 10_000
    text_long = "x" * 100_000 + "pat0001" + "x" * 100_000

    t0 = time.perf_counter()
    r_short = ac.search(text_short)
    t_short = time.perf_counter() - t0

    t0 = time.perf_counter()
    r_long = ac.search(text_long)
    t_long = time.perf_counter() - t0

    assert len(r_short) == 1
    assert len(r_long) == 1

    if t_short > 0.001:
        ratio = t_long / t_short
        assert ratio < 20, f"O(n) violation: ratio {ratio:.1f} >= 20 (t_short={t_short:.4f}, t_long={t_long:.4f})"

    ac2 = AhoCorasick(["a"])
    text_many = "a" * 50_000
    t0 = time.perf_counter()
    r_many = ac2.search(text_many)
    t_many = time.perf_counter() - t0
    assert len(r_many) == 50_000
    assert t_many < 1.0, f"too slow for O(n+z): {t_many:.3f}s for 50k matches"


def test_search_long_text_many_patterns():
    patterns = ["abc", "bcd", "cde", "def"]
    ac = AhoCorasick(patterns)
    text = "abcdef" * 1000
    result = ac.search(text)
    assert len(result) == 4 * 1000


def test_find_matches_module_level_basic():
    matches = find_matches("привет мир, привет!", ["привет", "мир"])
    assert len(matches) == 3
    assert matches[0] == Match(pattern="привет", start=0, end=5)
    assert matches[1] == Match(pattern="мир", start=7, end=9)
    assert matches[2] == Match(pattern="привет", start=12, end=17)
    for m in matches:
        assert m.span == (m.start, m.end + 1)
        assert m.matched_text == m.pattern


def test_find_matches_positions_correct():
    matches = find_matches("ushers", ["he", "she", "hers"])
    assert Match(pattern="she", start=1, end=3) in matches
    assert Match(pattern="he", start=2, end=3) in matches
    assert Match(pattern="hers", start=2, end=5) in matches
    text = "ushers"
    for m in matches:
        assert text[m.start : m.end + 1] == m.pattern


def test_find_matches_with_automaton():
    ac = AhoCorasick(["bad", "word"])
    ac.build()
    matches = find_matches("bad word bad", [], automaton=ac)
    assert len(matches) == 3
    assert matches[0].pattern == "bad"
    assert matches[0].start == 0
    assert matches[1].pattern == "word"
    assert matches[2].pattern == "bad"

    matches2 = find_matches("bad word", ["ignored"], automaton=ac)
    assert len(matches2) == 2


def test_find_matches_instance_method():
    ac = AhoCorasick(["мир", "привет"])
    matches = ac.find_matches("привет мир")
    assert matches == [
        Match(pattern="привет", start=0, end=5),
        Match(pattern="мир", start=7, end=9),
    ]
    matches2 = find_matches("привет мир", ["мир", "привет"])
    assert set((m.pattern, m.start, m.end) for m in matches) == set(
        (m.pattern, m.start, m.end) for m in matches2
    )


def test_find_matches_empty_and_duplicates():
    matches = find_matches("hello hello", ["", "hello", "hello", ""])
    assert len(matches) == 2
    assert all(m.pattern == "hello" for m in matches)

    assert find_matches("", ["hello"]) == []
    assert find_matches("hello", []) == []
    assert find_matches("hello", ["", ""]) == []


def test_find_matches_type_errors():
    with pytest.raises(TypeError):
        find_matches(123, ["hello"])  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        find_matches("hello", [123])  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        find_matches("hello", ["ok"], automaton="not automaton")  # type: ignore[arg-type]


def test_find_matches_overlapping():
    matches = find_matches("aaaa", ["a", "aa", "aaa"])
    assert len(matches) == 9
    text = "aaaa"
    for m in matches:
        assert text[m.start : m.end + 1] == m.pattern
        assert m.end - m.start + 1 == len(m.pattern)


def test_find_matches_unicode():
    matches = find_matches("hello 😀😀 world", ["😀", "😀😀"])
    assert len(matches) == 3
    text = "hello 😀😀 world"
    for m in matches:
        assert text[m.start : m.end + 1] == m.pattern


def test_search_iter_consistency():
    ac = AhoCorasick(["he", "she", "hers"])
    text = "ushers and she hers"
    assert list(ac.search_iter(text)) == ac.search(text)
    assert list(AhoCorasick().search_iter("text")) == []
    assert list(AhoCorasick(["a"]).search_iter("")) == []


def test_contains_len_patterns_repr():
    ac = AhoCorasick(["foo", "bar"])
    assert "foo" in ac
    assert "bar" in ac
    assert "baz" not in ac
    assert len(ac) == 2
    assert ac.patterns == ("foo", "bar")
    r = repr(ac)
    assert "AhoCorasick" in r
    assert "foo" in r

    ac_empty = AhoCorasick()
    assert len(ac_empty) == 0
    assert "anything" not in ac_empty


def test_search_single_char_patterns():
    ac = AhoCorasick(["a", "b", "c"])
    assert ac.search("abcabc") == [
        (0, "a"), (1, "b"), (2, "c"),
        (3, "a"), (4, "b"), (5, "c"),
    ]


def test_search_pattern_equals_text():
    ac = AhoCorasick(["exact"])
    assert ac.search("exact") == [(4, "exact")]
    assert ac.find_matches("exact") == [Match(pattern="exact", start=0, end=4)]


def test_search_special_characters():
    ac = AhoCorasick(["hello world", "foo-bar", "a.b"])
    assert ac.search("hello world foo-bar a.b") == [
        (10, "hello world"),
        (18, "foo-bar"),
        (22, "a.b"),
    ]
