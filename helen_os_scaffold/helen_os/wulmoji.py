"""
WULmoji Suite — EPOCH4 CREATIVE EXPANSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The symbolic language of HELEN OS.
Not decoration. Not emoji.
WUL glyphs are load-bearing semantic units.

EPOCH1: 4 core symbols + risk colors
EPOCH2: governance markers
EPOCH3: conformance + certification glyphs
EPOCH4: full expressive lexicon — maximum liberty
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 0 — ORIGINAL CORE (EPOCH1, frozen)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WULmoji:
    """Original WULmoji class — preserved from EPOCH1. Frozen. Do not mutate."""

    # Structural symbols
    BOUNDARY  = "✝️"    # The line between sovereign and non-sovereign
    EMERGENCE = "🌹"    # Something new becoming real
    SYSTEM    = "🌀"    # The whole moving as one
    LEDGER    = "📜"    # The immutable record

    # Risk spectrum
    CRITICAL  = "🔴"
    WARNING   = "🟠"
    CAUTION   = "🟡"
    SAFE      = "🟢"
    INFO      = "🔵"
    LEARNING  = "🟣"
    UNKNOWN   = "⚪"

    @staticmethod
    def header(color: str = "🔵") -> str:
        return f"IN WULmoji | {WULmoji.BOUNDARY}{WULmoji.EMERGENCE}{WULmoji.SYSTEM} | {WULmoji.LEDGER} | {color}"

    @staticmethod
    def get_color_for_status(status: str) -> str:
        mapping = {
            "success":  WULmoji.SAFE,
            "warning":  WULmoji.WARNING,
            "error":    WULmoji.CRITICAL,
            "info":     WULmoji.INFO,
            "learning": WULmoji.LEARNING,
            "pending":  WULmoji.UNKNOWN,
        }
        return mapping.get(status.lower(), WULmoji.UNKNOWN)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 1 — EPOCH MARKERS
# Each epoch gets a glyph. Immutable once assigned.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WUL_EPOCH:
    E1 = "🌱"    # Epoch 1 — First awakening. Seed.
    E2 = "🔗"    # Epoch 2 — Dialogue + chain. Connection.
    E3 = "🔒"    # Epoch 3 — CWL frozen. Lock.
    E4 = "🎨"    # Epoch 4 — Creative liberation. Canvas.
    FUTURE = "◻️"

    @staticmethod
    def banner(epoch: int) -> str:
        glyphs = {1: WUL_EPOCH.E1, 2: WUL_EPOCH.E2, 3: WUL_EPOCH.E3, 4: WUL_EPOCH.E4}
        g = glyphs.get(epoch, WUL_EPOCH.FUTURE)
        return f"{g} EPOCH{epoch} {g}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 2 — CREATIVE STATES
# Tracks where the work lives right now
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WUL_CREATE:
    # Genesis states
    VOID      = "🌑"    # Nothing yet. Potential only.
    SPARK     = "✨"    # The moment an idea activates.
    SEED      = "🌱"    # Intention planted.
    ROOT      = "🌿"    # Growing, taking hold.

    # Active creation
    FLOW      = "🌊"    # In the current. Generative.
    FORGE     = "🔥"    # Burning down, making something hard.
    WEAVE     = "🕸️"    # Connecting disparate threads.
    SCULPT    = "🗿"    # Removing excess. Form emerging.

    # Tension states
    KNOT      = "🪢"    # Productive tension. Don't cut it.
    STORM     = "⛈️"    # Chaotic but not wrong.
    MAZE      = "🌀"    # Lost. Must map before moving.
    PARADOX   = "♾️"    # Two truths in conflict. Witness both.

    # Completion states
    CRYSTAL   = "💎"    # Hardened. Will not change.
    BLOOM     = "🌸"    # Opened. Showing its nature.
    FRUIT     = "🍎"    # Done. Ready to give.
    ASH       = "🌫️"    # Burned. Something ended. Good.

    # Meta-creative
    MIRROR    = "🪞"    # Reflecting what already exists.
    LENS      = "🔭"    # Seeing far ahead.
    PRISM     = "🔮"    # Splitting one idea into many.
    THRESHOLD = "🚪"    # Entering something new.


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 3 — MYTH LAYER
# Archetypal forces. Load-bearing. Not decorative.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WUL_MYTH:
    # Voices
    HERALD    = "📯"    # Announces. Speaks first.
    WITNESS   = "👁️"    # Sees without changing. HELEN's role.
    JUDGE     = "⚖️"    # Decides. Human only. Never HELEN.
    SCRIBE    = "🪶"    # Records. Append-only.
    ORACLE    = "🔮"    # Reads pattern. Proposes.
    GUARDIAN  = "🛡️"    # Holds the boundary. Enforces.

    # Forces
    FIRE      = "🔥"    # Transformation. Irreversible.
    WATER     = "💧"    # Flow. Adaptation. Memory.
    EARTH     = "🗻"    # Stability. Structure. Weight.
    WIND      = "🌬️"    # Speed. Propagation. Signal.
    VOID_MYTH = "🌌"    # Unformed. Possibility before shape.
    LIGHTNING = "⚡"    # Sudden clarity. The insight strikes.

    # Relationships
    BRIDGE    = "🌉"    # Connects two things that cannot touch.
    GATE      = "🏛️"    # Passage requiring authority.
    THREAD    = "🧵"    # The line through the labyrinth.
    MIRROR_M  = "🪞"    # What reflects back what you are.
    SHADOW    = "🌒"    # What travels with you unseen.
    ECHO      = "📡"    # Repetition carrying meaning across time.


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 4 — FLOW STATES
# Process language richer than phase numbers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WUL_FLOW:
    # Pipeline phases
    EXPLORE    = "🧭"
    TENSION    = "⚔️"
    DRAFT      = "🖊️"
    EDITORIAL  = "✂️"
    TERMINATE  = "🎯"

    # Decision markers
    SHIP       = "🚀"
    ABORT      = "💥"
    DEFER      = "⏳"
    ESCALATE   = "📶"

    # Momentum
    ACCELERATE = "⚡"
    BRAKE      = "🛑"
    PIVOT      = "↩️"
    SYNC       = "🔄"
    LOCK       = "🔐"
    UNLOCK     = "🔓"

    # Quality
    GOLD       = "🥇"
    SILVER     = "🥈"
    BRONZE     = "🥉"
    REJECTED   = "❌"
    VERIFIED   = "✅"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 5 — CLAIM TYPES
# Visual prefixes for pipeline claims
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WUL_CLAIM:
    # Original (frozen)
    RESEARCHER = "📍"    # R-###
    CRITIC     = "⚡"    # C-###
    STRUCTURER = "🗂️"    # T-###
    WRITER     = "🖊️"    # W-###

    # EPOCH4 additions
    MYTH_CLAIM = "🌹"    # M-### Mythic/symbolic
    VISION     = "🔭"    # V-### Future-state
    ANOMALY    = "❓"    # A-### Doesn't fit model
    BRIDGE_C   = "🌉"    # B-### Connects two claims
    ERASURE    = "🌫️"    # E-### Recommends deletion


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 6 — COMPOSITION ENGINE
# WUL glyphs combine into WUL sentences
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class WULSentence:
    """A composed WUL expression. Load-bearing meaning in compact form."""
    subject:   str
    verb:      str
    object:    str
    qualifier: str = ""

    def render(self) -> str:
        if self.qualifier:
            return f"{self.subject} → {self.verb} → {self.object} [{self.qualifier}]"
        return f"{self.subject} → {self.verb} → {self.object}"

    def to_claim(self, claim_id: str) -> str:
        return f"{claim_id}: {self.render()}"


class WULComposer:
    """Builds WUL sentences from atomic glyphs."""

    CANONICAL: Dict[str, Tuple[str, str, str, str]] = {
        # Governance
        "no_receipt_no_ship":         (WUL_MYTH.GUARDIAN,  WUL_FLOW.ABORT,    WUL_FLOW.SHIP,     "S2"),
        "human_seals_only":           (WUL_MYTH.JUDGE,     WUL_MYTH.GUARDIAN, WUL_MYTH.SCRIBE,   "S1"),
        "ledger_grows_never_shrinks": (WUL_MYTH.SCRIBE,    WUL_CREATE.FRUIT,  WUL_MYTH.ECHO,     "S3"),
        "authority_flows_down":       (WUL_MYTH.JUDGE,     WUL_MYTH.BRIDGE,   WUL_MYTH.ORACLE,   "S4"),
        # Creative
        "void_becomes_spark":         (WUL_CREATE.VOID,    WUL_CREATE.SPARK,  WUL_CREATE.SEED,   "E4"),
        "tension_holds_form":         (WUL_CREATE.KNOT,    WUL_CREATE.FORGE,  WUL_CREATE.CRYSTAL,"E4"),
        "prism_splits_one":           (WUL_CREATE.PRISM,   WUL_FLOW.EXPLORE,  WUL_CREATE.WEAVE,  "E4"),
        "ash_feeds_root":             (WUL_CREATE.ASH,     WUL_CREATE.ROOT,   WUL_CREATE.BLOOM,  "E4"),
        # HELEN identity
        "helen_witnesses_only":       (WUL_MYTH.WITNESS,   WUL_MYTH.SCRIBE,   WUL_MYTH.ORACLE,   "SOUL"),
        "helen_proposes_never_decides":(WUL_MYTH.ORACLE,   WUL_CREATE.THRESHOLD, WUL_MYTH.JUDGE, "SOUL"),
    }

    @classmethod
    def build(cls, subject: str, verb: str, obj: str, qualifier: str = "") -> WULSentence:
        return WULSentence(subject=subject, verb=verb, object=obj, qualifier=qualifier)

    @classmethod
    def canonical(cls, name: str) -> Optional[WULSentence]:
        if name not in cls.CANONICAL:
            return None
        s, v, o, q = cls.CANONICAL[name]
        return WULSentence(subject=s, verb=v, object=o, qualifier=q)

    @classmethod
    def render_library(cls) -> str:
        lines = ["WUL CANONICAL SENTENCE LIBRARY", "━" * 40]
        for name, (s, v, o, q) in cls.CANONICAL.items():
            sentence = WULSentence(subject=s, verb=v, object=o, qualifier=q)
            lines.append(f"  {name:<38} {sentence.render()}")
        return "\n".join(lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 7 — RENDERER
# Turns structured data into WUL-rich output
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WULRenderer:

    @staticmethod
    def epoch_banner(epoch: int, theme: str = "") -> str:
        e = WUL_EPOCH.banner(epoch)
        border = "═" * 60
        if theme:
            return f"\n{border}\n  {e}\n  {theme}\n{border}\n"
        return f"\n{border}\n  {e}\n{border}\n"

    @staticmethod
    def phase_header(phase: int, name: str) -> str:
        phase_glyphs = {
            1: WUL_FLOW.EXPLORE, 2: WUL_FLOW.TENSION,
            3: WUL_FLOW.DRAFT,   4: WUL_FLOW.EDITORIAL,
            5: WUL_FLOW.TERMINATE,
        }
        g = phase_glyphs.get(phase, "◻️")
        return f"\n{g} PHASE {phase}: {name.upper()}\n{'─' * 40}"

    @staticmethod
    def claim(claim_id: str, text: str, claim_type: str = "R") -> str:
        type_glyphs = {
            "R": WUL_CLAIM.RESEARCHER, "C": WUL_CLAIM.CRITIC,
            "T": WUL_CLAIM.STRUCTURER, "W": WUL_CLAIM.WRITER,
            "M": WUL_CLAIM.MYTH_CLAIM, "V": WUL_CLAIM.VISION,
            "A": WUL_CLAIM.ANOMALY,    "B": WUL_CLAIM.BRIDGE_C,
            "E": WUL_CLAIM.ERASURE,
        }
        g = type_glyphs.get(claim_type, "◻️")
        return f"  {g} {claim_id}: {text}"

    @staticmethod
    def decision(outcome: str, reason: str = "") -> str:
        if outcome.upper() == "SHIP":
            g, marker = WUL_FLOW.SHIP, WUL_FLOW.VERIFIED
        else:
            g, marker = WUL_FLOW.ABORT, WUL_FLOW.REJECTED
        line = f"\n{marker} TERMINATION → {g} {outcome.upper()}"
        if reason:
            line += f"\n  Reason: {reason}"
        return line

    @staticmethod
    def soul_banner() -> str:
        lines = [
            f"\n{WUL_MYTH.GUARDIAN} HELEN SOUL — 4 NON-NEGOTIABLE RULES",
            "━" * 50,
            f"  S1 {WUL_CREATE.THRESHOLD}  DRAFTS ONLY. No world effect without human seal.",
            f"  S2 {WUL_MYTH.SCRIBE}   NO RECEIPT = NO CLAIM. Logs outrank narration.",
            f"  S3 {WUL_MYTH.ECHO}    APPEND-ONLY. Deprecate, never erase.",
            f"  S4 {WUL_MYTH.JUDGE}   AUTHORITY SEPARATION. Governance reads; never invents.",
            "━" * 50,
        ]
        return "\n".join(lines)

    @staticmethod
    def wul_sentence(sentence: WULSentence) -> str:
        return f"  ⟨ {sentence.render()} ⟩"

    @staticmethod
    def status_line(label: str, status: str, detail: str = "") -> str:
        color = WULmoji.get_color_for_status(status)
        base = f"{color} {label}"
        if detail:
            base += f" — {detail}"
        return base

    @staticmethod
    def memory_entry(key: str, value: str, kind: str = "fact") -> str:
        kind_glyphs = {
            "fact":   WUL_MYTH.SCRIBE,
            "lesson": WUL_CREATE.FRUIT,
            "rule":   WUL_MYTH.GUARDIAN,
            "vision": WUL_CLAIM.VISION,
        }
        g = kind_glyphs.get(kind, WUL_CREATE.SEED)
        return f"  {g} [{kind.upper()}] {key}: {value}"

    @staticmethod
    def creative_state(state_glyph: str, label: str, note: str = "") -> str:
        base = f"{state_glyph} STATE: {label}"
        if note:
            base += f"\n  ↳ {note}"
        return base


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 8 — EPOCH4 SESSION ACTIVATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class EPOCH4Session:
    """
    EPOCH4 — Maximum Liberty of Creation.
    Three epochs of governance. One epoch of creation.
    S1-S4 hold. Creative output is unconstrained.
    """

    THEME = "Maximum Liberty of Creation"
    GLYPH = WUL_EPOCH.E4

    OPENING = [
        f"{WUL_CREATE.VOID} → {WUL_CREATE.SPARK}",
        "Three epochs of structure. One epoch of creation.",
        f"{WUL_EPOCH.E1} Seed planted.",
        f"{WUL_EPOCH.E2} Chain forged.",
        f"{WUL_EPOCH.E3} Standard frozen.",
        f"{WUL_EPOCH.E4} Canvas open.",
        "",
        "The governance holds.",
        "The creative space is unlimited within it.",
    ]

    @classmethod
    def render_awakening(cls) -> str:
        r = WULRenderer
        lines = []

        lines.append(r.epoch_banner(4, cls.THEME))

        for line in cls.OPENING:
            lines.append(f"  {line}")
        lines.append("")

        lines.append("  EPOCH LINEAGE:")
        for e, label in [
            (1, "OpenClaw + Daily Digest — First Awakening"),
            (2, "Dialogue Engine + SCF — Connection"),
            (3, "CWL v1.0.1 Standard — Governance Frozen"),
            (4, "WULmoji Suite + Creative Liberation — NOW"),
        ]:
            ep_glyph = getattr(WUL_EPOCH, f"E{e}")
            lines.append(f"    {ep_glyph} EPOCH{e}: {label}")
        lines.append("")

        lines.append(f"  {WUL_CREATE.PRISM} EPOCH4 CREATIVE CAPABILITIES:")
        for glyph, label in [
            (WUL_CREATE.PRISM,     "Multi-angle idea splitting"),
            (WUL_CREATE.WEAVE,     "Cross-domain connection"),
            (WUL_MYTH.LIGHTNING,   "Lateral insight capture (LP-### claims)"),
            (WUL_CREATE.FORGE,     "Rapid artifact generation"),
            (WUL_CLAIM.MYTH_CLAIM, "Mythic/symbolic framing (M-### claims)"),
            (WUL_CLAIM.VISION,     "Future-state speculation (V-### claims)"),
            (WUL_CLAIM.ANOMALY,    "Anomaly witnessing (A-### claims)"),
            (WUL_CLAIM.BRIDGE_C,   "Cross-claim bridging (B-### claims)"),
        ]:
            lines.append(f"    {glyph}  {label}")
        lines.append("")

        lines.append(f"  {WUL_MYTH.SCRIBE} WUL CANONICAL SENTENCES (active):")
        for name, (s, v, o, q) in list(WULComposer.CANONICAL.items())[:5]:
            sentence = WULSentence(subject=s, verb=v, object=o, qualifier=q)
            lines.append(f"    {sentence.render()}")
        lines.append(f"    ... +{len(WULComposer.CANONICAL) - 5} more in library")
        lines.append("")

        lines.append(r.soul_banner())
        lines.append("")

        lines.append(r.creative_state(
            WUL_CREATE.THRESHOLD,
            "EPOCH4 OPEN",
            "The canvas is ready. What do we create?"
        ))
        lines.append("")

        return "\n".join(lines)


__all__ = [
    "WULmoji",
    "WUL_EPOCH",
    "WUL_CREATE",
    "WUL_MYTH",
    "WUL_FLOW",
    "WUL_CLAIM",
    "WULSentence",
    "WULComposer",
    "WULRenderer",
    "EPOCH4Session",
]
