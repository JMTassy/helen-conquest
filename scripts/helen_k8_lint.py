#!/usr/bin/env python3
"""
HELEN K8 — Non-Determinism Boundary Gate (v1.2, post-rereview hardening)
========================================================================
LLM/TTS/video subagent output is NEVER a primary ledger event.
It is always wrapped by a deterministic claim whose payload carries:
  - hash(payload) of the wrapped non-deterministic content
  - identity of model + voice/seed if applicable

Three invariants:
  μ_NDWRAP        Any call to a non-deterministic surface (TTS / image / video /
                  LLM) inside oracle_town/skills/{voice,video,feynman}/ that is
                  NOT inside a function whose direct body references a wrap
                  token (payload_hash / provenance / k8_wrap) as an identifier
                  — string literals and nested function scopes do NOT count
                  (REV-3 reopen, AST-based).
  μ_NDARTIFACT    Any non-deterministic artifact (audio, video, image, OR
                  AUDIT_V1 / REVIEW_V1 markdown under artifacts/{audio,media,
                  reviews,audits,session_notes}/) that lacks a sibling
                  .provenance.json or .provenance.md sidecar.
  μ_NDLEDGER      Any ledger entry whose op ∈ NON_DET_OPS, OR whose payload
                  schema starts with an ND prefix (AUDIT_V*, REVIEW_V*, etc.),
                  OR whose payload.text begins with a registered ND text marker
                  (REV-2 reopen — covers existing user_msg/turn carriers), must
                  have a top-level payload_hash that EQUALS sha256(canon(payload)).
                  Field-key matches are gated on op ∈ ND_FIELD_KEY_OPS to avoid
                  false positives (REV-2.1).
                  Missing ledger surface = fail-closed (REV-5).

Modes (REV-6 reopen): git_diff (default, no -C — runs from cwd like K-τ),
manifest_list, all_nd. Aborts if `git rev-parse --show-toplevel` disagrees
with repo_root() and --allow-nested-repo not set.

On FAIL (REV-7 reopen): appends type='k8_fail' (schema K8_FAIL_V1) directly
to town/ledger_v1.ndjson using helen_say's chained-hash protocol — bypasses
helen_say so the receipt lands even when the kernel is down. payload_hash
equals sha256(canon(payload)) and the entry is then verifiable by K8's own
mu_NDLEDGER on next run (self-witnessing contradiction).

Artifacts emitted:
  artifacts/k8_manifest.json   — frozen config snapshot
  artifacts/k8_trace.ndjson    — per-invariant margin trace
  artifacts/k8_summary.json    — k8, witness, counterexample

NO RECEIPT = NO CLAIM. (Core Law, HELEN / LNSA)
NO HASH = NO VOICE.    (K8 Corollary)
"""
from __future__ import annotations

import argparse
import ast
import datetime
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── Constants ────────────────────────────────────────────────────────────────

INVARIANTS = ["mu_NDWRAP", "mu_NDARTIFACT", "mu_NDLEDGER"]

ND_SURFACES = {
    "gemini": [
        "generativelanguage.googleapis.com",
        "google.generativeai",
        "genai.GenerativeModel",
    ],
    "openai":    ["openai.OpenAI", "openai.AsyncOpenAI", "ChatCompletion.create"],
    "anthropic": ["anthropic.Anthropic", "anthropic.AsyncAnthropic"],
    "tts":       [".synthesize_speech", ".generate_speech", "tts."],
    "hyperframes": ["npx hyperframes", "hyperframes.render"],
    "heygen":    ["heygen.com/api", "heygen.video"],
    "replicate": ["replicate.run("],
}

ND_SCOPED_DIRS = [
    "oracle_town/skills/voice/",
    "oracle_town/skills/video/",
    "oracle_town/skills/feynman/",
]

ND_BINARY_EXTS = {".wav", ".mp3", ".mp4", ".webm", ".png", ".jpg", ".gif"}
ND_BINARY_DIRS = ["artifacts/audio/", "artifacts/media/", "artifacts/video/"]

