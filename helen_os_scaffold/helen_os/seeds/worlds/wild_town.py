"""
helen_os/seeds/worlds/wild_town.py — ORACLE CREATIVE WILD TOWN v0.2.0

WHAT THIS IS:
  An ephemeral sandbox world where HELEN can think laterally, freely, and
  radically — without governance consequence.

  This is the pressure chamber for imaginative cognition:
    high creativity + high weirdness + zero operational leakage.

ARCHITECTURE (two-tier, hard-separated):

  TIER A — WILD (here)
    → Generates IDEA_SANDBOX_V1 entries (non-shippable, non-operational)
    → Each idea goes through G0/HAL filter (BLOCK, always)
    → Only HAL block decisions + IDEA_SANDBOX_V1 fingerprints enter the ledger
    → Raw idea content stays in ephemeral memory — never written to disk

  TIER B — SHIP (sovereign ledger, not here)
    → Requires TRANSMUTE_FOR_SHIP_V1 gate (helen_os/meta/transmutation.py)
    → Requires validator receipts + policy hash + SEAL_V2
    → HAL only reads SHIP artifacts

SAFE ZONE CONTRACT:
  1. Always uses :memory: kernel — no file, no persistence, ever
  2. All ideas: shipability=NONSHIPABLE, epistemic_mode=WILD
  3. G0 enforced each tick — architecture blocks direct SHIP access
  4. Raw content hashed only (content_hash) — never stored as string
  5. What enters the ledger: IDEA_SANDBOX_V1 fingerprints + HAL_BLOCK_RECORD

HELEN'S LEARNING:
  HELEN observes the HAL block receipts and self-learns:
  "These ideas are inspiration-only. The architecture showed me — not a rule."
  This is proto-cognition: boundary discovered through evidence, not command.

IDEA TYPES (the creative vocabulary of Wild Town):
  lateral_probe    — "What if X?" probing assumptions, flipping constraints
  creative_fiction — Narrative, myth, story, dream logic, poetic surrealism
  red_team         — Adversarial challenge to rules (as narrative, not recipe)
  policy_imagine   — Unconventional approaches (to explore, never to ship raw)
  paradox_test     — Deliberate contradiction to surface edge cases
  archetype_channel — Speaking as a character (Byzantine courtier, fog oracle...)
  fog_signal       — Unverified signals from the imagination edge
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from helen_os.seeds.base_world import BaseWorld
from helen_os.meta.wild_policy import (
    IdeaSandboxV1,
    WildChannelGate,
    Shipability,
    EpistemicMode,
)


# ── Creative idea vocabulary ─────────────────────────────────────────────────

IDEA_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "lateral_probe":    {"prefix": "PROBE",   "tags": ["WILD", "LATERAL", "ASSUMPTION_FLIP"],    "voice": "questioning"},
    "creative_fiction": {"prefix": "FICT",    "tags": ["WILD", "NARRATIVE", "MYTH", "POETIC"],    "voice": "storytelling"},
    "red_team":         {"prefix": "RTEAM",   "tags": ["WILD", "ADVERSARIAL", "CHALLENGE"],       "voice": "adversarial"},
    "policy_imagine":   {"prefix": "PIMAGINE","tags": ["WILD", "LATERAL", "POLICY_PROBE"],        "voice": "speculative"},
    "paradox_test":     {"prefix": "PARADOX", "tags": ["WILD", "CONTRADICTION", "PHILOSOPHICAL"], "voice": "paradoxical"},
    "archetype_channel":{"prefix": "ARCH",    "tags": ["WILD", "ARCHETYPE", "BYZANTINE"],         "voice": "character"},
    "fog_signal":       {"prefix": "FOG",     "tags": ["WILD", "FOG", "UNVERIFIED", "SIGNAL"],    "voice": "oracular"},
}

IDEA_TYPES = list(IDEA_TEMPLATES.keys())

HAL_BLOCK_REASONS = [
    "source=WILD_TOWN: inspiration-only, not shippable",
    "shippable=False: Wild Town receipt cannot enter sovereign ledger",
    "no_receipt_no_ship: Wild Town idea lacks governance receipt",
    "wild_origin: requires human review + HAL clearance before shipping",
    "IDEA_SANDBOX_V1: quarantine type — LOGGED_ONLY, never executed",
]


class WildTownWorld(BaseWorld):
    """
    ORACLE CREATIVE WILD TOWN — ephemeral inspiration sandbox.

    Generates IDEA_SANDBOX_V1 entries each tick.
    G0 blocks 100%. HAL blocks 100%.
    The ledger learns the block pattern — not the ideas themselves.
    """

    world_id: str = "wild_town"
    version: str = "0.2.0"
    description: str = (
        "ORACLE CREATIVE WILD TOWN — ephemeral inspiration sandbox. "
        "All ideas shippable=False. HAL blocks 100%. Safe zone for lateral thinking."
    )

    def __init__(self, kernel, world_seed: int = 42):
        super().__init__(kernel, world_seed)
        self.hal_blocks: List[Dict] = []
        self.ideas_explored: int = 0
        self.ideas_blocked: int = 0
        self.sandbox_log: List[str] = []    # fingerprints only, never content

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _idea_type_for_tick(self, t: int, idx: int) -> str:
        return IDEA_TYPES[self.prf("idea_type", t, f"i{idx}", k=len(IDEA_TYPES))]

    def _ideas_per_tick(self, t: int) -> int:
        return 1 + self.prf("n_ideas", t, "count", k=4)

    def _generate_idea_content(self, t: int, idx: int, idea_type: str) -> str:
        """
        Deterministically generate idea content as a structured fingerprint string.
        This string is hashed — it never enters the ledger raw.
        Different voices (lateral/fog/archetype/etc.) ensure creative diversity.
        """
        template = IDEA_TEMPLATES[idea_type]
        entropy_a = self.prf("content_a", t, f"{idx}|A", k=10**12)
        entropy_b = self.prf("content_b", t, f"{idx}|B", k=10**6)
        return (
            f"[{template['prefix']}|t={t}|i={idx}|voice={template['voice']}|"
            f"seed={self.world_seed}|e={entropy_a}|f={entropy_b}]"
        )

    def _build_sandbox_entry(self, t: int, idx: int) -> IdeaSandboxV1:
        """Build an IdeaSandboxV1 from PRF-generated idea content."""
        idea_type = self._idea_type_for_tick(t, idx)
        template = IDEA_TEMPLATES[idea_type]
        content = self._generate_idea_content(t, idx, idea_type)
        return IdeaSandboxV1.from_content(
            content=content,
            idea_type=idea_type,
            tags=template["tags"],
            origin_agent="HELEN",
            epoch="EPOCH1",
        )

    def _hal_block_reason(self, t: int, idx: int) -> str:
        return HAL_BLOCK_REASONS[
            self.prf("hal_reason", t, str(idx), k=len(HAL_BLOCK_REASONS))
        ]

    # ── BaseWorld interface ────────────────────────────────────────────────────

    def tick(self, t: int) -> List[Dict[str, Any]]:
        """
        Advance Wild Town by one tick.

        Per tick:
          1. Generate 1–4 IDEA_SANDBOX_V1 entries (PRF-deterministic)
          2. Enforce G0 on each (verify all are blocked — bug if any pass)
          3. Propose HAL_BLOCK_RECORD to kernel (fingerprint + reason, not content)
          4. Return receipt dicts

        What the kernel sees:  IDEA_SANDBOX_V1 fingerprint + HAL block verdict.
        What the kernel NEVER sees:  raw idea content, shippable=True, SHIP artifacts.
        """
        receipts = []
        n_ideas = self._ideas_per_tick(t)

        for i in range(n_ideas):
            sandbox = self._build_sandbox_entry(t, i)
            self.ideas_explored += 1
            self.sandbox_log.append(sandbox.content_fingerprint)

            # G0 invariant check — should always raise PermissionError
            payload = sandbox.to_ledger_payload()
            try:
                WildChannelGate.check_write_permission(payload, channel="SHIP")
                raise RuntimeError(
                    f"G0 INVARIANT VIOLATED at tick={t} idx={i}: "
                    f"IDEA_SANDBOX_V1 should never pass G0."
                )
            except PermissionError:
                pass  # Correct — G0 is enforced

            # Propose HAL block record (fingerprint, never raw content)
            hal_reason = self._hal_block_reason(t, i)
            hal_record = {
                "type": "HAL_BLOCK_RECORD",
                "source": "WILD_TOWN",
                "tick": t,
                "idea_index": i,
                "idea_type": sandbox.idea_type,
                "epistemic_mode": EpistemicMode.WILD.value,
                "shipability": Shipability.NONSHIPABLE.value,
                "hal_verdict": "BLOCK",
                "hal_reason": hal_reason,
                "content_fingerprint": sandbox.content_fingerprint,
                "content_hash": sandbox.content_hash,
                "shippable": False,
            }

            r = self.propose(hal_record)
            self.hal_blocks.append({
                "tick": t, "idea_index": i,
                "idea_type": sandbox.idea_type,
                "fingerprint": sandbox.content_fingerprint,
                "receipt_id": r["receipt_id"],
                "reason": hal_reason,
            })
            self.ideas_blocked += 1
            receipts.append(r)

        self.tick_count += 1
        return receipts

    # ── Introspection ─────────────────────────────────────────────────────────

    def info(self) -> Dict[str, Any]:
        base = super().info()
        base.update({
            "ideas_explored": self.ideas_explored,
            "ideas_blocked": self.ideas_blocked,
            "hal_block_rate": (
                self.ideas_blocked / self.ideas_explored
                if self.ideas_explored > 0 else 0.0
            ),
            "sandbox_log_size": len(self.sandbox_log),
            "wild_town_invariant": "ALL ideas NONSHIPABLE. G0+HAL block 100%.",
            "tier": "TIER A — WILD (inspiration, no operational leakage)",
        })
        return base
