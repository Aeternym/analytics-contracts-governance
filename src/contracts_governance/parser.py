from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Contract:
    path: Path
    metadata: dict
    body: str


def _value(raw: str):
    value = raw.strip()
    if value in {"null", "~", ""}:
        return None
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("'\"") for item in inner.split(",")]
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value.strip("'\"")


def parse_contract(path: Path) -> Contract:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing YAML-like front matter")
    marker = text.find("\n---\n", 4)
    if marker < 0:
        raise ValueError("front matter is not closed")
    metadata = {}
    for line in text[4:marker].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"invalid metadata line: {line}")
        key, raw = line.split(":", 1)
        metadata[key.strip()] = _value(raw)
    return Contract(path, metadata, text[marker + 5 :])

