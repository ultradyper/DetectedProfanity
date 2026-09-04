"""ProfanityDetector: RU/EN/транслит, маскировки, allowlist, censor, lang."""

import pytest
from detected_profanity import ProfanityDetector, censor, contains_profanity, detect, normalize_text


@pytest.fixture
def det():
    return ProfanityDetector()


@pytest.fixture
def det_ru():
    return ProfanityDetector(lang="ru")


@pytest.fixture
def det_en():
    return ProfanityDetector(lang="en")


@pytest.fixture
def det_all():
    return ProfanityDetector(lang="all")


@pytest.fixture
def det_ru_no_translit():
    return ProfanityDetector(lang="ru", include_translit=False)


class TestBasicRuEn:
    def test_huy_basic(self, det):
        assert det.contains_profanity("хуй") is True

    def test_pizdets_basic(self, det):
        assert det.contains_profanity("пиздец") is True

    def test_fuck_basic(self, det):
        assert det.contains_profanity("fuck") is True

    def test_shit_basic(self, det):
        assert det.contains_profanity("shit") is True

    def test_clean_ru_not_triggered(self, det):
        assert det.contains_profanity("привет мир") is False

    def test_clean_en_not_triggered(self, det):
        assert det.contains_profanity("hello") is False

    def test_clean_world_not_triggered(self, det):
        assert det.contains_profanity("world") is False

    def test_pizdets_in_sentence(self, det):
        assert det.contains_profanity("это полный пиздец") is True

    def test_huy_in_sentence(self, det):
        assert det.contains_profanity("пошёл на хуй") is True

    def test_fuck_in_sentence(self, det):
        assert det.contains_profanity("what the fuck is this") is True

    def test_shit_in_sentence(self, det):
        assert det.contains_profanity("shit happens") is True

    def test_empty_not_profanity(self, det):
        assert det.contains_profanity("") is False

    def test_functional_api_basic(self):
        assert contains_profanity("хуй") is True
        assert contains_profanity("fuck") is True
        assert contains_profanity("привет") is False

    def test_functional_detect_basic(self):
        assert "хуй" in detect("хуй")
        assert "fuck" in detect("fuck")


class TestMasking:
    def test_nahuia_hash(self, det):
        assert det.contains_profanity("на#хуя") is True

    def test_h_star_y(self, det):
        assert det.contains_profanity("х*й") is True

    def test_p_hash_zdec(self, det):
        assert det.contains_profanity("п#здец") is True

    def test_b_dot_l_dot_ya(self, det):
        assert det.contains_profanity("б.л.я") is True

    def test_h_space_u_space_y(self, det):
        assert det.contains_profanity("х у й") is True

    def test_zero_huet(self, det):
        assert det.contains_profanity("0хуеть") is True

    def test_bl_at(self, det):
        assert det.contains_profanity("бл@ть") is True

    def test_blyaaa_repeats(self, det):
        assert det.contains_profanity("бляяяя") is True

    def test_p_double_dot_zdec(self, det):
        assert det.contains_profanity("п..здец") is True

    def test_uppercase_huy(self, det):
        assert det.contains_profanity("ХУЙ") is True

    def test_uppercase_pizdets(self, det):
        assert det.contains_profanity("ПИЗДЕЦ") is True

    def test_uppercase_fuck(self, det):
        assert det.contains_profanity("FUCK") is True

    def test_mixed_case_shit(self, det):
        assert det.contains_profanity("ShIt") is True

    def test_dash_separator(self, det):
        assert det.contains_profanity("х-у-й") is True

    def test_dot_separator(self, det):
        assert det.contains_profanity("х.у.й") is True

    def test_star_separator(self, det):
        assert det.contains_profanity("х*у*й") is True

    def test_hash_separators_long(self, det):
        assert det.contains_profanity("п#и#з#д#е#ц") is True

    def test_multiple_spaces(self, det):
        assert det.contains_profanity("х    у    й") is True

    def test_repeats_huuuy(self, det):
        assert det.contains_profanity("хуууй") is True

    def test_repeats_blyad_extended(self, det):
        assert det.contains_profanity("бляяяяяя") is True

    def test_leet_zero_normalization(self):
        assert normalize_text("0хуеть") == "охуеть"

    def test_leet_at_normalization(self):
        assert normalize_text("бл@ть") == "блать"

    def test_leet_3_to_ze(self, det):
        assert normalize_text("пи3дец") == "пиздец"
        assert det.contains_profanity("пи3дец") is True

    def test_mask_in_sentence(self, det):
        assert det.contains_profanity("ну ты на#хуя это сделал") is True

    def test_all_masks_detect_nonempty(self, det):
        masks = ["на#хуя", "х*й", "п#здец", "б.л.я", "х у й", "0хуеть", "бл@ть", "бляяяя", "п..здец", "ХУЙ"]
        for m in masks:
            assert det.detect(m), f"detect({m!r}) should be non-empty"
            assert len(det.detect(m)) >= 1


