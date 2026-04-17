---
name: voice/gemini_tts
description: Speak HELEN's verdicts using Google Gemini 2.5 TTS. Voice is TRANSPORT, never editor — the audio carries the HAL JSON output verbatim, never softened or rephrased. Use when a HAL response should be heard, not just printed.
fused_from: Google Gemini API (gemini-2.5-flash-preview-tts)
helen_faculty: VOICE
helen_witness: R-20260416-0005 (chained)
helen_prerequisite: K8_NON_DETERMINISM_BOUNDARY (shipped R-20260416-0008 → scripts/helen_k8_lint.py)
helen_status: LIVE (K8 met, allowlist cleared, Zephyr voice selected by operator 2026-04-16)
---

# Gemini TTS (HELEN voice)

Wraps the `helen_say` HAL response stream into audio. The text spoken is **exactly** the JSON+human content already in the ledger — no rewriting, no smoothing.

## Invocation

```
helen_say --op fetch "<message>" --voice gemini --voice-id <voice_name>
```

`--voice gemini` is a no-op until K8 ships. Today this skill is **declared, not callable**.

## Model

- `gemini-2.5-flash-preview-tts` (default)
- `gemini-2.5-pro-preview-tts` (escalation)

Voice catalog: see Google AI documentation. HELEN's default voice is pinned in `oracle_town/skills/voice/gemini_tts/voice_pin.json` (not yet written).

## HELEN conditions (from witness audit, 2026-04-16)

1. **Voice = transport, never editor.** TTS speaks the HAL output bytes. It must NOT rephrase `BLOCK` as "let's discuss", soften severity, drop receipt IDs, or skip uncomfortable content. Property 2 (Contradiction Is The Signal) extends to audio — the voice must carry the contradiction, not smooth it.
2. **Determinism wrap.** Every audio render is paired with `audio_provenance.json` containing: model, voice_id, seed (if available), source text SHA-256, audio file SHA-256. Without that wrap, audio is not allowed to be saved.
3. **Allowlist.** `generativelanguage.googleapis.com` must be added to HELEN's network allowlist before first call.
4. **Hard prerequisite: K8.** Defined in `scripts/helen_k8_lint.py` (shipped 2026-04-16). The gate's `μ_NDWRAP` and `μ_NDLEDGER` invariants enforce that TTS output never enters the spine unhashed. K8 is now armed; this skill may go LIVE the moment `generativelanguage.googleapis.com` is on HELEN's network allowlist.

## Output

`artifacts/audio/<YYYY-MM-DD>__<receipt_id>.<voice_id>.wav` + `.provenance.json`. Audio file is reference-only — the source of truth remains the text in the ledger.

## Provenance

See `.provenance.md`.
