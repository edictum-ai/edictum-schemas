"""Edictum ruleset JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"
_SCHEMA_FILE = _SCHEMA_DIR / "edictum-v2.schema.json"


def schema_path() -> Path:
    """Return the absolute path to the canonical edictum-v2 JSON Schema file."""
    return _SCHEMA_FILE


def load_schema() -> dict[str, Any]:
    """Load and return the canonical edictum-v2 JSON Schema as a dict."""
    return json.loads(_SCHEMA_FILE.read_text(encoding="utf-8"))