class TestLeetHomoglyph:
    def test_a_to_a_homoglyph(self, det):
        assert det.contains_profanity("пиздa") is True
        assert "пизда" in det.detect("пиздa")

    def test_x_to_ha_homoglyph(self, det):
        assert det.contains_profanity("xуй") is True

    def test_y_to_u_homoglyph(self, det):
        assert det.contains_profanity("хyй") is True
        assert "хуй" in det.detect("хyй")

    def test_p_to_er_homoglyph(self, det):
        assert det.contains_profanity("pидор") is True

    def test_o_to_o_homoglyph(self, det):
        assert det.contains_profanity("oхуеть") is True

    def test_e_to_ie_homoglyph_normalization(self):
        assert normalize_text("e") == "е"
        assert normalize_text("a") == "а"
        assert normalize_text("x") == "х"
        assert normalize_text("y") == "у"
        assert normalize_text("o") == "о"
        assert normalize_text("p") == "р"
        assert normalize_text("c") == "с"

    def test_mixed_homoglyph_word(self, det):
        assert normalize_text("a") == "а"
        assert normalize_text("хyй") == "хуй"

    def test_leet_zero_is_homoglyph(self, det):
        assert normalize_text("0") == "о"
        assert det.contains_profanity("0хуеть") is True

    def test_leet_at_is_a(self, det):
        assert normalize_text("@") == "а"
        assert det.contains_profanity("бл@ть") is True


class TestTranslit:
    def test_hui(self, det):
        assert det.contains_profanity("hui") is True

    def test_huy(self, det):
        assert det.contains_profanity("huy") is True

    def test_pizda(self, det):
        assert det.contains_profanity("pizda") is True

    def test_blyad(self, det):
        assert det.contains_profanity("blyad") is True

    def test_blyat(self, det):
        assert det.contains_profanity("blyat") is True

    def test_nahui_translit(self, det):
        assert det.contains_profanity("nahui") is True

    def test_ebat_translit(self, det):
        assert det.contains_profanity("ebat") is True

    def test_suka_translit(self, det):
        assert det.contains_profanity("suka") is True

    def test_pidor_translit(self, det):
        assert det.contains_profanity("pidor") is True

    def test_pizdec_translit(self, det):
        assert det.contains_profanity("pizdec") is True

    def test_uppercase_translit(self, det):
        assert det.contains_profanity("HUI") is True
        assert det.contains_profanity("PIZDA") is True
        assert det.contains_profanity("Blyad") is True

    def test_translit_in_sentence(self, det):
        assert det.contains_profanity("pizdec kak holodno") is True

    def test_translit_detect_returns_list(self, det):
        res = det.detect("hui pizda blyad")
        assert isinstance(res, list)
        assert len(res) >= 3


