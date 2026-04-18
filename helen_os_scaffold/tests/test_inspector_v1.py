"""
tests/test_inspector_v1.py — InnerWorldV1 self-inspection schemas + CanonicalizerV1

Tests:
  IN1.1  InnerWorldSnapshotV1 validates required fields + rejects bad candidates_count
  IN1.2  InnerWorldSnapshotV1.to_receipt_payload() contains all required keys
  IN2.1  DeterminismReportV1 CONFIRMED: N=5 identical hashes → DETERMINISM_CONFIRMED
  IN2.2  DeterminismReportV1 DETECTED: mixed hashes → NONDETERMINISM_DETECTED
  IN2.3  DeterminismReportV1 UNCERTIFIABLE: config_id UNKNOWN → UNCERTIFIABLE
  IN2.4  make_determinism_report() derives verdict automatically from hashes
  IN3.1  GroundingReportV1 PASS: all OBSERVED + no NDQ → PASS
  IN3.2  GroundingReportV1 FAIL: SPECULATIVE claims above threshold → FAIL
  IN3.3  GroundingReportV1 FAIL: flagged NDQ → FAIL regardless of rate
  IN3.4  make_grounding_report() builds report from AtomicClaim list
  IN4.1  CanonicalizerV1 idempotence: f(f(x)).hash == f(x).hash
  IN4.2  CanonicalizerV1 normalizes CRLF, trailing whitespace, blank lines
  IN4.3  CanonicalizerV1 JSON path: sorts keys + no whitespace
  IN4.4  CanonicalizerV1 two distinct texts → distinct hashes
  IN5.1  ClaimSegmenterV1 segments text into AtomicClaims with passport=UNKNOWN
  IN5.2  ClaimSegmenterV1 flags claims containing numbers/dates/quotes
  IN5.3  ClaimSegmenterV1 filters short segments (< MIN_CLAIM_LENGTH)
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helen_os.meta.inspector import (
    InnerWorldSnapshotV1,
    DeterminismReportV1, DriftSummary,
    GroundingReportV1,
    AtomicClaim, SpanPointerV1,
    make_determinism_report, make_grounding_report,
    DETERMINISM_MIN_RUNS, GROUNDING_MAX_UNGROUNDED_RATE,
)
from helen_os.meta.canonicalizer_v1 import (
    CanonicalizerV1,
    CanonicalizationError,
    canonicalize_text, canonical_text_hash,
)
from helen_os.meta.claim_segmenter import ClaimSegmenterV1, MIN_CLAIM_LENGTH


# ── Helpers ───────────────────────────────────────────────────────────────────

NOW = datetime.now(timezone.utc).isoformat()

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def _make_inner_world(**overrides) -> InnerWorldSnapshotV1:
    defaults = dict(
        constraint_stack_hash = _sha256("constraints::v1"),
        input_digest          = _sha256("user input text"),
        candidates_count      = 3,
        selection_policy_id   = "POLICY_V1::abc12345",
        uncertainty_summary   = {"OBSERVED": 5, "INFERRED": 2, "SPECULATIVE": 0, "UNKNOWN": 1},
        snapshot_at           = NOW,
    )
    defaults.update(overrides)
    return InnerWorldSnapshotV1(**defaults)


def _make_observed_claim(claim_id: str = "CL-001") -> AtomicClaim:
    return AtomicClaim(
        claim_id     = claim_id,
        text         = "The sky appears blue due to Rayleigh scattering",
        passport     = "OBSERVED",
        span_pointer = SpanPointerV1(
            start_byte  = 0,
            end_byte    = 50,
            text_hash   = _sha256("span text")[:16],
            quoted_text = "The sky appears blue",
        ),
    )


def _make_inferred_claim(claim_id: str = "CL-002") -> AtomicClaim:
    return AtomicClaim(
        claim_id        = claim_id,
        text            = "If water temperature exceeds the boiling point it vaporizes",
        passport        = "INFERRED",
        inference_rule  = "thermodynamics::boiling_point_rule",
        premises        = ["CL-001"],
    )


def _make_unknown_claim(claim_id: str = "CL-003") -> AtomicClaim:
    return AtomicClaim.model_construct(
        claim_id       = claim_id,
        text           = "Unclassified statement about the world",
        passport       = "UNKNOWN",
        span_pointer   = None,
        inference_rule = None,
        premises       = [],
        flagged        = False,
        flag_reason    = None,
    )


# ── IN1.x — InnerWorldSnapshotV1 ─────────────────────────────────────────────

def test_in1_1_inner_world_validates():
    """IN1.1 — InnerWorldSnapshotV1 validates correctly; rejects invalid candidates_count."""
    snap = _make_inner_world()
    assert snap.type == "INNER_WORLD_SNAPSHOT_V1"
    assert snap.candidates_count == 3
    assert "OBSERVED" in snap.uncertainty_summary

    # Must reject candidates_count < 1
    import pytest
    with pytest.raises(Exception):
        _make_inner_world(candidates_count=0)


def test_in1_2_inner_world_receipt_payload():
    """IN1.2 — to_receipt_payload() contains all required keys."""
    snap    = _make_inner_world()
    payload = snap.to_receipt_payload()

    required = {
        "type", "constraint_stack_hash", "input_digest",
        "candidates_count", "selection_policy_id",
        "uncertainty_summary", "snapshot_at",
    }
    missing = required - set(payload.keys())
    assert not missing, f"Missing keys in payload: {missing}"
    assert payload["type"] == "INNER_WORLD_SNAPSHOT_V1"
    assert payload["candidates_count"] == 3


# ── IN2.x — DeterminismReportV1 ──────────────────────────────────────────────

def test_in2_1_determinism_confirmed():
    """IN2.1 — N=5 identical hashes → DETERMINISM_CONFIRMED."""
    h = _sha256("same output every time")
    report = make_determinism_report(
        config_id = "MODEL::mistral-7b::DECODE::sha256abc::POLICY::v1",
        hashes    = [h] * 5,
    )

    assert report.verdict == "DETERMINISM_CONFIRMED"
    assert report.n_runs  == 5
    assert report.drift_summary == []
    assert len(set(report.hashes)) == 1

    payload = report.to_receipt_payload()
    assert payload["verdict"] == "DETERMINISM_CONFIRMED"
    assert payload["distinct_hashes"] == 1


def test_in2_2_nondeterminism_detected():
    """IN2.2 — Mixed hashes → NONDETERMINISM_DETECTED + non-empty drift_summary."""
    h1 = _sha256("output version A")
    h2 = _sha256("output version B")
    report = make_determinism_report(
        config_id = "MODEL::mistral-7b::DECODE::sha256abc::POLICY::v1",
        hashes    = [h1, h1, h2, h1, h1],
    )

    assert report.verdict == "NONDETERMINISM_DETECTED"
    assert len(report.drift_summary) > 0

    payload = report.to_receipt_payload()
    assert payload["drift_count"] > 0


def test_in2_3_uncertifiable():
    """IN2.3 — config_id starts with UNKNOWN → UNCERTIFIABLE."""
    report = make_determinism_report(
        config_id = "UNKNOWN::config",
        hashes    = [_sha256("x")] * 5,
    )
    assert report.verdict == "UNCERTIFIABLE"


def test_in2_4_make_determinism_too_few_runs():
    """IN2.4 — N < DETERMINISM_MIN_RUNS even if identical → NONDETERMINISM_DETECTED."""
    h = _sha256("same")
    report = make_determinism_report(
        config_id = "MODEL::test::DECODE::x::POLICY::v1",
        hashes    = [h] * (DETERMINISM_MIN_RUNS - 1),  # N=4, threshold=5
    )
    # Not CONFIRMED because n < threshold (falls through to NONDETERMINISM)
    assert report.verdict != "DETERMINISM_CONFIRMED"
    assert report.n_runs == DETERMINISM_MIN_RUNS - 1


# ── IN3.x — GroundingReportV1 ────────────────────────────────────────────────

def test_in3_1_grounding_pass():
    """IN3.1 — All OBSERVED + no NDQ → PASS."""
    claims = [_make_observed_claim(f"CL-{i:03d}") for i in range(1, 101)]
    report = make_grounding_report(claims)

    assert report.verdict                       == "PASS"
    assert report.atomic_claims_total           == 100
    assert report.observed_count                == 100
    assert report.unknown_count                 == 0
    assert report.speculative_count             == 0
    assert report.unsupported_numeric_date_quote_count == 0
    assert report.ungrounded_rate               == 0.0

    payload = report.to_receipt_payload()
    assert payload["verdict"] == "PASS"
    assert payload["failure_count"] == 0


def test_in3_2_grounding_fail_rate():
    """IN3.2 — SPECULATIVE claims above threshold → FAIL."""
    observed   = [_make_observed_claim(f"CL-{i:03d}") for i in range(1, 99)]
    speculative = AtomicClaim.model_construct(
        claim_id="CL-099", text="Unsubstantiated claim", passport="SPECULATIVE",
        span_pointer=None, inference_rule=None, premises=[], flagged=False, flag_reason=None,
    )
    unknown = AtomicClaim.model_construct(
        claim_id="CL-100", text="Unknown assertion here", passport="UNKNOWN",
        span_pointer=None, inference_rule=None, premises=[], flagged=False, flag_reason=None,
    )
    claims = observed + [speculative, unknown]
    report = make_grounding_report(claims)

    # ungrounded_rate = 2/100 = 0.02 > 0.01 → FAIL
    assert report.verdict == "FAIL"
    assert report.ungrounded_rate > GROUNDING_MAX_UNGROUNDED_RATE


def test_in3_3_grounding_fail_ndq():
    """
    IN3.3 — Flagged NDQ claim → FAIL regardless of ungrounded_rate.

    A SPECULATIVE claim that is flagged (contains a number) should produce
    FAIL even if the ungrounded_rate would otherwise be below threshold,
    because unsupported_numeric_date_quote_count > 0 is a hard block.
    """
    # SPECULATIVE + flagged (contains a number) — no span_pointer required
    flagged = AtomicClaim.model_construct(
        claim_id       = "CL-001",
        text           = "Revenue grew by 42 percent last quarter",
        passport       = "SPECULATIVE",
        span_pointer   = None,
        inference_rule = None,
        premises       = [],
        flagged        = True,
        flag_reason    = "Contains number: '42'",
    )
    report = make_grounding_report([flagged])

    assert report.verdict                               == "FAIL"
    assert report.unsupported_numeric_date_quote_count  == 1


def test_in3_4_make_grounding_report_from_list():
    """IN3.4 — make_grounding_report() counts correctly from mixed list."""
    observed = _make_observed_claim("CL-001")
    inferred = _make_inferred_claim("CL-002")
    unknown  = _make_unknown_claim("CL-003")
    report   = make_grounding_report([observed, inferred, unknown])

    assert report.atomic_claims_total == 3
    assert report.observed_count      == 1
    assert report.inferred_count      == 1
    assert report.unknown_count       == 1
    assert report.speculative_count   == 0


# ── IN4.x — CanonicalizerV1 ──────────────────────────────────────────────────

def test_in4_1_canonicalizer_idempotent():
    """IN4.1 — f(f(x)).hash == f(x).hash (idempotence)."""
    canon = CanonicalizerV1()
    text  = "Hello world\r\n  trailing   \n\n\n\nblank lines below\n\n"

    r1 = canon.canonicalize(text)
    r2 = canon.canonicalize(r1.canonical_text)

    assert r1.canonical_hash == r2.canonical_hash, (
        f"Idempotence violated:\n"
        f"  r1.hash={r1.canonical_hash[:16]}\n"
        f"  r2.hash={r2.canonical_hash[:16]}\n"
        f"  r1.text={r1.canonical_text!r}\n"
        f"  r2.text={r2.canonical_text!r}"
    )
    assert "R1" in r1.rules_applied
    assert "R6" in r1.rules_applied


def test_in4_2_canonicalizer_normalizes():
    """
    IN4.2 — CRLF → LF, trailing whitespace stripped, blank lines collapsed.

    Note: CanonicalizerV1 strips TRAILING whitespace from each line, not leading.
    Leading whitespace is preserved (e.g., indentation).
    The input "  trailing  " → "  trailing" (trailing spaces removed, indent kept).
    """
    canon = CanonicalizerV1()
    # "  trailing  " has both leading spaces (indent) and trailing spaces (to strip)
    messy = "Line one\r\n  trailing  \r\n\n\n\nLine three\n"
    result = canon.canonicalize(messy)

    # R1: no carriage returns
    assert "\r" not in result.canonical_text, "CRLF not normalized (\\r remains)"

    # R2: no line ends with spaces or tabs
    for line in result.canonical_text.split("\n"):
        assert not (line.endswith(" ") or line.endswith("\t")), (
            f"Trailing whitespace found on line: {line!r}"
        )

    # R3: multiple blank lines collapsed to max 1
    assert "\n\n\n" not in result.canonical_text, (
        "Multiple consecutive blank lines not collapsed"
    )

    # R5: trailing newline stripped — must end with "Line three"
    assert result.canonical_text.endswith("Line three"), (
        f"Expected 'Line three' at end, got: {result.canonical_text!r}"
    )

    # Content preserved
    assert "Line one" in result.canonical_text
    assert "trailing" in result.canonical_text


def test_in4_3_canonicalizer_json_path():
    """IN4.3 — JSON path: sorts keys, removes whitespace."""
    canon = CanonicalizerV1()
    text  = '{"z": 1, "a": 2, "m": [3, 1, 2]}'
    result = canon.canonicalize(text, is_json=True)

    expected = '{"a":2,"m":[3,1,2],"z":1}'
    assert result.canonical_text == expected, (
        f"Expected {expected!r}, got {result.canonical_text!r}"
    )
    assert "J1" in result.rules_applied
    assert "J2" in result.rules_applied


def test_in4_4_canonicalizer_distinct_texts():
    """IN4.4 — Two distinct canonical texts → distinct hashes."""
    h1 = canonical_text_hash("Alpha output")
    h2 = canonical_text_hash("Beta output")
    assert h1 != h2, "Distinct texts must produce distinct canonical hashes"
    assert len(h1) == 64
    assert len(h2) == 64


# ── IN5.x — ClaimSegmenterV1 ─────────────────────────────────────────────────

def test_in5_1_claim_segmenter_basic():
    """IN5.1 — Segments text into AtomicClaims with passport=UNKNOWN."""
    seg    = ClaimSegmenterV1()
    text   = "The sky is blue. Grass is green. Clouds are white."
    claims = seg.segment(text)

    assert len(claims) >= 2, f"Expected >= 2 claims, got {len(claims)}"
    for claim in claims:
        assert claim.passport == "UNKNOWN", (
            f"Segmenter must output UNKNOWN passports, got {claim.passport!r}"
        )
        assert claim.claim_id.startswith("CL-")
        assert len(claim.text) >= MIN_CLAIM_LENGTH


def test_in5_2_claim_segmenter_flags_ndq():
    """IN5.2 — Claims with numbers/dates/quotes are flagged."""
    seg  = ClaimSegmenterV1()
    text = 'Revenue grew by 42% in 2024. "This is quoted." March was cold.'
    claims = seg.segment(text)

    flagged = [c for c in claims if c.flagged]
    assert len(flagged) >= 1, (
        f"Expected at least 1 flagged claim, got 0. Claims: {[(c.text, c.flagged) for c in claims]}"
    )
    for fc in flagged:
        assert fc.flag_reason is not None, "Flagged claim must have a flag_reason"


def test_in5_3_claim_segmenter_filters_short():
    """IN5.3 — Segments shorter than MIN_CLAIM_LENGTH are excluded."""
    seg  = ClaimSegmenterV1()
    text = "Hi. This is a complete and well-formed claim about the world."
    claims = seg.segment(text)

    for claim in claims:
        assert len(claim.text) >= MIN_CLAIM_LENGTH, (
            f"Short segment leaked through: {claim.text!r}"
        )
