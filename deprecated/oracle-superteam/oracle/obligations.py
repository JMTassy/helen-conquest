# oracle/obligations.py
def obligations_from_votes(votes):
    """
    Deterministic mapping:
    - CONDITIONAL => domain-specific obligation based on team jurisdiction
    - QUARANTINE/REJECT => contradiction/validation obligation
    - OBJECT => may or may not block; policy here: OBJECT does not open obligation unless rationale indicates insufficiency.
    """
    obligations = []

    for v in votes:
        team = v.get("team")
        vote = v.get("vote")

        if vote == "CONDITIONAL":
            if team == "Engineering Wing":
                obligations.append(("METRICS_INSUFFICIENT", team, v.get("rationale","")))
            elif team == "Legal Office":
                obligations.append(("LEGAL_COMPLIANCE", team, v.get("rationale","")))
            elif team == "Security Sector":
                obligations.append(("SECURITY_THREAT", team, v.get("rationale","")))
            elif team == "Data Validation Office":
                obligations.append(("METRICS_INSUFFICIENT", team, v.get("rationale","")))
            else:
                obligations.append(("EVIDENCE_MISSING", team, v.get("rationale","")))

        if vote in {"QUARANTINE", "REJECT"}:
            obligations.append(("CONTRADICTION_DETECTED", team, v.get("rationale","")))

    # Deduplicate deterministically
    seen = set()
    out = []
    for (typ, owner, rationale) in obligations:
        key = (typ, owner)
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "type": typ,
            "owner_team": owner,
            "closure_criteria": rationale or f"Resolve {typ} flagged by {owner}.",
            "status": "OPEN",
        })
    return out

def add_contradiction_obligations(contradictions, existing_obligations):
    if not contradictions:
        return existing_obligations
    # Only add if not already present
    has = any(o["type"] == "CONTRADICTION_DETECTED" for o in existing_obligations)
    if has:
        return existing_obligations
    existing_obligations = list(existing_obligations)
    existing_obligations.append({
        "type": "CONTRADICTION_DETECTED",
        "owner_team": "Data Validation Office",
        "closure_criteria": "Resolve detected evidence-tag contradictions.",
        "status": "OPEN",
    })
    return existing_obligations
