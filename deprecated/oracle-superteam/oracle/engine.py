# oracle/engine.py
import uuid
from oracle.config import OracleConfig
from oracle.adjudication import adjudicate
from oracle.qi_int_v2 import compute_qi_int_v2
from oracle.verdict import decide
from oracle.manifest import build_manifest

def run_oracle(payload: dict, code_version: str = "git::<PINNED_HASH>") -> dict:
    cfg = OracleConfig()

    claim = payload["claim"]
    evidence = payload.get("evidence", [])
    votes = payload.get("votes", [])

    event_log = []
    event_log.append({"t": payload.get("t0","__TS__"), "event": "CLAIM_CREATED", "by": claim.get("owner_team","unknown")})
    event_log.append({"t": payload.get("t0","__TS__"), "event": "VOTING_OPEN"})

    derived = adjudicate(claim, evidence, votes, cfg)

    # QI-INT: if kill-switch or rule-kill => score optional; keep deterministic output anyway
    if derived["kill_switch_triggered"] or derived["rule_kill_triggered"]:
        qi = {"A_c": {"re": 0.0, "im": 0.0}, "S_c": 0.0}
    else:
        q = compute_qi_int_v2(claim.get("tier","Tier III"), votes, cfg)
        qi = {"A_c": {"re": round(q.A_re, 4), "im": round(q.A_im, 4)}, "S_c": round(q.S, 4)}

    event_log.append({"t": payload.get("t1","__TS__"), "event": "SCORING_COMPLETED", "value": {"S_c": qi["S_c"]}})

    decision = decide(derived, qi["S_c"], cfg)
    event_log.append({"t": payload.get("t2","__TS__"), "event": "FINALIZED", "value": decision["final"]})

    if decision["ship_permitted"]:
        event_log.append({"t": payload.get("t2","__TS__"), "event": "SHIPPED", "value": True})

    cfg_public = {
        "qi_int_version": cfg.qi_int_version,
        "thresholds": {"accept": cfg.tau_accept, "quarantine": cfg.tau_quarantine},
        "team_weights": cfg.team_weights,
        "tier_magnitude_table": cfg.tier_mag,
        "vote_phase_table": {k: str(v) for k,v in cfg.vote_phase.items()},
        "canonicalization": {
            "votes_sort_key": "team",
            "exclude_fields_from_hash": sorted(list(cfg.exclude_from_hash)),
        }
    }

    run_id = f"uuid::{payload.get('scenario_id','NA')}::{uuid.uuid4()}"
    manifest = build_manifest(
        claim=claim,
        evidence=evidence,
        votes=votes,
        cfg=cfg_public,
        derived=derived,
        qi=qi,
        decision=decision,
        event_log=event_log,
        run_id=run_id,
        code_version=code_version,
    )
    return manifest
