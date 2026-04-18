"""
helen_os.render.video — Video embodiment layer.

Pure function of execution output. Position: after E, never before.

Contract:
    execution_output (receipted) → RenderRequest → RenderResult

The render function is a deterministic subprocess call — it never reasons,
never mutates state, never calls tools. It takes a receipted packet and
produces an MP4 + provenance.json. That is its entire scope.

Why this separation matters:
    Video makes things feel true. Rendering ≠ truth.
    The ledger receipt is the truth surface. The video is a face.
    Binding video to receipt_hash makes the face traceable.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT      = Path(__file__).resolve().parents[2]
TEMPLATE_DIR   = REPO_ROOT / "oracle_town/skills/video/hyperframes/templates/meditation"
ARTIFACTS_MEDIA = REPO_ROOT / "artifacts/media"
ARTIFACTS_AUDIO = REPO_ROOT / "artifacts/audio"
TTS_SCRIPT     = REPO_ROOT / "oracle_town/skills/voice/gemini_tts/helen_tts.py"
GENERATOR      = TEMPLATE_DIR / "generate_meditation.py"

VALID_TONES    = frozenset({"calm", "energetic", "serious", "reflective", "symbolic"})
VALID_PERSONAS = frozenset({"helen", "narrator", "temple", "oracle", "mayor"})


# ── Contracts ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RenderRequest:
    """
    Typed contract between execution output and the render layer.

    Produced by E (execution), consumed by render_video().
    Must carry receipt_hash — binds the video to the ledger.
    authority is always False: the render layer has no epistemic standing.
    """
    content:      str             # text to speak / display
    receipt_hash: str             # sha256: of the execution receipt — mandatory
    run_id:       str             # unique render ID (use execution receipt ID)
    date:         str             # ISO date YYYY-MM-DD
    topic:        str             # short description of what this render covers
    tone:         str = "calm"    # calm | energetic | serious | reflective | symbolic
    persona:      str = "helen"   # helen | narrator | temple | oracle | mayor
    commit_sha:   str = ""        # optional: git commit SHA of the run
    commit_repo:  str = ""        # optional: repo name
    authority:    bool = False    # always False — render layer never claims authority

    def __post_init__(self) -> None:
        if self.authority:
            raise ValueError("RenderRequest.authority must be False — render ≠ truth")
        if not self.receipt_hash.startswith("sha256:"):
            raise ValueError("receipt_hash must be a sha256: prefixed string")
        if self.tone not in VALID_TONES:
            raise ValueError(f"tone must be one of {VALID_TONES}")
        if self.persona not in VALID_PERSONAS:
            raise ValueError(f"persona must be one of {VALID_PERSONAS}")


@dataclass(frozen=True)
class RenderResult:
    """
    Output of render_video(). Immutable. Carries provenance chain.

    video_path:       absolute path to rendered MP4 (None if render failed)
    provenance_hash:  sha256: of the provenance.json file
    receipt_hash:     echoed from RenderRequest — ledger binding preserved
    render_sha:       sha256: of the MP4 bytes (None if render failed)
    ok:               True if render succeeded
    error:            error message if ok=False
    authority:        always False
    """
    receipt_hash:    str
    ok:              bool
    video_path:      Optional[Path] = None
    provenance_hash: Optional[str]  = None
    render_sha:      Optional[str]  = None
    error:           Optional[str]  = None
    authority:       bool           = False

    def __post_init__(self) -> None:
        if self.authority:
            raise ValueError("RenderResult.authority must be False")


# ── Pure helpers ──────────────────────────────────────────────────────────────

def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_config(req: RenderRequest) -> dict:
    """Convert RenderRequest to meditation.config.json format."""
    return {
        "date":            req.date,
        "topic":           req.topic,
        "meditation_text": req.content,
        "run_hash":        req.receipt_hash,
        "commit_sha":      req.commit_sha,
        "commit_repo":     req.commit_repo,
        "authority":       "NONE",
        "tone":            req.tone,
        "persona":         req.persona,
    }


# ── Main render function ──────────────────────────────────────────────────────

def render_video(
    req: RenderRequest,
    *,
    output_path: Optional[Path] = None,
    dry_run: bool = False,
    timeout: int = 600,
) -> RenderResult:
    """
    Render execution output to MP4 via HyperFrames.

    Pure function: same RenderRequest → same bytes (deterministic).
    Subprocess only — no reasoning, no LLM calls, no state mutation.

    Args:
        req:         RenderRequest from execution layer (receipted)
        output_path: override default output path
        dry_run:     build + TTS but skip npx render (for testing)
        timeout:     subprocess timeout in seconds

    Returns:
        RenderResult — immutable, authority=False always
    """
    if not GENERATOR.exists():
        return RenderResult(
            receipt_hash=req.receipt_hash,
            ok=False,
            error=f"Generator not found: {GENERATOR}",
        )

    ARTIFACTS_MEDIA.mkdir(parents=True, exist_ok=True)

    date_slug  = req.date.replace("-", "")
    topic_slug = "".join(c if c.isalnum() else "_" for c in req.topic.lower())[:30]

    if output_path is None:
        output_path = ARTIFACTS_MEDIA / f"{date_slug}__{topic_slug}.mp4"

    # Write config to a temp file — no side effects on the template dir
    cfg = _build_config(req)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, prefix="helen_render_"
    ) as f:
        json.dump(cfg, f, indent=2)
        config_path = Path(f.name)

    try:
        cmd = [
            sys.executable, str(GENERATOR),
            "--config", str(config_path),
            "--output", str(output_path),
        ]
        if dry_run:
            cmd.append("--dry-run")

        env = {**os.environ}  # inherit GEMINI_API_KEY etc.

        result = subprocess.run(
            cmd,
            cwd=str(TEMPLATE_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            return RenderResult(
                receipt_hash=req.receipt_hash,
                ok=False,
                error=f"Generator exited {result.returncode}:\n{result.stderr[-800:]}",
            )

        if dry_run or not output_path.exists():
            return RenderResult(
                receipt_hash=req.receipt_hash,
                ok=True,
                video_path=None,
            )

        render_sha    = _sha256(output_path)
        prov_path     = output_path.with_suffix(".provenance.json")
        prov_hash     = _sha256(prov_path) if prov_path.exists() else None

        return RenderResult(
            receipt_hash=req.receipt_hash,
            ok=True,
            video_path=output_path,
            render_sha=render_sha,
            provenance_hash=prov_hash,
        )

    except subprocess.TimeoutExpired:
        return RenderResult(
            receipt_hash=req.receipt_hash,
            ok=False,
            error=f"Render timed out after {timeout}s",
        )
    except Exception as exc:
        return RenderResult(
            receipt_hash=req.receipt_hash,
            ok=False,
            error=str(exc),
        )
    finally:
        config_path.unlink(missing_ok=True)


# ── Run-to-video pipeline ─────────────────────────────────────────────────────

def render_run_as_video(
    run_id: str,
    ledger_entries: list[dict],
    *,
    date: Optional[str] = None,
    topic: str = "run summary",
    dry_run: bool = False,
) -> RenderResult:
    """
    "Explain this run as video" — the first killer feature.

    Input:  run_id + ledger entries (from ledger reader)
    Pipeline: ledger → trace summary → script → RenderRequest → render_video()
    Output: HELEN explains what happened, as MP4.

    The summary is produced deterministically from the ledger entries —
    no LLM call, no reasoning. Plain text assembly from receipted facts.
    When a trace packet schema exists, this will consume it directly.
    """
    if not ledger_entries:
        return RenderResult(
            receipt_hash="sha256:" + "0" * 64,
            ok=False,
            error="No ledger entries for run_id: " + run_id,
        )

    # Deterministic script from ledger facts — no LLM
    lines: list[str] = [f"Run {run_id[:12]}."]
    admitted = [e for e in ledger_entries if e.get("decision") == "ADMITTED"]
    rejected = [e for e in ledger_entries if e.get("decision") == "REJECTED"]

    if admitted:
        lines.append(
            f"{len(admitted)} skill{'s' if len(admitted) != 1 else ''} admitted: "
            + ", ".join(e.get("skill_id", "unknown") for e in admitted) + "."
        )
    if rejected:
        lines.append(
            f"{len(rejected)} rejected by constitutional gates."
        )

    lines.append("No receipt — no claim. All of it is in the ledger.")

    content = " ".join(lines)

    # Receipt hash: hash of the run's ledger entries (deterministic)
    run_hash = "sha256:" + hashlib.sha256(
        json.dumps(ledger_entries, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    req = RenderRequest(
        content=content,
        receipt_hash=run_hash,
        run_id=run_id,
        date=date or _now()[:10],
        topic=topic,
        tone="calm",
        persona="helen",
    )

    return render_video(req, dry_run=dry_run)
