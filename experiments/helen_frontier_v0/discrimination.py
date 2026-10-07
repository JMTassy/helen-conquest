"""DISCRIMINATION_V0 — structural validation and declared grouping.

Proves: structure, types, required fields, closed property sets, authority=false.
Does not prove: semantic equivalence of two distinctions, independence of
contributions, or any cognitive value. Grouping below is *declared*
deduplication: items sharing a declared distinction_id are one group.
Recognising three different wordings of one distinction is out of scope.

NON_SOVEREIGN · authority=false · ledger_effect=none · fail-closed.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

try:  # fail-closed: without the validator library nothing validates
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - exercised only in a broken venv
    Draft202012Validator = None  # type: ignore[assignment]

SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "DISCRIMINATION_V0.schema.json"
SCHEMA_NAME = "DISCRIMINATION_V0"


def load_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_discrimination(obj: Any) -> tuple[bool, list[str]]:
    """Return (ok, errors). Any exception or any schema error -> (False, [...])."""
    if Draft202012Validator is None:
        return False, ["jsonschema unavailable: validation refused (fail-closed)"]
    if not isinstance(obj, Mapping):
        return False, [f"<root>: expected a mapping, got {type(obj).__name__}"]
    try:
        validator = Draft202012Validator(load_schema())
        errors = sorted(validator.iter_errors(obj), key=lambda e: [str(p) for p in e.absolute_path])
    except Exception as exc:  # noqa: BLE001 - refuse on any validator failure
        return False, [f"validator error: {type(exc).__name__}: {exc}"]
    messages = [
        f"{'/'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
        for err in errors
    ]
    return (not messages), messages


def declared_groups(items: Sequence[Mapping[str, Any]]) -> dict[str, tuple[str, ...]]:
    """Group VALID discriminations by declared distinction_id.

    Returns {distinction_id: sorted tuple of declared producers}. Refuses the
    whole batch if any item is invalid (fail-closed). This is declarative
    deduplication only.
    """
    groups: dict[str, list[str]] = {}
    for index, item in enumerate(items):
        ok, errors = validate_discrimination(item)
        if not ok:
            raise ValueError(f"item[{index}] invalid: {errors[:3]}")
        groups.setdefault(item["distinction_id"], []).append(item["provenance"]["producer"])
    return {k: tuple(sorted(v)) for k, v in sorted(groups.items())}


def group_signature(groups: Mapping[str, Sequence[str]]) -> tuple[tuple[int, int], ...]:
    """Name-free shape of a grouping: sorted (group_size, multiplicity) pairs.

    Two groupings that differ only by a bijective renaming of producers and of
    distinction_ids have the same signature.
    """
    sizes = Counter(len(v) for v in groups.values())
    return tuple(sorted(sizes.items()))
