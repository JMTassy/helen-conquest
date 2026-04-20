"""HELEN director-plan runner (v0.4 skeleton).

Reads a director_plan.json (example: ../director_plans/HELEN_3MIN_TEST_001.json),
drives the dual-canonical pipeline keyframe-by-keyframe, gates each keyframe
via Mirror Oracle (REAL + TWIN), runs retries per the plan's retry_policy,
assembles a sparse-keyframe video with Ken-Burns motion + crossfades, then
posts to Telegram.

Implementation discipline:
  - All keyframe generation routes through clone_from_latent(z_struct) — never
    through H(m) with payload mutations. Payload-salting invalidates slice
    isolation and is scientifically unacceptable per the locked doctrine.
  - z_id is computed ONCE from the identity.math_object_ref and held constant
    across all 18 keyframes. Only z_control and z_style are transported.
  - Failure cascade per plan: reduce_control_step → reduce_style_step →
    fallback_to_previous_accepted.
  - REAL_master_TWIN_oracle mode: master video uses REAL only; TWIN runs as
    a diagnostic Mirror Oracle on the same keyframe latents for logging.

Status: v0.4 SKELETON — stubs present for all backend hooks. Wire real
Higgsfield / Flux / ArcFace / Telegram endpoints before running for real.
No credits will be spent by this skeleton — every backend call raises
NotImplementedError until explicitly wired.

Run (when wired):
    PYTHONPATH=src python scripts/run_director_plan.py \
        ../director_plans/HELEN_3MIN_TEST_001.json \
        --mp3 ~/Downloads/Helen\\ Os.mp3 \
        --out-dir out/helen_3min_test_001
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


# ═════════════════════════════════════════════════════════════════════════
# Plan loading + validation
# ═════════════════════════════════════════════════════════════════════════

@dataclass
class RunManifest:
    plan_path: str
    plan: Dict[str, Any]
    out_dir: Path
    started_at: float
    accepted_keyframes: List[Dict[str, Any]] = field(default_factory=list)
    retries: int = 0
    mirror_green: int = 0
    mirror_yellow: int = 0
    mirror_red: int = 0
    drift_events: List[Dict[str, Any]] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps({
            "plan_path": self.plan_path,
            "out_dir": str(self.out_dir),
            "started_at": self.started_at,
            "accepted_keyframes": self.accepted_keyframes,
            "retries": self.retries,
            "mirror_green": self.mirror_green,
            "mirror_yellow": self.mirror_yellow,
            "mirror_red": self.mirror_red,
            "drift_events": self.drift_events,
            "pass_rate_real": self._pass_rate("real"),
            "pass_rate_twin": self._pass_rate("twin"),
            "retry_tax": self._retry_tax(),
        }, indent=2)

    def _pass_rate(self, lane: str) -> float:
        if not self.accepted_keyframes:
            return 0.0
        passes = sum(1 for k in self.accepted_keyframes if k.get(f"gate_{lane}_pass"))
        return passes / len(self.accepted_keyframes)

    def _retry_tax(self) -> float:
        if not self.accepted_keyframes:
            return 0.0
        return self.retries / len(self.accepted_keyframes)


def load_plan(path: str) -> Dict[str, Any]:
    with open(path) as f:
        plan = json.load(f)
    required_top_level = ["project", "identity", "gates", "timeline", "logging", "telegram"]
    for k in required_top_level:
        if k not in plan:
            raise ValueError(f"director_plan missing top-level key: {k}")
    keyframe_count = plan["project"]["keyframe_count"]
    timeline_len = len(plan["timeline"])
    if keyframe_count != timeline_len:
        raise ValueError(f"keyframe_count={keyframe_count} but timeline has {timeline_len} entries")
    return plan


# ═════════════════════════════════════════════════════════════════════════
# Emotion/camera/delta → latent-slice offsets
# ═════════════════════════════════════════════════════════════════════════

_DELTA_MAGNITUDE = {"low": 0.05, "mid": 0.15, "high": 0.30}


def emotion_to_control_offset(emotion: str, intensity: float) -> np.ndarray:
    """Deterministic mapping emotion → z_control delta direction.

    STUB: uses a small hardcoded dictionary. In production, replace with a
    learned mapping from the Emotions Spectrum plugin taxonomy to z_control.
    """
    import hashlib
    seed = int.from_bytes(hashlib.sha256(emotion.encode()).digest()[:4], "big")
    rng = np.random.default_rng(seed)
    direction = rng.normal(size=(128,)).astype(np.float32)
    direction /= np.linalg.norm(direction) + 1e-8
    return intensity * direction


def scene_to_style_offset(camera: str, palette_mode: str) -> np.ndarray:
    """Deterministic mapping (camera, palette) → z_style delta."""
    import hashlib
    seed = int.from_bytes(hashlib.sha256(f"{camera}|{palette_mode}".encode()).digest()[:4], "big")
    rng = np.random.default_rng(seed)
    direction = rng.normal(size=(128,)).astype(np.float32)
    direction /= np.linalg.norm(direction) + 1e-8
    return 0.15 * direction


# ═════════════════════════════════════════════════════════════════════════
# Keyframe generation + gating (STUBBED backends)
# ═════════════════════════════════════════════════════════════════════════

def compile_z_id(identity_cfg: Dict[str, Any]) -> Any:
    """Compute z_id once from the identity's math_object_ref.

    STUB: wire to src/helen/H_sha256.py with the actual MathObject loader.
    """
    raise NotImplementedError(
        "Wire to MathObject loader + H_SHA256 from the starter pipeline. "
        "Example: m = load_math_object(identity_cfg['math_object_ref']); "
        "z_struct = H_SHA256(latent_spec)(m)."
    )


def render_keyframe_dual(z_struct: Any, mode: str) -> Dict[str, Any]:
    """Render REAL + TWIN outputs for a structured latent.

    STUB: wire to src/helen/pipeline_dual.py (HelenDualCloner.clone_from_latent).
    """
    raise NotImplementedError(
        "Wire to HelenDualCloner.clone_from_latent(z_struct). Return dict with "
        "keys {real_img, twin_img, gate_real_pass, gate_twin_pass}."
    )


def mirror_oracle_verdict(gate_real_pass: bool, gate_twin_pass: bool) -> str:
    """Green / yellow / red per Twin Mirror Lie Detector (LATERAL_EMERGENT §11)."""
    if gate_real_pass and gate_twin_pass:
        return "green"
    if gate_real_pass != gate_twin_pass:
        return "yellow"
    return "red"


# ═════════════════════════════════════════════════════════════════════════
# Retry cascade per plan
# ═════════════════════════════════════════════════════════════════════════

def attempt_keyframe(
    z_struct_base: Any,
    scene: Dict[str, Any],
    retry_policy: Dict[str, Any],
    mode: str,
) -> Dict[str, Any]:
    """Generate one keyframe with up to N retries via the plan's failure cascade.

    Cascade: reduce_control_step → reduce_style_step → fallback_to_previous_accepted
    """
    max_retries = int(retry_policy.get("max_retries_per_keyframe", 2))
    attempts = []

    control_scale = _DELTA_MAGNITUDE[scene["control_delta"]]
    style_scale = _DELTA_MAGNITUDE[scene["style_delta"]]

    for attempt in range(max_retries + 1):
        # Apply scaled offsets to structured latent — stub; real impl in pipeline_dual
        # apply_scene_to_latent(z_struct_base, scene, control_scale, style_scale)
        try:
            result = render_keyframe_dual(z_struct_base, mode=mode)
        except NotImplementedError as e:
            return {"ok": False, "reason": "backends_not_wired", "detail": str(e),
                    "attempts": attempt + 1}

        verdict = mirror_oracle_verdict(result["gate_real_pass"], result["gate_twin_pass"])
        attempts.append({"attempt": attempt, "verdict": verdict,
                         "control_scale": control_scale, "style_scale": style_scale})

        if verdict == "green":
            return {"ok": True, "verdict": verdict, "attempts": attempts, "result": result}

        # Failure cascade
        if attempt == 0:
            control_scale *= 0.5  # reduce_control_step
        elif attempt == 1:
            style_scale *= 0.5    # reduce_style_step
        else:
            # fallback_to_previous_accepted — signal to caller
            return {"ok": False, "reason": "fallback_to_previous", "attempts": attempts}

    return {"ok": False, "reason": "exhausted_retries", "attempts": attempts}


# ═════════════════════════════════════════════════════════════════════════
# Assembly + distribution (STUBBED)
# ═════════════════════════════════════════════════════════════════════════

def assemble_ken_burns_video(
    keyframes: List[Dict[str, Any]],
    mp3_path: Path,
    out_mp4: Path,
    fps: int = 24,
) -> Path:
    """Build the 180-s master video from 18 accepted keyframes with Ken-Burns +
    crossfades, muxed with the MP3.

    STUB: wire to ffmpeg (see helen-director SKILL.md §16 for the canonical
    concat/xfade/amix pattern).
    """
    raise NotImplementedError("Wire to ffmpeg concat + xfade + audio mux.")


def publish_to_telegram(
    master_mp4: Path,
    teaser_mp4: Optional[Path],
    vertical_mp4: Optional[Path],
    poster_grid_png: Optional[Path],
    caption_template: str,
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """Post to the HELEN Telegram channel (chat_id 6624890918).

    STUB: wire to the same multipart sendVideo pattern used in
    oracle_town/skills/video/helen-director (msg 708 / 711 / 712 / 713).
    """
    raise NotImplementedError(
        "Wire to multipart sendVideo. Use TELEGRAM_BOT_TOKEN from ~/.helen_env."
    )


# ═════════════════════════════════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════════════════════════════════

def main() -> None:
    ap = argparse.ArgumentParser(description="HELEN director-plan runner (v0.4 skeleton)")
    ap.add_argument("plan", help="Path to director_plan.json")
    ap.add_argument("--mp3", help="Path to the 3-minute MP3", required=False)
    ap.add_argument("--out-dir", default="out/director_run")
    args = ap.parse_args()

    plan = load_plan(args.plan)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = RunManifest(
        plan_path=str(args.plan),
        plan=plan,
        out_dir=out_dir,
        started_at=time.time(),
    )

    print(f"[plan] {plan['project']['title']}  mode={plan['project']['render_mode']}")
    print(f"[plan] {plan['project']['duration_sec']}s  {plan['project']['keyframe_count']} keyframes")
    print(f"[plan] gate: {plan['gates']['real_profile']} + {plan['gates']['twin_profile']}  mirror_oracle={plan['gates']['mirror_oracle']}")

    # --- Lock identity once ---
    try:
        z_id_struct = compile_z_id(plan["identity"])
    except NotImplementedError as e:
        print(f"[skeleton] compile_z_id not wired yet: {e}")
        print(f"[skeleton] would generate {plan['project']['keyframe_count']} keyframes")
        print(f"[skeleton] REAL master / TWIN oracle mode: {plan['project']['render_mode'] == 'REAL_master_TWIN_oracle'}")
        manifest_path = out_dir / "run_manifest_dry.json"
        manifest_path.write_text(manifest.to_json())
        print(f"[skeleton] dry-run manifest written: {manifest_path}")
        sys.exit(0)

    # --- Iterate scenes ---
    accepted_keyframes = []
    for scene in plan["timeline"]:
        print(f"[scene {scene['label']}] emotion={scene['emotion']} intensity={scene['intensity']}")
        outcome = attempt_keyframe(
            z_struct_base=z_id_struct,
            scene=scene,
            retry_policy=plan["gates"]["retry_policy"],
            mode=plan["project"]["render_mode"],
        )
        if outcome["ok"]:
            accepted_keyframes.append({**scene, "verdict": outcome["verdict"], "attempts": outcome["attempts"]})
            manifest.accepted_keyframes.append({**scene, "verdict": outcome["verdict"]})
            if outcome["verdict"] == "green":
                manifest.mirror_green += 1
            elif outcome["verdict"] == "yellow":
                manifest.mirror_yellow += 1
            else:
                manifest.mirror_red += 1
            manifest.retries += len(outcome["attempts"]) - 1
        else:
            manifest.drift_events.append({"scene": scene["label"], "reason": outcome.get("reason")})

    # --- Assemble + distribute ---
    mp3_path = Path(args.mp3) if args.mp3 else None
    if mp3_path and mp3_path.exists() and accepted_keyframes:
        master = assemble_ken_burns_video(
            accepted_keyframes, mp3_path, out_dir / "master.mp4", fps=plan["project"]["fps_out"]
        )
        publish_to_telegram(
            master_mp4=master,
            teaser_mp4=None,
            vertical_mp4=None,
            poster_grid_png=None,
            caption_template=plan["telegram"]["caption_template"],
            metrics={},
        )

    manifest_path = out_dir / "run_manifest.json"
    manifest_path.write_text(manifest.to_json())
    print(f"[done] manifest: {manifest_path}")


if __name__ == "__main__":
    main()
