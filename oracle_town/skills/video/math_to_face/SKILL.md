---
name: video/math_to_face
description: Sovereign white-box rendering pipeline — bidirectional compiler between Math, Latent, and Image spaces. φ-resonant SDE refinement with HELEN identity anchoring. Complements helen-director (Seedance rental) as the long-term owned stack. DOCTRINE scaffold status; code is stubbed, needs H/G/E/H⁻¹ wiring + trained weights.
helen_faculty: RENDER / COGNITION
helen_status: DOCTRINE (scaffold landed 2026-04-20; NOT RUNNABLE until phases 3-5 complete)
helen_prerequisite: helen-director/SKILL.md (peer), HELEN_CHARACTER_V2.md (T3 empirical precursor), Emotions Spectrum plugin (structured emotion taxonomy as math input)
---

# MATH → FACE (HELEN) — Sovereign Rendering Skill

**Class**: Non-sovereign render layer. No kernel authority. No ledger write.

**Position vs helen-director**: helen-director is the **rental** pipeline (Higgsfield Seedance Pro API, closed-box, ~95% identity hold empirically). math_to_face is the **sovereign** pipeline (every component trained + owned + auditable). They coexist. helen-director delivers today; math_to_face delivers long-term ownership.

---

## 1. Canonical spaces + core maps

```
M  Math space      : primes, prime gaps, zeta zeros, fractal params, braid words
Z  Latent space    : R^512 (fixed per HELEN config schema)
I  Image space     : face images / avatars
```

Core mappings (all interfaces defined in `helen_os/render/math_to_face.py`):

| Map | Signature | Status | Scaffold location |
|---|---|---|---|
| **H**   | `M → Z` | stub | `helen_math_to_latent()` — baseline mix with HELEN anchor |
| **G**   | `Z → I` | NotImplementedError | `G_render()` — wire StyleGAN3 / SD / Flux |
| **E**   | `I → Z` | NotImplementedError | `E_invert()` — wire e4e / ReStyle / pSp |
| **H⁻¹** | `Z → M` | NotImplementedError | `H_inverse()` — constrained decoder |

**Canonical composition**: `Face = G(H(m))`
**Round-trip target**: `H⁻¹(E(G(H(m)))) = m`

---

## 2. φ-resonant SDE refinement (stabilizer) — IMPLEMENTED

This is the one layer that's fully scaffolded. φ-resonant diffusion wraps H → G with identity-stabilizing noise/denoise:

**Forward SDE** (data → noise):
```
dz_t = f(z, t) dt + g(t) dW_t
g(t) = γ √(1 − φ^{−2t})
f(z, t) = −φ^{−t} (z − Π_QAM(z))
```

**Reverse SDE** (noise → data, using trained score net):
```
dz_t = [f(z, t) − g(t)² · s_θ(z, t)] dt + g(t) dW̄_t
s_θ(z, t) ≈ ∇_z log p_t(z)
```

Scaffolded in `math_to_face.py`:
- `diffusion_schedule(t, gamma)` — the g(t)
- `phi_drift(z, t)` — the f(z, t)
- `qam_projection(z)` — Π_QAM (stub identity; replace with real QAM projector from MATH RIEMANN framework)
- `PhiScoreNet` — minimal MLP for s_θ (needs DSM training)
- `SDEConfig`, `forward_sde()`, `reverse_sde()` — Euler-Maruyama solver

---

## 3. HELEN Identity Artifact (per Phase 2)

```python
@dataclass
class HelenIdentity:
    helen_z_anchor: Tensor           # averaged latent from N reference photos
    helen_arcface_anchor: Tensor     # averaged ArcFace embedding
    reference_photos: list           # absolute paths
```

Build via `record_identity(face_images, arcface_model)` — iterate reference set, invert via E, ArcFace-embed, average. This is the **durable identity object** the operator can store and reuse ("make HELEN in this pose/emotion").

Empirical precursor: HELEN_CHARACTER_V2 §2 T3 method (single-photo Seedance seed). math_to_face formalizes this as averaged anchors + ArcFace gate.

---

## 4. Gates (identity preservation + round-trip invariants)

Per Phase 0.2 — the assistant must be **gated, not creative**. Three gate functions stubbed in the scaffold:

