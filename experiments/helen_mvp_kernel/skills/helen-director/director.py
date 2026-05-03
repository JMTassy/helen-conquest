"""HELEN Director — brief -> production packet -> receipt.

Implements §13 of the HELEN Video OS LaTeX spec:
    one-line brief -> typed production packet -> receipt

Outputs:
    - STORYBOARD_V1.md
    - shot_table.json
    - asset_binds.json
    - math_constraints.json
    - DIRECTOR_PACKET_RECEIPT_V1.json

Hard exclusions:
    - No LLM calls
    - No cloud rendering
    - No image generation
    - No RH claims
    - No sovereign promotion

Determinism invariant:
    same brief + same seed -> same packet hashes
"""

from __future__ import annotations

import datetime
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from cameras import select_camera_for_shot  # noqa: E402
from timing import PHI, phi_shot_durations, prime_turn_indices  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[4]
SUBSANDBOX_DIRECTOR = REPO_ROOT / "temple" / "subsandbox" / "director"

FORBIDDEN_TARGETS = {
    REPO_ROOT / "town" / "ledger_v1.ndjson",
    REPO_ROOT / "temple" / "subsandbox" / "renders",
    REPO_ROOT / "temple" / "subsandbox" / "research",
}

BRAID_STRANDS = [
    "face_identity",
    "pose_motion",
    "ledger_object",
    "light_interface",
    "camera_axis",
]

CONTINUITY_WEIGHTS = {"identity": 0.4, "style": 0.2, "pose": 0.2, "meaning": 0.2}
TAU_CONTINUITY = 0.85


class SovereignWriteRefused(RuntimeError):
    pass


# --- canonical hashing ---

