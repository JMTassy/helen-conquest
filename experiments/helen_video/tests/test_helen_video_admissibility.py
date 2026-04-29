"""HELEN video admissibility stack — invariant tests.

Confirms:
  1. Ralph cannot ship (no delivery path exists)
  2. Delivery cannot read candidates (only ACCEPTED ledger entries)
  3. ACCEPTED requires receipt (no receipt → REJECT)
  4. Ledger is append-only (verify_chain, no deletion)
"""
import hashlib
import pytest

from helen_video.admissibility_gate import (
    evaluate, verify_receipt_binding, VISUAL_COHERENCE_MIN, PIPELINE_SALT,
    HysteresisGate, HysteresisState, KEEP_FLOOR, REJECT_CEIL, PENALTY_STEP, PENALTY_CAP,
)
from helen_video.ralph_generator import generate_candidate, extract_receipt
from helen_video.video_ledger import VideoLedger


def _bound_receipt(content_hash: str = "abc123", **overrides) -> dict:
    """Build a receipt with a valid cryptographic binding."""
    pipeline_hash = hashlib.sha256((content_hash + PIPELINE_SALT).encode()).hexdigest()
    base = {
        "content_hash": content_hash,
        "pipeline_hash": pipeline_hash,
        "state_hash": "ghi789",
        "model_signature": "kling-v1",
        "visual_coherence": 0.85,
        "temporal_alignment": 0.75,
    }
    base.update(overrides)
    return base


_GOOD_RECEIPT = _bound_receipt()


# ── Invariant 1: Ralph cannot ship ────────────────────────────────────────────

def test_ralph_has_no_deliver_method():
    import helen_video.ralph_generator as rg
    public = [n for n in dir(rg) if not n.startswith("_") and callable(getattr(rg, n))]
    delivery_names = {"deliver", "ship", "send", "push", "publish", "export"}
    leaks = set(public) & delivery_names
    assert not leaks, f"ralph_generator exposes delivery methods: {leaks}"


def test_ralph_candidate_status_is_candidate():
    c = generate_candidate("test prompt")
    assert c["status"] == "CANDIDATE"
    assert c["receipt"] is None


def test_ralph_extract_receipt_is_not_implemented():
    with pytest.raises(NotImplementedError):
        extract_receipt({}, {})


# ── Invariant 2: Delivery cannot read candidates ───────────────────────────────

def test_ledger_accepted_excludes_candidates_and_rejected(tmp_path):
    ledger = VideoLedger(tmp_path / "v.ndjson")
    ledger.append("v1", "REJECTED", _GOOD_RECEIPT, "failed gate")
    ledger.append("v2", "PENDING", _GOOD_RECEIPT, "missing metrics")
    ledger.append("v3", "ACCEPTED", _GOOD_RECEIPT, "gate passed")
    accepted = ledger.accepted()
    ids = [e["video_id"] for e in accepted]
    assert ids == ["v3"]
    assert "v1" not in ids
    assert "v2" not in ids


def test_superseded_not_in_accepted(tmp_path):
    ledger = VideoLedger(tmp_path / "v.ndjson")
    ledger.append("v1", "ACCEPTED", _GOOD_RECEIPT, "gate passed")
    ledger.supersede("v1", "replaced by v2")
    accepted = [e["video_id"] for e in ledger.accepted()]
    assert "v1" not in accepted


# ── Invariant 3: ACCEPTED requires receipt ─────────────────────────────────────

def test_no_receipt_is_rejected():
    verdict = evaluate({}, None)
    assert verdict.decision == "REJECT"
    assert "receipt" in verdict.reason.lower()


def test_missing_required_fields_is_rejected():
    verdict = evaluate({}, {"visual_coherence": 0.9})  # missing content_hash, pipeline_hash
    assert verdict.decision == "REJECT"
    assert "missing" in verdict.reason.lower()


def test_low_visual_coherence_is_rejected():
    receipt = {**_GOOD_RECEIPT, "visual_coherence": 0.4}
    verdict = evaluate({}, receipt)
    assert verdict.decision == "REJECT"
    assert "visual_coherence" in verdict.reason


def test_low_temporal_alignment_is_rejected():
    receipt = {**_GOOD_RECEIPT, "temporal_alignment": 0.1}
    verdict = evaluate({}, receipt)
    assert verdict.decision == "REJECT"
    assert "temporal_alignment" in verdict.reason


def test_absent_metrics_is_pending():
    receipt = {k: v for k, v in _GOOD_RECEIPT.items()
               if k not in ("visual_coherence", "temporal_alignment")}
    verdict = evaluate({}, receipt)
    assert verdict.decision == "PENDING"
    assert "missing" in verdict.reason.lower()


def test_partial_metrics_is_pending():
    receipt = {**_GOOD_RECEIPT}
    del receipt["temporal_alignment"]
    verdict = evaluate({}, receipt)
    assert verdict.decision == "PENDING"


def test_full_good_receipt_is_accepted():
    verdict = evaluate({}, _GOOD_RECEIPT)
    assert verdict.decision == "ACCEPT"


# ── Receipt binding ────────────────────────────────────────────────────────────

def test_valid_binding_passes():
    assert verify_receipt_binding(_GOOD_RECEIPT) is True


def test_forged_pipeline_hash_is_rejected():
    forged = {**_GOOD_RECEIPT, "pipeline_hash": "arbitrary_string"}
    verdict = evaluate({}, forged)
    assert verdict.decision == "REJECT"
    assert "binding" in verdict.reason


# ── Invariant 4: Ledger is append-only ────────────────────────────────────────

