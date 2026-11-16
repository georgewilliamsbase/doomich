"""Нормализация русского текста перед синтезом.

Порядок важен: сначала разметка и спецсимволы, потом даты и время (в них есть
точки и двоеточия), потом числа с единицами, сокращения, аббревиатуры и в конце
одиночные числа.
"""

from __future__ import annotations

import re

from doomich_tts.normalize.numbers_ru import cardinal, decimal, digits, ordinal, plural

MONTHS_GEN = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября",
              "ноября", "декабря"]
MONTH_RE = "|".join(MONTHS_GEN)

UNITS: dict[str, tuple[str, str, str, str]] = {
    # обозначение: (одна, две, пять, род числительного)
    "%": ("процент", "процента", "процентов", "m"),
    "км": ("километр", "километра", "километров", "m"),
    "м": ("метр", "метра", "метров", "m"),
    "см": ("сантиметр", "сантиметра", "сантиметров", "m"),
    "мм": ("миллиметр", "миллиметра", "миллиметров", "m"),
    "кг": ("килограмм", "килограмма", "килограммов", "m"),
    "г": ("грамм", "грамма", "граммов", "m"),
    "мг": ("миллиграмм", "миллиграмма", "миллиграммов", "m"),
    "л": ("литр", "литра", "литров", "m"),
    "мл": ("миллилитр", "миллилитра", "миллилитров", "m"),
    "ч": ("час", "часа", "часов", "m"),
    "мин": ("минута", "минуты", "минут", "f"),
    "сек": ("секунда", "секунды", "секунд", "f"),
    "мс": ("миллисекунда", "миллисекунды", "миллисекунд", "f"),
    "₽": ("рубль", "рубля", "рублей", "m"),
    "руб": ("рубль", "рубля", "рублей", "m"),
    "коп": ("копейка", "копейки", "копеек", "f"),
    "$": ("доллар", "доллара", "долларов", "m"),
    "€": ("евро", "евро", "евро", "m"),
    "°C": ("градус Цельсия", "градуса Цельсия", "градусов Цельсия", "m"),
    "°": ("градус", "градуса", "градусов", "m"),
    "Вт": ("ватт", "ватта", "ватт", "m"),
    "кВт": ("киловатт", "киловатта", "киловатт", "m"),
    "Гц": ("герц", "герца", "герц", "m"),
    "МБ": ("мегабайт", "мегабайта", "мегабайт", "m"),
    "ГБ": ("гигабайт", "гигабайта", "гигабайт", "m"),
    "КБ": ("килобайт", "килобайта", "килобайт", "m"),
    "шт": ("штука", "штуки", "штук", "f"),
    "стр": ("страница", "страницы", "страниц", "f"),
    "тыс": ("тысяча", "тысячи", "тысяч", "f"),
    "млн": ("миллион", "миллиона", "миллионов", "m"),
    "млрд": ("миллиард", "миллиарда", "миллиардов", "m"),
    "чел": ("человек", "человека", "человек", "m"),
    "балл": ("балл", "балла", "баллов", "m"),
    "баллов": ("балл", "балла", "баллов", "m"),
}

ABBREVIATIONS = [
    (r"\bи т\. ?д\.", "и так далее"), (r"\bи т\. ?п\.", "и тому подобное"), (r"\bт\. ?е\.", "то есть"),
    (r"\bт\. ?к\.", "так как"), (r"\bт\. ?н\.", "так называемый"), (r"\bт\. ?ч\.", "том числе"),
    (r"\bи др\.", "и другие"), (r"\bи пр\.", "и прочее"), (r"\bнапр\.", "например"), (r"\bсм\.", "смотрите"),
    (r"\bрис\.", "рисунок"), (r"\bтабл\.", "таблица"), (r"\bстр\.", "страница"), (r"\bауд\.", "аудитория"),
    (r"\bкаб\.", "кабинет"), (r"\bкорп\.", "корпус"), (r"\bул\.", "улица"), (r"\bпросп\.", "проспект"),
    (r"\bпроф\.", "профессор"), (r"\bдоц\.", "доцент"), (r"\bакад\.", "академик"), (r"\bим\.", "имени"),
    (r"\bгр\.", "группа"), (r"\bзав\.", "заведующий"), (r"\bканд\.", "кандидат"), (r"\bд-р\b", "доктор"),
    (r"\bэкз\.", "экзамен"), (r"\bлаб\.", "лабораторная"), (r"\bлек\.", "лекция"),
    (r"\bвкл\.", "включительно"), (r"\bок\.", "около"), (r"\bмакс\.", "максимум"),
    (r"\bвв\.", "веков"), (r"\bв\. ", "век "),
]

# Аббревиатуры, которые читаются как слово, а не по буквам
WORD_ACRONYMS = {"ВУЗ", "ГОСТ", "МХАТ", "МИД", "РАН", "ТАСС", "ГУМ", "ЦУМ", "ЗАГС", "СИЗО", "ОМОН", "НАТО", "ЮНЕСКО",
                 "ВАК", "ЖЭК", "ВТУЗ", "НИИ"}
