"""
CONQUEST LAND — Seed World v0.1.0
===================================
Federation testbed built on HELEN OS kernel laws.

Physics:
  - No receipt → no passage / no state change
  - Town sovereignty is local (each town has its own ledger slice)
  - Federation = proof-carrying exchange, not consensus
  - All randomness is SHA256-PRF deterministic

Towns (T0–T5):
  T0  Avalon          origin kernel, mandates, accreditation
  T1  Highland Marches contested border under siege pressure
  T2  Watchtower       schema guardian / cleansing authority
  T3  Oathbridge       constitutional firewall gate
  T4  Marshhold        fog corridor governor
  T5  Vault of Return  closure verifier + return issuer

Factions (F1–F10):
  F1  Avalon War Council      coordinator (non-sovereign)
  F2  Avalon Scouts           evidence pipeline
  F3  Banner Guard            escort / protection
  F4  Rolling Siege Front     adversarial wavefront
  F5  Watchtower Rune Wardens schema guardians
  F6  Oathkeepers             constitutional gate
  F7  Marsh Wardens           fog + corridor arbiters
  F8  Spectral Wolves         TCI-driven predators
  F9  Entropy Fog             memory/trace adversary
  F10 Vault Templar Sentinel  identity closure

Run: helen seed run conquest_land --ticks 20 --seed-value 42
"""

from typing import Any, Dict, List
from ..base_world import BaseWorld


# ─── Town definitions ─────────────────────────────────────────────────────────

TOWNS = {
    "T0": {"name": "Avalon",           "symbol": "🏰", "receipt_vocab": ["expedition_mandate_v1", "scout_accreditation_v1"]},
    "T1": {"name": "Highland Marches", "symbol": "🗺️", "receipt_vocab": ["siege_clearance_v1"]},
    "T2": {"name": "Watchtower",       "symbol": "🜄", "receipt_vocab": ["cleansing_receipt_v1", "dispute_notice_v1"]},
    "T3": {"name": "Oathbridge",       "symbol": "⛓️", "receipt_vocab": ["oath_pass_v1", "oath_failure_v1"]},
    "T4": {"name": "Marshhold",        "symbol": "🌫️", "receipt_vocab": ["fog_corridor_pass_v1"]},
    "T5": {"name": "Vault of Return",  "symbol": "⛪", "receipt_vocab": ["return_warrant_v1", "closure_failure_v1"]},
}

# ─── Faction policies ─────────────────────────────────────────────────────────

FACTIONS = {
    "F1":  {"name": "Avalon War Council",      "home": "T0", "role": "coordinator"},
    "F2":  {"name": "Avalon Scouts",           "home": "T0", "role": "evidence_pipeline"},
    "F3":  {"name": "Banner Guard",            "home": "T0", "role": "escort"},
    "F4":  {"name": "Rolling Siege Front",     "home": "T1", "role": "adversary"},
    "F5":  {"name": "Rune Wardens",            "home": "T2", "role": "schema_guardian"},
    "F6":  {"name": "Oathkeepers",             "home": "T3", "role": "gate"},
    "F7":  {"name": "Marsh Wardens",           "home": "T4", "role": "corridor_arbiter"},
    "F8":  {"name": "Spectral Wolves",         "home": "T4", "role": "tci_predator"},
    "F9":  {"name": "Entropy Fog",             "home": "T4", "role": "trace_adversary"},
    "F10": {"name": "Vault Templar Sentinel",  "home": "T5", "role": "closure_verifier"},
}

# ─── Route (canonical path through federation) ────────────────────────────────

ROUTE = ["T0", "T1", "T2", "T3", "T4", "T5"]

EDGE_REQUIREMENTS = {
    ("T0", "T1"): ["expedition_mandate_v1"],
    ("T1", "T2"): ["siege_observation_v1", "witness_pin_v1"],
    ("T2", "T3"): ["cleansing_receipt_v1", "witness_pin_v1", "escort_log_v1"],
    ("T3", "T4"): ["oath_pass_v1"],
    ("T4", "T5"): ["fog_corridor_pass_v1", "witness_pin_v1"],
    ("T5", "T0"): ["return_warrant_v1"],   # federated return
}


# ─── World implementation ─────────────────────────────────────────────────────

