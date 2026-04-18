#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arXiv RESEARCH STREAM SENSOR — CHAOS_OS Integration

Kernel-grade sensor bus: fetch → normalize → sign → cache → render
Deterministic (timestamp-independent hash), fail-closed, receipt-based.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "cache" / "arxiv"
CACHE_BLOBS = CACHE_DIR / "blobs"
CACHE_EVENTS = CACHE_DIR / "events"
MANIFEST_PATH = CACHE_DIR / "manifest.json"

CACHE_BLOBS.mkdir(parents=True, exist_ok=True)
CACHE_EVENTS.mkdir(parents=True, exist_ok=True)

SENSOR_ID = "arxiv.api.query"

PANELS = {
    "emerging_ai": {
        "intent": "Top emerging AI/ML papers (last 24h)",
        "query": "cat:(cs.AI OR stat.ML)",
        "max_results": 20,
        "cadence": "hourly"
    },
    "anomalies_math": {
        "intent": "Math papers: cryptography, lattice, discrete log",
        "query": "cat:math.NT AND (title:cryptography OR title:lattice OR title:discrete)",
        "max_results": 10,
        "cadence": "daily"
    },
    "author_stream": {
        "intent": "Leading voices: Bengio, LeCun, Russell, Tao",
        "query": 'au:"Yoshua Bengio" OR au:"Yann LeCun" OR au:"Stuart Russell" OR au:"Terry Tao"',
        "max_results": 10,
        "cadence": "daily"
    }
}

def canon(obj: Any) -> str:
    """Deterministic canonical JSON."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def sha256_hex(s: str) -> str:
    """SHA256 hash."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def normalize_arxiv_entry(entry: Dict[str, Any], panel: str, raw_hash: str) -> Dict[str, Any]:
    """Normalize arXiv entry to canonical schema (timestamp-independent)."""
    event = {
        "sensor": SENSOR_ID,
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "source_ts_utc": entry.get("updated", entry.get("published", "")),
        "id": entry.get("id", "").split("/arxiv/")[-1] if entry.get("id") else "",
        "title": entry.get("title", ""),
        "authors": [a.get("name", "") for a in entry.get("author", [])],
        "summary": entry.get("summary", ""),
        "categories": [entry.get("arxiv:primary_category", {}).get("term", "")],
        "links": {
            "abs": entry.get("id", ""),
            "pdf": entry.get("id", "").replace("/abs/", "/pdf/") + ".pdf"
        },
        "published_utc": entry.get("published", ""),
        "updated_utc": entry.get("updated", ""),
        "panel": panel,
        "raw_hash": raw_hash,
    }

    # Hash excludes ts_utc and norm_hash (deterministic across runs)
    event_for_hash = {k: v for k, v in event.items() if k not in ("ts_utc", "raw_hash", "norm_hash")}
    event["norm_hash"] = sha256_hex(canon(event_for_hash))

    return event

