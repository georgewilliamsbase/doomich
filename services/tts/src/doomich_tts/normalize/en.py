"""Нормализация английского текста: числа, порядковые, время, проценты."""

from __future__ import annotations

import re

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
        "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
ORD_IRREGULAR = {"one": "first", "two": "second", "three": "third", "five": "fifth", "eight": "eighth",
                 "nine": "ninth", "twelve": "twelfth"}


def cardinal_en(n: int) -> str:
    if n < 0:
        return "minus " + cardinal_en(-n)
    if n < 20:
        return ONES[n]
    if n < 100:
        t, u = divmod(n, 10)
        return TENS[t] + ("-" + ONES[u] if u else "")
    if n < 1000:
        h, r = divmod(n, 100)
        return ONES[h] + " hundred" + (" " + cardinal_en(r) if r else "")
    for value, name in ((10**9, "billion"), (10**6, "million"), (1000, "thousand")):
        if n >= value:
            q, r = divmod(n, value)
            return cardinal_en(q) + " " + name + (" " + cardinal_en(r) if r else "")
    return str(n)


def ordinal_en(n: int) -> str:
    words = cardinal_en(n)
    head, sep, last = words.rpartition(" " if " " in words else "-")
    if "-" in last:
        head2, _, last = last.rpartition("-")
        head = f"{head} {head2}".strip() if head else head2
        sep = "-"
    if last in ORD_IRREGULAR:
        last = ORD_IRREGULAR[last]
    elif last.endswith("y"):
        last = last[:-1] + "ieth"
    else:
        last += "th"
    return f"{head}{sep}{last}" if head else last


def normalize_en(text: str) -> str:
    t = text.replace("&", " and ").replace("%", " percent")
    t = re.sub(r"\b(\d{1,2}):(\d{2})\b", lambda m: f"{cardinal_en(int(m.group(1)))} "
               + ("o'clock" if m.group(2) == "00" else ("oh " + cardinal_en(int(m.group(2)))
                                                         if m.group(2)[0] == "0" else cardinal_en(int(m.group(2))))), t)
    t = re.sub(r"\b(\d+)(st|nd|rd|th)\b", lambda m: ordinal_en(int(m.group(1))), t)
    t = re.sub(r"\b(\d+)\.(\d+)\b", lambda m: f"{cardinal_en(int(m.group(1)))} point "
               + " ".join(ONES[int(c)] for c in m.group(2)), t)
    t = re.sub(r"\b(1[0-9]|20)(\d{2})\b(?=\s*(?:year|AD|BC|,|\.|$))",
               lambda m: f"{cardinal_en(int(m.group(1)))} {cardinal_en(int(m.group(2)))}"
               if m.group(2) != "00" else cardinal_en(int(m.group(0))), t)
    t = re.sub(r"\b\d{1,3}(?:,\d{3})+\b", lambda m: cardinal_en(int(m.group(0).replace(",", ""))), t)
    t = re.sub(r"\b\d+\b", lambda m: cardinal_en(int(m.group(0))), t)
    return re.sub(r"\s+", " ", t).strip()
