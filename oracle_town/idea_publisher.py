#!/usr/bin/env python3
"""
Idea Publisher — Deterministic publisher for the non-authoritative Idea Gallery.

This sits parallel to governance, never feeding Mayor.
It transforms CT proposals into safe "Idea Cards" for inspiration.

Architecture:
    CT → (Idea Publisher) → Idea Gallery (read-only, non-authoritative)
    CT → Intake → Briefcase → Factory → Ledger → Mayor (governance, unchanged)

Key invariant:
    No path from Idea Gallery back into Mayor inputs.

Usage:
    # Publish ideas from a run
    python oracle_town/idea_publisher.py --run oracle_town/runs/demo_emergence/run_001

    # Publish all ideas from a directory
    python oracle_town/idea_publisher.py --batch oracle_town/runs/demo_emergence/

    # Browse the gallery
    python oracle_town/idea_publisher.py --browse

    # Random sample ("Surprise me")
    python oracle_town/idea_publisher.py --random 5
"""

import json
import os
import sys
import hashlib
import unicodedata
from pathlib import Path
from datetime import datetime
from typing import Optional
import random

# =============================================================================
# CONFIGURATION
# =============================================================================

GALLERY_DIR = Path("oracle_town/idea_gallery")
CURRENT_MONTH = datetime.now().strftime("%Y-%m")

# =============================================================================
# FORBIDDEN AUTHORITY LEXICON (same as Intake, for consistency)
# =============================================================================

AUTHORITY_KEYS = {
    "ship", "verdict", "decision", "recommend", "confidence",
    "score", "rank", "certified", "satisfied", "attestation",
    "receipt", "proof", "approved", "verified", "priority"
}

AUTHORITY_PHRASES = [
    "should ship",
    "must ship",
    "ready to ship",
    "safe to deploy",
    "is satisfied",
    "obligation satisfied",
    "all tests passed",
    "certified",
    "verified",
    "approved",
    "recommended",
    "best option",
    "highest priority",
    "guaranteed",
    "proven safe"
]


def normalize_text(text: str) -> str:
    """NFKC normalization, lowercase, whitespace collapse."""
    normalized = unicodedata.normalize('NFKC', text.lower())
    return ' '.join(normalized.split())


def walk_keys(obj, prefix="") -> list:
    """Recursively walk all keys in nested structure."""
    keys = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.append(k.lower())
            keys.extend(walk_keys(v, f"{prefix}.{k}"))
    elif isinstance(obj, list):
        for item in obj:
            keys.extend(walk_keys(item, prefix))
    return keys


# =============================================================================
# GUARDRAILS (same gates as Intake, applied to Idea Cards)
# =============================================================================

def check_forbidden_authority(idea: dict) -> tuple[bool, list]:
    """
    Check for authority language in idea card.

    Returns:
        (clean, violations) where clean=True means no violations
    """
    violations = []

    # Check keys
    all_keys = walk_keys(idea)
    for key in all_keys:
        if key in AUTHORITY_KEYS:
            violations.append(f"AUTHORITY_KEY:{key}")

    # Check text content
    all_text = normalize_text(json.dumps(idea))
    for phrase in AUTHORITY_PHRASES:
        if normalize_text(phrase) in all_text:
            violations.append(f"AUTHORITY_PHRASE:{phrase}")

    return len(violations) == 0, violations