def test_ledger_chain_is_valid_after_appends(tmp_path):
    ledger = VideoLedger(tmp_path / "v.ndjson")
    ledger.append("v1", "ACCEPTED", _GOOD_RECEIPT, "ok")
    ledger.append("v2", "REJECTED", None, "no receipt")
    assert ledger.verify_chain() is True


def test_ledger_supersede_appends_not_mutates(tmp_path):
    ledger = VideoLedger(tmp_path / "v.ndjson")
    ledger.append("v1", "ACCEPTED", _GOOD_RECEIPT, "ok")
    ledger.supersede("v1", "replaced")
    entries = ledger._read_all()
    assert len(entries) == 2
    assert entries[0]["status"] == "ACCEPTED"   # original unchanged
    assert entries[1]["status"] == "SUPERSEDED"  # new entry added


def test_tampered_entry_fails_chain(tmp_path):
    ledger = VideoLedger(tmp_path / "v.ndjson")
    ledger.append("v1", "ACCEPTED", _GOOD_RECEIPT, "ok")
    # Tamper with the file
    with (tmp_path / "v.ndjson").open("r+") as f:
        content = f.read()
        f.seek(0)
        f.write(content.replace('"ACCEPTED"', '"REJECTED"'))
    assert ledger.verify_chain() is False


def test_empty_ledger_chain_is_valid(tmp_path):
    ledger = VideoLedger(tmp_path / "v.ndjson")
    assert ledger.verify_chain() is True


# ── hysteresis gate ────────────────────────────────────────────────────────────

def _hysteresis_receipt(vc=0.85, ta=0.75, content_hash="abc123"):
    ph = hashlib.sha256((content_hash + PIPELINE_SALT).encode()).hexdigest()
    return {"content_hash": content_hash, "pipeline_hash": ph,
            "visual_coherence": vc, "temporal_alignment": ta}


_GOOD_CANDIDATE = {"character": "HELEN", "scene": "oracle", "duration": 5, "style": "cinematic"}


def test_hysteresis_state_default_floor():
    s = HysteresisState()
    assert s.effective_keep_floor() == KEEP_FLOOR


def test_hysteresis_state_penalty_accumulates():
    s = HysteresisState(reject_count=2)
    assert abs(s.effective_keep_floor() - (KEEP_FLOOR + 2 * PENALTY_STEP)) < 1e-9


def test_hysteresis_state_penalty_capped():
    s = HysteresisState(reject_count=100)
    assert s.effective_keep_floor() == KEEP_FLOOR + PENALTY_CAP


def test_combined_score_both_present():
    g = HysteresisGate()
    r = _hysteresis_receipt(vc=0.9, ta=0.7)
    assert abs(g.combined_score(r) - 0.8) < 1e-9


def test_combined_score_missing_returns_none():
    g = HysteresisGate()
    assert g.combined_score({"visual_coherence": 0.9}) is None
    assert g.combined_score({}) is None


def test_hysteresis_clean_accept_above_floor():
    """Score well above KEEP_FLOOR → ACCEPT, no penalty."""
    g = HysteresisGate()
    r = _hysteresis_receipt(vc=0.95, ta=0.95)
    v = g.evaluate(_GOOD_CANDIDATE, r, clip_id="c1")
    assert v.decision == "ACCEPT"


def test_hysteresis_borderline_below_floor_is_pending():
    """vc=0.75, ta=0.65 → combined=0.70 < KEEP_FLOOR(0.80) → PENDING."""
    g = HysteresisGate()
    r = _hysteresis_receipt(vc=0.75, ta=0.65)
    v = g.evaluate(_GOOD_CANDIDATE, r, clip_id="c2")
    assert v.decision == "PENDING"
    assert "effective keep floor" in v.reason


def test_hysteresis_reject_increments_penalty():
    """A structural REJECT (no receipt) raises reject_count."""
    g = HysteresisGate()
    g.evaluate(_GOOD_CANDIDATE, None, clip_id="c3")
    assert g._memory["c3"].reject_count == 1


def test_hysteresis_penalty_raises_floor_after_rejects():
    """After 4 rejects, effective floor = KEEP_FLOOR + PENALTY_CAP."""
    g = HysteresisGate()
    for _ in range(4):
        g.evaluate(_GOOD_CANDIDATE, None, clip_id="c4")
    s = g._memory["c4"]
    assert s.effective_keep_floor() == KEEP_FLOOR + PENALTY_CAP


def test_hysteresis_accept_clears_penalty_memory():
    """A clean ACCEPT resets the clip's rejection memory.

    reject_count=3 → effective_floor=0.95; use vc=ta=0.99 (sc=0.99) to clear safely.
    """
    g = HysteresisGate()
    g._memory["c5"] = HysteresisState(reject_count=3)
    r = _hysteresis_receipt(vc=0.99, ta=0.99)
    v = g.evaluate(_GOOD_CANDIDATE, r, clip_id="c5")
    assert v.decision == "ACCEPT"
    assert "c5" not in g._memory


def test_hysteresis_no_clip_id_is_stateless():
    """clip_id=None → no state written, no error."""
    g = HysteresisGate()
    g.evaluate(_GOOD_CANDIDATE, None, clip_id=None)
    assert g._memory == {}


def test_hysteresis_pending_from_structural_gate_propagates():
    """Missing metrics → PENDING from structural gate propagates unchanged."""
    g = HysteresisGate()
    ph = hashlib.sha256(("abc123" + PIPELINE_SALT).encode()).hexdigest()
    r = {"content_hash": "abc123", "pipeline_hash": ph}  # no vc/ta
    v = g.evaluate(_GOOD_CANDIDATE, r, clip_id="c6")
    assert v.decision == "PENDING"
