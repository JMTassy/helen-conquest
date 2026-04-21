# HELEN library taxonomy (v1)

Calibrated 2026-04-21. Used for tagging harvested stills.

## Categories

| Tag | Definition | Use case |
|---|---|---|
| `portrait` | Shoulder-up, face dominant (60%+ frame) | Identity anchor, close-up beats, dialogue shots |
| `half_body` | Torso-up, one-third face / two-thirds body | Medium narrative shots, gesture communication |
| `full_body` | Whole figure visible | Wide establishing shots, movement/choreography |
| `green_screen` | Flat neutral background (green / grey) | Compositing into new scenes, metaverse reuse |
| `ritual` | Stylized / ceremonial / cathedral context | CONQUEST-aligned content, doctrine carriers |
| `cinematic` | Narrative scene with environment context | Story-driven clips, trailer footage |
| `abstract` | Non-figurative or heavily stylized | Transitions, mood fragments |
| `unclassified` | Default after harvest, pre-tagging | Auto-assigned by `harvest_keyframes.py` |

## Tagging protocol

**v1: operator manual.** The harvester tags everything `unclassified`; operator reviews and updates the manifest JSON directly (or via a follow-up skill).

**v2: auto-classifier.** When an embedder is available (ArcFace for face detection, CLIP for scene/context), add `classify_keyframes.py` that updates taxonomy fields automatically. Still an overlay on top of the harvester — harvest stays dumb.

## Secondary dimensions (optional fields per frame)

| Field | Values | Default |
|---|---|---|
| `mood` | calm / dramatic / tender / playful / vulnerable / intense / serene / curious / joyful | `null` |
| `canonical_register` | real / twin / ritual / cinematic | `null` (inferred from source when possible) |
| `identity_score` | float 0-1 (Mahalanobis gate pass strength) | `null` (v2) |
| `usage_count` | integer (how many final videos reused this frame) | `0` |
| `operator_starred` | bool | `false` |

## Canonical invariants (per HELEN_CANONICAL_V1.md)

A frame tagged `portrait` or `half_body` should still honor the four identity invariants:
- copper/red hair
- blue/blue-grey eyes
- narrow soft face
- expressive aura

Frames that violate these should be tagged `drift` or excluded from the library rather than re-tagged `portrait`. Library is **identity-accountable**, not just catalog-accountable.

## Gap categories (aspirational, currently empty)

- `green_screen` — zero frames in current source material; requires fresh generation with green-bg prompt
- `profile` — side-view HELEN; sparse in current material
- `back_of_head` — useful for POV shots; essentially absent
- `hands_only` — reaction shots; absent

These gaps are the first **targeted-generation** targets when operator authorizes real-backend fire — harvest first, generate only what's missing.

## One-line summary

> Taxonomy is a vocabulary, not a judgment. Tag, reuse, and track what's missing — generation fills the gaps, not the scaffold.
