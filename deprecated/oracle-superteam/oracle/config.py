# oracle/config.py
from dataclasses import dataclass
from math import pi

@dataclass(frozen=True)
class OracleConfig:
    qi_int_version: str = "v2"
    tau_accept: float = 0.75
    tau_quarantine: float = 0.4

    # Vote -> phase (theta)
    vote_phase = {
        "APPROVE": 0.0,
        "CONDITIONAL": pi/4,
        "OBJECT": pi/2,
        "QUARANTINE": 3*pi/4,
        "REJECT": pi,
        # KILL handled separately (override)
    }

    # Tier -> magnitude (r)
    tier_mag = {
        "Tier I": 1.00,
        "Tier II": 0.70,
        "Tier III": 0.40,
    }

    # Team weights (w_t) — must be declared + pinned for replay
    team_weights = {
        "Legal Office": 1.00,        # kill-switch
        "Security Sector": 1.00,     # kill-switch
        "Engineering Wing": 0.85,
        "Data Validation Office": 0.80,
        "COO HQ": 0.75,
        "UX/Impact Bureau": 0.70,
        "Strategy HQ": 0.65,
    }

    # Kill-switch teams
    kill_switch_teams = {"Legal Office", "Security Sector"}

    # Canonical hashing exclusions
    exclude_from_hash = {
        "run_id",
        "timestamp_start",
        "timestamp_end",
        "votes[].timestamp",
        "event_log[].t",
    }

    # Deadlock policy
    max_resolution_cycles: int = 3
