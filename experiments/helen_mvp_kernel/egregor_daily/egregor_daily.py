#!/usr/bin/env python3
"""EGREGOR DAILY: one SUPERTEAM cycle per day across your lanes. NON_SOVEREIGN · authority=false · ledger_effect=none.

    python egregor_daily.py --config egregor.config.yaml           # run today's cycle
    python egregor_daily.py --config egregor.config.yaml --check   # check lanes and inputs, no model calls

Cycle (oracle_town/skills/ops/helen_superteam/SUPERTEAM_MVP_V0.md):
    collect (repo activity, inbox folder, Gmail label)
    -> GOBLIN  DreamSeeds          (sees raw inputs)
    -> HER     InsightCandidates   (sees stripped DreamSeeds only)
    -> HAL     ClaimCandidates     (sees stripped InsightCandidates only)
    -> MAYOR   ValidationReceiptCandidate (sees stripped ClaimCandidates only, no lineage)
    -> BRIEF.md + RECEIPT.json for JM. Nothing is admitted; no ledger is touched.

Lanes return content only. This script sets ids, lineage, source_refs, claim_status, authority and actor,
validates every artifact against schemas/helen_superteam/, and records in the receipt exactly what each lane saw.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
import urllib.request

import yaml

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
PROMPTS = HERE / "prompts"
SUPERTEAM = REPO / "oracle_town" / "skills" / "ops" / "helen_superteam" / "superteam_pipeline.py"
SCHEMAS = REPO / "schemas" / "helen_superteam"
TEXT_SUFFIXES = {".md", ".txt", ".json", ".ndjson", ".csv", ".html"}
GATE_FOR_VERDICT = {"YES": "ADMISSION_REVIEW", "NO": "REJECT_LOG", "HOLD": "HOLD_QUEUE"}


def _load_superteam():
    spec = importlib.util.spec_from_file_location("superteam_pipeline", SUPERTEAM)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ST = _load_superteam()


def now_iso():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def expand(p):
    return pathlib.Path(os.path.expanduser(str(p)))


# ---------------------------------------------------------------- validation

def validate(artifact, schema_name):
    """Full JSON-schema validation when jsonschema is installed, else the superteam minimal check."""
    try:
        import jsonschema
    except ImportError:
        return ST._validate(artifact, schema_name)
    schema = json.loads((SCHEMAS / f"{schema_name}.json").read_text())
    return [e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(artifact)] \
        if hasattr(jsonschema, "Draft202012Validator") else [e.message for e in jsonschema.Draft7Validator(schema).iter_errors(artifact)]


def fill(template, **values):
    """Replace only the named {placeholders}: prompts contain literal JSON braces, inputs may contain any text."""
    for k, v in values.items():
        template = template.replace("{" + k + "}", str(v))
    return template


def extract_json(text):
    """First JSON object in a model's answer (models wrap JSON in prose or fences)."""
    dec = json.JSONDecoder()
    for i, ch in enumerate(text or ""):
        if ch == "{":
            try:
                obj, _ = dec.raw_decode(text[i:])
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue
    raise ValueError("no JSON object in the answer")


# ---------------------------------------------------------------- lanes

class LaneError(Exception):
    pass


