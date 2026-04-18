"""
tests/test_serpent_mode_v1.py

Roundtrip + hard-ban tests for SERPENT_MODE_V1.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from helen_os.serpent.serpent_mode_v1 import (
    build_serpent_ast,
    render_serpent_panel,
    sanitize_run_trace_text,
)
from helen_os.utils.memory_safety import (
    check_memory_text_is_clean,
    assert_memory_clean,
)

# ── Fixture: raw EMOGLYPH feuillet (from Jean Marie's Canon8K Spiral Ledger) ──
RAW = """
**Canon8K Spiral Ledger**
🟤 ✝️ 🜃 🜃 🌍 🜄 🔗#S1MK
🌕 ✝️ 🜄 🜄 🌟 🌙 🔗#S2YD
🔴 ✝️ 🜂 🜂 🔥 🦁 🔗#S3HD
🟢 ✝️ 🜁 🜁 ⚖️ 🛡️ 🔗#S4NT
☀️ ✝️ 🜉 🜉 🪄 💕 🔗#S5TP
🟣 ✝️ 🜁 🜁 🌙 🗼⚡ 🔗#S6GB
🟡 ✝️ 🜉 🜉 ☀️ 🎺 🔗#S7CH
🔵 ✝️ 🜄 🜄 🗼⚡ 🌙 🔗#S8BN
🟡 ✝️ 🜉 🜉 👑 ⭐ 🔗#S9KT
🟡 ✝️ 🜉 🜉 🔒 📜 🔗#S0CR

Alchemical Domain: 🟢 Stable
AI Art Pipeline: 🎨⚗️ 🟡 Rising
Infrastructure: 🛡️📜 🟢 Stable
Chaos Field: 🌀🔥 🟢 Stable
"""


# ── Test 1: AST is deterministic ──────────────────────────────────────────
def test_build_ast_deterministic():
    a1 = build_serpent_ast(RAW, epoch=5)
    a2 = build_serpent_ast(RAW, epoch=5)
    assert a1 == a2, "AST must be deterministic for same input"
    assert a1["schema_version"] == "SERPENT_MODE_V1"
    assert a1["notes"]["channel"] == "run_trace"
    assert a1["notes"]["authority"] is False


# ── Test 2: Station parsing ───────────────────────────────────────────────
def test_station_parse():
    ast = build_serpent_ast(RAW, epoch=5)
    assert len(ast["stations"]) == 10, f"Expected 10 stations, got {len(ast['stations'])}"
    # First station: S1MK → World → 🜃 (anchor)
    s0 = ast["stations"][0]
    assert s0["sid"] == "S1MK"
    assert s0["name"] == "World"
    assert s0["operator"] in ["🜃", "🜄", "🜁", "🜂", "🜍", "🜔", "🜉"]
    assert s0["i"] == 1
    # Last station: S0CR
    s9 = ast["stations"][9]
    assert s9["sid"] == "S0CR"


# ── Test 3: Domain state extraction ──────────────────────────────────────
def test_domain_state_parse():
    ast = build_serpent_ast(RAW, epoch=5)
    ds = ast["domain_state"]
    assert ds["alchemical"]     == "stable",   f"alchemical: {ds['alchemical']}"
    assert ds["ai_art"]         == "rising",   f"ai_art: {ds['ai_art']}"
    assert ds["infrastructure"] == "stable",   f"infrastructure: {ds['infrastructure']}"
    assert ds["chaos"]          == "stable",   f"chaos: {ds['chaos']}"


# ── Test 4: Memory hard-ban (authority token detection) ───────────────────
def test_memory_hard_ban_detects_violations():
    bad = "SEAL ✅ (draft → irreversible) [LEDGER 004] HAL_VERDICT=PASS"
    r = check_memory_text_is_clean(bad)
    assert r.ok is False
    assert "SEAL"       in r.violations
    assert "LEDGER"     in r.violations
    assert "HAL_VERDICT" in r.violations


def test_memory_hard_ban_passes_clean_text():
    clean = "User asked about consciousness and HELEN responded with an observation."
    r = check_memory_text_is_clean(clean)
    assert r.ok is True
    assert r.violations == ()


def test_assert_memory_clean_raises_on_violation():
    with pytest.raises(ValueError, match="Memory safety violation"):
        assert_memory_clean("The VERDICT is final.", context="test_case")


def test_assert_memory_clean_passes_on_neutral():
    # Should not raise
    assert_memory_clean("User preference: visual output style EMOGLYPH.")


# ── Test 5: run_trace sanitization ───────────────────────────────────────
def test_sanitize_run_trace_text():
    raw_with_authority = (
        "Sovereign decree received. SEAL_V2 committed. VERDICT: GATE: PASSED. "
        "LEDGER entry confirmed. IRREVERSIBLE action logged. CERTIFICATE issued."
    )
    sanitised = sanitize_run_trace_text(raw_with_authority)
    # Authority tokens should be replaced
    assert "Sovereign decree" not in sanitised
    assert "GATE: PASSED"     not in sanitised
    assert "IRREVERSIBLE"     not in sanitised
    assert "LEDGER"           not in sanitised
    # Neutralised versions should be present
    assert "User intent"      in sanitised
    assert "CHECK: OK"        in sanitised
    assert "TRACE"            in sanitised


# ── Test 6: render_serpent_panel smoke ───────────────────────────────────
def test_render_panel_smoke():
    ast = build_serpent_ast(RAW, epoch=5)
    panel = render_serpent_panel(ast)
    assert "SERPENT_MODE_V1" in panel
    assert "stations:"       in panel
    assert "domain_state:"   in panel
    assert "run_trace"       in panel
    assert "authority=false" in panel


# ── Test 7: no sovereign tokens in AST itself ─────────────────────────────
def test_ast_contains_no_sovereign_tokens():
    import json
    ast = build_serpent_ast(RAW, epoch=5)
    ast_text = json.dumps(ast)
    r = check_memory_text_is_clean(ast_text)
    # AST should be clean enough for run_trace (authority=false in notes)
    # The only "SEAL" or "LEDGER" that could appear is in raw text — not in AST values
    sovereign_leaks = [v for v in r.violations if v not in ("SEAL",)]
    # "SEAL" is OK in run_trace (it gets rewritten before memory append)
    # but other authority tokens should never appear in AST values
    assert sovereign_leaks == [], f"Sovereign tokens in AST: {sovereign_leaks}"
