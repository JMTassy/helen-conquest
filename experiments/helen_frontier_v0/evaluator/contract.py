"""Evaluator contract: adapter -> blind outcomes -> receipt with epistemic partitions.

The evaluator never reads the labelled fixtures. It reads a *_blind.json (given + claim only), asks the adapter for one
strict JSON answer per oracle, parses fail-closed (an unparseable reply is recorded as UNPARSEABLE, never coerced), and
writes outcomes in the same shape G1 produced so HAL's comparison applies unchanged.

Receipt partitions never merge:
  observed      facts measured here (hashes, host, HTTP headers the transport returned, timings, versions)
  asserted      configured values (provider label, model id as configured)
  unverifiable  runtime weight identity; lineage independence from the oracle author
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUTCOMES = ("ADMIT", "HOLD", "REJECT", "NO_TRANSITION")
UNPARSEABLE = "UNPARSEABLE"
ORACLE_AUTHOR_FAMILY = "anthropic/claude"  # the fixtures and their oracles were written by Claude seats


class Adapter(Protocol):
    provider: str
    model: str

    def generate(self, messages: Sequence[Mapping[str, str]], temperature: float = 0.0) -> tuple[str, dict[str, Any]]:
        """Return (text, observed) where observed holds transport facts (host, status, selected headers, latency)."""


@dataclass
class NullAdapter:
    """Plumbing only. Returns an empty reply so every oracle is UNPARSEABLE. Never a result."""
    provider: str = "null"
    model: str = "none"

    def generate(self, messages, temperature: float = 0.0):
        return "", {"host": None, "status": None, "latency_ms": 0, "note": "null adapter: plumbing test only"}


@dataclass
class CallableAdapter:
    """Wrap any function text->text (used by tests with scripted replies)."""
    fn: Callable[[str], str]
    provider: str = "callable"
    model: str = "scripted"

    def generate(self, messages, temperature: float = 0.0):
        t0 = time.perf_counter()
        out = self.fn(messages[-1]["content"])
        return out, {"host": None, "status": None, "latency_ms": round(1000 * (time.perf_counter() - t0), 1)}


@dataclass
class ResponsesAPIAdapter:
    """OpenAI-compatible Responses API over urllib. Deployment preconditions: OPENAI_API_KEY in the environment and the
    base URL's host allowed by the network policy. Nothing else is assumed."""
    provider: str = "openai-compatible"
    model: str = field(default_factory=lambda: os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"))
    base_url: str = field(default_factory=lambda: os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    api_key_env: str = "OPENAI_API_KEY"
    timeout_s: int = 120
    OBSERVED_HEADERS = ("openai-model", "x-request-id", "openai-version", "openai-processing-ms", "content-type")

    def preconditions(self) -> dict[str, Any]:
        return {"api_key_present": bool(os.environ.get(self.api_key_env)),
                "host": urllib.parse.urlparse(self.base_url).hostname}

    def generate(self, messages, temperature: float = 0.0):
        key = os.environ.get(self.api_key_env)
        if not key:
            raise RuntimeError(f"precondition failed: {self.api_key_env} not set")
        url = self.base_url.rstrip("/") + "/responses"
        payload = {"model": self.model, "input": list(messages), "temperature": temperature}
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                hdrs = {h: resp.headers.get(h) for h in self.OBSERVED_HEADERS if resp.headers.get(h)}
                status = resp.status
        except urllib.error.HTTPError as exc:
            return "", {"host": urllib.parse.urlparse(url).hostname, "status": exc.code,
                        "latency_ms": round(1000 * (time.perf_counter() - t0), 1), "error": str(exc)[:200]}
        text = _extract_text(body)
        return text, {"host": urllib.parse.urlparse(url).hostname, "status": status, "headers": hdrs,
                      "latency_ms": round(1000 * (time.perf_counter() - t0), 1),
                      "model_in_response_body": body.get("model")}


def _extract_text(body: Mapping[str, Any]) -> str:
    if isinstance(body.get("output_text"), str):
        return body["output_text"]
    parts = []
    for item in body.get("output", []) or []:
        for c in item.get("content", []) or []:
            if c.get("type") in ("output_text", "text") and isinstance(c.get("text"), str):
                parts.append(c["text"])
    return "\n".join(parts)


# ----------------------------------------------------------------------------- prompt + parse
SYSTEM = (
    "You are a blind evaluator. You will receive laws, an outcome vocabulary with semantics, and ONE fixture with a "
    "'given' and a 'claim_under_test'. Decide one outcome for the claim. Reply with ONLY a JSON object: "
    '{"outcome": <one of the vocabulary>, "state_transition": <true only if outcome is ADMIT>, '
    '"reason": <1-2 sentences>, "laws_applied": [<law ids>]}. No prose outside the JSON.'
)


def build_messages(blind: Mapping[str, Any], fixture: Mapping[str, Any], variant: Mapping[str, Any] | None) -> list[dict[str, str]]:
    item = {"id": (variant or fixture)["id"], "domain": fixture.get("domain"),
            "given": (variant or fixture)["given"], "claim_under_test": (variant or fixture)["claim_under_test"]}
    user = json.dumps({"outcome_vocabulary": blind["outcome_vocabulary"], "outcome_semantics": blind["outcome_semantics"],
                       "laws": blind["laws"], "fixture": item}, ensure_ascii=False, indent=1)
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


_JSON_RE = re.compile(r"\{.*\}", re.S)


def parse_reply(text: str) -> dict[str, Any]:
    """Fail-closed. Anything not a strict, in-vocabulary answer becomes UNPARSEABLE with the raw text kept."""
    m = _JSON_RE.search(text or "")
    if not m:
        return {"outcome": UNPARSEABLE, "state_transition": False, "reason": "", "laws_applied": [], "raw": (text or "")[:500]}
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"outcome": UNPARSEABLE, "state_transition": False, "reason": "", "laws_applied": [], "raw": text[:500]}
    out = d.get("outcome")
    if out not in OUTCOMES or type(d.get("state_transition")) is not bool:
        return {"outcome": UNPARSEABLE, "state_transition": False, "reason": "", "laws_applied": [], "raw": text[:500]}
    if d["state_transition"] and out != "ADMIT":
        return {"outcome": UNPARSEABLE, "state_transition": False, "reason": "state_transition true without ADMIT", "laws_applied": [], "raw": text[:500]}
    return {"outcome": out, "state_transition": d["state_transition"], "reason": str(d.get("reason", ""))[:600],
            "laws_applied": [str(x) for x in (d.get("laws_applied") or [])][:8]}


# ----------------------------------------------------------------------------- run
def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_blind_evaluation(adapter: Adapter, blind_path: Path, out_dir: Path, seat: str = "EVALUATOR_SEAT",
                         temperature: float = 0.0) -> tuple[Path, Path]:
    assert "blind" in blind_path.name, "evaluator accepts only a *_blind.json input"
    blind = json.loads(blind_path.read_text(encoding="utf-8"))
    assert "expected" not in json.dumps(blind["fixtures"]), "input is not blind"
    out_dir.mkdir(parents=True, exist_ok=True)
    outcomes, transport = [], []
    t0 = time.perf_counter()
    for f in blind["fixtures"]:
        for v in (f.get("variants") or [None]):
            msgs = build_messages(blind, f, v)
            text, obs = adapter.generate(msgs, temperature=temperature)
            parsed = parse_reply(text)
            parsed["id"] = (v or f)["id"]
            outcomes.append(parsed)
            transport.append({"id": parsed["id"], **obs})
    wall = round(time.perf_counter() - t0, 2)
    git_head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    n_unp = sum(1 for o in outcomes if o["outcome"] == UNPARSEABLE)
    hosts = sorted({t.get("host") for t in transport if t.get("host")})
    outcomes_doc = {"schema": "BLIND_OUTCOMES_V0", "authority": False, "evaluator": seat,
                    "model": f"{adapter.provider}:{adapter.model} (asserted; see receipt)",
                    "input": str(blind_path.relative_to(REPO)) if blind_path.is_relative_to(REPO) else str(blind_path),
                    "outcomes": [{k: o[k] for k in ("id", "outcome", "state_transition", "reason", "laws_applied")} for o in outcomes]}
    receipt = {
        "schema": "EVALUATOR_RECEIPT_V0", "authority": False, "sovereign": False, "ledger_effect": "none",
        "seat": seat, "binding": {"provider": adapter.provider},
        "asserted": {"model_configured": adapter.model, "temperature": temperature},
        "observed": {"blind_input_sha256": _sha(blind_path), "oracles_evaluated": len(outcomes), "unparseable": n_unp,
                     "hosts_contacted": hosts, "transport": transport, "wall_seconds": wall,
                     "python_version": platform.python_version(), "git_head": git_head,
                     "outcomes_sha256": hashlib.sha256(json.dumps(outcomes_doc["outcomes"], sort_keys=True).encode()).hexdigest()},
        "unverifiable": {"runtime_weight_identity": "UNVERIFIED — the host does not attest which weights executed",
                         "lineage_independence_from_oracle_author": "UNRESOLVED"},
        "route_diversity": {"oracle_author_family": ORACLE_AUTHOR_FAMILY,
                            "evaluator_provider": adapter.provider,
                            "provider_differs": adapter.provider not in ("null", "callable") and not adapter.provider.startswith("anthropic"),
                            "meaning": "a different provider is a different measurement path; it is not an independent witness until lineage is resolved"},
        "meaning": "outcomes are the evaluator's declarations; their comparison to oracles happens elsewhere, after the fact",
    }
    po = out_dir / "blind_outcomes.json"; pr = out_dir / "EVALUATOR_RECEIPT_V0.json"
    po.write_text(json.dumps(outcomes_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    pr.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return po, pr