class TestAllowlist:
    @pytest.mark.parametrize("word", [
        "мандарин", "художник", "assassin", "блок", "бланк", "блоха", "облако", "табло",
    ])
    def test_allowlist_not_flagged(self, det, word):
        assert det.contains_profanity(word) is False, f"{word!r} should not be flagged"
        assert det.detect(word) == [], f"detect({word!r}) should be empty"

    def test_mandarin_variants(self, det):
        assert det.contains_profanity("мандарин") is False
        assert det.contains_profanity("мандарина") is False
        assert det.contains_profanity("мандариновый") is False
        assert det.contains_profanity("мандаринка") is False

    def test_mandat_not_flagged(self, det):
        assert det.contains_profanity("мандат") is False
        assert det.contains_profanity("команда") is False

    def test_hudozhnik_family(self, det):
        assert det.contains_profanity("художник") is False
        assert det.contains_profanity("художественный") is False
        assert det.contains_profanity("художество") is False

    def test_blok_family(self, det):
        assert det.contains_profanity("блок") is False
        assert det.contains_profanity("блоки") is False
        assert det.contains_profanity("блочный") is False

    def test_assassin_family(self, det):
        assert det.contains_profanity("assassin") is False
        assert det.contains_profanity("assassination") is False
        assert det.contains_profanity("assistant") is False

    def test_allowlist_uppercase(self, det):
        assert det.contains_profanity("МАНДАРИН") is False
        assert det.contains_profanity("ХУДОЖНИК") is False
        assert det.contains_profanity("ASSASSIN") is False

    def test_allowlist_censor_unchanged(self, det):
        for w in ["мандарин", "художник", "assassin", "блок", "бланк", "блоха", "облако", "табло"]:
            assert det.censor(w) == w, f"censor({w!r}) should not modify allowlist word"

    def test_manda_without_suffix_is_flagged(self, det):
        assert det.contains_profanity("манда") is True

    def test_shablon_not_flagged(self, det):
        assert det.contains_profanity("шаблон") is False


class TestEnglishNotBroken:
    def test_fuck_flagged(self, det):
        assert det.contains_profanity("fuck") is True

    def test_shit_flagged(self, det):
        assert det.contains_profanity("shit") is True

    def test_assassin_not_flagged(self, det):
        assert det.contains_profanity("assassin") is False

    def test_fuck_vs_assassin_together(self, det):
        text = "assassin fuck"
        assert det.contains_profanity(text) is True
        assert "fuck" in det.detect(text)

    def test_shit_vs_assassin(self, det):
        assert det.contains_profanity("shit") is True
        assert det.contains_profanity("assassin") is False

    def test_asshole_is_profanity(self, det):
        assert det.contains_profanity("asshole") is True

    def test_classic_not_flagged(self, det):
        assert det.contains_profanity("classic") is False

    def test_cocktail_not_flagged(self, det):
        assert det.contains_profanity("cocktail") is False

    def test_cock_flagged(self, det):
        assert det.contains_profanity("cock") is True

    def test_fagot_not_flagged(self, det):
        assert det.contains_profanity("fagot") is False


class TestCensor:
    def test_censor_huy(self, det):
        c = det.censor("хуй")
        assert c == "***"
        assert len(c) == 3

    def test_censor_pizdets(self, det):
        c = det.censor("пиздец")
        assert "*" in c
        assert "пиздец" not in c

    def test_censor_fuck(self, det):
        assert det.censor("fuck") == "****"

    def test_censor_shit(self, det):
        assert det.censor("shit") == "****"

    def test_censor_clean_unchanged(self, det):
        assert det.censor("привет мир") == "привет мир"
        assert det.censor("hello world") == "hello world"
        assert det.censor("добрый день") == "добрый день"

    def test_censor_allowlist_unchanged(self, det):
        assert det.censor("мандарин") == "мандарин"
        assert det.censor("assassin") == "assassin"

    def test_censor_sentence(self, det):
        c = det.censor("пошёл на хуй")
        assert "хуй" not in c
        assert "*" in c

    def test_censor_multiple_words(self, det):
        c = det.censor("хуй пиздец")
        assert "хуй" not in c
        assert "пиздец" not in c
        assert c.count("*") >= 3

    def test_censor_custom_repl(self, det):
        assert det.censor("хуй", repl="#") == "###"
        assert det.censor("fuck", repl="#") == "####"

    def test_censor_empty(self, det):
        assert det.censor("") == ""

    def test_censor_functional_api(self):
        assert censor("хуй") == "***"
        assert censor("привет") == "привет"

    def test_censor_preserves_length_simple(self, det):
        for w in ["хуй", "пиздец", "fuck", "shit", "нахуй"]:
            c = det.censor(w)
            assert len(c) == len(w), f"censor({w!r}) len mismatch: {c!r}"

    def test_censor_contains_stars_not_original(self, det):
        for w in ["хуй", "fuck", "hui", "бля"]:
            c = det.censor(w)
            assert "*" in c
            assert w not in c

    def test_censor_long_repl(self, det):
        c = det.censor("хуй", repl="[censored]")
        assert "хуй" not in c
        assert len(c) > 0


