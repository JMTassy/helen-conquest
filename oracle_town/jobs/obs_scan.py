#!/usr/bin/env python3
"""
ORACLE TOWN — OBS Module Implementation
Observation Collection & Structuring (Deterministic)

Ingests raw observations from multiple sources (notes, emails, metrics, meetings)
and structures them as normalized facts according to OBS charter.

No RNG, no timestamps (date-only), deterministic ordering.

Usage:
  python3 oracle_town/jobs/obs_scan.py \
    --date 2026-01-30 \
    --run-id 174 \
    --input-dir observations/ \
    --output artifacts/observations.json \
    --receipt artifacts/obs_receipt.json
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import hashlib


def normalize_text(text: str) -> str:
    """Strip whitespace, normalize newlines, remove control chars."""
    text = str(text).strip()
    text = text.replace('\t', ' ')  # tabs → spaces
    text = ' '.join(text.split())   # normalize internal whitespace
    return text


def load_observations_from_directory(input_dir: Path) -> List[Dict[str, Any]]:
    """
    Load observations from input directory.

    Supports:
    - .json files (array of observation objects)
    - .txt files (one observation per file, filename = source)
    - .md files (markdown notes)

    Returns sorted list of observation dicts (by ID).
    """
    observations = []

    if not input_dir.exists():
        print(f"⚠ Input directory not found: {input_dir}", file=sys.stderr)
        return []

    # Process JSON files (array format)
    for json_file in sorted(input_dir.glob("*.json")):
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                observations.extend(data)
            elif isinstance(data, dict) and "observations" in data:
                observations.extend(data["observations"])
        except Exception as e:
            print(f"⚠ Error loading {json_file}: {e}", file=sys.stderr)

    # Process text files (one per file)
    for txt_file in sorted(input_dir.glob("*.txt")):
        try:
            with txt_file.open("r", encoding="utf-8") as f:
                body = f.read().strip()
            if body:
                observations.append({
                    "source": txt_file.stem or "note",
                    "title": txt_file.stem[:100],
                    "body": body[:500],
                    "tags": [],
                    "confidence": 1.0
                })
        except Exception as e:
            print(f"⚠ Error loading {txt_file}: {e}", file=sys.stderr)

    # Process markdown files
    for md_file in sorted(input_dir.glob("*.md")):
        try:
            with md_file.open("r", encoding="utf-8") as f:
                body = f.read().strip()
            if body:
                # Extract title from first # heading if present
                lines = body.split('\n')
                title = lines[0].lstrip('#').strip()[:100] if lines[0].startswith('#') else md_file.stem[:100]
                observations.append({
                    "source": "markdown",
                    "title": title,
                    "body": body[:500],
                    "tags": ["document"],
                    "confidence": 0.9
                })
        except Exception as e:
            print(f"⚠ Error loading {md_file}: {e}", file=sys.stderr)

    return observations


def structure_observations(raw_obs: List[Dict[str, Any]],
                         date: str,
                         run_id: int) -> List[Dict[str, Any]]:
    """
    Transform raw observations into canonical form with IDs.

    Ensures:
    - Deterministic ID generation (hash-based, not timestamp)
    - Normalized text fields
    - Sorted output (by ID)
    """
    structured = []

    for idx, obs in enumerate(raw_obs):
        # Normalize text fields
        title = normalize_text(obs.get("title", ""))[:100]
        body = normalize_text(obs.get("body", ""))[:500]
        source = normalize_text(obs.get("source", "unknown"))
        tags = obs.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        tags = [normalize_text(t) for t in tags if t]
        confidence = float(obs.get("confidence", 0.8))
        confidence = max(0.0, min(1.0, confidence))  # clamp to [0,1]

        # Generate deterministic ID: hash(date + run_id + source + title + body)
        id_input = f"{date}:{run_id}:{source}:{title}:{body}".encode('utf-8')
        id_hash = hashlib.sha256(id_input).hexdigest()[:16]
        obs_id = f"obs_{date.replace('-','')}_{id_hash}"

        structured_obs = {
            "id": obs_id,
            "date": date,
            "run_id": run_id,
            "source": source or "unknown",
            "title": title,
            "body": body,
            "tags": sorted(set(tags)),  # deduplicated, sorted
            "confidence": confidence,
            "links": []
        }
        structured.append(structured_obs)

    # Sort by ID for determinism
    structured.sort(key=lambda x: x["id"])

    return structured


def create_receipt(observations: List[Dict[str, Any]],
                  run_id: int,
                  attestor_id: str = "obs_attestor_001") -> Dict[str, Any]:
    """
    Create a receipt structure (signature payload).

    Note: actual ed25519 signing happens at a higher level (TRI/PUB).
    This creates the structure that would be signed.
    """
    # Serialize observations to canonical JSON for hashing
    obs_json = json.dumps(observations, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    obs_hash = hashlib.sha256(obs_json.encode('utf-8')).hexdigest()

    receipt = {
        "obs_receipt": {
            "observation_count": len(observations),
            "observations_hash": f"sha256:{obs_hash}",
            "run_id": run_id,
            "attestor_id": attestor_id,
            "signature": "ed25519:PLACEHOLDER_SIGNATURE",
            "note": "Signature placeholder; actual signing by attestor_id required"
        }
    }
    return receipt


def main() -> None:
    ap = argparse.ArgumentParser(
        description="ORACLE TOWN OBS Module: Observation Collection"
    )
    ap.add_argument("--date", required=True, help="Run date (YYYY-MM-DD)")
    ap.add_argument("--run-id", type=int, required=True, help="Sequential run ID")
    ap.add_argument("--input-dir", default="observations/", help="Input observations directory")
    ap.add_argument("--output", default="artifacts/observations.json", help="Output observations file")
    ap.add_argument("--receipt", default="artifacts/obs_receipt.json", help="Output receipt file")
    ap.add_argument("--verbose", action="store_true", help="Verbose output")
    args = ap.parse_args()

    input_dir = Path(args.input_dir)
    output_file = Path(args.output)
    receipt_file = Path(args.receipt)

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    receipt_file.parent.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        print(f"[OBS] Scanning observations from: {input_dir}")

    # Load raw observations
    raw_obs = load_observations_from_directory(input_dir)

    if args.verbose:
        print(f"[OBS] Loaded {len(raw_obs)} raw observations")

    # Structure observations
    observations = structure_observations(raw_obs, args.date, args.run_id)

    if args.verbose:
        print(f"[OBS] Structured {len(observations)} observations")
        for obs in observations[:3]:  # Show first 3
            print(f"      - {obs['id']}: {obs['title'][:50]}")
        if len(observations) > 3:
            print(f"      ... and {len(observations) - 3} more")

    # Save observations
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(observations, f, sort_keys=True, indent=2, ensure_ascii=True)
        f.write("\n")

    if args.verbose:
        print(f"[OBS] Observations saved: {output_file}")

    # Create receipt
    receipt = create_receipt(observations, args.run_id)

    # Save receipt
    with receipt_file.open("w", encoding="utf-8") as f:
        json.dump(receipt, f, sort_keys=True, indent=2, ensure_ascii=True)
        f.write("\n")

    if args.verbose:
        print(f"[OBS] Receipt saved: {receipt_file}")
        print(f"[OBS] Total observations: {len(observations)}")

    # Update state (minimal)
    if args.verbose:
        print("[OBS] ✓ Complete")
        sys.exit(0)


if __name__ == "__main__":
    main()
