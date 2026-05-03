"""HELEN VIDEO OS — Phase 0 (DRY_RUN only).

Per HAL: scaffold the meta-pipeline that holds intake -> storyboard
-> shotlist -> prompts -> dry render stubs -> receipts -> ledger.
NON_SOVEREIGN. TEMPLE_SUBSANDBOX scope. Stdlib only. Deterministic.

Acceptance: same intake + same seed -> same VIDEO_RUN_RECEIPT_V1 hash.

Hard exclusions:
- No cloud rendering
- No image/video generation
- No top-level promotion
- No MAYOR admission
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, List


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_obj(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_receipt(receipt_type: str, project_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    receipt: Dict[str, Any] = {
        "type": receipt_type,
        "project_id": project_id,
        "scope": "TEMPLE_SUBSANDBOX",
        "sovereign_admitted": False,
        "payload": payload,
        "status": "PASS",
        "blocking_issues": [],
    }
    receipt["receipt_hash"] = sha256_obj(receipt)
    return receipt


def append_ledger(events: List[Dict[str, Any]], receipt: Dict[str, Any]) -> List[Dict[str, Any]]:
    prev = events[-1]["cum_hash"] if events else "sha256:GENESIS"
    event: Dict[str, Any] = {
        "event_type": "RECEIPT_ADDED",
        "project_id": receipt["project_id"],
        "receipt_type": receipt["type"],
        "receipt_hash": receipt["receipt_hash"],
        "prev_cum_hash": prev,
    }
    event["cum_hash"] = sha256_obj(event)
    events.append(event)
    return events


def build_storyboard(intake: Dict[str, Any]) -> Dict[str, Any]:
    duration = int(intake["duration_seconds"])
    beat_count = max(1, math.ceil(duration / 8))
    beat_duration = duration / beat_count

    purposes = [
        "Introduce the system",
        "Reveal the governance logic",
        "Show the production packet",
        "Close with receipt-bound proof",
    ]

    beats: List[Dict[str, Any]] = []
    for i in range(beat_count):
        start = round(i * beat_duration, 3)
        end = round((i + 1) * beat_duration, 3)
        beats.append({
            "beat_id": f"B{i+1:03d}",
            "time_range": [start, end],
            "purpose": purposes[min(i, len(purposes) - 1)],
            "narration": "HELEN sees. HELEN proposes. The gate authorizes.",
            "visual_intent": (
                f"{intake['main_character']} inside a luminous "
                "governed video operating interface."
            ),
        })

    return {
        "schema": "STORYBOARD_V1",
        "project_id": intake["project_id"],
        "title": intake["title"],
        "beats": beats,
    }


CAMERAS: List[str] = [
    "slow push-in",
    "wide establishing shot",
    "medium frontal shot",
    "over-the-shoulder interface shot",
    "close-up portrait",
    "insert object shot",
    "slow orbit",
    "vertical reveal",
]

PRIME_TURNS = {2, 3, 5, 7, 11, 13}


def build_shotlist(intake: Dict[str, Any], storyboard: Dict[str, Any]) -> Dict[str, Any]:
    shots: List[Dict[str, Any]] = []
    seed = int(intake["seed"])

    for beat_index, beat in enumerate(storyboard["beats"]):
        start, end = beat["time_range"]
        beat_len = end - start
        shots_per_beat = max(1, math.ceil(beat_len / 4))
        shot_len = beat_len / shots_per_beat

        for j in range(shots_per_beat):
            shot_index = len(shots) + 1
            prime_turn = shot_index in PRIME_TURNS
            camera = CAMERAS[(seed + shot_index + beat_index) % len(CAMERAS)]
            s0 = round(start + j * shot_len, 3)
            s1 = round(start + (j + 1) * shot_len, 3)

            shots.append({
                "shot_id": f"S{shot_index:03d}",
                "beat_id": beat["beat_id"],
                "time_range": [s0, s1],
                "duration": round(s1 - s0, 3),
                "camera": camera,
                "subject": intake["main_character"],
                "environment": "blue-gold receipt ledger interface",
                "action": beat["visual_intent"],
                "style": intake["style_canon"],
                "negative": [
                    "identity drift",
                    "wrong hair color",
                    "text glitches",
                    "distorted face",
                    "extra fingers",
                    "unreadable symbols",
                ],
                "math_constraints": {
                    "phi_timing": True,
                    "prime_turn": prime_turn,
                    "continuity_role": "prime_turn" if prime_turn else "support",
                    "perception_constraints": {
                        "identity": f"{intake['main_character']}_CANON",
                        "style_vector": intake["style_canon"],
                        "scene_topology": "ledger_interface",
                        "motion_curve": camera,
                    },
                    "braid_strands": [
                        "face_identity",
                        "pose_motion",
                        "ledger_object",
                        "light_interface",
                        "camera_axis",
                    ],
                },
            })

    return {
        "schema": "SHOTLIST_V1",
        "project_id": intake["project_id"],
        "shots": shots,
    }


def compile_prompts(intake: Dict[str, Any], shotlist: Dict[str, Any]) -> Dict[str, Any]:
    prompts: List[Dict[str, Any]] = []
    for shot in shotlist["shots"]:
        prompt_text = (
            f"Cinematic vertical video shot of {shot['subject']}, "
            f"in {shot['environment']}. "
            f"Action: {shot['action']} "
            f"Camera: {shot['camera']}. "
            f"Style: {shot['style']}. "
            "Maintain consistent identity, premium lighting, clean composition."
        )
        prompts.append({
            "schema": "PROMPT_V1",
            "project_id": intake["project_id"],
            "shot_id": shot["shot_id"],
            "backend": "DRY_RUN",
            "prompt": prompt_text,
            "negative_prompt": ", ".join(shot["negative"]),
            "duration": shot["duration"],
            "aspect_ratio": intake["aspect_ratio"],
            "seed": intake["seed"],
            "math_constraints_hash": sha256_obj(shot["math_constraints"]),
        })

    return {
        "schema": "PROMPT_TABLE_V1",
        "project_id": intake["project_id"],
        "prompts": prompts,
    }


def dry_render(prompts: Dict[str, Any]) -> Dict[str, Any]:
    renders: List[Dict[str, Any]] = []
    for prompt in prompts["prompts"]:
        renders.append({
            "schema": "DRY_RENDER_STUB_V1",
            "project_id": prompt["project_id"],
            "shot_id": prompt["shot_id"],
            "backend": "DRY_RUN",
            "asset_uri": None,
            "asset_hash": None,
            "request_hash": sha256_obj(prompt),
            "status": "DRY_RUN_ONLY",
        })
    return {
        "schema": "DRY_RENDER_TABLE_V1",
        "project_id": prompts["project_id"],
        "renders": renders,
    }


def write_json(path: Path, obj: Any) -> None:
    path.write_text(canonical(obj), encoding="utf-8")


def run(intake_path: str, out_dir: str) -> str:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "receipts").mkdir(exist_ok=True)
    (out / "prompts").mkdir(exist_ok=True)
    (out / "renders").mkdir(exist_ok=True)

    intake = json.loads(Path(intake_path).read_text(encoding="utf-8"))
    project_id = intake["project_id"]

    if intake.get("mode") != "DRY_RUN":
        raise SystemExit("Phase 0 only supports mode=DRY_RUN")

    storyboard = build_storyboard(intake)
    shotlist = build_shotlist(intake, storyboard)
    prompts = compile_prompts(intake, shotlist)
    renders = dry_render(prompts)

    write_json(out / "intake.json", intake)
    write_json(out / "storyboard.json", storyboard)
    write_json(out / "shotlist.json", shotlist)
    write_json(out / "prompts.json", prompts)
    write_json(out / "renders.json", renders)

    receipts: List[Dict[str, Any]] = []
    receipts.append(make_receipt("INTAKE_RECEIPT_V1", project_id, {
        "intake_hash": sha256_obj(intake),
    }))
    receipts.append(make_receipt("STORYBOARD_RECEIPT_V1", project_id, {
        "input_hash": sha256_obj(intake),
        "storyboard_hash": sha256_obj(storyboard),
    }))
    receipts.append(make_receipt("SHOTLIST_RECEIPT_V1", project_id, {
        "storyboard_hash": sha256_obj(storyboard),
        "shotlist_hash": sha256_obj(shotlist),
    }))
    receipts.append(make_receipt("PROMPT_RECEIPT_V1", project_id, {
        "shotlist_hash": sha256_obj(shotlist),
        "prompts_hash": sha256_obj(prompts),
    }))
    receipts.append(make_receipt("DRY_RENDER_RECEIPT_V1", project_id, {
        "prompts_hash": sha256_obj(prompts),
        "renders_hash": sha256_obj(renders),
    }))

    ledger: List[Dict[str, Any]] = []
    for receipt in receipts:
        write_json(out / "receipts" / f"{receipt['type']}.json", receipt)
        append_ledger(ledger, receipt)

    video_run_receipt = make_receipt("VIDEO_RUN_RECEIPT_V1", project_id, {
        "intake_hash": sha256_obj(intake),
        "storyboard_hash": sha256_obj(storyboard),
        "shotlist_hash": sha256_obj(shotlist),
        "prompts_hash": sha256_obj(prompts),
        "renders_hash": sha256_obj(renders),
        "ledger_tip": ledger[-1]["cum_hash"],
        "mode": "DRY_RUN",
    })
    write_json(out / "receipts" / "VIDEO_RUN_RECEIPT_V1.json", video_run_receipt)
    append_ledger(ledger, video_run_receipt)

    with (out / "ledger.ndjson").open("w", encoding="utf-8") as f:
        for event in ledger:
            f.write(canonical(event) + "\n")

    manifest = {
        "schema": "EXPORT_MANIFEST_V1",
        "project_id": project_id,
        "mode": "DRY_RUN",
        "video_run_receipt_hash": video_run_receipt["receipt_hash"],
        "ledger_tip": ledger[-1]["cum_hash"],
        "status": "PASS",
    }
    write_json(out / "EXPORT_MANIFEST_V1.json", manifest)

    print(video_run_receipt["receipt_hash"])
    return video_run_receipt["receipt_hash"]


def main() -> int:
    parser = argparse.ArgumentParser(description="HELEN VIDEO OS Phase 0 DRY_RUN")
    parser.add_argument("--intake", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run(args.intake, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