WORD_ACRONYMS_SPELLED = {"НИИ": "эн и и"}
LETTERS = {
    "А": "а", "Б": "бэ", "В": "вэ", "Г": "гэ", "Д": "дэ", "Е": "е", "Ё": "ё", "Ж": "жэ", "З": "зэ", "И": "и",
    "Й": "и краткое", "К": "ка", "Л": "эль", "М": "эм", "Н": "эн", "О": "о", "П": "пэ", "Р": "эр", "С": "эс",
    "Т": "тэ", "У": "у", "Ф": "эф", "Х": "ха", "Ц": "цэ", "Ч": "че", "Ш": "ша", "Щ": "ща", "Ъ": "твёрдый знак",
    "Ы": "ы", "Ь": "мягкий знак", "Э": "э", "Ю": "ю", "Я": "я",
}
ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}

SYMBOLS = [("&", " и "), ("№", " номер "), ("§", " параграф "), ("≈", " примерно "), ("±", " плюс минус "),
           ("≤", " меньше или равно "), ("≥", " больше или равно "), ("×", " на "), ("→", " "), ("…", "..."),
           ("«", '"'), ("»", '"'), ("—", ", "), ("–", "-")]

SUFFIX_FORMS = {  # 5-го -> (род, падеж)
    "й": ("m", "nom"), "ый": ("m", "nom"), "ой": ("m", "nom"), "ий": ("m", "nom"),
    "я": ("f", "nom"), "ая": ("f", "nom"), "ья": ("f", "nom"),
    "е": ("n", "nom"), "ое": ("n", "nom"), "ье": ("n", "nom"),
    "го": ("m", "gen"), "ого": ("m", "gen"), "его": ("m", "gen"),
    "му": ("m", "dat"), "ому": ("m", "dat"), "ему": ("m", "dat"),
    "м": ("m", "prep"), "ом": ("m", "prep"), "ем": ("m", "prep"), "ым": ("m", "ins"),
    "ю": ("f", "acc"), "ую": ("f", "acc"),
    "х": ("pl", "gen"), "ых": ("pl", "gen"), "ые": ("pl", "nom"),
}

PREP_GEN = {"до", "с", "со", "от", "после", "около", "из", "для", "без", "начиная с"}
PREP_DAT = {"к", "ко", "по"}


def _roman(s: str) -> int | None:
    total, prev = 0, 0
    for ch in reversed(s):
        v = ROMAN.get(ch)
        if v is None:
            return None
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return total if 0 < total < 4000 else None


def _case_before(text: str, start: int) -> str:
    before = text[:start].rstrip().lower()
    word = before.split()[-1] if before.split() else ""
    if word in PREP_GEN:
        return "gen"
    if word in PREP_DAT:
        return "dat"
    return "nom"


def _date(m: re.Match[str], text: str) -> str:
    day, month, year = int(m.group("d")), m.group("m"), m.group("y")
    month_idx = int(month) - 1 if month.isdigit() else MONTHS_GEN.index(month.lower())
    if not (1 <= day <= 31 and 0 <= month_idx < 12):
        return m.group(0)
    case = _case_before(text, m.start())
    out = f"{ordinal(day, 'n', case)} {MONTHS_GEN[month_idx]}"
    if year:
        y = int(year)
        if y < 100:
            y += 2000
        out += f" {ordinal(y, 'm', 'gen')} года"
    return out


def _time(m: re.Match[str]) -> str:
    h, mm = int(m.group(1)), int(m.group(2))
    if h > 23 or mm > 59:
        return m.group(0)
    if mm == 0:
        return f"{cardinal(h)} ноль ноль"
    if mm < 10:
        return f"{cardinal(h)} ноль {cardinal(mm, 'f')}"
    return f"{cardinal(h)} {cardinal(mm, 'f')}"


def _year_word(m: re.Match[str]) -> str:
    n = int(m.group(1))
    word = m.group(2).lower()
    case = {"год": "nom", "году": "prep", "года": "gen", "годом": "ins"}.get(word, "gen")
    if word in ("г", "г."):
        return f"{ordinal(n, 'm', 'gen')} года"
    return f"{ordinal(n, 'm', case)} {word}"


def _unit(m: re.Match[str]) -> str:
    num, unit = m.group(1), m.group(2)
    one, few, many, gender = UNITS[unit]
    if "," in num or "." in num:
        i, f = re.split(r"[.,]", num, maxsplit=1)
        return f"{decimal(i, f)} {few}"
    n = int(num.replace(" ", ""))
    return f"{cardinal(n, gender)} {plural(n, one, few, many)}"


def _ordinal_suffix(m: re.Match[str]) -> str:
    n, suffix = int(m.group(1)), m.group(2).lower()
    gender, case = SUFFIX_FORMS.get(suffix, ("m", "nom"))
    return ordinal(n, gender, case)