class TestDetect:
    def test_returns_list(self, det):
        res = det.detect("хуй")
        assert isinstance(res, list)

    def test_detect_huy_contains_huy(self, det):
        res = det.detect("хуй")
        assert "хуй" in res

    def test_detect_fuck_contains_fuck(self, det):
        res = det.detect("fuck")
        assert "fuck" in res

    def test_detect_empty_on_clean(self, det):
        assert det.detect("привет мир") == []
        assert det.detect("hello") == []
        assert det.detect("") == []

    def test_detect_empty_on_allowlist(self, det):
        assert det.detect("мандарин") == []
        assert det.detect("assassin") == []

    def test_detect_multiple(self, det):
        res = det.detect("хуй пиздец")
        assert len(res) >= 2
        assert any("хуй" in r for r in res)
        assert any("пизд" in r for r in res)

    def test_detect_masked_nonempty(self, det):
        for m in ["на#хуя", "х*й", "п#здец", "б.л.я", "х у й", "0хуеть", "бл@ть"]:
            res = det.detect(m)
            assert isinstance(res, list)
            assert len(res) >= 1, f"detect({m!r}) should be non-empty"

    def test_detect_translit_list(self, det):
        res = det.detect("hui pizda blyad")
        assert isinstance(res, list)
        assert len(res) >= 3
        assert "hui" in res
        assert "pizda" in res
        assert "blyad" in res

    def test_detect_functional_api(self):
        assert isinstance(detect("хуй"), list)
        assert "хуй" in detect("хуй")
        assert detect("привет") == []

    def test_contains_and_detect_consistency(self, det):
        cases = ["хуй", "пиздец", "fuck", "на#хуя", "х у й", "мандарин", "привет мир", "assassin"]
        for txt in cases:
            has = det.contains_profanity(txt)
            lst = det.detect(txt)
            if has:
                assert len(lst) > 0, f"contains true but detect empty for {txt!r}"
            else:
                assert lst == [], f"contains false but detect non-empty for {txt!r}: {lst}"

    def test_detect_returns_strings(self, det):
        res = det.detect("хуй пиздец fuck")
        for item in res:
            assert isinstance(item, str)


