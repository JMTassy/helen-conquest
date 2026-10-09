"""EGREGOR DAILY: full cycle with fixture lanes (no model, no network)."""
import json
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import egregor_daily as ed  # noqa: E402

SECRET_RAW = "RAW-ONLY-TEXT-zebra-7731"
SEEN = {}


def goblin(prompt):
    SEEN.setdefault("GOBLIN", []).append(prompt)
    return 'Sure! ```json\n{"seeds": [{"raw_fragments": ["zebra"], "motifs": ["stripes"], "wild_connections": ["ledger as barcode"],' \
           ' "why_it_feels_interesting": "the stripes look like a ledger barcode", "input_type": "fragment", "authority": true}]}```'


def her(prompt):
    SEEN["HER"] = prompt
    ids = sorted(set(__import__("re").findall(r"SEED-[a-f0-9]{8}", prompt)))
    return json.dumps({"insights": [
        {"derived_from_seed_ids": ids[:2], "insight_sentence": "Receipts behave like stripes on a zebra", "resonance": "strong visual rhyme",
         "possible_use": "teach the ledger with a picture", "uncertainty": "high, one image only", "evidence_needed": "a user test with five people"},
        {"derived_from_seed_ids": ["SEED-deadbeef"], "insight_sentence": "hallucinated lineage should be refused", "resonance": "none at all here",
         "possible_use": "nothing, it is a test", "uncertainty": "this seed does not exist", "evidence_needed": "a real seed id"}]})


def hal(prompt):
    SEEN["HAL"] = prompt
    iid = __import__("re").findall(r"INS-[a-f0-9]{8}", prompt)[0]
    return json.dumps({"claims": [
        {"derived_from_insight_id": iid, "claim_sentence": "Hash chains make tampering with receipts detectable", "claim_type": "governance",
         "evidence_refs": [], "evidence_requirement": "a replay that detects one altered receipt", "test_or_review_path": "run the replay test with a mutated fixture",
         "risk_if_wrong": "false sense of integrity", "hal_reason": "it is directly testable with existing fixtures"},
        {"derived_from_insight_id": iid, "claim_sentence": "an invalid claim type must be refused", "claim_type": "vibes", "evidence_refs": [],
         "evidence_requirement": "", "test_or_review_path": "", "risk_if_wrong": "", "hal_reason": ""},
        {"derived_from_insight_id": iid, "claim_sentence": "over cadence", "claim_type": "other", "evidence_refs": [],
         "evidence_requirement": "", "test_or_review_path": "", "risk_if_wrong": "", "hal_reason": ""}]})


def mayor(prompt):
    SEEN["MAYOR"] = prompt
    cid = __import__("re").findall(r"CLM-[a-f0-9]{8}", prompt)[0]
    return json.dumps({"validation": {"claim_id": cid, "mayor_verdict": "HOLD", "evidence_inspected": ["claim text"],
                                      "missing_evidence": "a replay run", "reason": "promising but untested", "dissent": "",
                                      "next_gate": "ADMISSION_REVIEW", "authority": True}})


def broken(prompt):
    raise OSError("lane offline")


def make_cfg(tmp_path, roles=None, **lanes):
    repo = tmp_path / "helen"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "a.txt").write_text("x")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "feat: ledger replay"], cwd=repo, check=True)
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "note.md").write_text(SECRET_RAW)
    (inbox / "image.png").write_bytes(b"\x89PNG")
    fns = {"goblin": goblin, "her": her, "hal": hal, "mayor": mayor, **lanes}
    return {"output_root": str(tmp_path / "out"), "max_input_chars": 6000, "timeout_seconds": 5,
            "inputs": {"repo": {"enabled": True, "path": str(repo), "since_hours": 24},
                       "inbox": {"enabled": True, "path": str(inbox)},
                       "gmail": {"enabled": False}},
            "roles": roles or {"GOBLIN": "goblin", "HER": "her", "HAL": "hal", "MAYOR": "mayor"},
            "lanes": {k: {"kind": "fixture", "fn": v} for k, v in fns.items()},
            "cadence": {"inputs_per_run": 10, "seeds_per_input": 2, "seeds_per_run": 20, "insights_max": 5,
                        "claims_max": 2, "validation_per_run": 1}}


