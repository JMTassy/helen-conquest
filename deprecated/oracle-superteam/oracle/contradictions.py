# oracle/contradictions.py

def evidence_tags(evidence_list):
    tags = set()
    for e in evidence_list or []:
        for t in e.get("tags", []):
            tags.add(t)
    return tags

def detect_contradictions(evidence_list):
    tags = evidence_tags(evidence_list)

    contradictions = []

    # HC-PRIV-001: "no_personal_data" vs biometric/face/pii
    if ("no_personal_data_claim" in tags or "anonymous_claim" in tags) and (
        "biometric" in tags or "face" in tags or "pii" in tags or "gdpr_special_category" in tags
    ):
        contradictions.append({
            "rule_id": "HC-PRIV-001",
            "triggered_on": ["no_personal_data_claim", "biometric"],
            "severity": "HIGH",
        })

    # HC-SEC-002: provably secure vs heuristic-only
    if ("provably_secure_claim" in tags or "formal_proof_claim" in tags) and (
        "heuristic_only" in tags or "no_formal_proof" in tags
    ):
        contradictions.append({
            "rule_id": "HC-SEC-002",
            "triggered_on": ["provably_secure_claim", "heuristic_only"],
            "severity": "MEDIUM",
        })

    # HC-LEGAL-003: gdpr compliant vs export without SCC
    if ("gdpr_compliant_claim" in tags or "gdpr_safe_claim" in tags) and ("no_scc" in tags):
        contradictions.append({
            "rule_id": "HC-LEGAL-003",
            "triggered_on": ["gdpr_compliant_claim", "no_scc"],
            "severity": "MEDIUM",
        })

    return contradictions