def call_lane(name, cfg, prompt, timeout):
    """Return (answer_text, meta). meta never contains the answer itself."""
    lane = cfg["lanes"][name]
    t0 = time.monotonic()
    meta = {"lane": name, "kind": lane["kind"], "prompt_sha256": sha(prompt), "prompt_chars": len(prompt)}
    try:
        if lane["kind"] == "ollama":
            body = json.dumps({"model": lane["model"], "prompt": prompt, "stream": False, "format": "json",
                               "options": {"temperature": lane.get("temperature", 0.7)}}).encode()
            req = urllib.request.Request(cfg.get("ollama_url", "http://localhost:11434") + "/api/generate", data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = json.loads(r.read())
            meta.update(model=out.get("model", lane["model"]), eval_count=out.get("eval_count"))
            answer = out.get("response", "")
        elif lane["kind"] == "cli":
            cmd = list(lane["cmd"])
            p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout,
                               encoding="utf-8", errors="replace")
            meta.update(cmd=" ".join(cmd), exit_code=p.returncode, stderr_tail=p.stderr[-400:])
            if p.returncode != 0:
                raise LaneError(f"exit {p.returncode}: {p.stderr.strip()[-300:]}")
            answer = p.stdout
            if lane.get("output") == "claude_json":
                j = extract_json(p.stdout)
                if j.get("is_error"):
                    raise LaneError(f"claude error: {str(j.get('result'))[:300]}")
                answer = j.get("result", "")
                meta.update({k: j.get(k) for k in ("num_turns", "duration_ms", "total_cost_usd", "session_id")})
                if j.get("modelUsage"):
                    meta["models_reported"] = sorted(j["modelUsage"].keys())
                if j.get("permission_denials"):
                    meta["permission_denials"] = len(j["permission_denials"])
        elif lane["kind"] == "fixture":  # tests: answers come from a Python callable
            answer = lane["fn"](prompt)
        else:
            raise LaneError(f"unknown lane kind {lane['kind']}")
    except (OSError, subprocess.TimeoutExpired, ValueError) as e:
        raise LaneError(f"{type(e).__name__}: {e}") from None
    finally:
        meta["seconds"] = round(time.monotonic() - t0, 1)
    meta["answer_sha256"] = sha(answer or "")
    return answer, meta


# ---------------------------------------------------------------- collectors