ND_TEXT_DIRS = ["artifacts/reviews/", "artifacts/audits/", "artifacts/session_notes/"]
ND_TEXT_EXTS = {".md", ".json"}
ND_TEXT_PROVENANCE_SUFFIXES = {".provenance.md", ".provenance.json"}

NON_DET_OPS = {
    "voice", "tts", "render_video", "image_gen",
    "llm_call", "subagent_output", "review", "audit",
    "k8_fail",
}

# REV-2.1: field-key shape detection only fires for these ops to avoid false positives
ND_FIELD_KEY_OPS = {"voice", "tts", "render_video", "image_gen",
                    "llm_call", "subagent_output", "review", "audit", "k8_fail"}

ND_PAYLOAD_SCHEMA_PREFIXES = ("AUDIT_V", "REVIEW_V", "REPLICATE_V", "TTS_V", "RENDER_V", "K8_FAIL_V")
ND_PAYLOAD_FIELD_KEYS = {"model_id", "subagent_output", "llm_output", "audio_sha", "render_sha"}

# REV-2 reopen: ND text markers — prefixes that, when found in payload.text of a
# user_msg/turn entry, scope it as ND-bearing (because helen_say is the only
# writer today, and the operator/agent uses these tags).
ND_TEXT_MARKERS = (
    "K8_FAIL:",
    "K8_SHIP:",
    "K8_V11_SHIP:",
    "REVIEW_V1",
    "AUDIT_V1",
    "FUSION_CLAIM",
    "FUSION_SHIP:",
    "TRIAGE_SHIP:",
    "ERRATUM_V1:",
)

WRAP_TOKENS = {"payload_hash", "provenance", "k8_wrap", "audio_provenance"}

DEFAULT_LEDGER = "town/ledger_v1.ndjson"
K8_FAIL_SCHEMA = "K8_FAIL_V1"
K8_LINT_MODEL_ID = "k8_lint_v1.2"

# ─── Utilities ────────────────────────────────────────────────────────────────

def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_text(p: Path) -> Optional[str]:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def in_nd_scope(path: str) -> bool:
    return any(path.startswith(s) for s in ND_SCOPED_DIRS)


def canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def now_utc_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


# ─── REV-3 reopen: AST-based wrap check ───────────────────────────────────────

class _WrapTokenInScope(ast.NodeVisitor):
    """Visit a single function/module body, skipping nested function/class defs.
    Sets self.found if a wrap token appears as a Name id, Attribute attr, or
    Assign target — never as a string-literal Constant value."""
    def __init__(self):
        self.found = False
    def visit_FunctionDef(self, node): pass        # skip nested
    def visit_AsyncFunctionDef(self, node): pass   # skip nested
    def visit_ClassDef(self, node): pass           # skip nested
    def visit_Name(self, node):
        if node.id in WRAP_TOKENS:
            self.found = True
            return
        self.generic_visit(node)
    def visit_Attribute(self, node):
        if node.attr in WRAP_TOKENS:
            self.found = True
            return
        self.generic_visit(node)


def _scope_has_wrap(scope) -> bool:
    """True if the scope's *direct* body (excluding nested function bodies)
    contains a wrap-token identifier/attribute (not a string literal)."""
    body = getattr(scope, "body", [])
    for stmt in body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        v = _WrapTokenInScope()
        v.visit(stmt)
        if v.found:
            return True
    return False


def _build_parents(tree: ast.AST) -> Dict[ast.AST, ast.AST]:
    parents: Dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def _enclosing_scope(node: ast.AST, parents: Dict[ast.AST, ast.AST], tree: ast.AST) -> ast.AST:
    cur = parents.get(node)
    while cur is not None and not isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
        cur = parents.get(cur)
    return cur or tree