| Gate | Definition | Pass condition | Scaffold |
|---|---|---|---|
| **Identity distance** | `1 − cos(ArcFace(face), anchor)` | `< δ_id` (default 0.35) | `passes_identity_gate()` |
| **Latent drift** | `‖z₁ − z₂‖` after m→z→I→z | `< ε` | stubbed in `round_trip_invariants()` |
| **Visual consistency** | `LPIPS(G(z), G'(z))` | `< δ` | stubbed |
| **Math attribution** | `H⁻¹(E(G(H(m)))) ≡ m` | equality | stubbed |
| **IP functional** | `sup_{d_M(m₁,m₂)<δ} ‖G(H(m₁)) − G(H(m₂))‖` | `< ε_preserved` | `identity_preservation_functional()` |

All gate thresholds and pass/fail verdicts become part of the per-run **manifest** (Phase 7.2).

---

## 5. MVP pipeline commands (Phase 7.1 intent router)

Four top-level commands, scaffolded in `math_to_face.py`:

| Command | Input | Output |
|---|---|---|
| `math_to_face_helen(m, helen, score_net, cfg)` | math vector `m` + HELEN identity | image + latent + logs |
| `face_to_math(image)` | face image | recovered math object `m` + confidence |
| `validate_roundtrip(m, ...)` | math object | gate report (drift, LPIPS, attribution) |
| `record_identity(face_images, arcface)` | N reference photos | `HelenIdentity` object |

All four return (or should return, when wired) a **manifest** containing: config hash, model versions, input hash, latents (z₀, zT, ẑ₀), gate metrics, pass/fail.

---

## 6. Build plan — Phase 0 → Phase 9 roadmap

From the operator's deep build plan (2026-04-20 session):

### Phase 0 — Non-negotiables (locked before coding)
- Canonical spaces + contracts (M, Z⊂R^512, I) — **DONE** (this doc + scaffold)
- Gates (identity / LPIPS / attribution) — **INTERFACE DEFINED** (stubs)

### Phase 1 — Repo skeleton (1 day)
Operator-proposed layout (`helen-assistant/src/...`) is deferred — current scaffold consolidates Phase 1 in the single file `helen_os/render/math_to_face.py`. Future refactor: split into `src/helen/identity.py`, `src/math/encoder_H.py`, `src/qam/projection.py`, `src/sde/phi_sde.py`, `src/score/phi_score_net.py`, `src/generator/G.py`, `src/pipeline/math_to_face.py`.

### Phase 2 — Identity anchoring (1-2 days)
- HELEN Identity Artifact dataclass — **DONE** (stub)
- ArcFace embedding pipeline (preprocess → detect → align → embed → store) — **PENDING** (wire insightface)
- Mean + covariance anchors — **PENDING**

### Phase 3 — H and H⁻¹ (1-2 weeks)
- Canonical math struct (primes, gaps, zeta zeros, fractal dim, braid word) — **PENDING**
- H baseline (handcrafted Fourier features + φ-reg) — **PARTIAL** (`helen_math_to_latent` is stub mix)
- H learned (Transformer/MLP) — **PENDING** (needs training data)
- H⁻¹ constrained decoder — **PENDING**
- Training pairs strategy: synthetic / real-faces-via-E / hybrid — **OPEN QUESTION**

### Phase 4 — G + E (1-2 weeks)
- G wrapped (StyleGAN W/W+ or SD conditioning, freeze as canonical Z) — **PENDING**
- E baseline (e4e / ReStyle pretrained) — **PENDING**

### Phase 5 — φ-SDE refinement (3-10 days)
- Forward SDE — **DONE** (`forward_sde()`)
- Reverse SDE — **DONE** (`reverse_sde()`)
- Π_QAM decision (identity / low-rank / HELEN-anchor projector) — **PENDING**
- Score net training (DSM loop) — **PENDING** (model defined, loop not)
- Wire into generation: m → H → forward_sde → reverse_sde → G — **INTERFACE DONE** (needs G + H wired)

### Phase 6 — QΦ-SoftPrompt (optional, 3-7 days)
- Prime-mask prompt utility — **PENDING**
- Hamiltonian edit (additive or unitary-inspired) — **PENDING**
- Use case: "HELEN, same identity, change only hairstyle/lighting/pose"

### Phase 7 — Assistant layer (3-10 days)
- Intent router → 5 tools — **INTERFACE DEFINED** (scaffold stubs)
- Manifest logging contract — **PENDING** (spec in §7.2)

