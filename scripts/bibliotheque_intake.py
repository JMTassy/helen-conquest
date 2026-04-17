#!/usr/bin/env python3
"""
Bibliothèque Intake System: Accept and integrate external knowledge

Validates, parses, and integrates:
- Math proofs (LaTeX, markdown)
- Code archives (Python, Go, Rust, etc)
- Research papers (PDFs, markdown)
- Empirical data (JSON, CSV, logs)
- Operational notes (incidents, post-mortems)
- Policy proposals (governance docs)

All integrated knowledge is:
- Hashed and pinned (K7 policy pinning)
- Cited in decision records
- Available for determinism replay (K5)
- Searchable in knowledge base
"""

import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime


def validate_content(content_type: str, content: str) -> dict:
    """Validate incoming content based on type."""
    if content_type == "MATH_PROOF":
        return validate_math(content)
    elif content_type == "CODE_ARCHIVE":
        return validate_code(content)
    elif content_type == "RESEARCH":
        return validate_research(content)
    elif content_type == "DATA":
        return validate_data(content)
    elif content_type == "OPERATIONAL":
        return validate_operational(content)
    elif content_type == "POLICY":
        return validate_policy(content)
    else:
        return {"status": "ERROR", "message": f"Unknown type: {content_type}"}


def validate_math(content: str) -> dict:
    """Validate math proof (LaTeX or markdown)."""
    # Check for basic LaTeX or markdown structure
    has_structure = (
        ("\\begin" in content or "\\end" in content) or  # LaTeX
        ("$$" in content or "$" in content) or  # Math mode
        ("Claim:" in content or "Proof:" in content) or  # Markdown
        ("**Lemma**" in content or "**Theorem**" in content)  # Markdown
    )

    # Check for prompt injection
    dangerous = ["$(", "`", "import ", "exec(", "eval("]
    is_safe = not any(d in content for d in dangerous)

    return {
        "status": "OK" if has_structure and is_safe else "WARN",
        "type": "MATH_PROOF",
        "has_structure": has_structure,
        "is_safe": is_safe,
        "claims_found": content.count("Claim:") + content.count("**Lemma**") + content.count("**Theorem**"),
        "message": "Math proof accepted" if has_structure and is_safe else "Review structure and safety"
    }


def validate_code(content: str) -> dict:
    """Validate code archive."""
    # Detect language
    language = "UNKNOWN"
    if content.startswith("package "):
        language = "GO"
    elif "fn " in content and "mut" in content:
        language = "RUST"
    elif "def " in content or "class " in content:
        language = "PYTHON"
    elif "#include" in content:
        language = "C++"

    # Check for basic syntax
    has_syntax = len(content) > 50  # Basic check

    # Check for injection
    dangerous = ["os.system(", "subprocess.call(", "exec(", "eval("]
    is_safe = not any(d in content for d in dangerous)

    return {
        "status": "OK" if has_syntax and is_safe else "WARN",
        "type": "CODE_ARCHIVE",
        "language": language,
        "functions_found": content.count("def ") + content.count("fn ") + content.count("func "),
        "is_safe": is_safe,
        "message": f"Code archive ({language}) accepted"
    }


def validate_research(content: str) -> dict:
    """Validate research paper/notes."""
    # Check for research markers
    has_claims = "claim" in content.lower() or "theorem" in content.lower()
    has_evidence = "table" in content.lower() or "result" in content.lower() or "fig" in content.lower()
    has_citations = "[" in content or "doi:" in content.lower()

    # Check for prompt injection
    dangerous = ["$(", "`", "import ", "exec("]
    is_safe = not any(d in content for d in dangerous)

    return {
        "status": "OK" if (has_claims or has_evidence) and is_safe else "WARN",
        "type": "RESEARCH",
        "has_claims": has_claims,
        "has_evidence": has_evidence,
        "has_citations": has_citations,
        "is_safe": is_safe,
        "message": "Research content accepted"
    }


def validate_data(content: str) -> dict:
    """Validate empirical data (JSON, CSV, logs)."""
    # Try JSON parsing
    try:
        json.loads(content)
        format_type = "JSON"
        is_valid = True
    except:
        format_type = "CSV/LOG"
        is_valid = len(content) > 10  # Basic check

    # Check for injection
    dangerous = ["DROP ", "DELETE ", "`", "$("]
    is_safe = not any(d in content for d in dangerous)

    return {
        "status": "OK" if is_valid and is_safe else "WARN",
        "type": "DATA",
        "format": format_type,
        "is_valid_format": is_valid,
        "is_safe": is_safe,
        "message": f"Data ({format_type}) accepted"
    }


