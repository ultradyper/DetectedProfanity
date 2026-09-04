"""Lexicons for RU/EN/translit and allowlist."""

from __future__ import annotations

import re
from typing import Final

_WORD_BOUNDARY_LEFT: Final[str] = r"(?<![\wЀ-ӿ])"
_WORD_BOUNDARY_RIGHT: Final[str] = r"(?![\wЀ-ӿ])"


def _compile(forms: list[str]) -> list[re.Pattern[str]]:
    """Compile forms to \\b-anchored case-insensitive patterns."""
    patterns: list[re.Pattern[str]] = []
    for form in forms:
        pat = rf"{_WORD_BOUNDARY_LEFT}{re.escape(form)}{_WORD_BOUNDARY_RIGHT}"
        patterns.append(re.compile(pat, re.IGNORECASE | re.UNICODE))
    return patterns


def _normalize(token: str) -> str:
    """Lower, ё→е, strip surrounding punctuation."""
    t = token.strip().lower().replace("ё", "е").replace("Ё", "е")
    t = t.strip(" \t\n\r\"'.,!?;:()[]{}<>«»—–-…`")
    return t


ALL_RU_ROOTS: Final[list[str]] = [
    "хуй",
    "пизда",
    "пизд",
    "ебать",
    "еб",
    "блядь",
    "бляд",
    "сук",
    "суч",
    "пидор",
    "пидар",
    "муд",
    "говн",
    "гандон",
    "шлюх",
    "залуп",
    "манд",
    "дроч",
    "долбоеб",
    "еблан",
    "уеб",
    "хуесос",
    "пиздобол",
    "жоп",
    "срат",
    "сса",
    "сц",
    "перд",
    "бзд",
    "дрист",
    "хер",
    "хрен",
    "очк",
    "гом",
    "педик",
    "чмо",
    "шмар",
    "курв",
    "трах",
    "выбляд",
    "ублюд",
    "падл",
    "гнид",
    "твар",
    "мраз",
    "засран",
    "блуд",
    "шалав",
    "пох",
    "сука",
    "мудак",
    "говно",
    "шлюха",
    "залупа",
    "манда",
    "дрочить",
]

