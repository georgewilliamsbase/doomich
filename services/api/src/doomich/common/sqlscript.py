"""Разбивка SQL-скрипта на отдельные команды.

asyncpg не выполняет несколько команд в одном подготовленном запросе, поэтому
миграции режут скрипт по точке с запятой. Учитываются строки в одинарных кавычках,
блоки $$...$$ (тела функций, DO) и комментарии "--".
"""

from __future__ import annotations


def split_sql(script: str) -> list[str]:
    statements: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(script)
    in_quote = False
    dollar_tag: str | None = None
    while i < n:
        ch = script[i]
        if dollar_tag is not None:
            if script.startswith(dollar_tag, i):
                buf.append(dollar_tag)
                i += len(dollar_tag)
                dollar_tag = None
                continue
            buf.append(ch)
            i += 1
            continue
        if in_quote:
            buf.append(ch)
            if ch == "'":
                in_quote = False
            i += 1
            continue
        if ch == "-" and script.startswith("--", i):
            end = script.find("\n", i)
            i = n if end == -1 else end
            continue
        if ch == "'":
            in_quote = True
            buf.append(ch)
            i += 1
            continue
        if ch == "$":
            end = script.find("$", i + 1)
            if end != -1:
                tag = script[i : end + 1]
                if tag == "$$" or tag[1:-1].replace("_", "").isalnum():
                    dollar_tag = tag
                    buf.append(tag)
                    i = end + 1
                    continue
        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def run_script(op, script: str) -> None:
    for stmt in split_sql(script):
        op.execute(stmt)