def _find_nd_call_sites(tree: ast.AST) -> List[Tuple[ast.AST, str]]:
    """Find Call/Attribute nodes whose unparsed source contains an ND surface needle.
    Returns list of (node, matched_needle)."""
    surfaces_flat = [n for needles in ND_SURFACES.values() for n in needles]
    sites: List[Tuple[ast.AST, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Call, ast.Attribute)):
            continue
        try:
            src = ast.unparse(node)
        except Exception:
            continue
        for needle in surfaces_flat:
            if needle in src:
                sites.append((node, needle))
                break
    return sites


def ndwrap_check_python(src: str) -> Tuple[bool, str]:
    """Returns (has_violation, detail). Bites only Python source via AST."""
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return (False, f"parse_skipped:{e}")  # don't block on syntactically broken files
    parents = _build_parents(tree)
    sites = _find_nd_call_sites(tree)
    if not sites:
        return (False, "no_nd_call_sites")
    violations: List[str] = []
    seen_scopes: set = set()
    for node, needle in sites:
        scope = _enclosing_scope(node, parents, tree)
        key = (id(scope), needle)
        if key in seen_scopes:
            continue
        seen_scopes.add(key)
        if not _scope_has_wrap(scope):
            scope_name = getattr(scope, "name", "module")
            violations.append(f"scope={scope_name} invokes {needle}")
    if violations:
        return (True, "; ".join(violations[:5]))
    return (False, "all_call_sites_wrapped")


# ─── Payload shape detection (REV-2 + REV-2.1) ────────────────────────────────

def payload_is_nd(payload: Any, op: Optional[str]) -> Tuple[bool, str]:
    if not isinstance(payload, dict):
        return (False, "")
    schema = payload.get("schema", "")
    if isinstance(schema, str):
        for pref in ND_PAYLOAD_SCHEMA_PREFIXES:
            if schema.startswith(pref):
                return (True, f"schema={schema}")
    # REV-2 reopen: text-marker prefix on user_msg/turn payloads
    if op in ("user_msg", "turn"):
        text = payload.get("text") or payload.get("her_text") or ""
        if isinstance(text, str):
            stripped = text.lstrip()
            for marker in ND_TEXT_MARKERS:
                if stripped.startswith(marker):
                    return (True, f"text_marker={marker}")
    # REV-2.1: field-keys only count when op is in explicit subset
    if op in ND_FIELD_KEY_OPS:
        hits = ND_PAYLOAD_FIELD_KEYS & set(payload.keys())
        if hits:
            return (True, f"fields={','.join(sorted(hits))}")
    return (False, "")


# ─── REV-6 reopen: change-detection without -C, with toplevel guard ───────────