RU_FORMS: Final[list[str]] = [
    "хй",
    "хуй", "хуя", "хую", "хуем", "хуёв", "хуям", "хуями", "хуях",
    "хуи", "хуев", "хуёвый", "хуёво", "хуёвая", "хуйня", "хуйнёй", "хуйню", "хуйло", "хуила", "хуюшки", "хуина",
    "охуеть", "охуел", "охуела", "охуевший", "охуенно", "охуительно", "охуительный",
    "нахуй", "нахуя", "нахуячить",
    "похуй", "похуист", "похуизм", "похуистический",
    "дохуя", "нихуя", "нихуёво",
    "хуйнуть", "хуйнул", "захуярить", "отхуячить", "выхуячить", "прихуеть", "прихуел",
    "хуеплёт", "хуесос", "хуесосить", "хуесосина",
    "хуюшки", "хуярить", "хуячить",
    "пизда", "пизды", "пиздой", "пизду", "пизде", "пиздам", "пиздами",
    "пиздец", "пиздецово", "пиздецовый",
    "пиздеть", "пиздел", "пиздела", "пиздёж", "пиздеж", "пиздобол", "пиздоболка", "пиздоболить",
    "пиздюк", "пиздюлина", "пиздюля", "пиздючий",
    "распиздяй", "распиздяйский", "распиздеть", "распиздеться",
    "спиздить", "спиздил", "спиздила",
    "пиздатый", "пиздато", "пиздануть", "пизданутый", "пизданутая",
    "опизденеть", "опизденевший", "опиздошить", "опиздюлить",
    "пиздошить", "впиздить", "впиздячить", "упиздить",
    "ебать", "ебал", "ебала", "ебали", "ебало", "ебёт", "ебет", "ебут", "ебись",
    "ебаный", "ебаная", "ебаное", "ебанутый", "ебанутая", "ебануться", "ебанулся",
    "ебанько", "еблан", "ебланище", "ебланский",
    "ебло", "ебливый", "ебля", "ебальник",
    "заебать", "заебал", "заебала", "заебало", "заебись", "заебавший", "заебанный", "заебенить",
    "наебать", "наебал", "наебала", "наебщик", "наебщица", "наёбка", "наебка",
    "проебать", "проебал", "проебала", "проеб", "проебанный",
    "уебать", "уебал", "уебан", "уебок", "уебище", "уебавший", "уебашиться",
    "долбоеб", "долбоёб", "долбоебина", "долбоебский",
    "отъебать", "отъебал", "отъебись", "отъебаться",
    "выебать", "выебал", "выёбываться", "выебываться",
    "поебать", "поебень", "ебашить", "ебашил", "ебеня", "ебеневый", "ебенячий",
    "переебать", "недоебок",
    "бля", "блядь", "блять", "бляд", "блать", "блядина", "блядина", "блядский", "блядская", "блядство", "блядовать", "блядует",
    "блядник", "блядун", "блядунья",
    "выблядок", "проблядь", "блядовитый", "блядовать", "блядская",
    "сука", "суки", "суку", "сукой", "сучка", "сучонок", "сучий", "сучья", "сучара", "сучище", "сучата",
    "пидор", "пидоры", "пидорас", "пидорасы", "пидарас", "пидарасы", "пидорский", "пидорасина", "пидоровка", "пидрила", "пидрильный",
    "мудак", "мудаки", "мудила", "мудачье", "мудацкий", "мудачина", "мудаковатый",
    "говно", "говна", "говнюк", "говнючка", "говнище", "говняный", "говенный", "говноед", "говномес",
    "гандон", "гандоны", "гандонский", "гандошить",
    "шлюха", "шлюхи", "шлюшка", "шлюховатый", "шлюхан", "шлюшонка",
    "залупа", "залупы", "залупный", "залупенец", "залупить", "залупиться",
    "манда", "манды", "мандавошка", "мандавошечный", "мандяра", "мандеть",
    "дрочить", "дрочил", "дрочила", "дрочка", "задрочить", "надрочить", "дрочун", "дрочер",
    "жопа", "жопы", "жопный", "жопник", "жопошник", "жопорванец", "жопошница",
    "срать", "срал", "сраный", "сранец", "засранец", "засранный", "обосрать", "обосраться", "просрать", "насрать", "срач", "срачище",
    "ссать", "ссал", "ссанина", "ссаный", "обоссать", "обоссаться", "насцать",
    "пердеть", "пердел", "пердеж", "пердун", "пердёж",
    "бздеть", "бздун",
    "дристать", "дристун", "дристануть",
    "хер", "хера", "херня", "хернёй", "херню", "херовый", "херово", "похерить", "нахера", "нахер", "охеренный", "охереть",
    "хрен", "хрена", "хреновый", "хреново", "хреновина", "охренеть", "охреневший", "нахрен", "нахрена",
    "очко", "очковый", "очкошник",
    "гомик", "гомики",
    "педик", "педики", "педрила",
    "чмо", "чмошник", "чмошный", "чмошница",
    "шмара", "шмарина", "шмаровоз",
    "курва", "курвить", "курвящий",
    "трахать", "трахал", "трахнуть", "трахнул", "трахальщик", "траханье",
    "ублюдок", "ублюдки", "ублюдочный", "ублюдский",
    "падла", "падлы", "падлюка", "падлючий",
    "гнида", "гниды", "гнидный",
    "тварь", "твари", "тварына",
    "мразь", "мрази", "мразота", "мразотный",
    "шалаева", "шалава", "шалавный", "шалавье",
    "похабный", "похабщина", "похабник",
    "блудить", "блудливый",
]

_seen_ru: set[str] = set()
_dedup_ru: list[str] = []
for _w in RU_FORMS:
    _lw = _w.lower().replace("ё", "е")
    if _lw not in _seen_ru:
        _seen_ru.add(_lw)
        _dedup_ru.append(_w)
RU_FORMS = _dedup_ru  # type: ignore[no-redef]

