"""Числа по-русски: количественные с родом, порядковые с родом и падежом, дроби.

Падежи количественных числительных не склоняются (только именительный),
этого хватает для коротких ответов ассистента. Порядковые склоняются
в нужных для дат, годов и суффиксов падежах.
"""

from __future__ import annotations

UNITS_M = ["ноль", "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
UNITS_F = ["ноль", "одна", "две", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
UNITS_N = ["ноль", "одно", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
TEENS = ["десять", "одиннадцать", "двенадцать", "тринадцать", "четырнадцать", "пятнадцать", "шестнадцать",
         "семнадцать", "восемнадцать", "девятнадцать"]
TENS = ["", "", "двадцать", "тридцать", "сорок", "пятьдесят", "шестьдесят", "семьдесят", "восемьдесят", "девяносто"]
HUNDREDS = ["", "сто", "двести", "триста", "четыреста", "пятьсот", "шестьсот", "семьсот", "восемьсот", "девятьсот"]

SCALES = [  # (значение, формы, род)
    (10**9, ("миллиард", "миллиарда", "миллиардов"), "m"),
    (10**6, ("миллион", "миллиона", "миллионов"), "m"),
    (10**3, ("тысяча", "тысячи", "тысяч"), "f"),
]


def plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def _below_1000(n: int, gender: str) -> list[str]:
    words: list[str] = []
    h, rest = divmod(n, 100)
    if h:
        words.append(HUNDREDS[h])
    if 10 <= rest < 20:
        words.append(TEENS[rest - 10])
    else:
        t, u = divmod(rest, 10)
        if t:
            words.append(TENS[t])
        if u:
            words.append({"f": UNITS_F, "n": UNITS_N}.get(gender, UNITS_M)[u])
    return words


def cardinal(n: int, gender: str = "m") -> str:
    if n == 0:
        return "ноль"
    if n < 0:
        return "минус " + cardinal(-n, gender)
    words: list[str] = []
    rest = n
    for value, forms, g in SCALES:
        count, rest = divmod(rest, value)
        if count:
            words += _below_1000(count, g)
            words.append(plural(count, *forms))
    if rest:
        words += _below_1000(rest, gender)
    return " ".join(words)


# Порядковые: основа и тип окончаний. A: -ый, B: -ой (ударное), C: третий.
ORD_SMALL = {
    1: ("перв", "A"), 2: ("втор", "B"), 3: ("трет", "C"), 4: ("четвёрт", "A"), 5: ("пят", "A"),
    6: ("шест", "B"), 7: ("седьм", "B"), 8: ("восьм", "B"), 9: ("девят", "A"), 10: ("десят", "A"),
    11: ("одиннадцат", "A"), 12: ("двенадцат", "A"), 13: ("тринадцат", "A"), 14: ("четырнадцат", "A"),
    15: ("пятнадцат", "A"), 16: ("шестнадцат", "A"), 17: ("семнадцат", "A"), 18: ("восемнадцат", "A"),
    19: ("девятнадцат", "A"),
}
ORD_TENS = {
    2: ("двадцат", "A"), 3: ("тридцат", "A"), 4: ("сороков", "B"), 5: ("пятидесят", "A"), 6: ("шестидесят", "A"),
    7: ("семидесят", "A"), 8: ("восьмидесят", "A"), 9: ("девяност", "A"),
}
ORD_HUNDREDS = {
    1: ("сот", "A"), 2: ("двухсот", "A"), 3: ("трёхсот", "A"), 4: ("четырёхсот", "A"), 5: ("пятисот", "A"),
    6: ("шестисот", "A"), 7: ("семисот", "A"), 8: ("восьмисот", "A"), 9: ("девятисот", "A"),
}
GEN_PREFIX = {1: "", 2: "двух", 3: "трёх", 4: "четырёх", 5: "пяти", 6: "шести", 7: "семи", 8: "восьми", 9: "девяти",
              10: "десяти", 20: "двадцати", 30: "тридцати", 40: "сорока", 50: "пятидесяти", 100: "сто"}

ENDINGS = {
    # (род, падеж): окончание для типов A, B, C
    ("m", "nom"): ("ый", "ой", "ий"),
    ("n", "nom"): ("ое", "ое", "ье"),
    ("f", "nom"): ("ая", "ая", "ья"),
    ("m", "gen"): ("ого", "ого", "ьего"),
    ("n", "gen"): ("ого", "ого", "ьего"),
    ("f", "gen"): ("ой", "ой", "ьей"),
    ("m", "dat"): ("ому", "ому", "ьему"),
    ("n", "dat"): ("ому", "ому", "ьему"),
    ("f", "dat"): ("ой", "ой", "ьей"),
    ("m", "prep"): ("ом", "ом", "ьем"),
    ("n", "prep"): ("ом", "ом", "ьем"),
    ("f", "prep"): ("ой", "ой", "ьей"),
    ("m", "ins"): ("ым", "ым", "ьим"),
    ("n", "ins"): ("ым", "ым", "ьим"),
    ("f", "ins"): ("ой", "ой", "ьей"),
    ("f", "acc"): ("ую", "ую", "ью"),
    ("pl", "nom"): ("ые", "ые", "ьи"),
    ("pl", "gen"): ("ых", "ых", "ьих"),
}


def _ending(stem: str, kind: str, gender: str, case: str) -> str:
    if case == "acc":
        case = "acc" if gender == "f" else "nom"
    forms = ENDINGS.get((gender, case)) or ENDINGS[("m", case if (("m", case) in ENDINGS) else "nom")]
    return stem + forms["ABC".index(kind)]


def ordinal(n: int, gender: str = "m", case: str = "nom") -> str:
    if n <= 0:
        return cardinal(n)
    if n >= 1000 and n % 1000 == 0 and n < 10**6:
        k = n // 1000
        prefix = GEN_PREFIX.get(k)
        if prefix is None:
            prefix = cardinal(k).replace(" ", "")
        return _ending(prefix + "тысячн", "A", gender, case)
    if n % 100 == 0:
        last = n % 1000
        high = n - last
        stem, kind = ORD_HUNDREDS[last // 100]
        word = _ending(stem, kind, gender, case)
        return (cardinal(high) + " " + word) if high else word
    last = n % 100
    high = n - last
    if last < 20:
        stem, kind = ORD_SMALL[last]
        word = _ending(stem, kind, gender, case)
    else:
        t, u = divmod(last, 10)
        if u == 0:
            stem, kind = ORD_TENS[t]
            word = _ending(stem, kind, gender, case)
        else:
            stem, kind = ORD_SMALL[u]
            word = TENS[t] + " " + _ending(stem, kind, gender, case)
    return (cardinal(high) + " " + word) if high else word


FRACTION_NAMES = {1: ("десятая", "десятых"), 2: ("сотая", "сотых"), 3: ("тысячная", "тысячных"),
                  4: ("десятитысячная", "десятитысячных")}


def decimal(integer: str, fraction: str) -> str:
    """3,14 -> три целых четырнадцать сотых."""
    i = int(integer)
    fraction = fraction[:4]
    f = int(fraction)
    whole = cardinal(i, "f") + " " + ("целая" if i % 10 == 1 and i % 100 != 11 else "целых")
    if f == 0:
        return whole
    one, many = FRACTION_NAMES[len(fraction)]
    name = one if f % 10 == 1 and f % 100 != 11 else many
    return f"{whole} {cardinal(f, 'f')} {name}"


def digits(s: str) -> str:
    """Поцифровое чтение (номера, коды): 0512 -> ноль пять один два."""
    return " ".join(UNITS_M[int(ch)] for ch in s if ch.isdigit())
