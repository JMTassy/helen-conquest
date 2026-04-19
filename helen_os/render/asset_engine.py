"""
HELEN ASSET_ENGINE_V1 — multi-model video clip generator.

Routes scene visual generation to optimal generator based on scene semantics.
Generators are pluggable: xAI, Higgsfield, Runway, local, or stub.

Pipeline position:
  STORYBOARD_V1 → ASSET_ENGINE → clips/ → MONTAGE → FINAL VIDEO

Authority: NONE — asset generation is non-sovereign.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import time
import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from helen_os.render.storyboard import Storyboard, StoryboardScene

logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return hashlib.sha256(h.digest()).hexdigest()  # nested to match montage convention


def _now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


# ── GeneratorConfig ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class GeneratorConfig:
    """Configuration for a single video generator backend."""
    name:        str
    api_base:    str                  # base URL for API calls (empty for local generators)
    api_key_env: str                  # env var name for API key (empty if none needed)
    model:       str                  # model identifier
    supports:    frozenset            # set of visual_type strings this generator handles

    def api_key(self) -> Optional[str]:
        """Read API key from environment. Returns None if not set."""
        if not self.api_key_env:
            return None
        return os.environ.get(self.api_key_env)

    def is_available(self) -> bool:
        """Check if this generator can be used (API key present or not needed)."""
        if not self.api_key_env:
            return True
        return bool(os.environ.get(self.api_key_env))


# ── GeneratorResult ──────────────────────────────────────────────────────────

@dataclass
class GeneratorResult:
    """Result of generating a single video clip for a scene."""
    scene_id:       str
    clip_path:      str               # path to generated clip (empty on failure)
    generator_used: str               # name of generator that produced the clip
    prompt:         str               # the prompt sent to the generator
    duration:       float             # requested duration in seconds
    content_hash:   str               # sha256 of the clip file (empty on failure)
    success:        bool
    error:          str = ""          # error message if success=False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id":       self.scene_id,
            "clip_path":      self.clip_path,
            "generator_used": self.generator_used,
            "prompt":         self.prompt,
            "duration":       self.duration,
            "content_hash":   self.content_hash,
            "success":        self.success,
            "error":          self.error,
        }


# ── Generator Registry ──────────────────────────────────────────────────────

GENERATOR_REGISTRY: Dict[str, GeneratorConfig] = {
    "xai_grok": GeneratorConfig(
        name="xai_grok",
        api_base="https://api.x.ai/v1",
        api_key_env="XAI_API_KEY",
        model="grok-2-video",
        supports=frozenset({"abstract", "energy", "human", "nature"}),
    ),
    "higgsfield": GeneratorConfig(
        name="higgsfield",
        api_base="https://api.higgsfield.ai/v1",
        api_key_env="HIGGSFIELD_API_KEY",
        model="higgsfield-v1",
        supports=frozenset({"abstract", "energy", "human", "nature"}),
    ),
    "runway": GeneratorConfig(
        name="runway",
        api_base="https://api.dev.runwayml.com/v1",
        api_key_env="RUNWAY_API_KEY",
        model="gen4_turbo",
        supports=frozenset({"abstract", "nature"}),
    ),
    "kling": GeneratorConfig(
        name="kling",
        api_base="https://api.klingai.com/v1",
        api_key_env="KLING_API_KEY",
        model="kling-v1",
        supports=frozenset({"energy"}),
    ),
    "sora": GeneratorConfig(
        name="sora",
        api_base="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        model="sora",
        supports=frozenset({"human"}),
    ),
    "stub": GeneratorConfig(
        name="stub",
        api_base="",
        api_key_env="",
        model="ffmpeg-stub",
        supports=frozenset({"abstract", "energy", "human", "nature"}),
    ),
}


# ── Visual Type Routing ──────────────────────────────────────────────────────
# Maps visual_type → ordered list of generator names to try (fallback chain).

VISUAL_TYPE_ROUTING: Dict[str, List[str]] = {
    "abstract": ["xai_grok", "runway",  "stub"],
    "energy":   ["xai_grok", "kling",   "stub"],
    "human":    ["xai_grok", "sora",    "stub"],
    "nature":   ["xai_grok", "runway",  "stub"],
}


# ── Prompt Construction ─────────────────────────────────────────────────────

# Emotion → visual modifiers for prompt enrichment
_EMOTION_MODIFIERS: Dict[str, str] = {
    "calm":       "serene, gentle, soft lighting",
    "vulnerable": "intimate, delicate, close-up, shallow depth of field",
    "powerful":   "dynamic, bold, strong contrast, cinematic",
    "intimate":   "warm, personal, soft focus, golden hour",
    "ascending":  "uplifting, rising, expansive, bright, open sky",
    "breaking":   "fragmenting, dissolving, dramatic shadows",
    "warm":       "warm tones, amber light, cozy, inviting",
    "tension":    "taut, stark, high contrast, compressed framing",
    "release":    "expanding, breathing, light breaking through",
}

# Camera motion → prompt hints
_CAMERA_PROMPT: Dict[str, str] = {
    "none":      "static shot",
    "slow_push": "slow push in, gradually closer",
    "drift":     "gentle drift, horizontal movement",
    "zoom_out":  "slow zoom out, revealing wider view",
    "pull_back":  "pulling back, expanding perspective",
    "orbit":     "slow orbit, circling the subject",
}


def scene_to_prompt(scene: StoryboardScene) -> str:
    """
    Convert a StoryboardScene into an optimal text prompt for video generation.

    Combines the visual description with emotion modifiers and camera hints
    to produce a prompt that captures the scene's intent.
    """
    parts: List[str] = []

    # Core visual description
    description = scene.visual.get("description", "").strip()
    if description:
        parts.append(description)

    # Emotion modifier
    emotion_mod = _EMOTION_MODIFIERS.get(scene.emotion, "")
    if emotion_mod:
        parts.append(emotion_mod)

    # Camera motion hint
    camera_motion = scene.camera.get("motion", "none")
    camera_hint = _CAMERA_PROMPT.get(camera_motion, "")
    if camera_hint:
        parts.append(camera_hint)

    # Visual type context
    vtype = scene.visual.get("type", "abstract")
    type_context = {
        "abstract":  "abstract visual, non-representational",
        "energy":    "energy visualization, flowing light, particles",
        "human":     "photorealistic human figure",
        "nature":    "natural landscape, organic forms",
    }
    if vtype in type_context:
        parts.append(type_context[vtype])

    # Cinematic quality baseline
    parts.append("cinematic quality, 4K, smooth motion")

    prompt = ". ".join(parts)
    logger.debug("scene_to_prompt(%s): %s", scene.scene_id, prompt[:120])
    return prompt


# ── Individual Generator Implementations ─────────────────────────────────────

def _generate_xai_grok(
    scene: StoryboardScene,
    config: GeneratorConfig,
    prompt: str,
    output_path: str,
) -> GeneratorResult:
    """
    Generate a video clip using xAI Grok video API.

    POST /v1/videos/generations → poll for completion → download result.
    """
    import urllib.request
    import urllib.error

    api_key = config.api_key()
    if not api_key:
        return GeneratorResult(
            scene_id=scene.scene_id, clip_path="", generator_used=config.name,
            prompt=prompt, duration=scene.duration, content_hash="",
            success=False, error=f"Missing API key: {config.api_key_env}",
        )

    # Submit generation request
    url = f"{config.api_base}/videos/generations"
    payload = json.dumps({
        "model": config.model,
        "prompt": prompt,
        "duration": min(int(scene.duration), 10),  # xAI max per request
    }).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        # Poll for completion
        job_id = result.get("id", "")
        if not job_id:
            # Synchronous response — data is inline
            video_url = _extract_video_url(result)
        else:
            video_url = _poll_xai_completion(config, job_id, timeout=300)

        if not video_url:
            return GeneratorResult(
                scene_id=scene.scene_id, clip_path="", generator_used=config.name,
                prompt=prompt, duration=scene.duration, content_hash="",
                success=False, error="No video URL in response",
            )

        # Download the video
        _download_file(video_url, output_path, api_key=api_key)
        content_hash = _sha256_file(output_path)

        return GeneratorResult(
            scene_id=scene.scene_id, clip_path=output_path,
            generator_used=config.name, prompt=prompt,
            duration=scene.duration, content_hash=content_hash,
            success=True,
        )

    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        return GeneratorResult(
            scene_id=scene.scene_id, clip_path="", generator_used=config.name,
            prompt=prompt, duration=scene.duration, content_hash="",
            success=False, error=f"xAI API error: {e}",
        )
    except Exception as e:
        return GeneratorResult(
            scene_id=scene.scene_id, clip_path="", generator_used=config.name,
            prompt=prompt, duration=scene.duration, content_hash="",
            success=False, error=f"xAI generation failed: {e}",
        )


def _extract_video_url(response: Dict[str, Any]) -> str:
    """Extract video URL from xAI response (handles multiple response shapes)."""
    # Direct URL
    if "url" in response:
        return response["url"]
    # data[0].url
    data = response.get("data", [])
    if data and isinstance(data, list) and "url" in data[0]:
        return data[0]["url"]
    # data[0].video.url
    if data and isinstance(data, list):
        video = data[0].get("video", {})
        if "url" in video:
            return video["url"]
    return ""


def _poll_xai_completion(
    config: GeneratorConfig,
    job_id: str,
    timeout: int = 300,
    interval: float = 5.0,
) -> str:
    """Poll xAI for job completion, return video URL or empty string."""
    import urllib.request

    api_key = config.api_key()
    url = f"{config.api_base}/videos/generations/{job_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            status = result.get("status", "").lower()
            if status in ("succeeded", "complete", "completed"):
                return _extract_video_url(result)
            if status in ("failed", "error", "cancelled"):
                logger.error("xAI job %s failed: %s", job_id, result.get("error", ""))
                return ""

            logger.debug("xAI job %s status: %s", job_id, status)
        except Exception as e:
            logger.warning("Poll error for job %s: %s", job_id, e)

        time.sleep(interval)

    logger.error("xAI job %s timed out after %ds", job_id, timeout)
    return ""


def _generate_higgsfield(
    scene: StoryboardScene,
    config: GeneratorConfig,
    prompt: str,
    output_path: str,
) -> GeneratorResult:
    """
    Generate a video clip using Higgsfield API.

    Two-step: text-to-image → image-to-video.
    """
    import urllib.request
    import urllib.error

    api_key = config.api_key()
    if not api_key:
        return GeneratorResult(
            scene_id=scene.scene_id, clip_path="", generator_used=config.name,
            prompt=prompt, duration=scene.duration, content_hash="",
            success=False, error=f"Missing API key: {config.api_key_env}",
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        # Step 1: text → image
        img_url = f"{config.api_base}/text-to-image"
        img_payload = json.dumps({
            "prompt": prompt,
            "width": 1920,
            "height": 1080,
        }).encode("utf-8")

        req = urllib.request.Request(img_url, data=img_payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            img_result = json.loads(resp.read().decode("utf-8"))

        image_url = img_result.get("url", img_result.get("image_url", ""))
        if not image_url:
            data = img_result.get("data", [])
            if data and isinstance(data, list):
                image_url = data[0].get("url", "")

        if not image_url:
            return GeneratorResult(
                scene_id=scene.scene_id, clip_path="", generator_used=config.name,
                prompt=prompt, duration=scene.duration, content_hash="",
                success=False, error="Higgsfield text-to-image returned no image URL",
            )

        # Step 2: image → video
        vid_url = f"{config.api_base}/image-to-video"
        vid_payload = json.dumps({
            "image_url": image_url,
            "prompt": prompt,
            "duration": min(int(scene.duration), 10),
        }).encode("utf-8")

        req = urllib.request.Request(vid_url, data=vid_payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            vid_result = json.loads(resp.read().decode("utf-8"))

        video_url = vid_result.get("url", vid_result.get("video_url", ""))
        if not video_url:
            data = vid_result.get("data", [])
            if data and isinstance(data, list):
                video_url = data[0].get("url", "")

        if not video_url:
            return GeneratorResult(
                scene_id=scene.scene_id, clip_path="", generator_used=config.name,
                prompt=prompt, duration=scene.duration, content_hash="",
                success=False, error="Higgsfield image-to-video returned no video URL",
            )

        _download_file(video_url, output_path, api_key=api_key)
        content_hash = _sha256_file(output_path)

        return GeneratorResult(
            scene_id=scene.scene_id, clip_path=output_path,
            generator_used=config.name, prompt=prompt,
            duration=scene.duration, content_hash=content_hash,
            success=True,
        )

    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        return GeneratorResult(
            scene_id=scene.scene_id, clip_path="", generator_used=config.name,
            prompt=prompt, duration=scene.duration, content_hash="",
            success=False, error=f"Higgsfield API error: {e}",
        )
    except Exception as e:
        return GeneratorResult(
            scene_id=scene.scene_id, clip_path="", generator_used=config.name,
            prompt=prompt, duration=scene.duration, content_hash="",
            success=False, error=f"Higgsfield generation failed: {e}",
        )


def _generate_stub(
    scene: StoryboardScene,
    config: GeneratorConfig,
    prompt: str,
    output_path: str,
) -> GeneratorResult:
    """
    Generate a stub clip: black background with text overlay using ffmpeg.

    Works offline with no API keys — essential for pipeline testing.
    """
    duration = max(scene.duration, 0.5)

    # Sanitise text for ffmpeg drawtext (escape special chars)
    label_text = scene.scene_id
    emotion_text = scene.emotion
    vtype_text = scene.visual.get("type", "abstract")
    # Truncate prompt for display
    prompt_display = prompt[:80].replace("'", "").replace(":", " ").replace("\\", "")

    # Build ffmpeg command
    drawtext_base = (
        "fontsize=36:fontcolor=white:x=(w-text_w)/2"
    )
    filter_parts = [
        f"color=c=black:s=1920x1080:d={duration:.2f}:r=30[bg]",
        # Scene ID label at top
        f"[bg]drawtext=text='{label_text}':{drawtext_base}:y=80[t1]",
        # Visual type + emotion in middle
        f"[t1]drawtext=text='{vtype_text} | {emotion_text}':{drawtext_base}:y=h/2-40[t2]",
        # Prompt excerpt at bottom
        f"[t2]drawtext=text='{prompt_display}':"
        f"fontsize=24:fontcolor=gray:x=(w-text_w)/2:y=h-120[out]",
    ]
    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=black:1920x1080:d={duration:.2f}:r=30",
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-t", f"{duration:.2f}",
        output_path,
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            # Fallback: simpler command without drawtext (in case fontconfig missing)
            logger.warning("Stub drawtext failed, falling back to plain black clip")
            cmd_simple = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=black:1920x1080:d={duration:.2f}:r=30",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
                "-pix_fmt", "yuv420p",
                "-t", f"{duration:.2f}",
                output_path,
            ]
            result = subprocess.run(
                cmd_simple, capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return GeneratorResult(
                    scene_id=scene.scene_id, clip_path="", generator_used=config.name,
                    prompt=prompt, duration=duration, content_hash="",
                    success=False,
                    error=f"ffmpeg failed: {result.stderr[-400:] if result.stderr else 'unknown'}",
                )

        content_hash = _sha256_file(output_path)
        return GeneratorResult(
            scene_id=scene.scene_id, clip_path=output_path,
            generator_used=config.name, prompt=prompt,
            duration=duration, content_hash=content_hash,
            success=True,
        )

    except FileNotFoundError:
        return GeneratorResult(
            scene_id=scene.scene_id, clip_path="", generator_used=config.name,
            prompt=prompt, duration=duration, content_hash="",
            success=False, error="ffmpeg not found in PATH",
        )
    except subprocess.TimeoutExpired:
        return GeneratorResult(
            scene_id=scene.scene_id, clip_path="", generator_used=config.name,
            prompt=prompt, duration=duration, content_hash="",
            success=False, error="ffmpeg stub timed out (>30s)",
        )


# ── Download helper ──────────────────────────────────────────────────────────

def _download_file(url: str, dest: str, api_key: str = "") -> None:
    """Download a file from URL to local path."""
    import urllib.request

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)


# ── Generator Dispatch ───────────────────────────────────────────────────────

# Maps generator name → implementation function
_GENERATOR_FN: Dict[str, Callable] = {
    "xai_grok":   _generate_xai_grok,
    "higgsfield": _generate_higgsfield,
    "runway":     _generate_xai_grok,     # Runway uses same REST pattern as xAI
    "kling":      _generate_xai_grok,     # Kling uses same REST pattern as xAI
    "sora":       _generate_xai_grok,     # Sora uses same REST pattern as xAI
    "stub":       _generate_stub,
}


def generate_clip(
    scene: StoryboardScene,
    generator_config: GeneratorConfig,
    output_dir: Path,
) -> GeneratorResult:
    """
    Generate a video clip for a single scene using the specified generator.

    Args:
        scene: The storyboard scene to generate a clip for.
        generator_config: Configuration of the generator to use.
        output_dir: Directory to write the clip into.

    Returns:
        GeneratorResult with success/failure details.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / f"{scene.scene_id}_{generator_config.name}.mp4")
    prompt = scene_to_prompt(scene)

    gen_fn = _GENERATOR_FN.get(generator_config.name)
    if gen_fn is None:
        return GeneratorResult(
            scene_id=scene.scene_id, clip_path="", generator_used=generator_config.name,
            prompt=prompt, duration=scene.duration, content_hash="",
            success=False, error=f"No implementation for generator: {generator_config.name}",
        )

    logger.info(
        "Generating clip: scene=%s generator=%s duration=%.1fs",
        scene.scene_id, generator_config.name, scene.duration,
    )

    result = gen_fn(scene, generator_config, prompt, output_path)
    if result.success:
        logger.info(
            "Clip generated: scene=%s generator=%s hash=%s",
            scene.scene_id, generator_config.name, result.content_hash[:16],
        )
    else:
        logger.warning(
            "Clip failed: scene=%s generator=%s error=%s",
            scene.scene_id, generator_config.name, result.error,
        )

    return result


