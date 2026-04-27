"""Policy loader and policy_hash computation."""
from __future__ import annotations

import json
from pathlib import Path

from helen_os.ledger.hash_chain import sha256_hex


def load_permissions(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_forbidden_tokens(path: str | Path) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return list(json.load(f))


def load_forbidden_desires(path: str | Path) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return list(json.load(f))


def policy_hash(path: str | Path) -> str:
    with open(path, "rb") as f:
        return sha256_hex(f.read())
