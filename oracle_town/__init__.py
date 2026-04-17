"""
ORACLE TOWN - Hierarchical Multi-Agent Governance System

A scalable, constitutional framework for transforming natural language inputs
into verified, shippable claims through civic simulation structure.

Architecture:
INPUT → CLAIM → STREETS → BUILDINGS → DISTRICTS → TOWN HALL → MAYOR → VERDICT

Combines:
- ChatDev: Structured turn protocol, orthogonal roles
- AI Town: Spatial simulation, emergent behaviors
- ORACLE SUPERTEAM: Constitutional governance, binary verdicts
"""

__version__ = "1.0.0"
__author__ = "ORACLE TOWN Team"

from .core.orchestrator import OracleTownOrchestrator, District, process_text
from .core.claim_compiler import ClaimCompiler
from .core.town_hall import TownHallAgent
from .core.mayor import MayorAgent
from .schemas import (
    TownInput,
    CompiledClaim,
    Obligation,
    Turn,
    StreetReport,
    BuildingBrief,
    DistrictVerdict,
    TownRecommendation,
    MayorVerdict,
    RemediationStep,
)

__all__ = [
    "OracleTownOrchestrator",
    "District",
    "process_text",
    "ClaimCompiler",
    "TownHallAgent",
    "MayorAgent",
    "TownInput",
    "CompiledClaim",
    "Obligation",
    "Turn",
    "StreetReport",
    "BuildingBrief",
    "DistrictVerdict",
    "TownRecommendation",
    "MayorVerdict",
    "RemediationStep",
]