def test_full_cycle_blindness_and_governance_fields(tmp_path):
    SEEN.clear()
    cfg = make_cfg(tmp_path)
    out, r = ed.run(cfg, "2026-10-09")
    assert r["counts"] == {"inputs": 2, "seeds": 2, "insights": 1, "claims": 1, "validations": 1}
    # blindness: raw text reaches GOBLIN only; MAYOR never sees insight/seed lineage
    assert any(SECRET_RAW in p for p in SEEN["GOBLIN"])
    for role in ("HER", "HAL", "MAYOR"):
        assert SECRET_RAW not in SEEN[role]
    assert "INS-" not in SEEN["MAYOR"] and "SEED-" not in SEEN["MAYOR"]
    assert "SEED-" not in SEEN["HAL"] or "derived_from_seed_ids" in SEEN["HAL"]  # HAL sees insight lineage fields only
    # governance fields are set by the runner, never by a lane
    seed = json.loads(next((out / "compost").glob("*.json")).read_text())
    assert seed["authority"] is False and seed["actor"] == "GOBLIN" and seed["claim_status"] == "NO_CLAIM"
    val = json.loads(next((out / "validation").glob("*.json")).read_text())
    assert val["authority"] is False and val["next_gate"] == "HOLD_QUEUE" and val["ledger_effect"] == "none"
    # every artifact validates against the superteam schemas
    for folder, schema in (("compost", "dream_seed_v0"), ("insights", "insight_candidate_v0"),
                           ("claims", "claim_candidate_v0"), ("validation", "validation_receipt_candidate_v0")):
        for f in (out / folder).glob("*.json"):
            assert ed.validate(json.loads(f.read_text()), schema) == []


def test_receipt_records_rejections_cadence_and_what_each_lane_saw(tmp_path):
    cfg = make_cfg(tmp_path)
    out, r = ed.run(cfg, "2026-10-09")
    calls = {c["stage"]: c for c in r["calls"] if c["stage"] != "GOBLIN"}
    assert calls["HER"]["rejected"][0]["errors"] == ["no valid derived_from_seed_ids"]   # hallucinated lineage refused
    assert len(calls["HAL"]["kept"]) == 1 and calls["HAL"]["over_cadence_dropped"] == 1    # 3 proposed, cap 2, 1 invalid
    assert calls["MAYOR"]["saw"] == calls["HAL"]["kept"]
    assert all("prompt_sha256" in c for c in r["calls"])
    assert r["coverage"]["inbox"]["skipped"] == ["image.png: unsupported type"]
    assert r["coverage"]["gmail"]["status"] == "skipped"
    brief = (out / "BRIEF.md").read_text()
    assert "authority=false" in brief and "HOLD" in brief and "nothing was admitted" in brief
    # inbox files are archived; the unsupported one stays for a human
    assert (tmp_path / "inbox/done/2026-10-09/note.md").exists() and (tmp_path / "inbox/image.png").exists()


def test_lane_failure_is_recorded_and_downstream_stops(tmp_path):
    cfg = make_cfg(tmp_path, her=broken)
    out, r = ed.run(cfg, "2026-10-09")
    assert r["counts"]["insights"] == 0 and r["counts"]["claims"] == 0 and r["counts"]["validations"] == 0
    assert any(c["stage"] == "HER" and "lane offline" in c["error"] for c in r["calls"])
    assert "lane offline" in (out / "BRIEF.md").read_text()


def test_one_run_per_day(tmp_path):
    cfg = make_cfg(tmp_path)
    ed.run(cfg, "2026-10-09")
    with pytest.raises(SystemExit):
        ed.run(cfg, "2026-10-09")


def test_extract_json_from_chatty_answers():
    assert ed.extract_json('Here you go:\n```json\n{"a": {"b": 1}}\n```') == {"a": {"b": 1}}
    with pytest.raises(ValueError):
        ed.extract_json("no json here")


def test_example_config_is_complete():
    cfg = ed.load_config(HERE / "egregor.config.example.yaml")
    assert set(cfg["roles"]) == {"GOBLIN", "HER", "HAL", "MAYOR"}
    assert all(cfg["roles"][r] in cfg["lanes"] for r in cfg["roles"])
    assert cfg["lanes"][cfg["roles"]["HAL"]]["kind"] == "cli" and cfg["lanes"][cfg["roles"]["MAYOR"]]["cmd"][0] == "codex"
