# REGISTRIES — Reference Constitutional Surfaces

This directory contains reference registries that define the enumerated types, finding codes, receipt types, and routing decisions used throughout HELEN governance.

These are constitutional in nature (frozen, versioned) but serve as reference data rather than architectural laws.

## Current Registries

| Registry | File | Status | Purpose |
|----------|------|--------|---------|
| Audit Finding Registry | AUDIT_FINDING_REGISTRY_V1.md | FROZEN_CANDIDATE | 13 finding codes with severity and routing effects |
| Receipt Schema Registry | RECEIPT_SCHEMA_REGISTRY_V1.md | FROZEN_CANDIDATE | 8 receipt types with emission conditions and lineage rules |
| Dispatch Decision Table | DISPATCH_DECISION_TABLE_V1.md | FROZEN | Routing decisions and consequence semantics |

## Use in Constitution

These registries are referenced by the constitutional layer:
- LIFECYCLE_INVARIANTS_V1 uses DISPATCH_DECISION_TABLE_V1 for routing mapping
- AUDIT_FINDING_REGISTRY_V1 defines findings emitted by Phase 3 (Knowledge Audit)
- RECEIPT_SCHEMA_REGISTRY_V1 defines receipt types emitted throughout lifecycle

## Versioning

Registries follow the same versioning rules as constitutional documents:
- **Patch bump:** Adding optional detail without changing semantics
- **Minor bump:** Adding new codes/types without breaking prior valid state
- **Major bump:** Removing codes/types or changing semantics (incompatible)

New finding codes or receipt types require enumeration in these registries.