def collect_repo(c, since):
    path = expand(c["path"])
    if not (path / ".git").exists():
        return [], {"status": "failed", "detail": f"not a git repository: {path}"}
    if c.get("fetch"):
        subprocess.run(["git", "-C", str(path), "fetch", "--quiet", "--all"], capture_output=True, timeout=120)
    p = subprocess.run(["git", "-C", str(path), "log", "--all", f"--since={since}", "--no-merges",
                        "--format=%H%x1f%ad%x1f%s%x1f%b%x1e", "--date=iso-strict", "--stat=120"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        return [], {"status": "failed", "detail": p.stderr.strip()[-200:]}
    commits = [c for c in p.stdout.split("\x1e") if c.strip()]
    if not commits:
        return [], {"status": "ok", "items": 0, "detail": "no commits in window"}
    text = "\n\n".join(" | ".join(x.strip() for x in c.split("\x1f")) for c in commits)
    head = commits[0].strip().split("\x1f")[0][:12]
    return [{"ref": f"git:{path.name}@{head}", "type": "other", "text": f"{len(commits)} commits since {since}:\n{text}"}], \
        {"status": "ok", "items": 1, "detail": f"{len(commits)} commits"}


def collect_inbox(c, today, dry=False):
    path = expand(c["path"])
    if not path.exists():
        return [], {"status": "failed", "detail": f"inbox folder missing: {path}"}
    items, skipped = [], []
    for f in sorted(p for p in path.iterdir() if p.is_file() and not p.name.startswith(".")):
        if f.suffix.lower() in TEXT_SUFFIXES:
            text = f.read_text(encoding="utf-8", errors="replace")
        elif f.suffix.lower() == ".pdf":
            try:
                from pypdf import PdfReader
                text = "\n".join((pg.extract_text() or "") for pg in PdfReader(str(f)).pages[:30])
            except Exception as e:  # pypdf missing or unreadable file
                skipped.append(f"{f.name}: {type(e).__name__}")
                continue
        else:
            skipped.append(f"{f.name}: unsupported type")
            continue
        items.append({"ref": f"inbox:{f.name}", "type": "pdf" if f.suffix.lower() == ".pdf" else "fragment",
                      "text": text, "_file": f})
    cov = {"status": "ok", "items": len(items)}
    if skipped:
        cov["skipped"] = skipped
    return items, cov


def archive_inbox(items, inbox_path, today):
    done = expand(inbox_path) / "done" / today
    for it in items:
        f = it.get("_file")
        if f and f.exists():
            done.mkdir(parents=True, exist_ok=True)
            shutil.move(str(f), done / f.name)


def collect_gmail(c, cfg, since, timeout):
    prompt = fill((PROMPTS / "gmail_collector.md").read_text(), label=c["label"], since=since, max_threads=c.get("max_threads", 5))
    lane = dict(cfg["lanes"][c.get("lane", "hal_collector")])
    lane["cmd"] = list(lane["cmd"]) + ["--allowedTools", ",".join(c["allowed_tools"])]
    cfg2 = {**cfg, "lanes": {**cfg["lanes"], "_gmail": lane}}
    try:
        answer, meta = call_lane("_gmail", cfg2, prompt, timeout)
        data = extract_json(answer)
    except (LaneError, ValueError) as e:
        return [], {"status": "failed", "detail": str(e)[:300]}, None
    items = [{"ref": f"gmail:{t.get('thread_id', '?')}", "type": "fragment",
              "text": f"Subject: {t.get('subject', '')}\nFrom domain: {t.get('from_domain', '')}\nDate: {t.get('date', '')}\n\n{t.get('text', '')}"}
             for t in (data.get("items") or [])[: c.get("max_threads", 5)]]
    return items, {"status": "ok", "items": len(items)}, meta


# ---------------------------------------------------------------- stages

def run_goblin(cfg, raws, out, receipt):
    cad = cfg["cadence"]
    template = (PROMPTS / "goblin.md").read_text()
    seeds = []
    for raw in raws:
        if len(seeds) >= cad["seeds_per_run"]:
            break
        text = raw["text"][: cfg.get("max_input_chars", 6000)]
        prompt = fill(template, max_seeds=cad["seeds_per_input"], input_ref=raw["ref"], input_text=text)
        rec = {"stage": "GOBLIN", "input_ref": raw["ref"], "saw": [raw["ref"]]}
        try:
            answer, meta = call_lane(cfg["roles"]["GOBLIN"], cfg, prompt, cfg["timeout_seconds"])
            rec.update(meta)
            proposed = (extract_json(answer).get("seeds") or [])[: cad["seeds_per_input"]]
        except (LaneError, ValueError) as e:
            rec["error"] = str(e)[:300]
            receipt["calls"].append(rec)
            continue
        rec["kept"], rec["rejected"] = [], []
        for s in proposed:
            content = {k: s.get(k) for k in ("raw_fragments", "motifs", "wild_connections", "why_it_feels_interesting", "input_type")}
            art = {"seed_id": ST._make_id("SEED", json.dumps(content, sort_keys=True) + raw["ref"]), "source_refs": [raw["ref"]],
                   **{k: v for k, v in content.items() if v is not None},
                   "claim_status": "NO_CLAIM", "authority": False, "actor": "GOBLIN", "created_at": now_iso()}
            if art.get("input_type") not in ("pdf", "tweet", "article", "noise", "failure", "fragment", "dream", "json", "ndjson", "other"):
                art["input_type"] = raw["type"]
            errs = validate(art, "dream_seed_v0")
            (rec["rejected"].append({"errors": errs[:3]}) if errs else (rec["kept"].append(art["seed_id"]), seeds.append(art)))
        receipt["calls"].append(rec)
    for s in seeds[: cad["seeds_per_run"]]:
        ST._write_artifact(out / "compost", s["seed_id"], s)
    return seeds[: cad["seeds_per_run"]]


def run_her(cfg, seeds, out, receipt):
    if not seeds:
        return []
    visible = [ST._strip_for_her(s) for s in seeds]
    prompt = fill((PROMPTS / "her.md").read_text(), max_insights=cfg["cadence"]["insights_max"],
                                                     seeds_json=json.dumps(visible, ensure_ascii=False, indent=1))
    by_id = {s["seed_id"]: s for s in seeds}
    return _stage(cfg, "HER", prompt, [s["seed_id"] for s in seeds], "insights", cfg["cadence"]["insights_max"], receipt,
                  lambda x: _make_insight(x, by_id), "insight_candidate_v0", out / "insights", "insight_id")


def _make_insight(x, by_id):
    ids = [i for i in (x.get("derived_from_seed_ids") or []) if i in by_id]
    if not ids:
        return None, "no valid derived_from_seed_ids"
    refs = sorted({r for i in ids for r in by_id[i]["source_refs"]})
    content = {k: x.get(k, "") for k in ("insight_sentence", "resonance", "possible_use", "uncertainty", "evidence_needed")}
    return {"insight_id": ST._make_id("INS", json.dumps(content, sort_keys=True)), "derived_from_seed_ids": ids, "source_refs": refs,
            **content, "claim_status": "CANDIDATE", "authority": False, "actor": "HER", "created_at": now_iso()}, None


def run_hal(cfg, insights, out, receipt):
    if not insights:
        return []
    visible = [ST._strip_for_hal(i) for i in insights]
    prompt = fill((PROMPTS / "hal.md").read_text(), max_claims=cfg["cadence"]["claims_max"],
                                                     insights_json=json.dumps(visible, ensure_ascii=False, indent=1))
    by_id = {i["insight_id"]: i for i in insights}
    return _stage(cfg, "HAL", prompt, [i["insight_id"] for i in insights], "claims", cfg["cadence"]["claims_max"], receipt,
                  lambda x: _make_claim(x, by_id), "claim_candidate_v0", out / "claims", "claim_id")


def _make_claim(x, by_id):
    iid = x.get("derived_from_insight_id")
    if iid not in by_id:
        return None, f"unknown derived_from_insight_id {iid}"
    content = {k: x.get(k, "") for k in ("claim_sentence", "claim_type", "evidence_requirement", "test_or_review_path",
                                         "risk_if_wrong", "hal_reason")}
    return {"claim_id": ST._make_id("CLM", json.dumps(content, sort_keys=True)), **content,
            "source_refs": by_id[iid]["source_refs"], "evidence_refs": list(x.get("evidence_refs") or []),
            "derived_from_insight_id": iid, "claim_status": "CLAIM_CANDIDATE", "authority": False, "actor": "HAL",
            "created_at": now_iso()}, None


def run_mayor(cfg, claims, out, receipt):
    if not claims or cfg["cadence"]["validation_per_run"] < 1:
        return []
    visible = [ST._strip_for_mayor(c) for c in claims]
    prompt = fill((PROMPTS / "mayor.md").read_text(), claims_json=json.dumps(visible, ensure_ascii=False, indent=1))
    ids = {c["claim_id"] for c in claims}
    return _stage(cfg, "MAYOR", prompt, sorted(ids), "validation", 1, receipt,
                  lambda x: _make_validation(x, ids), "validation_receipt_candidate_v0", out / "validation", "validation_id")


def _make_validation(x, ids):
    if x.get("claim_id") not in ids:
        return None, f"claim_id {x.get('claim_id')} was not presented"
    verdict = x.get("mayor_verdict")
    if verdict not in GATE_FOR_VERDICT:
        return None, f"invalid verdict {verdict}"
    content = {"claim_id": x["claim_id"], "mayor_verdict": verdict, "evidence_inspected": list(x.get("evidence_inspected") or []),
               "missing_evidence": x.get("missing_evidence", ""), "reason": x.get("reason", ""), "dissent": x.get("dissent", "")}
    return {"validation_id": ST._make_id("VAL", json.dumps(content, sort_keys=True)), **content,
            "next_gate": GATE_FOR_VERDICT[verdict], "claim_status": "VALIDATED_CLAIM_CANDIDATE", "authority": False,
            "ledger_effect": "none", "actor": "MAYOR", "created_at": now_iso()}, None


def _stage(cfg, role, prompt, saw, key, limit, receipt, make, schema, folder, id_field):
    rec = {"stage": role, "saw": saw, "kept": [], "rejected": []}
    try:
        answer, meta = call_lane(cfg["roles"][role], cfg, prompt, cfg["timeout_seconds"])
        rec.update(meta)
        data = extract_json(answer).get(key)
        proposed = [data] if isinstance(data, dict) else (data or [])
    except (LaneError, ValueError) as e:
        rec["error"] = str(e)[:300]
        receipt["calls"].append(rec)
        return []
    kept = []
    for x in proposed[:limit]:
        art, why = make(x if isinstance(x, dict) else {})
        errs = [why] if why else validate(art, schema)
        if errs:
            rec["rejected"].append({"errors": errs[:3]})
            continue
        ST._write_artifact(folder, art[id_field], art)
        kept.append(art)
        rec["kept"].append(art[id_field])
    if len(proposed) > limit:
        rec["over_cadence_dropped"] = len(proposed) - limit
    receipt["calls"].append(rec)
    return kept


# ---------------------------------------------------------------- brief

def brief(day, coverage, seeds, insights, claims, validations, receipt):
    L = [f"# EGREGOR DAILY · {day}", "", "NON_SOVEREIGN · authority=false · ledger_effect=none · "
         "Validated claim ≠ kernel truth. JM chooses; nothing was admitted.", "",
         "## Inputs", *[f"- {k}: {v.get('status')} ({v.get('items', 0)} item(s)) {v.get('detail', '')}" for k, v in coverage.items()], "",
         f"## GOBLIN · {len(seeds)} DreamSeed(s)", *[f"- {s['seed_id']} ({', '.join(s['source_refs'])}): {s.get('why_it_feels_interesting', '')[:160]}" for s in seeds], "",
         f"## HER · {len(insights)} InsightCandidate(s)", *[f"- **{i['insight_id']}** {i['insight_sentence']}  \n  uncertainty: {i['uncertainty']} · evidence needed: {i['evidence_needed']}" for i in insights], "",
         f"## HAL · {len(claims)} ClaimCandidate(s)", *[f"- **{c['claim_id']}** [{c['claim_type']}] {c['claim_sentence']}  \n  test/review: {c['test_or_review_path']} · risk if wrong: {c['risk_if_wrong']}" for c in claims], "",
         "## MAYOR", *([f"- **{v['mayor_verdict']}** on {v['claim_id']} → {v['next_gate']}  \n  reason: {v['reason']}  \n  missing: {v['missing_evidence']}" + (f"  \n  dissent: {v['dissent']}" if v.get('dissent') else "") for v in validations] or ["- no verdict today"]), "",
         "## Lane problems", *([f"- {c['stage']} ({c.get('lane')}): {c['error']}" for c in receipt["calls"] if c.get("error")] or ["- none"]), "",
         "## JM", "- To take a YES further: review it, then use the existing admission path (SUPERTEAM_MVP_V0 §5). This run wrote nothing outside its own folder.", ""]
    return "\n".join(L)


# ---------------------------------------------------------------- main

def load_config(path):
    cfg = yaml.safe_load(pathlib.Path(path).read_text(encoding="utf-8"))
    for k in ("output_root", "roles", "lanes", "cadence"):
        if k not in cfg:
            raise SystemExit(f"config: missing '{k}'")
    cfg.setdefault("timeout_seconds", 600)
    return cfg


def run(cfg, day=None):
    day = day or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    out = expand(cfg["output_root"]) / day
    if (out / "RECEIPT.json").exists():
        raise SystemExit(f"already ran for {day}: {out}")
    out.mkdir(parents=True, exist_ok=True)
    receipt = {"receipt": "EGREGOR_DAILY_RECEIPT_V0", "date": day, "started_at": now_iso(), "authority": False,
               "ledger_effect": "none", "repo_commit": _git_head(), "roles": cfg["roles"],
               "lanes": {k: {kk: vv for kk, vv in v.items() if kk not in ("fn",)} for k, v in cfg["lanes"].items()},
               "prompts_sha256": {p.name: sha(p.read_text()) for p in sorted(PROMPTS.glob("*.md"))},
               "blindness": "each stage prompt is built only from the previous stage's stripped artifacts (superteam _strip_for_*)",
               "calls": [], "coverage": {}}
    inputs = cfg.get("inputs", {})
    since_dt = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=24)
    raws = []
    for name in ("inbox", "gmail", "repo"):
        c = inputs.get(name) or {}
        if not c.get("enabled"):
            receipt["coverage"][name] = {"status": "skipped", "detail": "disabled"}
            continue
        since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=c.get("since_hours", 24))).strftime("%Y-%m-%dT%H:%M:%SZ")
        if name == "inbox":
            items, cov = collect_inbox(c, day)
        elif name == "gmail":
            items, cov, meta = collect_gmail(c, cfg, since, cfg["timeout_seconds"])
            if meta:
                receipt["calls"].append({"stage": "COLLECT_GMAIL", **meta})
        else:
            items, cov = collect_repo(c, since)
        receipt["coverage"][name] = cov
        raws += items
    raws = raws[: cfg["cadence"]["inputs_per_run"]]
    raw_dir = out / "raw"
    raw_dir.mkdir(exist_ok=True)
    for r in raws:
        (raw_dir / (sha(r["ref"])[:12] + ".txt")).write_text(f"REF: {r['ref']}\n\n{r['text']}", encoding="utf-8")
    receipt["inputs"] = [{"ref": r["ref"], "chars": len(r["text"]), "sha256": sha(r["text"])} for r in raws]

    seeds = run_goblin(cfg, raws, out, receipt)
    insights = run_her(cfg, seeds, out, receipt)
    claims = run_hal(cfg, insights, out, receipt)
    validations = run_mayor(cfg, claims, out, receipt)

    if inputs.get("inbox", {}).get("enabled"):
        archive_inbox(raws, inputs["inbox"]["path"], day)
    receipt["counts"] = {"inputs": len(raws), "seeds": len(seeds), "insights": len(insights), "claims": len(claims),
                         "validations": len(validations)}
    receipt["finished_at"] = now_iso()
    (out / "BRIEF.md").write_text(brief(day, receipt["coverage"], seeds, insights, claims, validations, receipt), encoding="utf-8")
    (out / "RECEIPT.json").write_text(json.dumps(receipt, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    return out, receipt


def _git_head():
    p = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True)
    return p.stdout.strip() or None


def check(cfg):
    ok = True
    for role, lane in cfg["roles"].items():
        l = cfg["lanes"][lane]
        if l["kind"] == "ollama":
            try:
                with urllib.request.urlopen(cfg.get("ollama_url", "http://localhost:11434") + "/api/tags", timeout=5) as r:
                    names = {m["name"] for m in json.loads(r.read()).get("models", [])}
                found = l["model"] in names or f"{l['model']}:latest" in names
                print(f"{role:6} {lane}: ollama model {l['model']} {'present' if found else 'MISSING -> ollama pull ' + l['model']}")
                ok &= found
            except OSError as e:
                print(f"{role:6} {lane}: ollama not reachable ({e}) -> start Ollama")
                ok = False
        elif l["kind"] == "cli":
            exe = shutil.which(l["cmd"][0])
            print(f"{role:6} {lane}: {l['cmd'][0]} {'found at ' + exe if exe else 'NOT FOUND'} (login is checked on the first real call)")
            ok &= bool(exe)
    for name, c in (cfg.get("inputs") or {}).items():
        if c.get("enabled") and "path" in c:
            print(f"input  {name}: {expand(c['path'])} {'exists' if expand(c['path']).exists() else 'MISSING'}")
            ok &= expand(c["path"]).exists()
    print("output", expand(cfg["output_root"]))
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(HERE / "egregor.config.yaml"))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--date", help="override the run date (YYYY-MM-DD)")
    args = ap.parse_args()
    cfg = load_config(args.config)
    if args.check:
        sys.exit(0 if check(cfg) else 1)
    out, r = run(cfg, args.date)
    print(f"EGREGOR {r['date']}: {r['counts']} -> {out / 'BRIEF.md'}")
    for c in r["calls"]:
        if c.get("error"):
            print(f"  {c['stage']} ({c.get('lane')}): {c['error']}")


if __name__ == "__main__":
    main()
