# Ontology Category Model v1

This document formalizes the four-layer ontology as a small category with non-interference.

## Objects
- **L0**: Agent (Cognition)
- **L1**: Servitor (Deterministic pipeline)
- **L2**: Street (Emergent memory field)
- **L3**: Town (Constitutional kernel)

## Morphisms (Allowed)
- `f01: L0 -> L1`  (proposals -> structured execution)
- `f12: L1 -> L2`  (execution traces -> emergent patterns)
- `f03: L0 -> L3`  (receipts only, via evidence)
- `f13: L1 -> L3`  (attestations -> receipts)
- `f23: L2 -> L1`  (culture biases proposals; non-sovereign influence)

## Forbidden Morphism (Firewall)
- **No direct arrow** `L2 -> L3` (emergence cannot alter sovereign state)
- **No direct arrow** `L0 -> L3` without receipts (narrative cannot alter sovereign state)

## Composition Law
All compositions that reach `L3` must factor through **receipt-bearing evidence**.

Formally, if `g: X -> L3` then `g = reduce ∘ evidence` for some `evidence` map that validates receipts.

## Non-Interference Lemma (Informal)
Any morphism originating in `L2` cannot change `L3` without a receipt-bearing intermediary.
Therefore, emergent patterns may influence proposals but cannot mutate sovereign state.

## Implementation Check
This maps to two invariants:
1. Ledger accepts **only** schema-validated, receipt-bound events.
2. Conversational memory is append-only and ignored by the reducer unless transformed into receipts.

This categorical view is minimal and sufficient to encode the authority firewall.
