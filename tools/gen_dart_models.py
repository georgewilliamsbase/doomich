#!/usr/bin/env python3
"""Генерация моделей Dart из OpenAPI схемы Core API.

    python3 tools/gen_dart_models.py docs/api/openapi.json packages/doomich_api/lib/src/models.g.dart

Берутся только схемы, на которые ссылаются пользовательские пути (/v1/...),
админские модели клиентам не нужны. Результат: неизменяемые классы с fromJson/toJson.
CI проверяет, что сгенерированный файл совпадает с закоммиченным.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

RESERVED = {"default", "is", "in", "class", "new", "switch", "case", "enum", "extends", "with", "final", "const",
            "var", "void", "null", "true", "false", "this", "super", "return", "import", "library", "part", "get",
            "set", "operator", "external", "factory", "static", "abstract", "dynamic", "late", "required", "do"}


def camel(name: str) -> str:
    parts = re.split(r"[_\-]", name)
    out = parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])
    return out + "_" if out in RESERVED else out


def ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def collect_refs(node: Any, acc: set[str]) -> None:
    if isinstance(node, dict):
        if "$ref" in node:
            acc.add(ref_name(node["$ref"]))
        for v in node.values():
            collect_refs(v, acc)
    elif isinstance(node, list):
        for v in node:
            collect_refs(v, acc)


def user_schemas(spec: dict[str, Any]) -> list[str]:
    schemas = spec["components"]["schemas"]
    found: set[str] = set()
    for path, ops in spec["paths"].items():
        if path.startswith("/admin"):
            continue
        collect_refs(ops, found)
    frontier = set(found)
    while frontier:
        nxt: set[str] = set()
        for name in frontier:
            collect_refs(schemas.get(name, {}), nxt)
        frontier = nxt - found
        found |= nxt
    skip = {"HTTPValidationError", "ValidationError"}
    return sorted(n for n in found if n in schemas and n not in skip and not n.startswith("Body_"))


class Field:
    def __init__(self, name: str, schema: dict[str, Any], required: bool) -> None:
        self.json = name
        self.dart = camel(name)
        self.schema = schema
        self.nullable = False
        inner = schema
        if "anyOf" in schema:
            variants = [v for v in schema["anyOf"] if v.get("type") != "null"]
            self.nullable = len(variants) < len(schema["anyOf"])
            inner = variants[0] if len(variants) == 1 else {"type": "object"}
        self.inner = inner
        self.default = schema.get("default", None)
        has_default = "default" in schema and schema["default"] is not None
        if not required and not has_default:
            self.nullable = True
        if schema.get("default", "missing") is None:
            self.nullable = True

    def type(self) -> str:
        t = dart_type(self.inner)
        return t + "?" if self.nullable else t


def dart_type(s: dict[str, Any]) -> str:
    if "$ref" in s:
        return ref_name(s["$ref"])
    t = s.get("type")
    fmt = s.get("format")
    if t == "string":
        return "DateTime" if fmt in ("date-time", "date") else "String"
    if t == "integer":
        return "int"
    if t == "number":
        return "double"
    if t == "boolean":
        return "bool"
    if t == "array":
        return f"List<{dart_type(s.get('items', {}))}>"
    if t == "object":
        ap = s.get("additionalProperties")
        if isinstance(ap, dict) and ap.get("type") in ("boolean", "string", "integer"):
            return f"Map<String, {dart_type(ap)}>"
        return "Map<String, dynamic>"
    return "dynamic"


def from_json(expr: str, s: dict[str, Any]) -> str:
    if "$ref" in s:
        return f"{ref_name(s['$ref'])}.fromJson({expr} as Map<String, dynamic>)"
    t = s.get("type")
    if t == "string" and s.get("format") in ("date-time", "date"):
        return f"DateTime.parse({expr} as String)"
    if t == "number":
        return f"({expr} as num).toDouble()"
    if t == "integer":
        return f"({expr} as num).toInt()"
    if t == "array":
        item = s.get("items", {})
        return f"({expr} as List<dynamic>).map((e) => {from_json('e', item)}).toList()"
    if t == "object":
        typ = dart_type(s)
        if typ == "Map<String, dynamic>":
            return f"Map<String, dynamic>.from({expr} as Map)"
        return f"{typ}.from({expr} as Map)"
    return f"{expr} as {dart_type(s)}"


def to_json(expr: str, s: dict[str, Any]) -> str:
    if "$ref" in s:
        return f"{expr}.toJson()"
    t = s.get("type")
    if t == "string" and s.get("format") == "date-time":
        return f"{expr}.toUtc().toIso8601String()"
    if t == "string" and s.get("format") == "date":
        return f"_date({expr})"
    if t == "array":
        item = s.get("items", {})
        inner = to_json("e", item)
        return expr if inner == "e" else f"{expr}.map((e) => {inner}).toList()"
    return expr


def default_literal(f: Field) -> str | None:
    d = f.default
    if d is None:
        return None
    if isinstance(d, bool):
        return "true" if d else "false"
    if isinstance(d, (int, float)):
        return str(float(d)) if dart_type(f.inner) == "double" else str(d)
    if isinstance(d, str):
        return "'" + d.replace("'", "\\'") + "'"
    if isinstance(d, list):
        return "const []"
    if isinstance(d, dict):
        return "const {}"
    return None


def gen_class(name: str, schema: dict[str, Any]) -> str:
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    fields = [Field(k, v, k in required) for k, v in props.items()]
    lines = []
    desc = schema.get("description")
    if desc:
        for dl in desc.strip().splitlines():
            lines.append(f"/// {dl.strip()}")
    lines.append(f"class {name} {{")
    for f in fields:
        lines.append(f"  final {f.type()} {f.dart};")
    if fields:
        lines.append("")
        ctor = []
        for f in fields:
            dl = default_literal(f)
            if f.nullable:
                ctor.append(f"this.{f.dart}")
            elif dl is not None and f.json not in required:
                ctor.append(f"this.{f.dart} = {dl}")
            else:
                ctor.append(f"required this.{f.dart}")
        lines.append(f"  const {name}({{" + ", ".join(ctor) + "});")
    else:
        lines.append(f"  const {name}();")
    lines.append("")
    lines.append(f"  factory {name}.fromJson(Map<String, dynamic> j) => {name}(")
    for f in fields:
        conv = from_json(f"j['{f.json}']", f.inner)
        dl = default_literal(f)
        if f.nullable:
            lines.append(f"        {f.dart}: j['{f.json}'] == null ? null : {conv},")
        elif dl is not None and f.json not in required:
            lines.append(f"        {f.dart}: j['{f.json}'] == null ? {dl.replace('const ', '')} : {conv},")
        else:
            lines.append(f"        {f.dart}: {conv},")
    lines.append("      );")
    lines.append("")
    lines.append("  Map<String, dynamic> toJson() => {")
    for f in fields:
        conv = to_json(f.dart if not f.nullable else f"{f.dart}!", f.inner)
        if f.nullable:
            lines.append(f"        if ({f.dart} != null) '{f.json}': {conv},")
        else:
            lines.append(f"        '{f.json}': {conv},")
    lines.append("      };")
    lines.append("}")
    return "\n".join(lines)


def main() -> None:
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    spec = json.loads(src.read_text(encoding="utf-8"))
    names = user_schemas(spec)
    schemas = spec["components"]["schemas"]
    out = [
        "// Сгенерировано tools/gen_dart_models.py из docs/api/openapi.json. Руками не править.",
        "// ignore_for_file: unnecessary_null_comparison, prefer_const_constructors",
        "",
        "String _date(DateTime d) =>",
        "    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';",
        "",
    ]
    for n in names:
        out.append(gen_class(n, schemas[n]))
        out.append("")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(out), encoding="utf-8")
    print(f"{dst}: {len(names)} моделей")


if __name__ == "__main__":
    main()