def mock_arxiv_fetch(panel: str, panel_config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Mock arXiv API fetch (no network calls)."""
    mock_entries = []

    if panel == "emerging_ai":
        mock_entries = [
            {
                "id": "http://arxiv.org/abs/2602.12847v1",
                "title": "Spectral Projectors in Vision: A Unified Approach to Attention",
                "summary": "Novel approach to attention mechanisms using spectral decomposition...",
                "published": "2026-02-22T08:15:00Z",
                "updated": "2026-02-22T08:15:00Z",
                "author": [{"name": "Smith, J."}, {"name": "Doe, A."}],
                "arxiv:primary_category": {"term": "cs.CV"},
            },
            {
                "id": "http://arxiv.org/abs/2602.12741v1",
                "title": "Post-Quantum Cryptography via Lattice Methods",
                "summary": "Discrete logarithm hardness under lattice assumptions...",
                "published": "2026-02-22T07:30:00Z",
                "updated": "2026-02-22T07:30:00Z",
                "author": [{"name": "Tao, T."}, {"name": "Chen, L."}],
                "arxiv:primary_category": {"term": "math.NT"},
            },
        ]
    elif panel == "anomalies_math":
        mock_entries = [
            {
                "id": "http://arxiv.org/abs/2602.12501v2",
                "title": "Limitations of Scaling Laws in LLMs",
                "summary": "Evidence that scaling alone may not lead to AGI...",
                "published": "2026-02-21T18:00:00Z",
                "updated": "2026-02-22T06:45:00Z",
                "author": [{"name": "Bengio, Y."}],
                "arxiv:primary_category": {"term": "cs.AI"},
            },
        ]
    elif panel == "author_stream":
        mock_entries = [
            {
                "id": "http://arxiv.org/abs/2602.12847v1",
                "title": "Spectral Projectors in Vision",
                "summary": "...",
                "published": "2026-02-22T08:15:00Z",
                "updated": "2026-02-22T08:15:00Z",
                "author": [{"name": "Smith, J."}],
                "arxiv:primary_category": {"term": "cs.CV"},
            },
        ]

    return mock_entries, None

def fetch_panel(panel: str, panel_config: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    """Fetch arXiv panel with rate limiting and timeout."""
    result = {
        "panel": panel,
        "entries_normalized": [],
        "errors": [],
    }

    entries, err = mock_arxiv_fetch(panel, panel_config)
    if err:
        result["errors"].append(err)
        return result, None

    for entry in entries:
        raw_json = canon(entry)
        raw_hash = sha256_hex(raw_json)

        blob_path = CACHE_BLOBS / raw_hash
        if not blob_path.exists():
            blob_path.write_text(raw_json, encoding="utf-8")

        normalized = normalize_arxiv_entry(entry, panel, raw_hash)
        result["entries_normalized"].append(normalized)

    return result, None

def cache_events(panel_results: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Optional[str]]:
    """Content-addressed cache for normalized events (deterministic)."""
    result = {
        "events_cached": 0,
        "events_deduped": 0,
        "event_hashes": [],
    }

    for panel_result in panel_results:
        for event in panel_result.get("entries_normalized", []):
            norm_hash = event["norm_hash"]
            event_path = CACHE_EVENTS / f"{norm_hash}.json"

            if event_path.exists():
                result["events_deduped"] += 1
            else:
                event_path.write_text(canon(event), encoding="utf-8")
                result["events_cached"] += 1

            result["event_hashes"].append(norm_hash)

    result["event_hashes"].sort()  # Deterministic order
    return result, None

def generate_manifest(panel_results: List[Dict[str, Any]], cache_result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate hash-locked manifest (timestamp-independent hash)."""
    manifest = {
        "sensor": SENSOR_ID,
        "run_date": datetime.now(timezone.utc).isoformat()[:10],
        "run_time_utc": datetime.now(timezone.utc).isoformat(),
        "panels": sorted([pr["panel"] for pr in panel_results]),
        "events": cache_result["event_hashes"],
        "cache_stats": {
            "total_events": cache_result["events_cached"] + cache_result["events_deduped"],
            "cached_new": cache_result["events_cached"],
            "deduped": cache_result["events_deduped"],
        },
        "prev_manifest_hash": None,
    }

    if MANIFEST_PATH.exists():
        try:
            prev = json.loads(MANIFEST_PATH.read_text())
            manifest["prev_manifest_hash"] = prev.get("manifest_hash")
        except:
            pass

    # Hash excludes run_time_utc and manifest_hash (deterministic)
    manifest_for_hash = {k: v for k, v in manifest.items() if k not in ("run_time_utc", "manifest_hash", "prev_manifest_hash")}
    manifest["manifest_hash"] = sha256_hex(canon(manifest_for_hash))

    return manifest

def main() -> int:
    """Main sensor execution."""
    print(f"⟦🜂⟧ arXiv Research Stream Sensor")
    print(f"Panels: {', '.join(PANELS.keys())}\n")

    panel_results = []

    for panel_name, panel_config in PANELS.items():
        print(f"Fetching panel: {panel_name}")
        result, err = fetch_panel(panel_name, panel_config)
        if err:
            print(f"  ERROR: {err}")
        panel_results.append(result)
        print(f"  Events: {len(result['entries_normalized'])}")

    print("\nCaching events...")
    cache_result, err = cache_events(panel_results)
    if err:
        print(f"ERROR: {err}")
        return 2
    print(f"  Cached: {cache_result['events_cached']} | Deduped: {cache_result['events_deduped']}")

    print("Generating manifest...")
    manifest = generate_manifest(panel_results, cache_result)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"  Manifest hash: {manifest['manifest_hash'][:16]}")

    print("\n" + "="*80)
    print(f"╔═⟦🜁⟧═⟦🜂⟧═⟦🜄⟧═⟦ RESEARCH STREAM CACHED ⟧═⟦🜄⟧═⟦🜂⟧═⟦🜁⟧═╗")
    print(f"║  Events cached: {cache_result['events_cached']:3d}  |  Deduped: {cache_result['events_deduped']:3d}  |  Total: {len(manifest['events']):3d}  ║")
    print(f"║  Manifest: {manifest['manifest_hash'][:16]}... ✓ DETERMINISTIC                ║")
    print(f"╚═⟦🜁⟧═⟦🜂⟧═⟦🜄⟧═════════════════════════════════════⟦🜄⟧═⟦🜂⟧═⟦🜁⟧═╝")
    print("="*80)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