def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_obj(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def now_utc_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


# --- brief validation ---

REQUIRED_BRIEF_FIELDS = {
    "project_id",
    "title",
    "duration_seconds",
    "n_shots",
    "aspect_ratio",
    "character_id",
    "style_vector",
    "theme",
    "seed",
}


def validate_brief(brief: Dict[str, Any]) -> None:
    missing = REQUIRED_BRIEF_FIELDS - set(brief.keys())
    if missing:
        raise ValueError(f"brief missing required fields: {sorted(missing)}")
    if brief["duration_seconds"] <= 0:
        raise ValueError("duration_seconds must be > 0")
    if brief["n_shots"] < 1:
        raise ValueError("n_shots must be >= 1")
    if not isinstance(brief["seed"], int):
        raise ValueError("seed must be an integer")


# --- beat structure ---

def assign_beat_role(k_zero_indexed: int, n: int) -> str:
    """3-act distribution. k is 0..n-1."""
    if k_zero_indexed < n / 3:
        return "intro"
    if k_zero_indexed < 2 * n / 3:
        return "development"
    return "payoff"


# --- packet assembly ---

def build_shot_table(
    brief: Dict[str, Any],
    durations: List[float],
    prime_turns: List[int],
) -> List[Dict[str, Any]]:
    n = brief["n_shots"]
    shots: List[Dict[str, Any]] = []
    for i in range(n):
        shot_index_1b = i + 1
        camera = select_camera_for_shot(shot_index_1b)
        beat_role = assign_beat_role(i, n)
        is_prime_turn = shot_index_1b in prime_turns

        shot = {
            "shot_id": f"S{shot_index_1b:03d}",
            "duration": durations[i],
            "camera": {
                "name": camera["name"],
                "lens": camera["lens"],
                "motion": camera["motion"],
            },
            "subject": brief["character_id"],
            "environment": f"{brief['theme']}-themed scene, HELEN-canonical setting",
            "action": f"{beat_role} action expressing {brief['theme']}",
            "math_constraints": {
                "phi_timing": True,
                "prime_turn": is_prime_turn,
                "perception_constraints": {
                    "identity": brief["character_id"],
                    "style_vector": brief["style_vector"],
                    "motion_curve": camera["motion"],
                    "scene_topology": f"{brief['theme']}_topology",
                    "pose": "calm_director_presence" if beat_role != "payoff" else "resolved_stance",
                },
                "continuity_role": beat_role,
                "braid_strands": list(BRAID_STRANDS),
            },
        }
        shots.append(shot)
    return shots


def build_asset_binds(brief: Dict[str, Any]) -> Dict[str, Any]:
    n = brief["n_shots"]
    return {
        "character_refs": {
            brief["character_id"]: f"video/library/refs/canonical/{brief['character_id'].lower()}_canon_01.png"
        },
        "style_refs": {
            brief["style_vector"]: f"video/library/refs/canonical/{brief['style_vector'].lower()}_01.png"
        },
        "shot_to_character_ref": {
            f"S{k+1:03d}": brief["character_id"] for k in range(n)
        },
        "shot_to_style_ref": {
            f"S{k+1:03d}": brief["style_vector"] for k in range(n)
        },
    }


def build_math_constraints(
    brief: Dict[str, Any],
    durations: List[float],
    prime_turns: List[int],
) -> Dict[str, Any]:
    return {
        "phi": "{:.12f}".format(PHI),
        "phi_shot_durations": ["{:.12f}".format(d) for d in durations],
        "duration_total": "{:.12f}".format(sum(durations)),
        "prime_turn_indices": prime_turns,
        "tau_continuity": "{:.12f}".format(TAU_CONTINUITY),
        "continuity_weights": {k: "{:.12f}".format(v) for k, v in CONTINUITY_WEIGHTS.items()},
        "braid_strands": list(BRAID_STRANDS),
        "decimal_precision": 12,
    }


def render_storyboard_md(
    brief: Dict[str, Any],
    shot_table: List[Dict[str, Any]],
) -> str:
    lines: List[str] = [
        f"# STORYBOARD_V1 — {brief['title']}",
        "",
        f"**Project:** `{brief['project_id']}`",
        f"**Duration:** {brief['duration_seconds']}s",
        f"**Aspect:** {brief['aspect_ratio']}",
        f"**Character:** {brief['character_id']}",
        f"**Style:** {brief['style_vector']}",
        f"**Theme:** {brief['theme']}",
        f"**Seed:** {brief['seed']}",
        "",
        "**Math constraints:** φ-timing ON, prime-rhythm ON, braid-continuity tracked.",
        "",
        "## Shot table",
        "",
        "| Shot | Camera | Lens | Motion | Duration | Beat | Prime turn |",
        "|------|--------|------|--------|----------|------|------------|",
    ]
    for shot in shot_table:
        cam = shot["camera"]
        lines.append(
            f"| {shot['shot_id']} | {cam['name']} | {cam['lens']} | "
            f"{cam['motion']} | {shot['duration']:.3f}s | "
            f"{shot['math_constraints']['continuity_role']} | "
            f"{'★' if shot['math_constraints']['prime_turn'] else ''} |"
        )
    lines.append("")
    lines.append("## Backend agnostic")
    lines.append("")
    lines.append(
        "This packet is consumable by any render backend (DRY_RUN, "
        "rental Higgsfield/Seedance/etc., or future white-box math_to_face). "
        "Backend selection happens downstream — this artifact is purely directorial."
    )
    return "\n".join(lines) + "\n"


def make_packet(brief: Dict[str, Any]) -> Dict[str, Any]:
    validate_brief(brief)
    n = brief["n_shots"]
    duration = float(brief["duration_seconds"])

    durations = phi_shot_durations(duration, n)
    prime_turns = prime_turn_indices(n)

    shot_table = build_shot_table(brief, durations, prime_turns)
    asset_binds = build_asset_binds(brief)
    math_constraints = build_math_constraints(brief, durations, prime_turns)
    storyboard_md = render_storyboard_md(brief, shot_table)

    return {
        "project_id": brief["project_id"],
        "brief": brief,
        "storyboard_md": storyboard_md,
        "shot_table": shot_table,
        "asset_binds": asset_binds,
        "math_constraints": math_constraints,
    }


# --- write + receipt ---

def _safe_target(target: Path) -> None:
    target_resolved = target.resolve(strict=False)
    for f in FORBIDDEN_TARGETS:
        try:
            f_resolved = f.resolve(strict=False)
        except Exception:
            continue
        if target_resolved == f_resolved:
            raise SovereignWriteRefused(f"forbidden write target: {target}")
        try:
            target_resolved.relative_to(f_resolved)
        except ValueError:
            continue
        else:
            raise SovereignWriteRefused(f"forbidden write target (descendant): {target}")


def emit_packet(brief: Dict[str, Any], out_dir: Path) -> Dict[str, Any]:
    _safe_target(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    packet = make_packet(brief)

    # Write artifacts
    (out_dir / "STORYBOARD_V1.md").write_text(packet["storyboard_md"], encoding="utf-8")
    (out_dir / "shot_table.json").write_text(
        canonical_json(packet["shot_table"]) + "\n", encoding="utf-8"
    )
    (out_dir / "asset_binds.json").write_text(
        canonical_json(packet["asset_binds"]) + "\n", encoding="utf-8"
    )
    (out_dir / "math_constraints.json").write_text(
        canonical_json(packet["math_constraints"]) + "\n", encoding="utf-8"
    )

    # Compute hashes
    storyboard_hash = sha256_text(packet["storyboard_md"])
    shot_table_hash = sha256_obj(packet["shot_table"])
    asset_binds_hash = sha256_obj(packet["asset_binds"])
    math_constraints_hash = sha256_obj(packet["math_constraints"])
    input_hash = sha256_obj(brief)

    # Packet hash binds all artifact hashes deterministically
    packet_core = {
        "input_hash": input_hash,
        "storyboard_hash": storyboard_hash,
        "shot_table_hash": shot_table_hash,
        "asset_binds_hash": asset_binds_hash,
        "math_constraints_hash": math_constraints_hash,
        "seed": brief["seed"],
    }
    packet_hash = sha256_obj(packet_core)

    receipt: Dict[str, Any] = {
        "type": "DIRECTOR_PACKET_RECEIPT_V1",
        "project_id": brief["project_id"],
        "input_hash": input_hash,
        "packet_hash": packet_hash,
        "storyboard_hash": storyboard_hash,
        "shot_table_hash": shot_table_hash,
        "asset_binds_hash": asset_binds_hash,
        "math_constraints_hash": math_constraints_hash,
        "seed": brief["seed"],
        "n_shots": brief["n_shots"],
        "duration_seconds": brief["duration_seconds"],
        "scope": "TEMPLE_SUBSANDBOX",
        "sovereign_admitted": False,
        "status": "PASS",
        "timestamp_utc": now_utc_iso(),
    }
    (out_dir / "DIRECTOR_PACKET_RECEIPT_V1.json").write_text(
        canonical_json(receipt) + "\n", encoding="utf-8"
    )
    return receipt


def receipt_canonical_hash(receipt: Dict[str, Any]) -> str:
    """Hash a receipt with timestamp_utc excluded for replay invariant."""
    core = {k: v for k, v in receipt.items() if k != "timestamp_utc"}
    return sha256_obj(core)


def run_one(brief_path: Path, out_dir: Path | None = None) -> Dict[str, Any]:
    with brief_path.open("r", encoding="utf-8") as f:
        brief = json.load(f)
    if out_dir is None:
        out_dir = SUBSANDBOX_DIRECTOR / brief["project_id"]
    return emit_packet(brief, out_dir)


def run_replay(brief_path: Path, n: int = 3) -> Dict[str, Any]:
    if n < 2:
        raise ValueError("replay requires n >= 2")
    receipts = [run_one(brief_path) for _ in range(n)]
    keys = [
        "input_hash",
        "packet_hash",
        "storyboard_hash",
        "shot_table_hash",
        "asset_binds_hash",
        "math_constraints_hash",
    ]
    consistent = all(
        all(receipts[i][k] == receipts[0][k] for k in keys) for i in range(1, n)
    )
    return {
        "project_id": receipts[0]["project_id"],
        "replay_n": n,
        "replay_consistent": consistent,
        "replay_check_hashes": {k: receipts[0][k] for k in keys},
        "status": "PASS" if consistent else "DIRECTOR_HASH_DRIFT_BLOCK",
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "usage: python director.py <brief.json> [--replay N]",
            file=sys.stderr,
        )
        return 2
    brief_path = Path(sys.argv[1])
    if not brief_path.exists():
        print(f"brief not found: {brief_path}", file=sys.stderr)
        return 1
    if "--replay" in sys.argv:
        idx = sys.argv.index("--replay")
        n = int(sys.argv[idx + 1])
        result = run_replay(brief_path, n=n)
        print(canonical_json(result))
        return 0 if result["replay_consistent"] else 1

    receipt = run_one(brief_path)
    print(canonical_json({
        "project_id": receipt["project_id"],
        "packet_hash": receipt["packet_hash"],
        "storyboard_hash": receipt["storyboard_hash"],
        "shot_table_hash": receipt["shot_table_hash"],
        "asset_binds_hash": receipt["asset_binds_hash"],
        "math_constraints_hash": receipt["math_constraints_hash"],
        "status": receipt["status"],
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
