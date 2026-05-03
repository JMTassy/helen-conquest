"""higgsfield_seedance.dry_run — end-to-end DRY_RUN orchestrator.

Parses a STORYBOARD_V1 markdown packet, extracts the shot list, and
issues DRY_RUN render_shot calls for each shot. Emits per-shot receipts
to temple/subsandbox/renders/<task_id>/. Produces a final manifest.json
summarizing what WOULD be sent if mode=LIVE.

This is the switch point: when the higgsfield_seedance skill is admitted
to oracle_town/ AND the operator authorizes a LIVE run, the same packet
flows through this orchestrator with mode=LIVE and the cloud render runs.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Make sibling imports work whether run as module or script
HERE = Path(__file__).resolve().parent
EXP_ROOT = HERE.parent
if str(EXP_ROOT) not in sys.path:
    sys.path.insert(0, str(EXP_ROOT))

from higgsfield_seedance.client import render_shot  # noqa: E402
from higgsfield_seedance.receipts import emit_receipt  # noqa: E402
from higgsfield_seedance.music_stub import music_for_storyboard  # noqa: E402

REPO_ROOT = EXP_ROOT.parents[1]
SUBSANDBOX = REPO_ROOT / "temple" / "subsandbox" / "renders"


def _parse_task_id(text: str) -> str:
    m = re.search(r"task_id:\s*(\S+)", text)
    if not m:
        raise ValueError("STORYBOARD_V1 packet missing task_id")
    return m.group(1)


def _parse_shot_table(text: str) -> List[Dict[str, Any]]:
    """Extract shots from the markdown table.

    Expected row shape:
      | 1 | Extreme close-up (Sheet #1) | 4s | <action> | <voice> | <music cue> |
    """
    shots: List[Dict[str, Any]] = []
    in_table = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("| #") and "Camera" in s:
            in_table = True
            continue
        if in_table:
            if not s.startswith("|"):
                in_table = False
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not cells or not cells[0].isdigit():
                continue
            try:
                shot_n = int(cells[0])
                camera = cells[1]
                dur_str = cells[2].lower().rstrip("s")
                duration_s = float(dur_str)
                action = cells[3] if len(cells) > 3 else ""
                voice = cells[4] if len(cells) > 4 else ""
                shots.append(
                    {
                        "shot_n": shot_n,
                        "camera": camera,
                        "duration_s": duration_s,
                        "action": action,
                        "voice": voice,
                    }
                )
            except (ValueError, IndexError):
                continue
    return shots


def _build_prompt(shot: Dict[str, Any]) -> str:
    return (
        f"{shot['camera']}; {shot['action']}; cyberpunk-cathedral aesthetic, "
        "red hair, dark navy + gold ornament robe, candlelit + holographic UI"
    )


def dry_run_storyboard(
    packet_path: Path,
    ref_image: Optional[Path] = None,
    out_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run a full DRY_RUN over a STORYBOARD_V1 packet.

    Returns a manifest dict; also writes manifest.json + per-shot receipts
    to temple/subsandbox/renders/<task_id>/.
    """
    text = Path(packet_path).read_text(encoding="utf-8")
    task_id = _parse_task_id(text)
    shots = _parse_shot_table(text)
    if not shots:
        raise ValueError(f"no shots parsed from {packet_path}")

    target_dir = (out_dir or SUBSANDBOX) / task_id
    target_dir.mkdir(parents=True, exist_ok=True)

    if ref_image is None:
        # synthesize a placeholder ref image so DRY_RUN doesn't fail on missing file
        ref_image = target_dir / "_synth_ref.png"
        ref_image.write_bytes(b"\x89PNG\r\nDRY_RUN_SYNTH_REF")

    shot_receipts: List[Dict[str, Any]] = []
    total_duration = 0.0

    for shot in shots:
        seed = 2026050200 + shot["shot_n"]
        prompt = _build_prompt(shot)
        receipt = render_shot(
            ref_image=str(ref_image),
            prompt=prompt,
            duration_s=shot["duration_s"],
            seed=seed,
            task_id=task_id,
            shot_n=shot["shot_n"],
            mode="DRY_RUN",
        )
        emit_receipt(receipt, task_id=task_id)
        shot_receipts.append(receipt)
        total_duration += shot["duration_s"]

    music_manifest = music_for_storyboard(task_id, total_duration, target_dir)

    manifest = {
        "schema": "DRY_RUN_MANIFEST_V0",
        "task_id": task_id,
        "packet_path": str(packet_path),
        "n_shots": len(shots),
        "total_duration_s": total_duration,
        "shots": shot_receipts,
        "music": music_manifest,
        "scope": "TEMPLE_SUBSANDBOX",
        "sovereign_admitted": False,
        "mode": "DRY_RUN",
        "switch_to_live_requires": [
            "MAYOR admission of MAYOR_TASK_PACKET_HIGGSFIELD_SCHEMA.md",
            "MAYOR admission of MAYOR_TASK_PACKET_HIGGSFIELD_SKILL.md",
            "Skill code migrated to oracle_town/skills/video/higgsfield_seedance/",
            "HIGGSFIELD_API_KEY set on the executing node",
            "Operator-issued LIVE authorization for this task_id",
        ],
    }

    manifest_path = target_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "usage: python -m higgsfield_seedance.dry_run <STORYBOARD_V1.md>",
            file=sys.stderr,
        )
        return 2
    packet = Path(sys.argv[1])
    if not packet.exists():
        print(f"packet not found: {packet}", file=sys.stderr)
        return 1
    manifest = dry_run_storyboard(packet)
    print(json.dumps({
        "task_id": manifest["task_id"],
        "n_shots": manifest["n_shots"],
        "total_duration_s": manifest["total_duration_s"],
        "manifest_path": str(SUBSANDBOX / manifest["task_id"] / "manifest.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