def _sh_lines(cmd: List[str], cwd: Optional[Path] = None) -> List[str]:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=str(cwd) if cwd else None)
        if out.returncode != 0:
            return []
        return [l for l in out.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def _git_toplevel(cwd: Path) -> Optional[Path]:
    out = _sh_lines(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    if not out:
        return None
    try:
        return Path(out[0]).resolve()
    except Exception:
        return None


def list_changed_files(mode: str, explicit: List[str], root: Path) -> Tuple[List[str], str]:
    if mode == "manifest_list":
        return ([f.strip() for f in explicit if f.strip()], "manifest_list")
    if mode == "all_nd":
        out = []
        for d in ND_SCOPED_DIRS:
            base = root / d
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if p.is_file():
                    out.append(str(p.relative_to(root)))
        return (out, "all_nd")
    # git_diff (default) — no -C, mirrors K-τ. Run from repo root cwd.
    for cmd in (
        ["git", "diff", "--name-only", "HEAD~1..HEAD"],
        ["git", "diff", "--name-only"],
    ):
        files = _sh_lines(cmd, cwd=root)
        if files:
            return (files, "git_diff")
    return ([], "git_diff_empty")


# ─── Three Invariant Checks ───────────────────────────────────────────────────

def mu_ndwrap(root: Path, changed: List[str]) -> Tuple[float, List[str], str]:
    offenders: List[str] = []
    for f in changed:
        if not in_nd_scope(f):
            continue
        if not f.endswith(".py"):
            continue  # v1.2 narrows to Python; JS/TS support deferred
        p = root / f
        if not p.exists() or p.is_dir():
            continue
        src = read_text(p) or ""
        has_v, detail = ndwrap_check_python(src)
        if has_v:
            offenders.append(f"{f} :: {detail}")
    if offenders:
        files = [o.split(" :: ")[0] for o in offenders]
        return (-1.0, files, "ND surfaces invoked without wrap (AST scope check) | " + "; ".join(offenders[:5]))
    return (+1.0, [], "ok")


def mu_ndartifact(root: Path, changed: List[str]) -> Tuple[float, List[str], str]:
    offenders: List[str] = []
    targets: List[Path] = []
    for f in changed:
        p = root / f
        if p.is_file() and p.suffix.lower() in ND_BINARY_EXTS:
            targets.append(p)
    if not targets:
        for d in ND_BINARY_DIRS:
            base = root / d
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if p.is_file() and p.suffix.lower() in ND_BINARY_EXTS:
                    targets.append(p)
    text_targets: List[Path] = []
    for d in ND_TEXT_DIRS:
        base = root / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if any(p.name.endswith(suf) for suf in ND_TEXT_PROVENANCE_SUFFIXES):
                continue
            if p.suffix.lower() in ND_TEXT_EXTS:
                text_targets.append(p)
    targets.extend(text_targets)
    for p in targets:
        candidates = [
            p.with_suffix(p.suffix + ".provenance.json"),
            p.with_suffix(p.suffix + ".provenance.md"),
            p.with_name(p.stem + ".provenance.json"),
            p.with_name(p.stem + ".provenance.md"),
        ]
        if not any(c.exists() for c in candidates):
            offenders.append(str(p.relative_to(root)))
    if offenders:
        return (-1.0, offenders, "ND artifact missing .provenance.{json,md} sidecar | " + "; ".join(offenders[:5]))
    return (+1.0, [], "ok")


def mu_ndledger(root: Path, ledger_path: str, allow_absent: bool) -> Tuple[float, List[str], str]:
    p = root / ledger_path
    if not p.exists():
        if allow_absent:
            return (+1.0, [], f"no ledger at {ledger_path} (--allow-absent-ledger)")
        return (-1.0, [ledger_path], f"ledger absent at {ledger_path} — fail-closed per NO RECEIPT = NO CLAIM (use --allow-absent-ledger to waive)")
    offenders: List[str] = []
    in_scope = 0
    try:
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue
            op = entry.get("op") or entry.get("type")
            payload = entry.get("payload")
            op_in = op in NON_DET_OPS
            shape_in, shape_reason = payload_is_nd(payload, op)
            if not (op_in or shape_in):
                continue
            in_scope += 1
            seq = entry.get("seq", "?")
            top_hash = entry.get("payload_hash")
            inner_hash = payload.get("payload_hash") if isinstance(payload, dict) else None
            present_hash = top_hash or inner_hash
            if not present_hash:
                offenders.append(f"seq={seq} op={op} reason={shape_reason or 'op_in_set'} missing=payload_hash")
                continue
            try:
                expected = sha256_hex(canon(payload))
                if present_hash != expected:
                    offenders.append(f"seq={seq} op={op} hash_mismatch (got={present_hash[:12]} expected={expected[:12]})")
                    continue
            except Exception as e:
                offenders.append(f"seq={seq} op={op} hash_recompute_error={e}")
                continue
            # model_id check (informational): only required for non-helen-say ops
            if isinstance(payload, dict) and op not in ("user_msg", "turn", "seal"):
                if "model_id" not in payload:
                    offenders.append(f"seq={seq} op={op} missing=model_id")
    except Exception as e:
        return (-1.0, [ledger_path], f"ledger read error: {e}")
    if offenders:
        return (-1.0, [ledger_path], f"ND ledger entries failed integrity ({in_scope} in scope) | " + "; ".join(offenders[:5]))
    return (+1.0, [], f"ok ({in_scope} ND entries verified)")


# ─── REV-7 reopen: direct ledger append, kernel-independent ───────────────────

def _tail_prev_state(ledger_path: Path) -> Tuple[int, str]:
    """Mirror tools/helen_say.py:tail_prev_state — last (seq, cum_hash)."""
    if not ledger_path.exists() or ledger_path.stat().st_size == 0:
        return (0, "0" * 64)
    last_seq = 0
    last_cum = "0" * 64
    with ledger_path.open("rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - 65536), os.SEEK_SET)
        chunk = f.read().decode("utf-8", "replace").strip().splitlines()
    for line in reversed(chunk):
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
            if isinstance(ev, dict) and "seq" in ev and "cum_hash" in ev:
                last_seq = int(ev["seq"])
                last_cum = str(ev["cum_hash"])
                break
        except Exception:
            continue
    return (last_seq, last_cum)


def append_k8_fail_receipt_direct(root: Path, ledger_path: Path, summary: Dict[str, Any]) -> Tuple[bool, str]:
    """Append type='k8_fail' directly to the ledger. Bypasses helen_say so the
    receipt lands even when the kernel is down. Returns (success, detail)."""
    try:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        last_seq, prev_cum = _tail_prev_state(ledger_path)
        seq = last_seq + 1 if ledger_path.exists() and ledger_path.stat().st_size > 0 else 0
        # Payload self-references the summary by SHA, and includes model_id for K8 self-witnessing
        payload: Dict[str, Any] = {
            "schema": K8_FAIL_SCHEMA,
            "model_id": K8_LINT_MODEL_ID,
            "run_id": summary.get("run_id"),
            "k8": summary.get("k8"),
            "verdict": summary.get("verdict"),
            "witness": summary.get("witness"),
            "summary_sha": sha256_hex(canon(summary)),
        }
        meta = {"timestamp_utc": now_utc_iso(), "source": "helen_k8_lint", "kernel_required": False}
        payload_hash = sha256_hex(canon(payload))
        cum_hash = sha256_hex(bytes.fromhex(prev_cum) + bytes.fromhex(payload_hash))
        entry = {
            "type": "k8_fail",
            "seq": seq,
            "payload": payload,
            "meta": meta,
            "payload_hash": payload_hash,
            "prev_cum_hash": prev_cum,
            "cum_hash": cum_hash,
        }
        with ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=False, ensure_ascii=False) + "\n")
        return (True, f"appended seq={seq} payload_hash={payload_hash[:16]} cum={cum_hash[:16]}")
    except Exception as e:
        return (False, f"append_failed: {e}")


# ─── IO ───────────────────────────────────────────────────────────────────────

def write_ndjson(path: Path, obj: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def write_json(path: Path, obj: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="HELEN K8 — Non-Determinism Boundary linter (v1.2)")
    ap.add_argument("--run-id", default="RUN-K8-LOCAL")
    ap.add_argument("--mode", choices=["git_diff", "manifest_list", "all_nd"], default="git_diff")
    ap.add_argument("--changed", nargs="*", default=[])
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--out-dir", default="artifacts")
    ap.add_argument("--allow-absent-ledger", action="store_true",
                    help="Waive REV-5 fail-closed on missing ledger (CI bootstrap only)")
    ap.add_argument("--allow-nested-repo", action="store_true",
                    help="Allow REV-6 git toplevel != repo_root() (subtree workflows)")
    ap.add_argument("--no-fail-receipt", action="store_true",
                    help="Skip REV-7 ledger append on FAIL (testing only)")
    args = ap.parse_args()

    root = repo_root()
    out = root / args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    # REV-6 reopen: toplevel guard
    nested_repo_warning: Optional[str] = None
    toplevel = _git_toplevel(root)
    if toplevel is not None and toplevel != root:
        msg = f"git toplevel ({toplevel}) != repo_root ({root})"
        if not args.allow_nested_repo and args.mode == "git_diff":
            print(f"K8 ABORT  {msg} — pass --allow-nested-repo to proceed", file=sys.stderr)
            sys.exit(2)
        nested_repo_warning = msg

    changed, mode_used = list_changed_files(args.mode, args.changed, root)

    manifest = {
        "schema": "K8_MANIFEST_V1",
        "run_id": args.run_id,
        "version": "v1.2",
        "invariants": INVARIANTS,
        "nd_surfaces": ND_SURFACES,
        "nd_scoped_dirs": ND_SCOPED_DIRS,
        "nd_binary_exts": sorted(ND_BINARY_EXTS),
        "nd_binary_dirs": ND_BINARY_DIRS,
        "nd_text_dirs": ND_TEXT_DIRS,
        "nd_text_exts": sorted(ND_TEXT_EXTS),
        "non_det_ops": sorted(NON_DET_OPS),
        "nd_field_key_ops": sorted(ND_FIELD_KEY_OPS),
        "nd_payload_schema_prefixes": list(ND_PAYLOAD_SCHEMA_PREFIXES),
        "nd_payload_field_keys": sorted(ND_PAYLOAD_FIELD_KEYS),
        "nd_text_markers": list(ND_TEXT_MARKERS),
        "wrap_tokens": sorted(WRAP_TOKENS),
        "ledger_path": args.ledger,
        "mode_requested": args.mode,
        "mode_used": mode_used,
        "changed_count": len(changed),
        "allow_absent_ledger": args.allow_absent_ledger,
        "allow_nested_repo": args.allow_nested_repo,
        "nested_repo_warning": nested_repo_warning,
        "k8_fail_schema": K8_FAIL_SCHEMA,
        "k8_lint_model_id": K8_LINT_MODEL_ID,
    }
    write_json(out / "k8_manifest.json", manifest)

    results: List[Tuple[str, float, List[str], str]] = []
    mu, files, detail = mu_ndwrap(root, changed)
    results.append(("mu_NDWRAP", mu, files, detail))
    mu, files, detail = mu_ndartifact(root, changed)
    results.append(("mu_NDARTIFACT", mu, files, detail))
    mu, files, detail = mu_ndledger(root, args.ledger, args.allow_absent_ledger)
    results.append(("mu_NDLEDGER", mu, files, detail))

    trace_path = out / "k8_trace.ndjson"
    if trace_path.exists():
        trace_path.unlink()
    for name, mu, files, detail in results:
        write_ndjson(trace_path, {
            "schema": "K8_TRACE_V1",
            "run_id": args.run_id,
            "invariant": name,
            "mu": mu,
            "files": files,
            "detail": detail,
        })

    k8 = min(r[1] for r in results)
    witness = min(results, key=lambda r: r[1])
    summary = {
        "schema": "K8_SUMMARY_V1",
        "run_id": args.run_id,
        "k8": k8,
        "verdict": "PASS" if k8 > 0 else "FAIL",
        "witness": {
            "invariant": witness[0],
            "mu": witness[1],
            "files": witness[2],
            "detail": witness[3],
        },
        "invariants": [
            {"name": n, "mu": mu, "files": files, "detail": detail}
            for n, mu, files, detail in results
        ],
    }
    summary_path = out / "k8_summary.json"
    write_json(summary_path, summary)

    print(f"K8 {summary['verdict']}  k8={k8:+.3f}  witness={witness[0]}  mode={mode_used}  changed={len(changed)}")
    for n, mu, files, detail in results:
        marker = "PASS" if mu > 0 else "FAIL"
        print(f"  [{marker}] {n:14s} mu={mu:+.2f}  {detail}")

    # REV-7 reopen: append k8_fail directly to ledger (works even with kernel down)
    if k8 <= 0 and not args.no_fail_receipt:
        ok, detail = append_k8_fail_receipt_direct(root, root / args.ledger, summary)
        marker = "OK" if ok else "FAILED"
        print(f"--- k8_fail direct receipt: [{marker}] {detail}")

    sys.exit(0 if k8 > 0 else 1)


if __name__ == "__main__":
    main()
