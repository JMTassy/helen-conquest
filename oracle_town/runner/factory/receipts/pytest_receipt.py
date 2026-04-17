"""
PyTest Receipt Plugin

Executes pytest and generates a signed attestation.
"""

import json
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


def generate_receipt(
    proposal: Dict[str, Any],
    staging_dir: str,
    repo_root: str
) -> Optional[Dict[str, Any]]:
    """
    Execute pytest and generate attestation.

    Returns: Attestation dict (unsigned - Factory must sign)
    """
    # Run pytest
    result = _run_pytest(repo_root)

    if result is None:
        return None

    # Compute evidence digest
    evidence_digest = _hash_evidence(result)

    # Build attestation (unsigned)
    attestation = {
        "attestor_class": "ci_automation",
        "signing_key_id": "key-ci-automation-2026",  # TODO: Get from config
        "obligation": "unit_tests",
        "evidence_type": "pytest-junit",
        "evidence_digest": evidence_digest,
        "policy_match": 1 if result['passed'] else 0,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {
            "total_tests": result['total'],
            "passed": result['passed'],
            "failed": result['failed'],
            "duration_seconds": result['duration']
        }
    }

    return attestation


def _run_pytest(repo_root: str) -> Optional[Dict[str, Any]]:
    """Run pytest and return results"""
    try:
        # Run pytest with JSON output
        cmd = [
            'python', '-m', 'pytest',
            '--tb=short',
            '--quiet',
            '--json-report',
            '--json-report-file=/tmp/pytest_report.json',
            'tests/'
        ]

        result = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=120
        )

        # Parse JSON report if available
        report_path = Path('/tmp/pytest_report.json')
        if report_path.exists():
            with open(report_path) as f:
                report = json.load(f)

            return {
                'passed': result.returncode == 0,
                'total': report.get('summary', {}).get('total', 0),
                'passed': report.get('summary', {}).get('passed', 0),
                'failed': report.get('summary', {}).get('failed', 0),
                'duration': report.get('duration', 0),
                'raw_output': result.stdout + result.stderr
            }
        else:
            # Fallback: parse from exit code
            return {
                'passed': result.returncode == 0,
                'total': -1,
                'passed': -1 if result.returncode == 0 else 0,
                'failed': -1 if result.returncode != 0 else 0,
                'duration': 0,
                'raw_output': result.stdout + result.stderr
            }

    except subprocess.TimeoutExpired:
        print("⚠️  pytest timed out")
        return None
    except Exception as e:
        print(f"⚠️  pytest failed: {e}")
        return None


def _hash_evidence(result: Dict[str, Any]) -> str:
    """Compute SHA256 hash of canonical evidence"""
    # Canonical evidence (deterministic)
    evidence = {
        'total': result['total'],
        'passed': result['passed'],
        'failed': result['failed'],
        'duration': result['duration'],
    }

    canonical = json.dumps(evidence, sort_keys=True, separators=(',', ':'))
    return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()}"