def _keep_case(source: str, replacement: str) -> str:
    return replacement[:1].upper() + replacement[1:] if source[:1].isupper() else replacement


def _acronym(m: re.Match[str]) -> str:
    word = m.group(0)
    if word in WORD_ACRONYMS_SPELLED:
        return WORD_ACRONYMS_SPELLED[word]
    if word in WORD_ACRONYMS:
        return word.lower()
    return " ".join(LETTERS.get(ch, ch) for ch in word)


def _century(m: re.Match[str]) -> str:
    n = _roman(m.group(1))
    if n is None:
        return m.group(0)
    word = m.group(2).lower()
    case = {"век": "nom", "века": "gen", "веке": "prep", "веку": "dat", "веком": "ins", "веков": "gen"}.get(word, "nom")
    gender = "pl" if word == "веков" else "m"
    return f"{ordinal(n, gender, case)} {word}"


def normalize_ru(text: str) -> str:
    t = text
    for a, b in SYMBOLS:
        t = t.replace(a, b)
    # Даты: 15.11.2026, 15.11.26, 15 ноября 2026 г., 15 ноября
    t = re.sub(r"(?<!\d)(?P<d>\d{1,2})\.(?P<m>\d{1,2})\.(?P<y>\d{4}|\d{2})(?!\d)(?:\s*г\.)?",
               lambda m: _date(m, t), t)
    t = re.sub(rf"(?<!\d)(?P<d>\d{{1,2}})\s+(?P<m>{MONTH_RE})(?:\s+(?P<y>\d{{4}})(?:\s*(?:г\.|года))?)?",
               lambda m: _date(m, t), t, flags=re.IGNORECASE)
    # Годы: 2026 год, в 2026 году, 2026 г.
    t = re.sub(r"(?<!\d)(\d{3,4})\s*(годом|году|года|год|г\.)(?![а-яё])", _year_word, t, flags=re.IGNORECASE)
    # Время 10:30, 9:05
    t = re.sub(r"(?<![\d:])(\d{1,2}):(\d{2})(?![\d:])", _time, t)
    # Века: XX век
    t = re.sub(r"\b([IVXLC]{1,7})\s+(век|века|веке|веку|веком|веков)\b", _century, t)
    # Порядковые с суффиксом: 1-й, 5-го, 21-м
    t = re.sub(r"(?<!\d)(\d{1,4})-(ого|его|ому|ему|ый|ой|ий|ая|ья|ое|ье|ую|ые|ых|ым|ом|ем|го|му|й|я|е|ю|х|м)(?![а-яё])",
               _ordinal_suffix, t)
    # Числа с единицами: 5 км, 3,5 кг, 15%, 100 ₽
    units = "|".join(sorted((re.escape(u) for u in UNITS), key=len, reverse=True))
    t = re.sub(rf"(?<![\d.,])(\d{{1,3}}(?: \d{{3}})+|\d+(?:[.,]\d+)?)\s?({units})(?![а-яёa-z])\.?", _unit, t)
    for pattern, repl in ABBREVIATIONS:
        t = re.sub(pattern, lambda m, r=repl: _keep_case(m.group(0), r), t, flags=re.IGNORECASE)
    # Аббревиатуры из заглавных букв: ИВТ, МГУ
    t = re.sub(r"(?<![А-ЯЁа-яё])[А-ЯЁ]{2,6}(?![а-яё])", _acronym, t)
    # Десятичные дроби
    t = re.sub(r"(?<![\d.,])(\d+),(\d{1,4})(?![\d,])", lambda m: decimal(m.group(1), m.group(2)), t)
    # Длинные коды и телефоны читаем по цифрам
    t = re.sub(r"(?<!\d)0\d{2,}(?!\d)", lambda m: digits(m.group(0)), t)
    t = re.sub(r"(?<!\d)\d{7,}(?!\d)", lambda m: digits(m.group(0)), t)
    # Диапазоны: 2-3 -> два три
    t = re.sub(r"(?<!\d)(\d{1,6})-(\d{1,6})(?!\d)", lambda m: f"{cardinal(int(m.group(1)))} {cardinal(int(m.group(2)))}", t)
    # Отрицательные числа и остальные целые
    t = re.sub(r"(?<![\w\d])-(\d{1,9})(?!\d)", lambda m: "минус " + cardinal(int(m.group(1))), t)
    t = re.sub(r"(?<!\d)(\d{1,3}(?: \d{3})+)(?!\d)", lambda m: cardinal(int(m.group(1).replace(" ", ""))), t)
    t = re.sub(r"(?<!\d)\d{1,9}(?!\d)", lambda m: cardinal(int(m.group(0))), t)
    t = t.replace("+", " плюс ").replace("=", " равно ")
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,.!?;:])", r"\1", t)
    return t.strip()