EN_FORMS: Final[list[str]] = [
    "fuck", "fucks", "fucking", "fucked", "fucker", "fuckers",
    "fuckface", "fuckhead", "fuckwit", "fuckboy", "fucktard", "fuckhole",
    "fuckoff", "fuck-off", "fucked-up", "fuckup",
    "motherfucker", "motherfuckers", "motherfucking", "motherfuckin",
    "shit", "shits", "shitting", "shitted", "shitty", "shittiest",
    "shithead", "shitheads", "shithole", "shitholes", "shitface", "shitbag",
    "shitstorm", "shitshow", "shitload",
    "bullshit", "bullshits", "bullshitting", "bullshitted",
    "horseshit", "batshit", "dipshit", "dipshits",
    "ass", "asses",
    "asshole", "assholes", "asshat", "asshats", "assclown", "assclowns",
    "assfuck", "assfucker", "asswipe", "asswipes",
    "dumbass", "dumbasses", "jackass", "jackasses", "badass", "smartass", "lameass", "kissass",
    "bitch", "bitches", "bitching", "bitched", "bitchy", "bitchass",
    "son of a bitch", "sonofabitch",
    "cunt", "cunts", "cunty",
    "dick", "dicks", "dickhead", "dickheads", "dickface", "dickwad", "dickbag",
    "cock", "cocks", "cockhead", "cocksucker", "cocksuckers", "cockface", "cocksucking",
    "pussy", "pussies", "pussypower", "pussywhipped",
    "whore", "whores", "whorehouse", "whorehouses", "whoreish",
    "slut", "sluts", "slutty", "sluttiest", "slutbag", "slutbags", "slut-shaming",
    "fag", "fags", "faggot", "faggots", "faggoty", "faggy",
    "nigger", "niggers", "nigga", "niggas", "niglet",
    "coon", "coons", "chink", "chinks", "spic", "spics", "kike", "kikes",
    "gook", "gooks", "wop", "wops", "raghead", "ragheads",
    "bastard", "bastards",
    "bollocks", "bollocked",
    "wanker", "wankers", "wanking", "wank", "wanks",
    "jerkoff", "jerk-off", "jerkoffs",
    "douche", "douchebag", "douchebags", "douchey",
    "prick", "pricks", "pricky",
    "twat", "twats", "twatty",
    "arse", "arses", "arsehole", "arseholes",
    "tosser", "tossers",
    "bugger", "buggers", "buggery",
    "bloody hell",
    "damn", "damned", "goddamn", "goddamned", "damnit", "dammit",
    "retard", "retards", "retarded", "tard",
    "moron", "morons", "moronic",
    "dildo", "dildos",
    "jizz", "jizzed", "cumshot", "cumshots",
    "tit", "tits", "titties", "titfuck",
    "boob", "boobs", "booby",
    "wop", "heeb",
    "nonce", "nonces",
]

_seen_en: set[str] = set()
_dedup_en: list[str] = []
for _w in EN_FORMS:
    _lw = _w.lower()
    if _lw not in _seen_en:
        _seen_en.add(_lw)
        _dedup_en.append(_w)
EN_FORMS = _dedup_en  # type: ignore[no-redef]

TRANSLIT_FORMS: Final[list[str]] = [
    "hui", "huy", "huii", "khui", "khuy", "hyi", "hooy",
    "huya", "huyu", "huem", "huevyi", "huinia", "huilo", "huila",
    "ohuelt", "ohuel", "ohueno", "ohuitelno",
    "nahui", "nahuya", "nahuyachit",
    "pohui", "pohuist", "pohuizm", "pohuisticheskii",
    "dohuya", "nihuya", "nihuia",
    "huinut", "zahu-yarit", "zakhuyarit", "othuyachit", "vyhuyachit",
    "huesos", "huesosit", "huarit", "huyarit",
    "pizda", "pizdy", "pizdoi", "pizdu", "pizde",
    "pizdec", "pizdets", "pizdetsovo",
    "pizdet", "pizdel", "pizdiоzh", "pizdezh", "pizdobol", "pizdobolka",
    "pizdyuk", "pizdyulina", "pizdyuchii",
    "raspizdyai", "raspizdyaiskii",
    "spizdit", "spizdil", "pizdatyi", "pizdato", "pizdanut", "pizdanutyi",
    "opizdenet", "opizdenevshii", "vpizdit", "upizdit",
    "ebat", "yebat", "ebal", "yebal", "ebala", "ebalo", "ebyot", "ebet",
    "ebanyi", "yebanyi", "ebanuty", "yebanuty", "ebanutsya", "ebanko",
    "eblan", "yeblan", "eblo", "eblya",
    "zaebat", "zayebat", "zaebal", "zaebis", "zayebis", "zaebalo", "zaebannyi",
    "naebat", "nayebat", "naebal", "naebshik", "nayobka", "nayobshik",
    "proebat", "proyebat", "proebal", "proeb",
    "uebat", "uyebat", "ueban", "uyeban", "uebok", "uyebok", "uebishche",
    "dolboeb", "dolboyob", "dolboebina",
    "otyebat", "otebat", "otebis", "otyebis",
    "vyebat", "vyebal", "vyebyvatsya", "vyobivatsya",
    "poebat", "poeben", "ebashit", "yebashit", "yebenya",
    "blyad", "blyat", "blyadina", "blyadskii", "blyadstvo", "blyadovat", "blyadnik", "blyadun",
    "vyblyadok", "problyad", "blya", "blyaha",
    "suka", "suchka", "suchonok", "suchii", "suchara", "suchishche",
    "pidor", "pidoras", "pidaras", "pidar", "pidoraskii", "pidorasina", "pidrila",
    "mudak", "mudila", "mudache", "mudatskii",
    "govno", "govnyuk", "govnishche", "govnyanyi", "govnoed",
    "gandon", "gandonskii",
    "shlyuha", "shliuha", "shlyushka", "shlyukha", "shlyuha",
    "zalupa", "zalupnyi", "zalupenets", "zalupit",
    "manda", "mandavoshka", "mandyara",
    "drochit", "drochila", "drochka", "zadrochit", "nadrochit",
    "zhopa", "zhopy", "zhopnyi", "zhopnik", "zhoposhnik",
    "srat", "sranyi", "sranets", "zasranec", "zasranets", "obosrat", "prosrat", "srach",
    "ssat", "ssal", "ssanina", "obossat",
    "perdet", "perdezh", "perdun",
    "bzdet", "bzdet", "bzdun",
    "dristat", "dristun",
    "her", "hernya", "herovyi", "poherit", "naher", "oherennyi", "oheret",
    "hren", "hrenovyi", "hrenovina", "ohrenet", "nahren",
    "ochko", "ochkovyi",
    "gomik", "pedik", "pedrila",
    "chmo", "chmoshnik", "chmoshnyi",
    "shmara", "kurva", "kurvit",
    "trahat", "trahnut", "trahalshchik",
    "ublyudok", "padla", "padlyuka", "gnida", "tvar", "mraz", "mrazota",
    "shalava", "pohabnyi", "bludit",
]