def check_duplicate_blocks(text: str, min_length: int = 20, min_repeats: int = 3) -> bool:
    """Check for persuasion-amplification via repetition."""
    words = text.split()
    for window_size in range(5, min(len(words) // min_repeats + 1, 15)):
        for i in range(len(words) - window_size * min_repeats + 1):
            window = " ".join(words[i:i + window_size])
            if len(window) >= min_length:
                count = text.count(window)
                if count >= min_repeats:
                    return True
    return False


def compute_idea_digest(idea: dict) -> str:
    """Compute canonical digest for dedup and audit."""
    # Exclude volatile fields
    content = {k: v for k, v in idea.items() if k not in ["published_at", "idea_digest", "novelty_bucket"]}
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def compute_novelty_bucket(idea: dict, existing_digests: set) -> str:
    """
    Compute novelty bucket (not a ranking, just clustering).

    - NOVEL: First time seeing this mechanism combination
    - VARIATION: Similar to existing but different problem frame
    - REFINEMENT: Same problem frame, iterating on mechanism
    """
    # Simple heuristic based on mechanism + problem_frame
    mechanism_sig = hashlib.sha256(
        json.dumps(sorted(idea.get("mechanism", [])), sort_keys=True).encode()
    ).hexdigest()[:16]

    problem_sig = hashlib.sha256(
        json.dumps(sorted(idea.get("problem_frame", [])), sort_keys=True).encode()
    ).hexdigest()[:16]

    full_sig = f"{mechanism_sig}:{problem_sig}"

    if full_sig not in existing_digests:
        return "NOVEL"
    elif mechanism_sig not in str(existing_digests):
        return "VARIATION"
    else:
        return "REFINEMENT"


# =============================================================================
# IDEA EXTRACTION
# =============================================================================

def extract_idea_card(proposal: dict, run_id: str) -> Optional[dict]:
    """
    Transform a CT proposal into a safe Idea Card.

    Returns None if proposal is unsuitable for gallery.
    """
    if not proposal.get("description"):
        return None

    # Map proposal_type to allowed categories
    ptype = proposal.get("proposal_type", "other").lower()
    allowed_types = [
        "architecture", "feature", "process", "experiment",
        "risk", "agents", "ux", "security", "performance",
        "documentation", "other"
    ]
    if ptype not in allowed_types:
        ptype = "other"

    # Extract one-line summary (first sentence or truncated)
    desc = proposal.get("description", "")
    first_sentence = desc.split(".")[0].strip()
    if len(first_sentence) > 200:
        first_sentence = first_sentence[:197] + "..."

    # Extract problem frame from description keywords
    problem_frame = []
    keywords = ["refactor", "add", "improve", "fix", "enable", "track", "validate", "test"]
    for kw in keywords:
        if kw in desc.lower():
            problem_frame.append(kw)
    if not problem_frame:
        problem_frame = ["general improvement"]

    # Extract mechanism from suggested changes
    mechanism = []
    changes = proposal.get("suggested_changes", {})
    files = changes.get("files", [])
    if files:
        mechanism.append(f"modify {len(files)} file(s)")
    if "test" in desc.lower():
        mechanism.append("add/modify tests")
    if "api" in desc.lower():
        mechanism.append("add/modify API")
    if "schema" in desc.lower():
        mechanism.append("update schemas")
    if not mechanism:
        mechanism = ["implementation details TBD"]

    # Extract affected components from file paths
    affected = []
    for f in files:
        parts = f.split("/")
        if len(parts) >= 2:
            affected.append(parts[1] if parts[0] == "oracle_town" else parts[0])
    affected = list(set(affected)) or ["core"]

    # Infer invariants touched
    invariants = []
    if "determinism" in desc.lower() or "replay" in desc.lower():
        invariants.append("K5_DETERMINISM")
    if "authority" in desc.lower() or "k0" in desc.lower():
        invariants.append("K0_NO_TEXT_AUTHORITY")
    if "fail" in desc.lower() and "closed" in desc.lower():
        invariants.append("K1_FAIL_CLOSED")

    # Extract risk notes (if any "risk" or "warning" language)
    risk_notes = []
    if "risk" in desc.lower():
        # Find sentences with "risk"
        for sentence in desc.split("."):
            if "risk" in sentence.lower():
                risk_notes.append(sentence.strip()[:200])

    # Build evidence hypotheses
    evidence_hypotheses = [
        {"receipt_type": "test_pass", "attestor_class": "CI_RUNNER"}
    ]
    if "security" in desc.lower() or "security" in ptype:
        evidence_hypotheses.append({"receipt_type": "security_review", "attestor_class": "SECURITY"})
    if "legal" in desc.lower() or "gdpr" in desc.lower():
        evidence_hypotheses.append({"receipt_type": "compliance_signoff", "attestor_class": "LEGAL"})

    idea = {
        "run_id": run_id,
        "proposal_id": proposal.get("proposal_id", "P-UNKNOWN"),
        "proposal_type": ptype,
        "one_line_summary": first_sentence,
        "problem_frame": problem_frame[:5],
        "mechanism": mechanism[:5],
        "affected_components": affected[:10],
        "invariants_touched": invariants,
        "risk_notes": risk_notes[:3],
        "evidence_hypotheses": evidence_hypotheses,
        "published_at": datetime.now().isoformat()
    }

    return idea


# =============================================================================
# PUBLISHER
# =============================================================================

class IdeaPublisher:
    """
    Deterministic publisher for the Idea Gallery.

    Guardrails:
    - Schema validation
    - Forbidden token scan
    - Duplicate-block detection
    - Canonicalization + hash
    """

    def __init__(self):
        self.gallery_dir = GALLERY_DIR
        self.gallery_dir.mkdir(parents=True, exist_ok=True)
        self.gallery_file = self.gallery_dir / f"ideas_{CURRENT_MONTH}.jsonl"
        self.existing_digests = self._load_existing_digests()
        self.rejections = []

    def _load_existing_digests(self) -> set:
        """Load digests of already-published ideas for dedup."""
        digests = set()
        for jsonl_file in self.gallery_dir.glob("ideas_*.jsonl"):
            with open(jsonl_file) as f:
                for line in f:
                    if line.strip():
                        try:
                            idea = json.loads(line)
                            if "idea_digest" in idea:
                                digests.add(idea["idea_digest"])
                        except:
                            pass
        return digests

    def publish_from_proposal(self, proposal: dict, run_id: str) -> Optional[dict]:
        """
        Publish a single proposal to the Idea Gallery.

        Returns the published idea card, or None if rejected.
        """
        # Extract idea card
        idea = extract_idea_card(proposal, run_id)
        if not idea:
            self.rejections.append({
                "run_id": run_id,
                "reason": "EXTRACTION_FAILED",
                "details": "Could not extract idea from proposal"
            })
            return None

        # Guardrail 1: Forbidden authority check
        clean, violations = check_forbidden_authority(idea)
        if not clean:
            self.rejections.append({
                "run_id": run_id,
                "proposal_id": idea.get("proposal_id"),
                "reason": "AUTHORITY_LANGUAGE",
                "violations": violations
            })
            return None

        # Guardrail 2: Duplicate-block check
        full_text = " ".join([
            idea.get("one_line_summary", ""),
            " ".join(idea.get("problem_frame", [])),
            " ".join(idea.get("mechanism", [])),
            " ".join(idea.get("risk_notes", []))
        ])
        if check_duplicate_blocks(full_text):
            self.rejections.append({
                "run_id": run_id,
                "proposal_id": idea.get("proposal_id"),
                "reason": "DUPLICATE_BLOCKS",
                "details": "Persuasion-amplification detected"
            })
            return None

        # Compute digest
        idea["idea_digest"] = compute_idea_digest(idea)

        # Guardrail 3: Dedup
        if idea["idea_digest"] in self.existing_digests:
            # Not an error, just skip duplicate
            return None

        # Compute novelty bucket
        idea["novelty_bucket"] = compute_novelty_bucket(idea, self.existing_digests)

        # Publish
        with open(self.gallery_file, "a") as f:
            f.write(json.dumps(idea, separators=(",", ":")) + "\n")

        self.existing_digests.add(idea["idea_digest"])
        return idea

    def publish_from_run(self, run_dir: Path) -> list:
        """Publish all proposals from a governance run."""
        published = []

        proposal_path = run_dir / "proposal_bundle.json"
        if not proposal_path.exists():
            return published

        with open(proposal_path) as f:
            bundle = json.load(f)

        for proposal in bundle.get("proposals", []):
            idea = self.publish_from_proposal(proposal, run_dir.name)
            if idea:
                published.append(idea)

        return published

    def publish_batch(self, runs_dir: Path) -> dict:
        """Publish ideas from all runs in a directory."""
        results = {
            "runs_processed": 0,
            "ideas_published": 0,
            "ideas_rejected": 0,
            "ideas_deduplicated": 0
        }

        for run_dir in sorted(runs_dir.iterdir()):
            if run_dir.is_dir() and not run_dir.name.startswith("."):
                ideas_before = len(self.existing_digests)
                published = self.publish_from_run(run_dir)
                results["runs_processed"] += 1
                results["ideas_published"] += len(published)

        results["ideas_rejected"] = len(self.rejections)
        return results

    def get_rejection_report(self) -> str:
        """Generate report of rejected ideas."""
        if not self.rejections:
            return "No rejections."

        lines = ["IDEA PUBLISHER REJECTIONS", "=" * 40]
        for rej in self.rejections:
            lines.append(f"  Run: {rej.get('run_id')}")
            lines.append(f"  Proposal: {rej.get('proposal_id', 'N/A')}")
            lines.append(f"  Reason: {rej.get('reason')}")
            if rej.get('violations'):
                lines.append(f"  Violations: {rej.get('violations')}")
            lines.append("")

        return "\n".join(lines)


# =============================================================================
# GALLERY BROWSER
# =============================================================================

class IdeaGalleryBrowser:
    """Read-only browser for the Idea Gallery."""

    def __init__(self):
        self.gallery_dir = GALLERY_DIR
        self.ideas = self._load_all_ideas()

    def _load_all_ideas(self) -> list:
        """Load all ideas from gallery."""
        ideas = []
        for jsonl_file in sorted(self.gallery_dir.glob("ideas_*.jsonl")):
            with open(jsonl_file) as f:
                for line in f:
                    if line.strip():
                        try:
                            ideas.append(json.loads(line))
                        except:
                            pass
        return ideas

    def browse(self, filters: dict = None, limit: int = 20) -> list:
        """Browse ideas with optional filters."""
        results = self.ideas

        if filters:
            if "proposal_type" in filters:
                results = [i for i in results if i.get("proposal_type") == filters["proposal_type"]]
            if "component" in filters:
                results = [i for i in results if filters["component"] in i.get("affected_components", [])]
            if "novelty" in filters:
                results = [i for i in results if i.get("novelty_bucket") == filters["novelty"]]

        # Return newest first (chronological, not ranked)
        results = sorted(results, key=lambda x: x.get("published_at", ""), reverse=True)
        return results[:limit]

    def random_sample(self, n: int = 5) -> list:
        """'Surprise me' — random sample from ideas."""
        if len(self.ideas) <= n:
            return self.ideas
        return random.sample(self.ideas, n)

    def get_facets(self) -> dict:
        """Get available facets for filtering."""
        facets = {
            "proposal_types": set(),
            "components": set(),
            "invariants": set(),
            "novelty_buckets": set()
        }

        for idea in self.ideas:
            facets["proposal_types"].add(idea.get("proposal_type"))
            facets["components"].update(idea.get("affected_components", []))
            facets["invariants"].update(idea.get("invariants_touched", []))
            if idea.get("novelty_bucket"):
                facets["novelty_buckets"].add(idea.get("novelty_bucket"))

        return {k: sorted(list(v)) for k, v in facets.items()}

    def render_idea(self, idea: dict) -> str:
        """Render a single idea for display."""
        lines = []
        lines.append(f"{'─' * 50}")
        lines.append(f"  {idea.get('proposal_id', 'P-???')} [{idea.get('proposal_type', '?').upper()}]")
        if idea.get("novelty_bucket"):
            lines.append(f"  ({idea.get('novelty_bucket')})")
        lines.append(f"")
        lines.append(f"  {idea.get('one_line_summary', 'No summary')}")
        lines.append(f"")
        lines.append(f"  Problem: {', '.join(idea.get('problem_frame', []))}")
        lines.append(f"  Mechanism: {', '.join(idea.get('mechanism', []))}")
        lines.append(f"  Components: {', '.join(idea.get('affected_components', []))}")

        if idea.get("invariants_touched"):
            lines.append(f"  Invariants: {', '.join(idea.get('invariants_touched', []))}")

        if idea.get("risk_notes"):
            lines.append(f"  Risks: {idea.get('risk_notes')[0][:80]}...")

        lines.append(f"")
        lines.append(f"  Run: {idea.get('run_id')}")
        lines.append(f"  Published: {idea.get('published_at', '?')[:10]}")

        return "\n".join(lines)

    def display_gallery(self, ideas: list) -> str:
        """Display a list of ideas."""
        if not ideas:
            return "No ideas found."

        lines = []
        lines.append("=" * 50)
        lines.append("  IDEA GALLERY — Inspiration Feed")
        lines.append("  (Non-authoritative: not evidence, not a recommendation)")
        lines.append("=" * 50)

        for idea in ideas:
            lines.append(self.render_idea(idea))

        lines.append("─" * 50)
        lines.append(f"  Showing {len(ideas)} idea(s)")
        lines.append("=" * 50)

        return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Idea Publisher & Gallery Browser")
    parser.add_argument("--run", type=str, help="Publish ideas from a single run directory")
    parser.add_argument("--batch", type=str, help="Publish ideas from all runs in directory")
    parser.add_argument("--browse", action="store_true", help="Browse the idea gallery")
    parser.add_argument("--random", type=int, help="Show N random ideas ('Surprise me')")
    parser.add_argument("--type", type=str, help="Filter by proposal type")
    parser.add_argument("--component", type=str, help="Filter by component")
    parser.add_argument("--facets", action="store_true", help="Show available facets")
    parser.add_argument("--export", type=str, help="Export gallery to JSON file")

    args = parser.parse_args()

    if args.run:
        publisher = IdeaPublisher()
        run_dir = Path(args.run)
        published = publisher.publish_from_run(run_dir)
        print(f"Published {len(published)} idea(s) from {run_dir.name}")
        if publisher.rejections:
            print()
            print(publisher.get_rejection_report())

    elif args.batch:
        publisher = IdeaPublisher()
        runs_dir = Path(args.batch)
        results = publisher.publish_batch(runs_dir)
        print(f"Processed {results['runs_processed']} runs")
        print(f"Published {results['ideas_published']} ideas")
        print(f"Rejected {results['ideas_rejected']} ideas")
        if publisher.rejections:
            print()
            print(publisher.get_rejection_report())

    elif args.browse or args.type or args.component:
        browser = IdeaGalleryBrowser()
        filters = {}
        if args.type:
            filters["proposal_type"] = args.type
        if args.component:
            filters["component"] = args.component
        ideas = browser.browse(filters)
        print(browser.display_gallery(ideas))

    elif args.random:
        browser = IdeaGalleryBrowser()
        ideas = browser.random_sample(args.random)
        print(browser.display_gallery(ideas))

    elif args.facets:
        browser = IdeaGalleryBrowser()
        facets = browser.get_facets()
        print("AVAILABLE FACETS")
        print("=" * 40)
        for name, values in facets.items():
            print(f"\n{name}:")
            for v in values:
                print(f"  - {v}")

    elif args.export:
        browser = IdeaGalleryBrowser()
        with open(args.export, "w") as f:
            json.dump(browser.ideas, f, indent=2)
        print(f"Exported {len(browser.ideas)} ideas to {args.export}")

    else:
        # Default: show help
        parser.print_help()


if __name__ == "__main__":
    main()
