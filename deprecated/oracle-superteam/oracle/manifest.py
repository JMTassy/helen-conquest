# oracle/manifest.py
from datetime import datetime, timezone
from oracle.canonical import sha256_hex

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def build_manifest(claim: dict, evidence: list, votes: list, cfg: dict, derived: dict, qi: dict, decision: dict, event_log: list, run_id: str, code_version: str):
    manifest = {
        "run_id": run_id,
        "timestamp_start": now_iso(),
        "timestamp_end": now_iso(),
        "code_version": code_version,
        "config": cfg,
        "claim": claim,
        "evidence": evidence,
        "votes": votes,
        "derived": {
            **derived,
            "qi_int": qi,
        },
        "decision": decision,
        "event_log": event_log,
    }

    # Hash inputs and outputs deterministically
    inputs_view = {
        "config": cfg,
        "claim": claim,
        "evidence": evidence,
        "votes": votes,
    }
    outputs_view = {
        "derived": manifest["derived"],
        "decision": decision,
    }

    manifest["hashes"] = {
        "inputs_hash": "sha256:" + sha256_hex(inputs_view),
        "outputs_hash": "sha256:" + sha256_hex(outputs_view),
    }
    return manifest