_seen_tr: set[str] = set()
_dedup_tr: list[str] = []
for _w in TRANSLIT_FORMS:
    _lw = _w.lower().replace("-", "")
    if _lw not in _seen_tr:
        _seen_tr.add(_lw)
        _dedup_tr.append(_w.replace("-", ""))
TRANSLIT_FORMS = _dedup_tr  # type: ignore[no-redef]

RU_PATTERNS: Final[list[re.Pattern[str]]] = _compile(RU_FORMS)
EN_PATTERNS: Final[list[re.Pattern[str]]] = _compile(EN_FORMS)
TRANSLIT_PATTERNS: Final[list[re.Pattern[str]]] = _compile(TRANSLIT_FORMS)

ALLOWLIST: Final[set[str]] = {
    "мандарин", "мандарина", "мандарины", "мандаринка", "мандаринки",
    "мандаринчик", "мандаринчиковый", "мандариновый", "мандариновка", "мандариновый",
    "мандат", "мандата", "мандаты", "мандатный", "мандатник", "мандатка",
    "мандатность",
    "команда", "команды", "командный", "командовать", "командующий", "командование",
    "командор", "командос", "командир", "командировка", "командование",
    "мандамус",
    "художник", "художника", "художники", "художница", "художниц",
    "художественный", "художественно", "художественность", "художество", "художеств",
    "художества", "художнический",
    "худощавый", "худощавость",
    "страхование", "страховать", "подстраховать", "перестраховать",
    "бляшка", "бляшки", "бляшечный",
    "блок", "блока", "блоку", "блоком", "блоке", "блоки", "блоков", "блочный", "блочная", "блочно",
    "бланк", "бланка", "бланку", "бланком", "бланке", "бланки", "бланков", "бланковый",
    "блоха", "блохи", "блохой", "блошиный", "блошка", "блошки",
    "облако", "облака", "облаков", "облачный", "облачность",
    "табло", "таблоид", "таблетка", "таблетки",
    "шаблон", "шаблона", "шаблоны", "шаблонный",
    "пистолет", "пистолеты", "пистолетный",
    "эксплуатация", "эксплуатировать",
    "сучок", "сучки", "сучками",
    "шлюпка", "шлюпки", "шлюпочный",
    "мандрагора", "мандрагоры",
    "assassin", "assassins", "assassinate", "assassinated", "assassination",
    "assistant", "assistants", "assistance", "assisting", "associate", "associates",
    "association", "associations", "associative",
    "assuage", "assuaged",
    "classic", "classics", "classical", "classically", "classification", "classify", "classified",
    "bass", "basses", "bassline", "embarrass", "embarrassed", "embarrassing", "embarrassment",
    "embassy", "embassies",
    "pass", "passes", "passage", "passages", "passenger", "passengers", "compass", "encompass",
    "mass", "masses", "massive", "massacre", "amass", "amassed",
    "grass", "grasses", "glass", "glasses", "classroom", "classrooms",
    "assault", "assaulted", "assignment", "assignments",
    "assorted", "assortment",
    "are", "her", "other", "there", "here", "where", "whether", "however", "when", "then", "them", "they",
    "site", "sites", "click", "its", "like", "price", "prices", "state", "music", "them", "then", "good", "books", "years", "book",
    "county", "think", "title", "class", "standard", "problem", "china", "problems", "once", "topics", "thanks", "are", "other",
    "are", "her", "site", "there", "here", "price", "state", "music", "them", "her", "then", "good", "where", "books", "years", "book",
    "management", "county", "think", "title", "class", "visit", "card", "sale", "stock", "sales", "look", "start", "human", "yahoo", "topic",
    "standard", "below", "blog", "problem", "rates", "hard", "china", "star", "areas", "cards", "problems", "share", "until", "once", "cars",
    "rock", "topics", "fast", "meet", "watch", "bank", "thanks", "deals", "construction", "manager", "cases", "quick", "none", "basic", "death", "standards", "base",
    "price", "prices", "county", "title", "class", "standard", "problem", "china", "thanks", "other", "there", "here", "where",
    "great", "real", "ebay", "area", "want", "black", "case", "care", "three", "water", "board", "white", "rate", "sale", "stock", "sales", "look", "start", "human", "yahoo", "topic", "standard", "below", "blog", "hard", "china", "star", "areas", "cards", "share", "until", "once", "cars", "rock", "topics", "fast", "meet", "watch", "bank", "thanks", "deals", "construction", "manager", "cases", "quick", "none", "basic", "death", "standards", "base",
    "hello", "hellos", "world", "worlds", "word", "words", "wording", "worldwide",
    "cocktail", "cocktails", "cockpit", "cockpits", "cockatoo", "peacock", "peacocks",
    "cockroach", "cockroaches", "cocker", "cockers", "cockney",
    "shiitake", "shiitakes",
    "fagot", "fagots", "fagotto",
}