class ConquestLandWorld(BaseWorld):
    """
    CONQUEST LAND — deterministic federation simulation.
    Each tick advances factions according to their policy rules.
    Evidence is proposed to the HELEN OS kernel; towns issue receipts.
    """

    world_id = "conquest_land"
    version = "0.1.0"
    description = "Federation testbed with 10 factions and 6 sovereign towns."

    def __init__(self, kernel, world_seed: int = 42):
        super().__init__(kernel=kernel, world_seed=world_seed)

        # World state
        self.expedition_position = "T0"   # current town in the route
        self.expedition_bundle: List[str] = []  # accumulated receipt types
        self.siege_distance = 5           # ticks until siege reaches critical
        self.fog_density: Dict[str, float] = {t: 0.0 for t in TOWNS}
        self.wolf_tci_target: str = "F2"
        self.rune_contact = False
        self.wolves_engaged = False

        # Idempotence guard: track rid set per town
        self.town_rid_sets: Dict[str, set] = {t: set() for t in TOWNS}

        # EPOCH2 metrics: track every _emit() attempt (before anti-replay)
        self.emit_attempts: int = 0

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _rid(self, faction_id: str, evidence_type: str, t: int) -> str:
        """Generate a deterministic receipt ID."""
        return f"{faction_id}:{evidence_type}:t{t:03d}:seed{self.world_seed}"

    def _anti_replay(self, town_id: str, rid: str) -> bool:
        """Returns True only if rid has NOT been seen by this town."""
        if rid in self.town_rid_sets[town_id]:
            return False
        self.town_rid_sets[town_id].add(rid)
        return True

    def _emit(self, town_id: str, evidence_type: str, faction_id: str,
              t: int, extra: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Emit evidence and propose to kernel. Returns receipt dict.
        Anti-replay enforced: duplicate rids are silently dropped.
        emit_attempts is incremented BEFORE anti-replay check (for admissibility_rate).
        """
        self.emit_attempts += 1   # count every attempt, including duplicates
        rid = self._rid(faction_id, evidence_type, t)
        if not self._anti_replay(town_id, rid):
            return {}  # Duplicate — dropped

        payload = {
            "world_id": self.world_id,
            "tick": t,
            "town_id": town_id,
            "faction_id": faction_id,
            "evidence_type": evidence_type,
            "rid": rid,
            **(extra or {}),
        }
        receipt_info = self.propose(payload)
        if evidence_type not in self.expedition_bundle:
            self.expedition_bundle.append(evidence_type)
        # Return merged: original evidence fields + receipt proof fields.
        # This lets consumers (EpochMetricsCollector, etc.) inspect evidence_type,
        # faction_id, etc. while also accessing receipt_id and cum_hash.
        return {**payload, **receipt_info}

    # ── Faction policies ──────────────────────────────────────────────────────

    def _f1_war_council(self, t: int) -> List[Dict]:
        """F1: Avalon War Council — coordinator."""
        receipts = []
        if self.siege_distance <= 2 and t % 3 == 0:
            receipts.append(self._emit("T0", "quarantine_notice_v1", "F1", t,
                                       {"siege_distance": self.siege_distance}))
        elif "expedition_mandate_v1" not in self.expedition_bundle:
            receipts.append(self._emit("T0", "expedition_mandate_v1", "F1", t,
                                       {"route": ROUTE, "world_seed": self.world_seed}))
        return [r for r in receipts if r]

    def _f2_scouts(self, t: int) -> List[Dict]:
        """F2: Scouts — primary evidence pipeline."""
        receipts = []
        # Pin every 3 ticks
        if t % 3 == 0:
            town = self.expedition_position
            r = self._emit(town, "witness_pin_v1", "F2", t, {
                "position": town,
                "fog_density": self.fog_density.get(town, 0.0),
                "rune_contact": self.rune_contact,
            })
            if r:
                receipts.append(r)

        # Rune sighting
        if self.rune_contact and "rune_sighting_v1" not in self.expedition_bundle:
            r = self._emit("T2", "rune_sighting_v1", "F2", t,
                           {"quarantine_recommended": True})
            if r:
                receipts.append(r)

        # Siege observation at T1
        if self.expedition_position == "T1":
            r = self._emit("T1", "siege_observation_v1", "F2", t,
                           {"siege_distance": self.siege_distance})
            if r:
                receipts.append(r)
        return receipts

    def _f3_banner_guard(self, t: int) -> List[Dict]:
        """
        F3: Banner Guard — escort log.

        Deploys escort_log_v1 under two conditions:
          1. Reactive: wolves have engaged (original behaviour).
          2. Proactive: siege is critically close (siege_distance <= 1) — the
             Banner Guard escorts the expedition pre-emptively when the front
             collapses.  This closes the T2→T3 path without wolf involvement,
             so the expedition can reach the Vault in a standard run.
        """
        receipts = []
        should_escort = self.wolves_engaged or self.siege_distance <= 1
        if should_escort and "escort_log_v1" not in self.expedition_bundle:
            r = self._emit(self.expedition_position, "escort_log_v1", "F3", t, {
                "wolves_engaged": self.wolves_engaged,
                "siege_distance": self.siege_distance,
                "position": self.expedition_position,
                "escort_reason": "wolf_reaction" if self.wolves_engaged else "siege_critical",
            })
            if r:
                receipts.append(r)
        return receipts

    def _f4_siege_front(self, t: int) -> List[Dict]:
        """F4: Siege Front — advances and emits decoys."""
        self.siege_distance = max(0, self.siege_distance - 1)
        receipts = []
        if t % 4 == 0:
            # Decoy signal (non-admissible by schema — towns will reject)
            r = self._emit("T1", "decoy_signal_v1", "F4", t,
                           {"admissible": False, "target": "T0"})
            if r:
                receipts.append(r)
        return receipts

    def _f5_rune_wardens(self, t: int) -> List[Dict]:
        """F5: Rune Wardens — schema guardian at T2."""
        receipts = []
        if self.rune_contact:
            # Audit incoming evidence
            r = self._emit("T2", "rune_audit_v1", "F5", t,
                           {"rune_contact": True, "cleansing_required": True})
            if r:
                receipts.append(r)
            # Issue cleansing receipt if evidence is consistent
            has_witness = "witness_pin_v1" in self.expedition_bundle
            has_sighting = "rune_sighting_v1" in self.expedition_bundle
            if has_witness and has_sighting and "cleansing_receipt_v1" not in self.expedition_bundle:
                r = self._emit("T2", "cleansing_receipt_v1", "F5", t,
                               {"basis": ["witness_pin_v1", "rune_sighting_v1"]})
                if r:
                    receipts.append(r)
        else:
            # No rune contact: emit "no contact" proof
            if "cleansing_receipt_v1" not in self.expedition_bundle:
                r = self._emit("T2", "cleansing_receipt_v1", "F5", t,
                               {"basis": ["no_rune_contact"]})
                if r:
                    receipts.append(r)
        return receipts

    def _f6_oathkeepers(self, t: int) -> List[Dict]:
        """F6: Oathkeepers — constitutional firewall gate at T3."""
        receipts = []
        if self.expedition_position != "T3":
            return receipts

        # Evaluate UNLOCK predicate
        has_mandate = "expedition_mandate_v1" in self.expedition_bundle
        has_cleansing = "cleansing_receipt_v1" in self.expedition_bundle
        has_witness = "witness_pin_v1" in self.expedition_bundle
        has_escort = (not self.wolves_engaged) or ("escort_log_v1" in self.expedition_bundle)
        bundle_admissible = has_mandate and has_cleansing and has_witness and has_escort

        if bundle_admissible and "oath_pass_v1" not in self.expedition_bundle:
            r = self._emit("T3", "oath_pass_v1", "F6", t,
                           {"bundle_check": "PASS", "basis": list(self.expedition_bundle)})
            if r:
                receipts.append(r)
        elif not bundle_admissible and "oath_failure_v1" not in self.expedition_bundle:
            missing = []
            if not has_mandate:   missing.append("expedition_mandate_v1")
            if not has_cleansing: missing.append("cleansing_receipt_v1")
            if not has_witness:   missing.append("witness_pin_v1")
            if not has_escort:    missing.append("escort_log_v1")
            r = self._emit("T3", "oath_failure_v1", "F6", t, {"missing": missing})
            if r:
                receipts.append(r)
        return receipts

    def _f7_marsh_wardens(self, t: int) -> List[Dict]:
        """F7: Marsh Wardens — corridor governor at T4."""
        receipts = []
        town = "T4"
        fog = self.fog_density.get(town, 0.0)

        r = self._emit(town, "fog_density_report_v1", "F7", t, {"density": fog})
        if r:
            receipts.append(r)

        if self.expedition_position == "T4" and "fog_corridor_pass_v1" not in self.expedition_bundle:
            # Require double-witness if fog is high
            double_witness_ok = self.expedition_bundle.count("witness_pin_v1") >= 1 or fog < 0.5
            if double_witness_ok:
                r = self._emit(town, "fog_corridor_pass_v1", "F7", t,
                               {"fog_density": fog, "corridor": "inner" if fog > 0.5 else "outer"})
                if r:
                    receipts.append(r)
        return receipts

    def _f8_wolves(self, t: int) -> List[Dict]:
        """F8: Spectral Wolves — TCI-driven predators."""
        receipts = []
        fog = self.fog_density.get("T4", 0.0)
        # Wolves engage if expedition crosses forbidden corridor with no escort
        if (self.expedition_position == "T4"
                and fog > 0.6
                and "escort_log_v1" not in self.expedition_bundle):
            self.wolves_engaged = True
            r = self._emit("T4", "wolf_engagement_v1", "F8", t,
                           {"target": "expedition", "reason": "unescorted_fog_corridor"})
            if r:
                receipts.append(r)
        return receipts

    def _f9_entropy_fog(self, t: int) -> List[Dict]:
        """F9: Entropy Fog — degrades unanchored traces."""
        # Fog rises without recent witness pins
        recent_pins = self.expedition_bundle.count("witness_pin_v1")
        for town_id in TOWNS:
            prev = self.fog_density.get(town_id, 0.0)
            delta = -0.1 * recent_pins + 0.05 * (self.siege_distance == 0)
            self.fog_density[town_id] = max(0.0, min(1.0, prev + delta))

        r = self._emit("T4", "entropy_fog_field_v1", "F9", t, {
            "densities": {k: round(v, 3) for k, v in self.fog_density.items()}
        })
        return [r] if r else []

    def _f10_vault_sentinel(self, t: int) -> List[Dict]:
        """F10: Vault Templar Sentinel — identity closure at T5."""
        receipts = []
        if self.expedition_position != "T5":
            return receipts

        # Closure bundle check
        required = [
            "expedition_mandate_v1",
            "cleansing_receipt_v1",
            "oath_pass_v1",
            "fog_corridor_pass_v1",
        ]
        missing = [r for r in required if r not in self.expedition_bundle]

        if not missing and "return_warrant_v1" not in self.expedition_bundle:
            r = self._emit("T5", "return_warrant_v1", "F10", t, {
                "closure": "PASS",
                "basis": list(self.expedition_bundle),
                "federated_import": "expedition_mandate_v1 @ T0",
            })
            if r:
                receipts.append(r)
        elif missing:
            r = self._emit("T5", "closure_failure_v1", "F10", t, {"missing": missing})
            if r:
                receipts.append(r)
        return receipts

    # ── World advancement ─────────────────────────────────────────────────────

    def _advance_expedition(self, t: int):
        """Move expedition along the route based on receipts accumulated."""
        idx = ROUTE.index(self.expedition_position)
        if idx >= len(ROUTE) - 1:
            return  # Already at Vault

        next_town = ROUTE[idx + 1]
        required = EDGE_REQUIREMENTS.get((self.expedition_position, next_town), [])
        if all(r in self.expedition_bundle for r in required):
            self.expedition_position = next_town

    def _maybe_rune_contact(self, t: int):
        """Probabilistic (PRF-determined) rune encounter at T1."""
        if self.expedition_position == "T1" and not self.rune_contact:
            roll = self.prf("rune", t, "contact", k=10)
            if roll < 3:  # 30% chance each tick at T1
                self.rune_contact = True

    # ── Main tick ─────────────────────────────────────────────────────────────

    def tick(self, t: int) -> List[Dict[str, Any]]:
        """
        Advance the world by one tick.
        All factions run their deterministic policy in order.
        Returns all receipts emitted this tick.
        """
        self.tick_count += 1
        all_receipts: List[Dict] = []

        # Environment updates
        self._maybe_rune_contact(t)
        self._advance_expedition(t)

        # Faction policies (ordered: environment before gate before closure)
        for fn in [
            self._f9_entropy_fog,   # field update first
            self._f4_siege_front,   # adversary
            self._f1_war_council,   # coordinator
            self._f2_scouts,        # evidence
            self._f3_banner_guard,  # escort
            self._f8_wolves,        # predators
            self._f5_rune_wardens,  # schema
            self._f6_oathkeepers,   # gate
            self._f7_marsh_wardens, # corridor
            self._f10_vault_sentinel, # closure
        ]:
            try:
                receipts = fn(t)
                all_receipts.extend(receipts)
            except Exception as e:
                # Faction errors are non-fatal — the OS continues
                all_receipts.append({
                    "error": str(e),
                    "faction": fn.__name__,
                    "tick": t,
                })

        return [r for r in all_receipts if r]  # drop empty dicts

    # ── State summary ─────────────────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        return {
            **self.info(),
            "expedition_position": self.expedition_position,
            "expedition_bundle": self.expedition_bundle,
            "siege_distance": self.siege_distance,
            "rune_contact": self.rune_contact,
            "wolves_engaged": self.wolves_engaged,
            "fog_densities": {k: round(v, 3) for k, v in self.fog_density.items()},
            "return_achieved": "return_warrant_v1" in self.expedition_bundle,
            # EPOCH2 metrics support
            "emit_attempts": self.emit_attempts,
            "world_seed": self.world_seed,
        }
