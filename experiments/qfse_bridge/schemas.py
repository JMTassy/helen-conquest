"""QFSE_EVIDENCE_OBJECT_V1 schema definition and validation."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

COMPILER_VERSION = "qfse_evidence_compiler_v1"
SCHEMA_TYPE = "QFSE_EVIDENCE_OBJECT_V1"

REQUIRED_FIELDS = frozenset({
    "type", "trajectory_hash", "entropy", "phi_coherence",
    "identity_preservation", "braid_stability", "valid", "compiler_version",
})


@dataclass
class QFSEEvidenceObject:
    trajectory_hash: str
    entropy: float
    phi_coherence: float
    identity_preservation: float
    braid_stability: float
    valid: bool
    type: str = field(default=SCHEMA_TYPE, init=False)
    compiler_version: str = field(default=COMPILER_VERSION, init=False)

    def to_dict(self) -> dict:
        return asdict(self)

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


class SchemaValidationError(Exception):
    pass


def validate(obj: dict) -> None:
    missing = REQUIRED_FIELDS - set(obj.keys())
    if missing:
        raise SchemaValidationError(f"missing fields: {missing}")
    if obj.get("type") != SCHEMA_TYPE:
        raise SchemaValidationError(f"wrong type: {obj.get('type')!r}")
    if obj.get("compiler_version") != COMPILER_VERSION:
        raise SchemaValidationError(f"wrong compiler_version: {obj.get('compiler_version')!r}")
    for f in ("entropy", "phi_coherence", "identity_preservation", "braid_stability"):
        v = obj.get(f)
        if not isinstance(v, (int, float)):
            raise SchemaValidationError(f"{f} must be numeric, got {type(v)}")
    if not isinstance(obj.get("valid"), bool):
        raise SchemaValidationError("'valid' must be bool")