_ALLOWLIST_NORM: Final[set[str]] = {_normalize(w) for w in ALLOWLIST}

__all__ = [
    "ALL_RU_ROOTS",
    "RU_FORMS",
    "EN_FORMS",
    "TRANSLIT_FORMS",
    "RU_PATTERNS",
    "EN_PATTERNS",
    "TRANSLIT_PATTERNS",
    "ALLOWLIST",
    "get_patterns",
    "is_allowed",
]


def is_allowed(token: str) -> bool:
    """Return True if token is in the allowlist (prefix-aware)."""
    if not token:
        return False
    norm = _normalize(token)
    if not norm:
        return False
    if norm in _ALLOWLIST_NORM:
        return True
    for allow in _ALLOWLIST_NORM:
        if len(allow) >= 4 and norm.startswith(allow):
            if len(norm) > len(allow):
                return True
    return False


def get_patterns(
    lang: str | None = None,
    *,
    include_translit: bool = True,
) -> list[re.Pattern[str]] | dict[str, list[re.Pattern[str]]]:
    """Return compiled patterns for the given language."""
    if lang is not None:
        lang = lang.strip().lower()

    if lang == "ru":
        if include_translit:
            return RU_PATTERNS + TRANSLIT_PATTERNS
        return list(RU_PATTERNS)

    if lang == "en":
        return list(EN_PATTERNS)

    if lang == "translit":
        return list(TRANSLIT_PATTERNS)

    if lang == "all" or lang is None:
        return {
            "ru": list(RU_PATTERNS),
            "en": list(EN_PATTERNS),
            "translit": list(TRANSLIT_PATTERNS),
        }

    raise ValueError(f"unknown lang={lang!r}, expected ru/en/translit/all/None")


assert len(ALL_RU_ROOTS) >= 40, f"ALL_RU_ROOTS={len(ALL_RU_ROOTS)} < 40"
assert len(RU_FORMS) >= 150, f"RU_FORMS={len(RU_FORMS)} < 150"
assert len(EN_FORMS) >= 30, f"EN_FORMS={len(EN_FORMS)} < 30"
assert len(TRANSLIT_FORMS) >= 30, f"TRANSLIT_FORMS={len(TRANSLIT_FORMS)} < 30"
assert "мандарин" in ALLOWLIST
assert "художник" in ALLOWLIST