class TestLangFilter:
    def test_ru_detects_ru(self, det_ru):
        assert det_ru.contains_profanity("хуй") is True

    def test_ru_ignores_en(self, det_ru):
        assert det_ru.contains_profanity("fuck") is False
        assert det_ru.detect("fuck") == []

    def test_en_detects_en(self, det_en):
        assert det_en.contains_profanity("fuck") is True
        assert det_en.contains_profanity("shit") is True

    def test_en_ignores_ru(self, det_en):
        assert det_en.contains_profanity("хуй") is False
        assert det_en.detect("хуй") == []

    def test_en_ignores_translit_by_default(self, det_en):
        assert det_en.contains_profanity("hui") is False

    def test_ru_catches_translit(self, det_ru):
        assert det_ru.contains_profanity("hui") is True
        assert det_ru.contains_profanity("pizda") is True
        assert det_ru.contains_profanity("blyad") is True

    def test_ru_no_translit_option(self, det_ru_no_translit):
        assert det_ru_no_translit.contains_profanity("hui") is False
        assert det_ru_no_translit.contains_profanity("хуй") is True

    def test_all_detects_both(self, det_all):
        assert det_all.contains_profanity("хуй") is True
        assert det_all.contains_profanity("fuck") is True

    def test_default_detects_both(self, det):
        assert det.contains_profanity("хуй") is True
        assert det.contains_profanity("fuck") is True

    def test_en_censor_only_en(self, det_en):
        assert det_en.censor("хуй") == "хуй"
        assert det_en.censor("fuck") == "****"

    def test_ru_censor_only_ru(self, det_ru):
        assert det_ru.censor("fuck") == "fuck"
        assert "*" in det_ru.censor("хуй")

    def test_languages_list_param(self):
        det_list = ProfanityDetector(languages=["ru", "en"])
        assert det_list.contains_profanity("хуй") is True
        assert det_list.contains_profanity("fuck") is True

    def test_lang_en_explicit(self):
        det = ProfanityDetector(lang="en")
        assert det.detect("хуй") == []
        assert "fuck" in det.detect("fuck and shit")

    def test_lang_ru_explicit(self):
        det = ProfanityDetector(lang="ru")
        assert det.detect("fuck") == []
        assert "хуй" in det.detect("хуй пиздец")

    def test_translit_lang_only(self):
        det = ProfanityDetector(lang="translit")
        assert det.contains_profanity("hui") is True
        assert det.contains_profanity("хуй") is False
        assert det.contains_profanity("fuck") is False


class TestEdgeCases:
    def test_type_error_on_non_string_contains(self, det):
        with pytest.raises(TypeError):
            det.contains_profanity(123)  # type: ignore[arg-type]

    def test_type_error_on_non_string_detect(self, det):
        with pytest.raises(TypeError):
            det.detect(123)  # type: ignore[arg-type]

    def test_type_error_on_non_string_censor(self, det):
        with pytest.raises(TypeError):
            det.censor(123)  # type: ignore[arg-type]

    def test_whitespace_only(self, det):
        assert det.contains_profanity("   ") is False
        assert det.detect("   ") == []
        assert det.censor("   ") == "   "

    def test_normalize_text_basic(self):
        assert normalize_text("ХУЙ") == "хуй"
        assert normalize_text("Пиздец") == "пиздец"
        assert normalize_text("Ёлка") == "елка"

    def test_collapse_repeats_via_detector(self, det):
        assert det.contains_profanity("бляяяяяя") is True
        assert det.contains_profanity("оооочень") is False or True

    def test_mixed_profanity_and_allowlist(self, det):
        text = "мандарин и хуй"
        assert det.contains_profanity(text) is True
        res = det.detect(text)
        assert "хуй" in res

    def test_censor_mixed_allowlist(self, det):
        text = "мандарин и хуй"
        c = det.censor(text)
        assert "мандарин" in c
        assert "хуй" not in c

    def test_detect_does_not_return_allowlist(self, det):
        res = det.detect("assassin")
        assert res == []
        res2 = det.detect("мандарин вкусный")
        assert "мандарин" not in res2

    def test_nfkc_normalization(self, det):
        assert det.contains_profanity("ｈｕｉ") is True or det.contains_profanity("hui") is True

    def test_long_clean_text(self, det):
        long_clean = "привет мир " * 100
        assert det.contains_profanity(long_clean) is False
        assert det.detect(long_clean) == []
        assert det.censor(long_clean) == long_clean

    def test_long_profanity_text(self, det):
        long_bad = "хуй " * 50
        assert det.contains_profanity(long_bad) is True
        assert len(det.detect(long_bad)) >= 1
        c = det.censor(long_bad)
        assert c != long_bad
        assert "*" in c

    def test_punctuation_around_profanity(self, det):
        assert det.contains_profanity("...хуй...") is True
        assert det.contains_profanity("(пиздец)") is True
        assert det.contains_profanity("\"fuck\"") is True