# ── Batch Generation with Fallback ───────────────────────────────────────────

def generate_all_clips(
    storyboard: Storyboard,
    output_dir: Path,
    generators: Optional[List[str]] = None,
) -> List[GeneratorResult]:
    """
    Generate video clips for every scene in a storyboard.

    Routes each scene through VISUAL_TYPE_ROUTING and tries generators in
    order until one succeeds (fallback chain).

    Args:
        storyboard: The source storyboard.
        output_dir: Directory to write clips into (created if missing).
        generators: Optional explicit list of generator names to try
                    (overrides VISUAL_TYPE_ROUTING for all scenes).

    Returns:
        List of GeneratorResult, one per scene.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: List[GeneratorResult] = []

    for scene in storyboard.scenes:
        vtype = scene.visual.get("type", "abstract")

        # Determine generator fallback chain
        if generators:
            chain = generators
        else:
            chain = VISUAL_TYPE_ROUTING.get(vtype, VISUAL_TYPE_ROUTING["abstract"])

        logger.info(
            "Scene %s (type=%s): trying generators %s",
            scene.scene_id, vtype, chain,
        )

        result: Optional[GeneratorResult] = None

        for gen_name in chain:
            config = GENERATOR_REGISTRY.get(gen_name)
            if config is None:
                logger.warning("Unknown generator in chain: %s (skipping)", gen_name)
                continue

            # Check if generator supports this visual type
            if vtype not in config.supports:
                logger.debug(
                    "Generator %s does not support type=%s (skipping)",
                    gen_name, vtype,
                )
                continue

            # Check if generator is available (API key present)
            if not config.is_available():
                logger.debug(
                    "Generator %s unavailable (no %s set, skipping)",
                    gen_name, config.api_key_env,
                )
                continue

            result = generate_clip(scene, config, output_dir)
            if result.success:
                break
            else:
                logger.info(
                    "Generator %s failed for %s, trying next: %s",
                    gen_name, scene.scene_id, result.error,
                )

        if result is None:
            # No generator was even attempted
            result = GeneratorResult(
                scene_id=scene.scene_id, clip_path="", generator_used="none",
                prompt=scene_to_prompt(scene), duration=scene.duration,
                content_hash="", success=False,
                error=f"No available generator for visual_type={vtype}",
            )

        results.append(result)

    # Summary log
    succeeded = sum(1 for r in results if r.success)
    logger.info(
        "Asset generation complete: %d/%d scenes succeeded",
        succeeded, len(results),
    )

    return results


# ── ASSET_RECEIPT_V1 ─────────────────────────────────────────────────────────

@dataclass
class AssetReceipt:
    """
    Receipt for a batch of generated video clips.

    Proves: these clips were generated from this storyboard, by these generators,
    with these content hashes, at this time.

    Authority is always NONE — asset generation is non-sovereign.
    """
    storyboard_id:  str
    clips:          List[Dict[str, Any]]   # per-clip: scene_id, clip_path, hash, generator
    generators_used: List[str]             # unique list of generators that produced clips
    total_scenes:   int
    scenes_succeeded: int
    scenes_failed:  int
    timestamp:      str = ""
    authority:      str = "NONE"

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError(f"AssetReceipt.authority must be NONE, got {self.authority}")
        if not self.timestamp:
            self.timestamp = _now_utc()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type":              "ASSET_RECEIPT_V1",
            "storyboard_id":     self.storyboard_id,
            "clips":             self.clips,
            "generators_used":   self.generators_used,
            "total_scenes":      self.total_scenes,
            "scenes_succeeded":  self.scenes_succeeded,
            "scenes_failed":     self.scenes_failed,
            "timestamp":         self.timestamp,
            "authority":         self.authority,
        }

    def receipt_hash(self) -> str:
        return _sha256(_canon(self.to_dict()))

    @classmethod
    def from_results(
        cls,
        storyboard_id: str,
        results: List[GeneratorResult],
    ) -> AssetReceipt:
        """Build a receipt from a list of GeneratorResults."""
        clips = [
            {
                "scene_id":     r.scene_id,
                "clip_path":    r.clip_path,
                "content_hash": r.content_hash,
                "generator":    r.generator_used,
                "duration":     r.duration,
                "success":      r.success,
                "error":        r.error,
            }
            for r in results
        ]

        generators_used = sorted(set(
            r.generator_used for r in results if r.success
        ))

        succeeded = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)

        return cls(
            storyboard_id=storyboard_id,
            clips=clips,
            generators_used=generators_used,
            total_scenes=len(results),
            scenes_succeeded=succeeded,
            scenes_failed=failed,
        )
