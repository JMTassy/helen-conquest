"""
helen_os/temporal_decay.py — TEMPORAL_DECAY_V1

Memory decay engine for the Autoresearch Loop.

CONSTITUTIONAL STATUS: Experimental mechanism. NOT yet sealed as invariant I11.
Invariant canonization is blocked until:
  G1  live_run_completed
  G2  receipts_complete (pre/post decay state, token delta, protected tiers)
  G3  protected_tiers_preserved (SEALED + ANCHORED never pruned)
  G4  recall_not_degraded_beyond_threshold
  G5  benchmark_completed (6-system comparison)
  G6  temporal_decay_outperforms_or_matches_baselines

DECREE_T59: Activate in next live Autoresearch mission. Log receipts.
            Block I11 until evidence exists. Block sigil until doctrine earned.

Three-tier memory hierarchy (immutable):

    SEALED    — Receipt-bearing items from the sovereign ledger.
                Never pruned. Examples: SHIP manifests, WORLD_PATCH_GEN_V1 receipts.
                Comes from: manifest_hash, receipt_hash, law_surface_hash.

    ANCHORED  — Explicitly protected items. Decay-exempt until anchor expires.
                Re-anchored when cited by a receipt-bearing operation.
                Weight stays at anchor_weight (default: 0.9) until anchor released.

    EPHEMERAL — All other working memory. Decays monotonically by cycle age.
                weight(item, t) = base_weight * exp(-lambda * (t - t_last_use))
                where lambda = 0.001 (frozen).
                Pruned from context injection when weight < PRUNE_THRESHOLD.

Decay law (candidate for I11 — NOT YET SEALED):
    Ephemeral memory items decay monotonically unless re-anchored
    by receipt-bearing reuse.

Context injection:
    select_context(memory_pool, cycle_id) -> (injected_items, decay_receipt)
    Returns only items with weight >= PRUNE_THRESHOLD.
    Always includes ALL SEALED and ANCHORED items.
    SEALED items are ordered before ANCHORED, ANCHORED before EPHEMERAL.

Receipt schema:
    TEMPORAL_DECAY_RECEIPT_V1 — emitted once per autoresearch cycle.
    Not sovereign (does not append to the main ledger).
    Recorded in the autoresearch audit log only.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ── Constants (frozen for TEMPORAL_DECAY_V1) ──────────────────────────────────

DECAY_LAMBDA: float  = 0.001   # λ per cycle (1 cycle = 1 autoresearch iteration)
PRUNE_THRESHOLD: float = 0.10  # weight below which ephemeral items are excluded
ANCHOR_WEIGHT: float   = 0.90  # weight of ANCHORED items (decay-exempt)
INITIAL_WEIGHT: float  = 1.00  # initial weight for new ephemeral items
TEMPORAL_DECAY_VERSION: str = "TEMPORAL_DECAY_V1"


# ── Memory tiers ──────────────────────────────────────────────────────────────

class MemoryTier(str, Enum):
    SEALED    = "SEALED"     # receipt-bearing, never pruned
    ANCHORED  = "ANCHORED"   # explicitly protected, decay-exempt
    EPHEMERAL = "EPHEMERAL"  # decays by cycle age


# ── Memory item ───────────────────────────────────────────────────────────────

@dataclass
class MemoryItem:
    """
    A single item in the working memory pool.

    Fields:
        item_id:         Unique identifier (e.g. manifest_hash for SEALED items).
        content:         The actual content (dict, str, etc.).
        tier:            MemoryTier — SEALED / ANCHORED / EPHEMERAL.
        cycle_added:     Cycle number when this item was added.
        cycle_last_used: Cycle number of last access (updated on injection).
        base_weight:     Initial weight (always INITIAL_WEIGHT for EPHEMERAL).
        current_weight:  Current decayed weight (recomputed on each decay pass).
        receipt_hash:    For SEALED items: the hash from the sovereign ledger.
                         For ANCHORED items: hash of the anchor receipt.
                         For EPHEMERAL: None.
        anchor_expires_at_cycle: For ANCHORED items: cycle at which anchor expires
                                 (becomes EPHEMERAL after this cycle).
                                 None = permanent anchor (use with caution).
        tags:            Optional labels for filtering / analysis.
    """
    item_id:                  str
    content:                  Any
    tier:                     MemoryTier
    cycle_added:              int
    cycle_last_used:          int
    base_weight:              float = INITIAL_WEIGHT
    current_weight:           float = INITIAL_WEIGHT
    receipt_hash:             Optional[str] = None
    anchor_expires_at_cycle:  Optional[int] = None
    tags:                     list = field(default_factory=list)

    @property
    def is_sealed(self) -> bool:
        return self.tier == MemoryTier.SEALED

    @property
    def is_anchored(self) -> bool:
        return self.tier == MemoryTier.ANCHORED

    @property
    def is_ephemeral(self) -> bool:
        return self.tier == MemoryTier.EPHEMERAL


# ── Decay receipt ─────────────────────────────────────────────────────────────

@dataclass
class TemporalDecayReceiptV1:
    """
    TEMPORAL_DECAY_RECEIPT_V1 — emitted once per autoresearch cycle.

    Records the pre/post decay state for evidence collection (DECREE_T59).
    Not sovereign. Written to autoresearch audit log only.
    """
    artifact_type:          str  = "TEMPORAL_DECAY_RECEIPT_V1"
    decay_version:          str  = TEMPORAL_DECAY_VERSION
    cycle_id:               str  = ""
    cycle_number:           int  = 0
    lambda_param:           float = DECAY_LAMBDA
    prune_threshold:        float = PRUNE_THRESHOLD

    # Pre-decay snapshot
    pre_total_items:        int  = 0
    pre_sealed_items:       int  = 0
    pre_anchored_items:     int  = 0
    pre_ephemeral_items:    int  = 0

    # Post-decay results
    post_total_items:       int  = 0
    sealed_retained:        int  = 0
    anchored_retained:      int  = 0
    ephemeral_retained:     int  = 0
    ephemeral_pruned:       int  = 0
    anchors_expired:        int  = 0    # anchors that crossed expiry → became ephemeral

    # Context injection metrics
    injected_item_count:    int  = 0
    estimated_tokens_injected: int = 0  # rough estimate (content str length / 4)

    # Outcome tracking (filled after mission completes)
    recall_hits:            int  = 0
    recall_misses:          int  = 0
    mission_verdict:        str  = ""   # "SHIP" / "ABORT" / ""

    # Integrity
    canonical_payload_hash: str  = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_type":          self.artifact_type,
            "decay_version":          self.decay_version,
            "cycle_id":               self.cycle_id,
            "cycle_number":           self.cycle_number,
            "lambda_param":           self.lambda_param,
            "prune_threshold":        self.prune_threshold,
            "pre_total_items":        self.pre_total_items,
            "pre_sealed_items":       self.pre_sealed_items,
            "pre_anchored_items":     self.pre_anchored_items,
            "pre_ephemeral_items":    self.pre_ephemeral_items,
            "post_total_items":       self.post_total_items,
            "sealed_retained":        self.sealed_retained,
            "anchored_retained":      self.anchored_retained,
            "ephemeral_retained":     self.ephemeral_retained,
            "ephemeral_pruned":       self.ephemeral_pruned,
            "anchors_expired":        self.anchors_expired,
            "injected_item_count":    self.injected_item_count,
            "estimated_tokens_injected": self.estimated_tokens_injected,
            "recall_hits":            self.recall_hits,
            "recall_misses":          self.recall_misses,
            "mission_verdict":        self.mission_verdict,
            "canonical_payload_hash": self.canonical_payload_hash,
        }

    def to_ndjson(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


# ── Core decay engine ─────────────────────────────────────────────────────────

class TemporalDecayEngine:
    """
    TEMPORAL_DECAY_V1 engine.

    Manages a working memory pool with three tiers and applies exponential
    decay to EPHEMERAL items on each cycle. Emits TEMPORAL_DECAY_RECEIPT_V1.

    Usage:
        engine = TemporalDecayEngine()

        # Add items
        engine.add_sealed("MAN-001", manifest_dict, receipt_hash="abc123...")
        engine.add_anchored("lesson-X", lesson_dict, anchor_until_cycle=5)
        engine.add_ephemeral("working-note-Y", note_dict)

        # At start of each cycle: apply decay and select context
        injected, receipt = engine.decay_and_select_context("LOOP-20260311", cycle=3)

        # After mission: record outcome
        engine.record_outcome(receipt, mission_verdict="SHIP",
                              recall_hits=3, recall_misses=0)
    """

    def __init__(
        self,
        lambda_param:    float = DECAY_LAMBDA,
        prune_threshold: float = PRUNE_THRESHOLD,
    ) -> None:
        self.lambda_param    = lambda_param
        self.prune_threshold = prune_threshold
        self._pool:          dict[str, MemoryItem] = {}  # item_id → MemoryItem

    # ── Item management ───────────────────────────────────────────────────────

    def add_sealed(
        self,
        item_id:      str,
        content:      Any,
        receipt_hash: str,
        cycle:        int = 0,
        tags:         Optional[list] = None,
    ) -> MemoryItem:
        """
        Add a SEALED item (receipt-bearing, never pruned).

        Args:
            item_id:      Unique ID (typically the manifest_hash or receipt_hash).
            content:      The item's content.
            receipt_hash: SHA256 from the sovereign ledger.
            cycle:        Cycle number when this item was added.
            tags:         Optional labels.
        """
        item = MemoryItem(
            item_id=item_id,
            content=content,
            tier=MemoryTier.SEALED,
            cycle_added=cycle,
            cycle_last_used=cycle,
            base_weight=INITIAL_WEIGHT,
            current_weight=INITIAL_WEIGHT,
            receipt_hash=receipt_hash,
            tags=tags or [],
        )
        self._pool[item_id] = item
        return item

    def add_anchored(
        self,
        item_id:               str,
        content:               Any,
        cycle:                 int = 0,
        receipt_hash:          Optional[str] = None,
        anchor_expires_at_cycle: Optional[int] = None,
        tags:                  Optional[list] = None,
    ) -> MemoryItem:
        """
        Add an ANCHORED item (decay-exempt until anchor expires).

        Args:
            item_id:                 Unique ID.
            content:                 The item's content.
            cycle:                   Cycle number when added.
            receipt_hash:            Optional anchor receipt hash.
            anchor_expires_at_cycle: Cycle at which anchor expires → item becomes EPHEMERAL.
                                     None = permanent anchor (use sparingly).
            tags:                    Optional labels.
        """
        item = MemoryItem(
            item_id=item_id,
            content=content,
            tier=MemoryTier.ANCHORED,
            cycle_added=cycle,
            cycle_last_used=cycle,
            base_weight=ANCHOR_WEIGHT,
            current_weight=ANCHOR_WEIGHT,
            receipt_hash=receipt_hash,
            anchor_expires_at_cycle=anchor_expires_at_cycle,
            tags=tags or [],
        )
        self._pool[item_id] = item
        return item

    def add_ephemeral(
        self,
        item_id: str,
        content: Any,
        cycle:   int = 0,
        tags:    Optional[list] = None,
    ) -> MemoryItem:
        """
        Add an EPHEMERAL item (decays by cycle age).

        Args:
            item_id: Unique ID.
            content: The item's content.
            cycle:   Cycle number when added.
            tags:    Optional labels.
        """
        item = MemoryItem(
            item_id=item_id,
            content=content,
            tier=MemoryTier.EPHEMERAL,
            cycle_added=cycle,
            cycle_last_used=cycle,
            base_weight=INITIAL_WEIGHT,
            current_weight=INITIAL_WEIGHT,
            tags=tags or [],
        )
        self._pool[item_id] = item
        return item

    def re_anchor(
        self,
        item_id:               str,
        receipt_hash:          str,
        current_cycle:         int,
        anchor_expires_at_cycle: Optional[int] = None,
    ) -> Optional[MemoryItem]:
        """
        Re-anchor an item (elevate EPHEMERAL → ANCHORED, or refresh ANCHORED).

        Called when an item is cited by a receipt-bearing operation.
        Weight resets to ANCHOR_WEIGHT.

        Returns the updated item, or None if item_id not found.
        """
        item = self._pool.get(item_id)
        if item is None:
            return None
        if item.is_sealed:
            return item   # SEALED items are immutable; no re-anchoring needed

        item.tier                    = MemoryTier.ANCHORED
        item.current_weight          = ANCHOR_WEIGHT
        item.receipt_hash            = receipt_hash
        item.cycle_last_used         = current_cycle
        item.anchor_expires_at_cycle = anchor_expires_at_cycle
        return item

    # ── Decay pass ────────────────────────────────────────────────────────────

    def decay_and_select_context(
        self,
        cycle_id:     str,
        cycle_number: int,
    ) -> tuple[list[MemoryItem], TemporalDecayReceiptV1]:
        """
        Apply one decay pass and return the context injection list.

        Algorithm:
            1. Expire anchors past their expiry cycle → downgrade to EPHEMERAL.
            2. For each EPHEMERAL item: recompute weight using exponential decay.
            3. Prune items with weight < prune_threshold.
            4. Return (injected_items, receipt).

        Ordering of injected_items:
            SEALED first (sorted by item_id),
            then ANCHORED (sorted by current_weight desc),
            then EPHEMERAL above threshold (sorted by current_weight desc).

        Args:
            cycle_id:     Human-readable cycle identifier (e.g. "LOOP-20260311-001").
            cycle_number: Integer cycle number (monotonically increasing).

        Returns:
            (injected_items, receipt) — injected_items is the context selection.
        """
        # ── Snapshot pre-decay state ──────────────────────────────────────────
        pre_total     = len(self._pool)
        pre_sealed    = sum(1 for i in self._pool.values() if i.is_sealed)
        pre_anchored  = sum(1 for i in self._pool.values() if i.is_anchored)
        pre_ephemeral = sum(1 for i in self._pool.values() if i.is_ephemeral)

        # ── Step 1: Expire anchors ────────────────────────────────────────────
        anchors_expired = 0
        for item in self._pool.values():
            if (item.is_anchored
                    and item.anchor_expires_at_cycle is not None
                    and cycle_number > item.anchor_expires_at_cycle):
                item.tier           = MemoryTier.EPHEMERAL
                item.current_weight = item.base_weight  # reset for fresh decay
                anchors_expired    += 1

        # ── Step 2: Recompute decay weights for EPHEMERAL items ───────────────
        pruned_ids: list[str] = []
        for item in self._pool.values():
            if not item.is_ephemeral:
                continue
            age = cycle_number - item.cycle_last_used
            item.current_weight = item.base_weight * math.exp(-self.lambda_param * age)
            if item.current_weight < self.prune_threshold:
                pruned_ids.append(item.item_id)

        # ── Step 3: Remove pruned items from pool ─────────────────────────────
        for pid in pruned_ids:
            del self._pool[pid]

        # ── Snapshot post-decay state ─────────────────────────────────────────
        sealed_retained    = sum(1 for i in self._pool.values() if i.is_sealed)
        anchored_retained  = sum(1 for i in self._pool.values() if i.is_anchored)
        ephemeral_retained = sum(1 for i in self._pool.values() if i.is_ephemeral)
        ephemeral_pruned   = len(pruned_ids)
        post_total         = len(self._pool)

        # ── Step 4: Build injection list ─────────────────────────────────────
        sealed_items   = sorted(
            [i for i in self._pool.values() if i.is_sealed],
            key=lambda i: i.item_id,
        )
        anchored_items = sorted(
            [i for i in self._pool.values() if i.is_anchored],
            key=lambda i: (-i.current_weight, i.item_id),
        )
        ephemeral_items = sorted(
            [i for i in self._pool.values() if i.is_ephemeral],
            key=lambda i: (-i.current_weight, i.item_id),
        )

        injected = sealed_items + anchored_items + ephemeral_items

        # Update last_used for injected items
        for item in injected:
            item.cycle_last_used = cycle_number

        # Estimate token usage (rough: len(str(content)) / 4)
        estimated_tokens = sum(
            len(str(item.content)) // 4
            for item in injected
        )

        # ── Build receipt ─────────────────────────────────────────────────────
        receipt = TemporalDecayReceiptV1(
            artifact_type="TEMPORAL_DECAY_RECEIPT_V1",
            decay_version=TEMPORAL_DECAY_VERSION,
            cycle_id=cycle_id,
            cycle_number=cycle_number,
            lambda_param=self.lambda_param,
            prune_threshold=self.prune_threshold,
            pre_total_items=pre_total,
            pre_sealed_items=pre_sealed,
            pre_anchored_items=pre_anchored,
            pre_ephemeral_items=pre_ephemeral,
            post_total_items=post_total,
            sealed_retained=sealed_retained,
            anchored_retained=anchored_retained,
            ephemeral_retained=ephemeral_retained,
            ephemeral_pruned=ephemeral_pruned,
            anchors_expired=anchors_expired,
            injected_item_count=len(injected),
            estimated_tokens_injected=estimated_tokens,
        )

        # Compute canonical payload hash
        payload = {k: v for k, v in receipt.to_dict().items()
                   if k != "canonical_payload_hash"}
        receipt.canonical_payload_hash = _sha256_hex(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        )

        return injected, receipt

    def record_outcome(
        self,
        receipt:         TemporalDecayReceiptV1,
        mission_verdict: str,
        recall_hits:     int = 0,
        recall_misses:   int = 0,
    ) -> TemporalDecayReceiptV1:
        """
        Update a receipt with post-mission outcome metrics.

        Call this after the autoresearch cycle completes.
        Recomputes canonical_payload_hash to include outcome data.
        """
        receipt.mission_verdict = mission_verdict
        receipt.recall_hits     = recall_hits
        receipt.recall_misses   = recall_misses

        # Recompute hash with outcome data
        payload = {k: v for k, v in receipt.to_dict().items()
                   if k != "canonical_payload_hash"}
        receipt.canonical_payload_hash = _sha256_hex(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        )
        return receipt

    # ── Pool introspection ────────────────────────────────────────────────────

    def pool_snapshot(self) -> dict[str, Any]:
        """Return a summary of the current pool state (for debugging/logging)."""
        items = list(self._pool.values())
        return {
            "total_items":    len(items),
            "sealed_count":   sum(1 for i in items if i.is_sealed),
            "anchored_count": sum(1 for i in items if i.is_anchored),
            "ephemeral_count": sum(1 for i in items if i.is_ephemeral),
            "weight_distribution": {
                item.item_id: round(item.current_weight, 4)
                for item in sorted(items, key=lambda i: -i.current_weight)
            },
        }

    def item_count(self) -> int:
        return len(self._pool)

    def get_item(self, item_id: str) -> Optional[MemoryItem]:
        return self._pool.get(item_id)

    def sealed_item_ids(self) -> list[str]:
        return [i.item_id for i in self._pool.values() if i.is_sealed]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def compute_decay_weight(
    base_weight:   float,
    cycles_elapsed: int,
    lambda_param:  float = DECAY_LAMBDA,
) -> float:
    """
    Pure function: weight after `cycles_elapsed` cycles of decay.

    weight = base_weight * exp(-lambda * cycles_elapsed)
    """
    return base_weight * math.exp(-lambda_param * cycles_elapsed)


def cycles_until_prune(
    base_weight:     float = INITIAL_WEIGHT,
    prune_threshold: float = PRUNE_THRESHOLD,
    lambda_param:    float = DECAY_LAMBDA,
) -> int:
    """
    How many cycles until an item drops below prune_threshold?

    Derived from: base * exp(-λ * t) < threshold
    → t > -ln(threshold / base) / λ
    """
    if base_weight <= prune_threshold:
        return 0
    return int(math.ceil(math.log(prune_threshold / base_weight) / (-lambda_param)))
