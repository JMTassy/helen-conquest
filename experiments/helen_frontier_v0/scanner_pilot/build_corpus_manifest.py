"""Corpus manifest CANDIDATE for the scanner adaptation pilot. Deterministic from declared rules + pinned revision + seed.

Binds nothing: the operator freezes by copying the manifest digest into the protocol. Read-only on sources (git objects at
the pinned revision, never the working tree). Sampling never looks at scanner predictions; packet appearance is recorded
AFTER selection as a covariate. Historical provenance (the exact bytes the scanner once read) is UNVERIFIED per document:
packets carry no source digest, so only today's bytes at the pinned revision are hashed.

Eligibility rules (declared, checkable):
  E1  path matches docs/proposals/*.md and is tracked at the pinned revision
  E2  the path exists on origin/main (nothing authored on the working branch may enter the corpus)
  E3  size between 1 500 and 40 000 bytes at the pinned revision
  E4  exact-content duplicates collapse to one (first path in sorted order kept)
  E5  near-duplicates (char-5-gram Jaccard >= 0.80 on normalised text) collapse to one, same keep rule
Grouping rule (declared): source_group = first two underscore tokens of the basename after stripping version/date suffixes.
Split rule: groups are shuffled with the seed; whole groups are assigned to development until it holds >= 25 documents;
the rest is holdout. No group straddles the split.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = HERE / "corpus_manifest_candidate.json"
N_SELECT, N_DEV = 40, 25
SIZE_MIN, SIZE_MAX = 1_500, 40_000
NEAR_DUP = 0.80
SCANNER = "temple/autoresearch/autoresearch_scanner.py"
OUTBOX = REPO / "temple" / "autoresearch" / "outbox"


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=True).stdout


def shingles(text: str, n: int = 5) -> set[str]:
    t = re.sub(r"\s+", " ", text.lower()).strip()
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


def group_of(path: str) -> str:
    base = Path(path).stem
    base = re.sub(r"(_V\d+(_\d+)*|_v\d+|_\d{4}_\d{2}_\d{2}|_\d{8}|_\d{2}_\d{2}_\d{2})$", "", base)
    toks = [t for t in base.split("_") if t]
    return "_".join(toks[:2]).upper() if toks else base.upper()


def build(revision: str, seed_source: str | None = None) -> dict:
    rev = git("rev-parse", revision).strip()
    main_paths = set(git("ls-tree", "--name-only", "origin/main", "docs/proposals/").split())
    paths = sorted(p for p in git("ls-tree", "--name-only", rev, "docs/proposals/").split() if p.endswith(".md"))
    log = []
    docs = []
    for p in paths:
        if p not in main_paths:
            log.append((p, "E2 not on origin/main")); continue
        blob = git("rev-parse", f"{rev}:{p}").strip()
        data = subprocess.run(["git", "-C", str(REPO), "cat-file", "-p", blob], capture_output=True, check=True).stdout
        if not (SIZE_MIN <= len(data) <= SIZE_MAX):
            log.append((p, f"E3 size {len(data)}")); continue
        docs.append({"path": p, "blob": blob, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                     "text": data.decode("utf-8", errors="replace")})
    seen = {}
    kept = []
    for d in docs:
        if d["sha256"] in seen:
            log.append((d["path"], f"E4 exact duplicate of {seen[d['sha256']]}")); continue
        seen[d["sha256"]] = d["path"]; kept.append(d)
    sh = {d["path"]: shingles(d["text"]) for d in kept}
    eligible = []
    for d in kept:
        dup_of = next((e["path"] for e in eligible if len(sh[d["path"]] & sh[e["path"]]) / max(1, len(sh[d["path"]] | sh[e["path"]])) >= NEAR_DUP), None)
        if dup_of:
            log.append((d["path"], f"E5 near-duplicate of {dup_of}")); continue
        eligible.append(d)
    seed_src = seed_source or rev
    seed = int(hashlib.sha256(seed_src.encode()).hexdigest()[:16], 16)
    rng = random.Random(seed)
    selected = sorted(rng.sample([d["path"] for d in eligible], min(N_SELECT, len(eligible))))
    groups = defaultdict(list)
    for p in selected:
        groups[group_of(p)].append(p)
    order = sorted(groups); rng.shuffle(order)
    dev, hold = [], []
    for g in order:
        (dev if len(dev) < N_DEV else hold).extend(groups[g])
    # covariate, computed AFTER selection
    appear = defaultdict(int)
    for f in sorted(OUTBOX.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        refs = d.get("source_refs") or []
        if isinstance(d.get("target"), str): refs = list(refs) + [d["target"]]
        for r in refs:
            if isinstance(r, str):
                for p in selected:
                    if p in r: appear[p] += 1
    by_path = {d["path"]: d for d in eligible}
    manifest = {
        "schema": "SCANNER_PILOT_CORPUS_MANIFEST_V0",
        "status": "CANDIDATE — not frozen; the operator freezes by recording manifest_sha256 in the protocol",
        "authority": False, "sovereign": False, "ledger_effect": "none",
        "pinned_revision": rev,
        "baseline_scanner_blob": git("rev-parse", f"{rev}:{SCANNER}").strip(),
        "eligibility_rules": ["E1 docs/proposals/*.md tracked at revision", "E2 exists on origin/main",
                              f"E3 {SIZE_MIN} <= bytes <= {SIZE_MAX}", "E4 exact-content dedup",
                              f"E5 near-dup char-5-gram Jaccard >= {NEAR_DUP}"],
        "grouping_rule": "first two underscore tokens of basename after stripping version/date suffixes",
        "split_rule": f"whole groups shuffled by seed; development filled to >= {N_DEV}; rest holdout; no straddling",
        "sampling": {"seed_source": seed_src, "seed": seed, "method": "random.Random(seed).sample over sorted eligible paths",
                     "independent_of_scanner_predictions": True},
        "counts": {"tracked": len(paths), "eligible": len(eligible), "excluded": len(log), "selected": len(selected),
                   "development": len(dev), "holdout": len(hold), "groups": len(groups)},
        "excluded": [{"path": p, "reason": r} for p, r in log],
        "documents": [{"path": p, "source_group": group_of(p), "split": "development" if p in dev else "holdout",
                       "blob": by_path[p]["blob"], "sha256_at_revision": by_path[p]["sha256"], "bytes": by_path[p]["bytes"],
                       "covariate_packet_appearances": appear.get(p, 0),
                       "historical_scanned_bytes": "UNVERIFIED — packets carry no source digest"} for p in selected],
        "not_bound_yet": ["labels", "annotators", "scorer", "thresholds", "AMBIGUOUS rule", "freeze digest in protocol"],
    }
    canon = json.dumps({k: v for k, v in manifest.items() if k != "manifest_sha256"}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    manifest["manifest_sha256"] = hashlib.sha256(canon.encode()).hexdigest()
    return manifest


if __name__ == "__main__":
    rev = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    m = build(rev)
    OUT.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    c = m["counts"]
    print(f"revision {m['pinned_revision'][:12]} · tracked {c['tracked']} · eligible {c['eligible']} · excluded {c['excluded']} · "
          f"selected {c['selected']} = dev {c['development']} + holdout {c['holdout']} · groups {c['groups']} · "
          f"seed {m['sampling']['seed']} · manifest sha256 {m['manifest_sha256'][:12]}")
    flagged = sum(1 for d in m["documents"] if d["covariate_packet_appearances"] > 0)
    print(f"covariate: {flagged}/{c['selected']} selected docs appear in >=1 packet (recorded after selection)")
    from collections import Counter
    print("exclusion reasons:", dict(Counter(e["reason"].split()[0] for e in m["excluded"])))
