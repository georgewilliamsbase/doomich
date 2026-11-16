"""Ударения по словарю.

Формат словаря: слово<TAB>форма с "+" перед ударной гласной, например "звонит\tзвон+ит".
Общий словарь лежит рядом с модулем, словари вузов (названия корпусов, фамилии
из расписания, термины) кладутся в <dicts_dir>/<slug вуза>.tsv.
Модели по-разному понимают ударения: одни ждут "+" перед гласной, другие
знак ударения после гласной (U+0301), третьи не понимают вовсе.
"""

from __future__ import annotations

import re
from pathlib import Path

VOWELS = "аеёиоуыэюяАЕЁИОУЫЭЮЯ"
WORD_RE = re.compile(r"[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)?")

BUILTIN = """
звонит	звон+ит
звонишь	звон+ишь
договор	догов+ор
договоры	догов+оры
каталог	катал+ог
квартал	кварт+ал
обеспечение	обесп+ечение
средства	ср+едства
торты	т+орты
красивее	крас+ивее
кухонный	к+ухонный
шарфы	ш+арфы
банты	б+анты
жалюзи	жалюз+и
щавель	щав+ель
свёкла	св+ёкла
мышление	м+ышление
ходатайство	ход+атайство
вероисповедание	вероисповед+ание
диспансер	диспанс+ер
гражданство	гражд+анство
документ	докум+ент
намерение	нам+ерение
некролог	некрол+ог
эксперт	эксп+ерт
досуг	дос+уг
феномен	фен+омен
облегчить	облегч+ить
углубить	углуб+ить
включит	включ+ит
кремень	крем+ень
атлас	+атлас
декан	дек+ан
доцент	доц+ент
семинар	семин+ар
лекция	л+екция
практикум	пр+актикум
коллоквиум	колл+оквиум
бакалавр	бакал+авр
магистратура	магистрат+ура
аспирантура	аспирант+ура
деканат	декан+ат
кафедра	к+афедра
сессия	с+ессия
зачётка	зач+ётка
расписание	распис+ание
аудитория	аудит+ория
""".strip()


def parse(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "\t" not in line:
            continue
        word, stressed = line.split("\t", 1)
        out[word.lower().replace("ё", "е")] = stressed.strip()
    return out


class StressDict:
    def __init__(self, dicts_dir: Path | None = None) -> None:
        self.base = parse(BUILTIN)
        self.dicts_dir = dicts_dir
        self._tenant: dict[str, dict[str, str]] = {}

    def for_tenant(self, tenant: str | None) -> dict[str, str]:
        if not tenant or not self.dicts_dir or not re.fullmatch(r"[a-z0-9-]{1,64}", tenant):
            return self.base
        if tenant not in self._tenant:
            path = self.dicts_dir / f"{tenant}.tsv"
            extra = parse(path.read_text(encoding="utf-8")) if path.exists() else {}
            self._tenant[tenant] = {**self.base, **extra}
        return self._tenant[tenant]

    def apply(self, text: str, tenant: str | None = None, style: str = "plus") -> str:
        if style == "none":
            return text
        table = self.for_tenant(tenant)

        def repl(m: re.Match[str]) -> str:
            word = m.group(0)
            stressed = table.get(word.lower().replace("ё", "е"))
            if not stressed:
                return word
            # Сохраняем регистр первой буквы
            if word[0].isupper():
                stressed = stressed[0].upper() + stressed[1:] if stressed[0] != "+" else "+" + stressed[1:2].upper() + stressed[2:]
            return convert(stressed, style)

        return WORD_RE.sub(repl, text)


def convert(stressed: str, style: str) -> str:
    if style == "plus":
        return stressed
    if style == "acute":
        return re.sub(r"\+([" + VOWELS + "])", lambda m: m.group(1) + "́", stressed)
    return stressed.replace("+", "")


def strip_marks(text: str) -> str:
    return text.replace("+", "").replace("́", "")
