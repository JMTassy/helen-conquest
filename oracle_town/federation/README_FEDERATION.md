# Federation of Towns (v1)

This directory contains the minimal, checkable artifacts for a federation layer.

## Schemas
- `schemas/federation_treaty_v1.schema.json`
- `schemas/federation_link_v1.schema.json`
- `schemas/federation_receipt_v1.schema.json`

## Tools
- `tools/validate_federation.py` validates a single JSON document against schema + invariants
- `tools/federation_reduce.py` performs a deterministic PASS/BLOCK reduction for a treaty/link pair

## Minimal Usage
```bash
python3 oracle_town/federation/tools/validate_federation.py path/to/treaty.json
python3 oracle_town/federation/tools/validate_federation.py path/to/link.json
python3 oracle_town/federation/tools/validate_federation.py path/to/receipt.json

python3 oracle_town/federation/tools/federation_reduce.py treaty.json link.json receipt.json
```

## Invariants
- Treaties define an allowlisted set of towns.
- Links must connect two towns from the treaty.
- If `receipt_required` is true, a PASS receipt is required for a PASS reduction.
