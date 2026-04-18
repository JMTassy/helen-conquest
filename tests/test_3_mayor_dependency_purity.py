"""
Constitutional Test 3: No Confidence in Truth Path

RULE: Mayor V2 must not import cognition layer modules (scoring, telemetry, confidence)

ENFORCEMENT:
- Parse Mayor V2 imports using AST
- Forbidden imports: scoring, superteam, telemetry, town_hall, qi_int
- Mayor may only read: briefcase, attestations, kill_switch_signals

VIOLATION: Confidence leak into decision path → NO_SHIP
"""
import pytest
import ast
from pathlib import Path

FORBIDDEN_IMPORTS = {
    "oracle_town.core.scoring",
    "oracle_town.core.town_hall",
    "oracle_town.superteam",
    "oracle_town.creative",  # Layer 2 must never influence Mayor
    "oracle_town.districts",  # Districts output via Concierge only
    "telemetry",
    "qi_int",
}


def test_mayor_has_no_forbidden_imports():
    """
    Constitutional Test 3: Mayor Dependency Purity

    Parses mayor_v2.py imports to ensure no cognition layer modules.
    Mayor must be a pure predicate over attestations.
    """
    repo_root = Path(__file__).parent.parent
    mayor_v2_path = repo_root / "oracle_town" / "core" / "mayor_v2.py"

    assert mayor_v2_path.exists(), "mayor_v2.py must exist"

    content = mayor_v2_path.read_text(encoding="utf-8")
    tree = ast.parse(content)

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    # Check for forbidden imports
    violations = []
    for imp in imports:
        for forbidden in FORBIDDEN_IMPORTS:
            if forbidden in imp:
                violations.append(imp)

    assert not violations, (
        f"CONSTITUTIONAL VIOLATION: Mayor V2 imports cognition layer:\n"
        f"Forbidden imports found: {violations}\n\n"
        f"Mayor must not import scoring, telemetry, or confidence modules."
    )


def test_mayor_has_no_confidence_references():
    """
    Verify Mayor V2 code has no 'confidence' or 'score' variable references.

    More strict than just checking imports - checks actual code.
    """
    repo_root = Path(__file__).parent.parent
    mayor_v2_path = repo_root / "oracle_town" / "core" / "mayor_v2.py"

    content = mayor_v2_path.read_text(encoding="utf-8")

    # Remove comments and docstrings
    import re
    content_code = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
    content_code = re.sub(r'""".*?"""', '', content_code, flags=re.DOTALL)
    content_code = re.sub(r"'''.*?'''", '', content_code, flags=re.DOTALL)

    # Check for forbidden variable patterns (not in strings)
    forbidden_vars = [
        "confidence",
        "score",
        "recommendation",
        "qi_int",
    ]

    violations = []
    for var in forbidden_vars:
        # Look for variable usage (not in string literals)
        pattern = rf'\b{var}\b'
        matches = re.findall(pattern, content_code, re.IGNORECASE)

        # Filter out matches that are in string literals
        real_matches = [m for m in matches if not (
            f'"{var}"' in content_code or f"'{var}'" in content_code
        )]

        if real_matches:
            violations.append(f"{var} ({len(real_matches)} occurrences)")

    assert not violations, (
        f"CONSTITUTIONAL VIOLATION: Mayor V2 references confidence/scoring:\n"
        f"Found: {violations}\n\n"
        f"Mayor must use only attestations (policy_match), not confidence."
    )


def test_mayor_decision_uses_only_attestations():
    """Verify Mayor's decide() method signature uses only allowed inputs"""
    repo_root = Path(__file__).parent.parent
    mayor_v2_path = repo_root / "oracle_town" / "core" / "mayor_v2.py"

    content = mayor_v2_path.read_text()
    tree = ast.parse(content)

    # Find the decide method (sync or async)
    decide_method = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "decide":
            decide_method = node
            break

    assert decide_method, "Mayor must have decide() method"

    # Check parameters
    param_names = [arg.arg for arg in decide_method.args.args]

    # Allowed: self, briefcase, attestations, kill_switch_signals
    allowed_params = {"self", "briefcase", "attestations", "kill_switch_signals"}

    forbidden_params = set(param_names) - allowed_params

    assert not forbidden_params, (
        f"CONSTITUTIONAL VIOLATION: Mayor.decide() has forbidden parameters:\n"
        f"Found: {forbidden_params}\n"
        f"Allowed: {allowed_params}\n\n"
        f"Mayor may only read briefcase, attestations, and kill_switch_signals."
    )


def test_mayor_has_no_creative_imports():
    """
    Specific check: Mayor must not import from oracle_town.creative.*

    This ensures Layer 2 (Creative Town) has zero influence on Layer 0 (Kernel).
    """
    repo_root = Path(__file__).parent.parent
    mayor_v2_path = repo_root / "oracle_town" / "core" / "mayor_v2.py"

    assert mayor_v2_path.exists(), "mayor_v2.py must exist"

    content = mayor_v2_path.read_text(encoding="utf-8")
    tree = ast.parse(content)

    creative_imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("oracle_town.creative"):
                creative_imports.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("oracle_town.creative"):
                    creative_imports.append(alias.name)

    assert not creative_imports, (
        f"CONSTITUTIONAL VIOLATION: Mayor imports from Creative Town (Layer 2).\n"
        f"Found: {creative_imports}\n\n"
        f"Creative Town proposals must pass through:\n"
        f"  Translator → Concierge → Briefcase → Factory → Attestations\n"
        f"Mayor sees only Briefcase + Attestations (never direct creative output)."
    )


def test_mayor_has_no_district_imports():
    """
    Specific check: Mayor must not import from oracle_town.districts.*

    This ensures districts output BuilderPackets (via Concierge) only.
    """
    repo_root = Path(__file__).parent.parent
    mayor_v2_path = repo_root / "oracle_town" / "core" / "mayor_v2.py"

    assert mayor_v2_path.exists(), "mayor_v2.py must exist"

    content = mayor_v2_path.read_text(encoding="utf-8")
    tree = ast.parse(content)

    district_imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("oracle_town.districts"):
                district_imports.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("oracle_town.districts"):
                    district_imports.append(alias.name)

    assert not district_imports, (
        f"CONSTITUTIONAL VIOLATION: Mayor imports from districts.\n"
        f"Found: {district_imports}\n\n"
        f"Districts must not directly influence Mayor.\n"
        f"District outputs flow: BuilderPacket → Concierge → Briefcase."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