### Phase 8 — Verification protocol (ongoing)
- Unit tests: `E(G(z)) ≈ z`, `H⁻¹(H(m)) ≈ m`, SDE stability — **PENDING**
- Acceptance tests: identity ≥ threshold, LPIPS ≤ threshold, round-trip success rate — **PENDING**

### Phase 9 — Deployment (when local works)
- GPU inference service (G, E, score net) — **PENDING**
- CPU service (routing + logging) — **PENDING**
- Artifact store (identity objects + manifests) — **PENDING**

---

## 7. Config schema (Phase 1.2 — `configs/helen.json` equivalent)

Defined inline in scaffold via `SDEConfig`. Canonical values per HELEN config schema:
- `latent_dim`: 512 (fixed)
- `phi_regularization`: true
- `face_embedding_model`: `insightface/arcface_resnet50`
- Default SDE: `gamma=0.10`, `steps=200`, `t ∈ [0, 1]`

---

## 8. Interaction with helen-director (the rental pipeline)

Two pipelines, one repo, different purposes:

| Question | helen-director (today) | math_to_face (long-term) |
|---|---|---|
| Identity preservation | ~95% empirical (operator-rated) | ArcFace cosine-distance gate, mathematically measurable |
| Cost per 6s clip | ~10 Higgsfield credits | GPU inference only (owned hardware) |
| Latency | ~2-5 min/clip API wait | TBD after Phase 4 (G speed dependent) |
| Control over mapping | None (API black box) | Full (every layer trainable/tunable) |
| Math-conditioned | No | Yes (the point) |
| Round-trip `face → math → face` | Not possible | Yes (E then H⁻¹ then H then G) |
| Readiness | PRODUCTION (msg 708, 711, 712, 713) | SCAFFOLD |

**Interim**: use helen-director for deliverables. Route research-grade rendering experiments through math_to_face as components come online.

---

## 9. Integration with Emotions Spectrum plugin

The operator's `#pluginEmotionsSpectrum.pdf` defines 100+ structured emotions (Vibrant Serenity, Curious Joy, Transcendent Awe, Ethereal Melancholy, etc.). These become valid inputs to the math encoder H:

```python
emotion_vec = encode_emotion_taxonomy(emotion_name)  # future: M-space embedding
face = math_to_face_helen(emotion_vec, helen, score_net, cfg)
```

This is the "MATH → FACE" semantic loop: emotion (math-typed) → HELEN's rendered expression. Operator's vision from today's session.

---

## 10. Governance notes

- All files under `helen_os/render/**` are non-sovereign per `~/.claude/CLAUDE.md` firewall. Writes to the render layer do not touch kernel, governance, schemas, ledger, mayor, or closures.
- Training data + model weights should live in `artifacts/` (non-firewalled) or `/tmp/helen_temple/` during dev.
- Trained checkpoints must ship with their own `.provenance.json` (model hash, training data hash, training run id) before being cited in any claim — K8 extension to the render layer.
- Per `NO RECEIPT = NO CLAIM`: no rendered face counts as "HELEN" until an identity gate (§4) has run and passed, with the resulting metrics receipted via `helen_say.py`.

---

## 11. Admission status

**DOCTRINE scaffold** — interfaces + SDE core landed 2026-04-20. The document itself is not INVARIANT. Promotion gates:

- At least H + G wired end-to-end producing an image that passes the identity gate on HELEN's anchor
- `helen_say.py` receipt binding this document's SHA256 to the ledger
- K2 / Rule 3: the session that promotes must not be the session that authored
- Second fresh-lane reproduction of the SDE forward/reverse round-trip on synthetic data

Until then: cite as "sovereign rendering scaffold per 2026-04-20 session — interfaces defined, backends not wired."

---

## 12. Cross-references

- `helen_os/render/math_to_face.py` — the scaffold module (single file, all interfaces)
- `oracle_town/skills/video/helen-director/SKILL.md` — peer skill (Seedance rental pipeline)
- `oracle_town/skills/video/helen-director/HELEN_CHARACTER_V2.md` — T3 photo-seed empirical precursor
- `/Users/jean-marietassy/Desktop/PLUGINS_JMT/#pluginEmotionsSpectrum.pdf` — emotion taxonomy (input vocabulary for H)
- `/Users/jean-marietassy/Desktop/#pluginHELEN 20 avril 26.pdf` — MATH RIEMANN / QAM framework (source for Π_QAM projector)
