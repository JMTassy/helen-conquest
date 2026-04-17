"""Governance audit: which schemas in helen_os/schemas/ carry a constitutional identity const?

A schema is considered INDEXED iff it declares a const artifact-identity field together
with a const schema_version. Two identity-field conventions are accepted:

  - Constitutional: properties.schema_name.const + properties.schema_version.const
  - Receipt-style:  properties.schema.const      + properties.schema_version.const

Both bind a frozen identifier to the schema shape. Files with neither convention are
reported UNINDEXED. Registry-style schemas (enum lookups without artifact identity,
e.g. reason_codes.schema.json) are reported separately as EXEMPT.

This is an audit tool. It does not mutate schemas, emitters, or the kernel.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = REPO_ROOT / "helen_os" / "schemas"

# Schemas that are registries (enum lookups), not artifacts with identity.
REGISTRY_EXEMPT = {"reason_codes.schema.json"}


def _const_of(props: dict, field: str) -> str | None:
    node = props.get(field)
    if isinstance(node, dict) and "const" in node:
        return node["const"]
    return None


def classify(schema_path: Path) -> Tuple[str, Dict]:
    """Return (status, detail) for a single schema file.

    status ∈ {"INDEXED_SCHEMA_NAME", "INDEXED_SCHEMA", "EXEMPT", "UNINDEXED"}.
    """
    try:
        schema = json.loads(schema_path.read_text())
    except Exception as exc:
        return "UNINDEXED", {"error": f"parse_error: {exc!r}"}

    if schema_path.name in REGISTRY_EXEMPT:
        return "EXEMPT", {"reason": "registry (enum lookup, no artifact identity)"}

    props = schema.get("properties", {}) if isinstance(schema, dict) else {}
    name_const = _const_of(props, "schema_name")
    legacy_const = _const_of(props, "schema")
    version_const = _const_of(props, "schema_version")

    if name_const and version_const:
        return "INDEXED_SCHEMA_NAME", {"schema_name": name_const, "schema_version": version_const}
    if legacy_const and version_const:
        return "INDEXED_SCHEMA", {"schema": legacy_const, "schema_version": version_const}

    return "UNINDEXED", {
        "schema_name_const": name_const,
        "schema_const": legacy_const,
        "schema_version_const": version_const,
    }


def audit(schemas_dir: Path = SCHEMAS_DIR) -> Dict:
    files = sorted(schemas_dir.glob("*.json"))
    buckets: Dict[str, List[dict]] = {
        "INDEXED_SCHEMA_NAME": [],
        "INDEXED_SCHEMA": [],
        "EXEMPT": [],
        "UNINDEXED": [],
    }
    for f in files:
        status, detail = classify(f)
        buckets[status].append({"file": f.name, **detail})

    total = len(files)
    indexed = len(buckets["INDEXED_SCHEMA_NAME"]) + len(buckets["INDEXED_SCHEMA"])
    exempt = len(buckets["EXEMPT"])
    unindexed = len(buckets["UNINDEXED"])
    return {
        "schemas_dir": str(schemas_dir.relative_to(REPO_ROOT)),
        "total_files": total,
        "indexed_count": indexed,
        "indexed_denominator_excl_exempt": total - exempt,
        "exempt_count": exempt,
        "unindexed_count": unindexed,
        "buckets": buckets,
    }


def main() -> int:
    result = audit()
    print(json.dumps(result, indent=2))
    return 0 if result["unindexed_count"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
