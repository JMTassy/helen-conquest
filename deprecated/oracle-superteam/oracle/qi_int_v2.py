# oracle/qi_int_v2.py
from dataclasses import dataclass
from math import cos, sin
from oracle.config import OracleConfig

@dataclass(frozen=True)
class QIResult:
    A_re: float
    A_im: float
    S: float

def compute_qi_int_v2(claim_tier: str, votes: list, cfg: OracleConfig) -> QIResult:
    """
    Deterministic complex amplitude sum:
      a_{c,t} = r(tier) * exp(i theta(vote))
      A = sum_t w_t * a_{c,t}
      S = |A|^2
    KILL votes are excluded here (handled as override upstream).
    """
    r = cfg.tier_mag.get(claim_tier, 0.40)
    A_re, A_im = 0.0, 0.0

    for v in votes:
        team = v.get("team")
        vote = v.get("vote")
        if vote == "KILL":
            continue

        w = cfg.team_weights.get(team, 0.0)
        theta = cfg.vote_phase.get(vote, 0.0)

        a_re = r * cos(theta)
        a_im = r * sin(theta)

        A_re += w * a_re
        A_im += w * a_im

    S = A_re*A_re + A_im*A_im
    return QIResult(A_re, A_im, S)