def validate_operational(content: str) -> dict:
    """Validate operational notes (incidents, logs)."""
    # Check for incident markers
    has_structure = any(
        keyword in content.lower()
        for keyword in ["incident", "failure", "error", "outage", "post-mortem", "log", "timestamp"]
    )

    # Check for prompt injection
    dangerous = ["$(", "`"]
    is_safe = not any(d in content for d in dangerous)

    failures = content.lower().count("fail") + content.lower().count("error") + content.lower().count("incident")

    return {
        "status": "OK" if has_structure and is_safe else "WARN",
        "type": "OPERATIONAL",
        "has_structure": has_structure,
        "is_safe": is_safe,
        "failure_markers_found": failures,
        "message": "Operational log accepted"
    }


def validate_policy(content: str) -> dict:
    """Validate policy proposal (will be hardened by system)."""
    # Check for policy markers
    has_structure = any(
        keyword in content
        for keyword in ["District", "Attestor", "Quorum", "Rule", "Policy", "Obligation"]
    )

    # Check for soft language (needs hardening)
    soft_language = ["usually", "probably", "maybe", "if needed", "might", "could", "try to"]
    softness_count = sum(content.lower().count(s) for s in soft_language)

    # Check for injection
    dangerous = ["$(", "`"]
    is_safe = not any(d in content for d in dangerous)

    return {
        "status": "OK" if has_structure and is_safe else "WARN",
        "type": "POLICY",
        "has_structure": has_structure,
        "is_safe": is_safe,
        "soft_language_count": softness_count,
        "message": f"Policy proposal accepted (contains {softness_count} soft language phrases to harden)"
    }


def compute_hash(content: str) -> str:
    """Compute SHA256 hash of content (K7 pinning)."""
    return "sha256:" + hashlib.sha256(content.encode()).hexdigest()


def main():
    """Interactive intake system."""
    print("=" * 70)
    print("ORACLE TOWN: BIBLIOTHÈQUE INTAKE SYSTEM")
    print("=" * 70)
    print()

    if len(sys.argv) < 2:
        print("Usage: python3 scripts/bibliotheque_intake.py <content_type>")
        print()
        print("Content types:")
        print("  MATH_PROOF     — LaTeX, markdown, handwritten proofs")
        print("  CODE_ARCHIVE   — Python, Go, Rust, C++, etc.")
        print("  RESEARCH       — Papers, excerpts, summaries")
        print("  DATA           — Benchmarks, logs, time-series (JSON/CSV)")
        print("  OPERATIONAL    — Incidents, post-mortems, failure logs")
        print("  POLICY         — Governance proposals (will be hardened)")
        print()
        print("Submit content via stdin:")
        print("  cat proof.tex | python3 scripts/bibliotheque_intake.py MATH_PROOF")
        print()
        return 1

    content_type = sys.argv[1].upper()

    # Read content from stdin
    try:
        content = sys.stdin.read()
    except EOFError:
        content = ""

    if not content:
        print("ERROR: No content provided on stdin")
        return 1

    # Validate
    result = validate_content(content_type, content)

    # Compute hash (K7 pinning)
    content_hash = compute_hash(content)

    # Add metadata
    result["hash"] = content_hash
    result["timestamp"] = datetime.now().isoformat()
    result["content_length"] = len(content)

    # Output results
    print(f"Content Type: {content_type}")
    print(f"Length: {result['content_length']} bytes")
    print(f"Hash (K7 pinning): {content_hash[:30]}...")
    print()
    print("Validation Results:")
    for key, value in result.items():
        if key not in ["hash", "timestamp", "content_length"]:
            print(f"  {key}: {value}")
    print()

    if result["status"] == "OK":
        print("✅ ACCEPTED — Content ready for integration")
        print()
        print("Next steps:")
        print(f"  1. mkdir -p oracle_town/memory/bibliotheque/{content_type.lower()}/")
        print(f"  2. Save content to oracle_town/memory/bibliotheque/{content_type.lower()}/original.*")
        print(f"  3. Create oracle_town/memory/bibliotheque/{content_type.lower()}/metadata.json")
        print(f"  4. git add && git commit")
        return 0
    else:
        print("⚠️  WARNING — Review validation results")
        print()
        print("Issues:")
        print(f"  - Status: {result['status']}")
        print(f"  - Message: {result['message']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
