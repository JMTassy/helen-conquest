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
import sys
from pathlib import Path
from typing import Any, Dict, List

# Bridge to the helen-director skill — replaces internal storyboard/shotlist
# builders so the system has ONE decision engine, not two.
HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent / "skills" / "helen-director"
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from director import run_director  # noqa: E402


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


# build_storyboard / build_shotlist / CAMERAS / PRIME_TURNS removed in this
# upgrade. The Director (skills/helen-director/director.py) is now the
# single decision engine producing both. This file stays a thin pipeline
# orchestrator: intake -> Director -> prompts -> dry render -> receipts -> ledger.


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

    # Director call replaces the old internal builders.
    storyboard, shotlist = run_director(intake)
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
    receipts.append(make_receipt("DIRECTOR_RECEIPT_V1", project_id, {
        "intake_hash": sha256_obj(intake),
        "storyboard_hash": sha256_obj(storyboard),
        "shotlist_hash": sha256_obj(shotlist),
        "seed": intake["seed"],
        "deterministic": True,
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
