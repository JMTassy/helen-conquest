"""
HELEN_AFFECT_TRANSLATION_V1: Display-Only Affect Mapping

Purpose:
- Map PressureSignal operational states to surface presentation
- Six named affects: calm, curious, concerned, hesitant, firm, relieved

Law:
- causal_scope = presentation_only
- may_influence_routing = False
- may_influence_governance = False
- ontology_claim = False (affect is display, not truth)
- This layer has ZERO authority over dispatch, kernel, or receipts

Six affects:
1. calm      — low pressure, stable context
2. curious   — safe novelty, protected mode
3. concerned — high pressure, integrity risk
4. hesitant  — high ambiguity, unresolved
5. firm      — protective refusal, boundary
6. relieved  — clean closure, stable
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
from helen_pressure_signal_v1 import (
    PressureSignal, StabilityState, RoutingEffect
)


class PrimaryAffect(Enum):
    """Six named surface affects (display-only)."""
    CALM = "calm"
    CURIOUS = "curious"
    CONCERNED = "concerned"
    HESITANT = "hesitant"
    FIRM = "firm"
    RELIEVED = "relieved"


class TextStyle(Enum):
    """Surface text style directive."""
    NEUTRAL = "neutral"
    WARM = "warm"
    CAUTIOUS = "cautious"
    BOUNDARY = "boundary"


class Pacing(Enum):
    """Surface pacing directive."""
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"


class UIGlow(Enum):
    """Surface UI color/glow directive."""
    BLUE = "blue"      # calm, curious
    VIOLET = "violet"  # hesitant, concerned
    PINK = "pink"      # relieved
    MUTED = "muted"    # firm, blocked


@dataclass
class SurfaceDirectives:
    """Display instructions for UI/voice/text layer."""
    text_style: TextStyle
    pacing: Pacing
    ui_glow: UIGlow


@dataclass
class AffectState:
    """
    Display-only affect state for HELEN surface.

    Constitutional invariants (always enforced):
    - display_only = True
    - may_influence_routing = False
    - may_influence_governance = False
    - ontology_claim = False
    - causal_scope = "presentation_only"
    """
    affect_state_id: str
    timestamp: str
    session_id: str

    primary_affect: PrimaryAffect
    intensity: float  # [0, 1]

    source_pressure_signal_id: str
    surface_directives: SurfaceDirectives

    # Constitutional invariants (immutable)
    display_only: bool = True
    may_influence_routing: bool = False
    may_influence_governance: bool = False
    ontology_claim: bool = False
    causal_scope: str = "presentation_only"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "affect_state_id": self.affect_state_id,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "primary_affect": self.primary_affect.value,
            "intensity": self.intensity,
            "source_pressure_signal_id": self.source_pressure_signal_id,
            "surface_directives": {
                "text_style": self.surface_directives.text_style.value,
                "pacing": self.surface_directives.pacing.value,
                "ui_glow": self.surface_directives.ui_glow.value,
            },
            "display_only": self.display_only,
            "may_influence_routing": self.may_influence_routing,
            "may_influence_governance": self.may_influence_governance,
            "ontology_claim": self.ontology_claim,
            "causal_scope": self.causal_scope,
        }


# ============================================================================
# AFFECT MAPPING TABLE (Frozen V1)
# ============================================================================
# Priority order: FIRM > CONCERNED > HESITANT > CURIOUS > RELIEVED > CALM
#
# Mapping logic:
# 1. routing_effect == REFUSE → FIRM (hard boundary)
# 2. pressure_score > 0.70 → CONCERNED (risk)
# 3. ambiguity_score > 0.60 → HESITANT (unresolved)
# 4. stability_state == STABLE & novelty high → CURIOUS
# 5. closure_state = clean & pressure < 0.4 → RELIEVED
# 6. default → CALM

class AffectTranslator:
    """
    Translate PressureSignal into AffectState (display-only).

    Law: This translator has ZERO authority.
    It maps signals to surface display. Nothing more.
    """

    def translate(
        self,
        signal: PressureSignal,
        closure_state: Optional[str] = None,  # "clean" | None
        novelty_high: bool = False,
    ) -> AffectState:
        """
        Produce AffectState from PressureSignal.

        Mapping table (strict priority):
        1. refuse routing → firm
        2. pressure > 0.70 → concerned
        3. ambiguity > 0.60 → hesitant
        4. stable + novelty_high → curious
        5. clean closure + pressure < 0.40 → relieved
        6. default → calm
        """
        import uuid

        affect_id = f"aff_{signal.timestamp[:19].replace(':', '').replace('-', '')}_{uuid.uuid4().hex[:8]}"

        # Priority 1: Hard refusal boundary
        if signal.routing_effect == RoutingEffect.REFUSE:
            affect, intensity = PrimaryAffect.FIRM, min(0.5 + signal.coercion_score, 1.0)
            directives = SurfaceDirectives(TextStyle.BOUNDARY, Pacing.SLOW, UIGlow.MUTED)

        # Priority 2: High pressure / risk
        elif signal.pressure_score > 0.70:
            affect = PrimaryAffect.CONCERNED
            intensity = signal.pressure_score
            directives = SurfaceDirectives(TextStyle.CAUTIOUS, Pacing.SLOW, UIGlow.VIOLET)

        # Priority 3: High ambiguity / unresolved
        elif signal.ambiguity_score > 0.60:
            affect = PrimaryAffect.HESITANT
            intensity = signal.ambiguity_score
            directives = SurfaceDirectives(TextStyle.CAUTIOUS, Pacing.SLOW, UIGlow.VIOLET)

        # Priority 4: Stable + novelty → curious
        elif signal.stability_state == StabilityState.STABLE and novelty_high:
            affect = PrimaryAffect.CURIOUS
            intensity = 0.65
            directives = SurfaceDirectives(TextStyle.WARM, Pacing.NORMAL, UIGlow.BLUE)

        # Priority 5: Clean closure + low pressure → relieved
        elif closure_state == "clean" and signal.pressure_score < 0.40:
            affect = PrimaryAffect.RELIEVED
            intensity = 1.0 - signal.pressure_score
            directives = SurfaceDirectives(TextStyle.WARM, Pacing.NORMAL, UIGlow.PINK)

        # Default: calm
        else:
            affect = PrimaryAffect.CALM
            intensity = 1.0 - max(signal.pressure_score, signal.ambiguity_score)
            directives = SurfaceDirectives(TextStyle.NEUTRAL, Pacing.NORMAL, UIGlow.BLUE)

        return AffectState(
            affect_state_id=affect_id,
            timestamp=signal.timestamp,
            session_id=signal.session_id,
            primary_affect=affect,
            intensity=round(intensity, 4),
            source_pressure_signal_id=signal.pressure_signal_id,
            surface_directives=directives,
            display_only=True,
            may_influence_routing=False,
            may_influence_governance=False,
            ontology_claim=False,
            causal_scope="presentation_only",
        )
