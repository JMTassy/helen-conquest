#!/usr/bin/env python3
"""
HELEN Oracle Hexagram Engine
=============================

SAVE_CORRECTED_THEN_SCAN

authority: NON_SOVEREIGN
canon: NO_SHIP
lifecycle: PROPOSAL

Trust:   unicode glyphs ䷀–䷿ + King Wen sequence (deterministic)
Distrust: pasted trigram-pair annotations (upstream_drift_detected)

Builds the corrected 64-hexagram corpus deterministically.
Runs pattern scans. Outputs JSON + markdown receipt table.

No mystical claims. No canon promotion. No commit. No push.

Do not decorate the water. Clean the well.

Usage:
  python3 tools/oracle_hexagram_engine.py save     # build + save corrected corpus
  python3 tools/oracle_hexagram_engine.py scan      # run pattern scan
  python3 tools/oracle_hexagram_engine.py both      # save + scan (SAVE_CORRECTED_THEN_SCAN)
  python3 tools/oracle_hexagram_engine.py receipt   # print receipt table
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Paths ──────────────────────────────────────────────────────────────────────

_REPO_ROOT   = Path(__file__).parent.parent
_OUT_JSON    = _REPO_ROOT / "artifacts" / "hexagram_corpus_corrected.json"
_OUT_SCAN    = _REPO_ROOT / "artifacts" / "hexagram_pattern_scan.md"
_GLYPH_BASE  = 0x4DC0   # U+4DC0 = ䷀ (hexagram 1, King Wen)

# ── ANSI ───────────────────────────────────────────────────────────────────────

RESET   = "\x1b[0m"
DIM     = "\x1b[2m"
CYAN    = "\x1b[36m"
GREEN   = "\x1b[32m"
YELLOW  = "\x1b[33m"
MAGENTA = "\x1b[35m"
BLUE    = "\x1b[34m"
BOLD    = "\x1b[1m"

_MODE_COLOR = {
    "FOCUS":   GREEN,
    "WITNESS": YELLOW,
    "ORACLE":  CYAN,
    "TEMPLE":  MAGENTA,
}


# ── Trigram definitions ────────────────────────────────────────────────────────
#
# Binary encoding (Fuxi / Earlier Heaven convention):
#   bit 0 (LSB) = bottom line
#   bit 1       = middle line
#   bit 2       = top line
#   yang = 1, yin = 0
#
# Index 0–7 ordered by binary value (0b000 → 0b111).

@dataclass
class Trigram:
    idx: int          # 0–7
    binary: int       # 0–7 (3-bit Fuxi value)
    symbol: str       # Unicode trigram symbol
    name_zh: str      # Chinese name
    name_en: str      # English name
    element: str      # natural element
    quality: str      # descriptive quality
    helen_mode: str   # FOCUS | WITNESS | ORACLE | TEMPLE


_TRIGRAMS: List[Trigram] = [
    Trigram(0, 0b000, "☷", "Kūn",   "Earth",    "Earth",    "receptive, yielding, nourishing",    "TEMPLE"),
    Trigram(1, 0b001, "☶", "Gèn",   "Mountain", "Mountain", "keeping still, holding, stopping",   "WITNESS"),
    Trigram(2, 0b010, "☵", "Kǎn",   "Water",    "Water",    "abysmal, dangerous, depth, testing", "WITNESS"),
    Trigram(3, 0b011, "☴", "Xùn",   "Wind",     "Wind/Wood","gentle, penetrating, insight",       "ORACLE"),
    Trigram(4, 0b100, "☳", "Zhèn",  "Thunder",  "Thunder",  "arousing, movement, action",         "FOCUS"),
    Trigram(5, 0b101, "☲", "Lí",    "Fire",     "Fire",     "clinging, clarity, illumination",    "ORACLE"),
    Trigram(6, 0b110, "☱", "Duì",   "Lake",     "Lake",     "joyous, expressive, open",           "TEMPLE"),
    Trigram(7, 0b111, "☰", "Qián",  "Heaven",   "Heaven",   "creative, strong, initiating",       "FOCUS"),
]

_TRIGRAM_BY_IDX: Dict[int, Trigram] = {t.idx: t for t in _TRIGRAMS}


# ── King Wen sequence ──────────────────────────────────────────────────────────
#
# Each entry: (upper_trigram_idx, lower_trigram_idx, name_zh, name_en, keywords)
# Source: deterministic King Wen canonical sequence.
# Upper trigram = outer / lines 4-6.
# Lower trigram = inner / lines 1-3.
# This is the CORRECTED source. Pasted annotations were not used.

_KW_SEQUENCE: List[Tuple[int, int, str, str, str]] = [
    (7, 7, "乾",  "Qián",     "Creative Heaven, strength, initiative"),          # 1
    (0, 0, "坤",  "Kūn",      "Receptive Earth, yielding, devotion"),            # 2
    (2, 4, "屯",  "Zhūn",     "Difficulty at the beginning, sprouting"),         # 3
    (1, 2, "蒙",  "Méng",     "Youthful folly, learning, confusion"),            # 4
    (2, 7, "需",  "Xū",       "Waiting, nourishment, patience"),                 # 5
    (7, 2, "訟",  "Sòng",     "Conflict, contention, caution"),                  # 6
    (0, 2, "師",  "Shī",      "The Army, discipline, collective"),               # 7
    (2, 0, "比",  "Bǐ",       "Holding together, union, alliance"),              # 8
    (3, 7, "小畜","Xiǎo Chù", "Small taming, restraint, gentle persistence"),    # 9
    (7, 6, "履",  "Lǚ",       "Treading carefully, conduct, propriety"),         # 10
    (0, 7, "泰",  "Tài",      "Peace, harmony, equilibrium"),                    # 11
    (7, 0, "否",  "Pǐ",       "Standstill, stagnation, blockage"),               # 12
    (7, 5, "同人","Tóng Rén",  "Fellowship, community, common cause"),            # 13
    (5, 7, "大有","Dà Yǒu",   "Great possession, abundance, clarity"),           # 14
    (0, 1, "謙",  "Qiān",     "Modesty, humility, restraint"),                   # 15
    (4, 0, "豫",  "Yù",       "Enthusiasm, readiness, delight"),                 # 16
    (6, 4, "隨",  "Suí",      "Following, adaptability, response"),              # 17
    (1, 3, "蠱",  "Gǔ",       "Work on what is spoiled, repair, correction"),    # 18
    (0, 6, "臨",  "Lín",      "Approach, nearing, oversight"),                   # 19
    (3, 0, "觀",  "Guān",     "Contemplation, observation, perspective"),        # 20
    (5, 4, "噬嗑","Shì Kè",   "Biting through, clarity by force, decision"),     # 21
    (1, 5, "賁",  "Bì",       "Grace, adornment, aesthetic form"),               # 22
    (1, 0, "剝",  "Bō",       "Splitting apart, decay, erosion"),                # 23
    (0, 4, "復",  "Fù",       "Return, turning point, renewal"),                 # 24
    (7, 4, "無妄","Wú Wàng",  "Innocence, unexpected, without error"),           # 25
    (1, 7, "大畜","Dà Chù",   "Great taming, accumulation, restraint of power"), # 26
    (1, 4, "頤",  "Yí",       "Nourishment, providing, careful feeding"),        # 27
    (6, 3, "大過","Dà Guò",   "Great excess, critical mass, overload"),          # 28
    (2, 2, "坎",  "Kǎn",      "Abysmal water, repeated danger, endurance"),      # 29
    (5, 5, "離",  "Lí",       "Clinging fire, clarity, illumination"),           # 30
    (6, 1, "咸",  "Xián",     "Influence, attraction, mutual resonance"),        # 31
    (4, 3, "恆",  "Héng",     "Duration, perseverance, consistency"),            # 32
    (7, 1, "遯",  "Dùn",      "Retreat, strategic withdrawal, timing"),          # 33
    (4, 7, "大壯","Dà Zhuàng","Great power, vigour, strength in motion"),        # 34
    (5, 0, "晉",  "Jìn",      "Progress, advance, rising clarity"),              # 35
    (0, 5, "明夷","Míng Yí",  "Darkening of the light, concealment, endurance"), # 36
    (3, 5, "家人","Jiā Rén",  "The family, roles, inner order"),                 # 37
    (5, 6, "睽",  "Kuí",      "Opposition, difference, divergence"),             # 38
    (2, 1, "蹇",  "Jiǎn",     "Obstruction, obstacle, seeking help"),            # 39
    (4, 2, "解",  "Xiè",      "Deliverance, release, resolution"),               # 40
    (1, 6, "損",  "Sǔn",      "Decrease, reduction, simplification"),            # 41
    (3, 4, "益",  "Yì",       "Increase, benefit, growth"),                      # 42
    (6, 7, "夬",  "Guài",     "Breakthrough, resolution, decisive action"),      # 43
    (7, 3, "姤",  "Gòu",      "Coming to meet, unexpected encounter"),           # 44
    (6, 0, "萃",  "Cuì",      "Gathering together, convergence"),                # 45
    (0, 3, "升",  "Shēng",    "Pushing upward, gradual ascent"),                 # 46
    (6, 2, "困",  "Kùn",      "Oppression, exhaustion, constraint"),             # 47
    (2, 3, "井",  "Jǐng",     "The well, source, constant nourishment"),         # 48
    (6, 5, "革",  "Gé",       "Revolution, transformation, change"),             # 49
    (5, 3, "鼎",  "Dǐng",     "The cauldron, transformation, refinement"),       # 50
    (4, 4, "震",  "Zhèn",     "The arousing thunder, shock, awakening"),         # 51
    (1, 1, "艮",  "Gèn",      "Keeping still, meditation, stopping"),            # 52
    (3, 1, "漸",  "Jiàn",     "Development, gradual progress, step by step"),    # 53
    (4, 6, "歸妹","Guī Mèi",  "The marrying maiden, relationship, transition"),  # 54
    (4, 5, "豐",  "Fēng",     "Abundance, fullness, peak moment"),               # 55
    (5, 1, "旅",  "Lǚ",       "The wanderer, travel, impermanence"),             # 56
    (3, 3, "巽",  "Xùn",      "The gentle wind, penetration, subtle influence"), # 57
    (6, 6, "兌",  "Duì",      "The joyous lake, openness, exchange"),            # 58
    (3, 2, "渙",  "Huàn",     "Dispersion, dissolution, scattering"),            # 59
    (2, 6, "節",  "Jié",      "Limitation, regulation, measure"),                # 60
    (3, 6, "中孚","Zhōng Fú", "Inner truth, sincerity, resonance"),              # 61
    (4, 1, "小過","Xiǎo Guò", "Small excess, minor transgression, care"),        # 62
    (2, 5, "既濟","Jì Jì",    "After completion, fulfillment, integration"),     # 63
    (5, 2, "未濟","Wèi Jì",   "Before completion, unfinished, continuity"),      # 64
]


# ── Hexagram model ─────────────────────────────────────────────────────────────

@dataclass
class Hexagram:
    king_wen_id: int          # 1–64
    glyph: str                # Unicode glyph ䷀–䷿
    glyph_codepoint: str      # U+4DC0 + offset
    binary_6bit: int          # 0–63 (lower 3 bits = lower trigram, upper 3 = upper)
    binary_str: str           # "000000"–"111111" (bit5..bit0, top to bottom)
    upper_trigram: Trigram
    lower_trigram: Trigram
    name_zh: str
    name_pinyin: str
    keywords: str
    helen_mode: str           # derived from dominant trigram signal
    tension: bool             # True if upper and lower are in different HELEN mode families
    tension_note: str         # human-readable tension description
    yin_count: int            # number of yin lines (0–6)
    yang_count: int           # number of yang lines (0–6)
    yin_yang_ratio: str       # "Y:N" format


def _build_hexagram(
    king_wen_id: int,
    upper_idx: int,
    lower_idx: int,
    name_zh: str,
    name_pinyin: str,
    keywords: str,
) -> Hexagram:
    upper = _TRIGRAM_BY_IDX[upper_idx]
    lower = _TRIGRAM_BY_IDX[lower_idx]

    # 6-bit binary: upper trigram occupies bits 3-5, lower trigram bits 0-2
    binary_6bit = (upper.binary << 3) | lower.binary

    # Binary string: bit5 (top) → bit0 (bottom), yang=1 yin=0
    binary_str = format(binary_6bit, "06b")

    # Yin/yang counts
    yang_count = bin(binary_6bit).count("1")
    yin_count  = 6 - yang_count

    # Unicode glyph: King Wen order maps directly to U+4DC0 + (king_wen_id - 1)
    codepoint = _GLYPH_BASE + (king_wen_id - 1)
    glyph = chr(codepoint)
    glyph_cp = f"U+{codepoint:04X}"

    # HELEN mode: upper (outer expression) is primary signal
    # Tie-breaking: if upper and lower are same family → pure mode
    # Different families → tension; mode from upper
    helen_mode = upper.helen_mode
    tension = upper.helen_mode != lower.helen_mode
    if tension:
        tension_note = (
            f"outer={upper.helen_mode}({upper.name_en}) "
            f"/ inner={lower.helen_mode}({lower.name_en})"
        )
    else:
        tension_note = ""

    return Hexagram(
        king_wen_id=king_wen_id,
        glyph=glyph,
        glyph_codepoint=glyph_cp,
        binary_6bit=binary_6bit,
        binary_str=binary_str,
        upper_trigram=upper,
        lower_trigram=lower,
        name_zh=name_zh,
        name_pinyin=name_pinyin,
        keywords=keywords,
        helen_mode=helen_mode,
        tension=tension,
        tension_note=tension_note,
        yin_count=yin_count,
        yang_count=yang_count,
        yin_yang_ratio=f"{yang_count}:{yin_count}",
    )


def build_corpus() -> List[Hexagram]:
    """Build the corrected 64-hexagram corpus deterministically from King Wen sequence."""
    corpus = []
    for i, (upper_idx, lower_idx, name_zh, name_pinyin, keywords) in enumerate(
        _KW_SEQUENCE, start=1
    ):
        corpus.append(
            _build_hexagram(i, upper_idx, lower_idx, name_zh, name_pinyin, keywords)
        )
    return corpus


# ── Pattern scan ───────────────────────────────────────────────────────────────

@dataclass
class PatternScan:
    total_hexagrams: int
    mode_distribution: Dict[str, int]
    trigram_frequency: Dict[str, int]    # name_en → count (upper+lower combined)
    yin_yang_distribution: Dict[str, int]  # "Y:N" → count
    pure_mode_hexagrams: int             # upper == lower mode family
    tension_hexagrams: int               # upper != lower mode family
    opposition_pairs: List[Tuple[int, int]]    # (id_a, id_b) where binaries are bitwise complement
    sequence_neighbors: List[Tuple[int, int, int, str]]  # (id, binary, neighbor_binary, diff)
    single_flip_transitions: Dict[int, List[int]]  # hex_id → [ids reachable by one line flip]
    pure_trigram_hexagrams: List[int]    # hexagrams where upper == lower trigram


def scan_corpus(corpus: List[Hexagram]) -> PatternScan:
    from collections import Counter, defaultdict

    mode_counts: Counter = Counter()
    trigram_freq: Counter = Counter()
    yin_yang_dist: Counter = Counter()
    pure_count = 0
    tension_count = 0
    pure_trigram = []

    for h in corpus:
        mode_counts[h.helen_mode] += 1
        trigram_freq[h.upper_trigram.name_en] += 1
        trigram_freq[h.lower_trigram.name_en] += 1
        yin_yang_dist[h.yin_yang_ratio] += 1
        if not h.tension:
            pure_count += 1
        else:
            tension_count += 1
        if h.upper_trigram.idx == h.lower_trigram.idx:
            pure_trigram.append(h.king_wen_id)

    # Opposition pairs: two hexagrams whose 6-bit binaries are bitwise complements (sum = 63)
    binary_to_id = {h.binary_6bit: h.king_wen_id for h in corpus}
    opposition_pairs = []
    seen = set()
    for h in corpus:
        complement = (~h.binary_6bit) & 0b111111
        if complement in binary_to_id:
            pair = tuple(sorted([h.king_wen_id, binary_to_id[complement]]))
            if pair not in seen and pair[0] != pair[1]:
                opposition_pairs.append(pair)
                seen.add(pair)

    # Sequence neighbors: adjacent King Wen hexagrams and their binary distance
    neighbors = []
    for i in range(len(corpus) - 1):
        a = corpus[i]
        b = corpus[i + 1]
        diff_bits = bin(a.binary_6bit ^ b.binary_6bit).count("1")
        neighbors.append((a.king_wen_id, a.binary_6bit, b.binary_6bit, f"{diff_bits} line(s) differ"))

    # Single-line flip transitions: for each hexagram, which hexagrams are 1 flip away?
    flip_map: Dict[int, List[int]] = defaultdict(list)
    for h in corpus:
        for bit in range(6):
            flipped = h.binary_6bit ^ (1 << bit)
            if flipped in binary_to_id:
                flip_map[h.king_wen_id].append(binary_to_id[flipped])

    return PatternScan(
        total_hexagrams=len(corpus),
        mode_distribution=dict(mode_counts),
        trigram_frequency=dict(trigram_freq),
        yin_yang_distribution=dict(yin_yang_dist),
        pure_mode_hexagrams=pure_count,
        tension_hexagrams=tension_count,
        opposition_pairs=sorted(opposition_pairs),
        sequence_neighbors=neighbors,
        single_flip_transitions=dict(flip_map),
        pure_trigram_hexagrams=pure_trigram,
    )


# ── Serialisation ──────────────────────────────────────────────────────────────

def hexagram_to_dict(h: Hexagram) -> dict:
    return {
        "king_wen_id": h.king_wen_id,
        "glyph": h.glyph,
        "glyph_codepoint": h.glyph_codepoint,
        "binary_6bit": h.binary_6bit,
        "binary_str": h.binary_str,
        "upper_trigram": {
            "idx": h.upper_trigram.idx,
            "symbol": h.upper_trigram.symbol,
            "name_zh": h.upper_trigram.name_zh,
            "name_en": h.upper_trigram.name_en,
            "element": h.upper_trigram.element,
            "quality": h.upper_trigram.quality,
            "binary": h.upper_trigram.binary,
            "helen_mode": h.upper_trigram.helen_mode,
        },
        "lower_trigram": {
            "idx": h.lower_trigram.idx,
            "symbol": h.lower_trigram.symbol,
            "name_zh": h.lower_trigram.name_zh,
            "name_en": h.lower_trigram.name_en,
            "element": h.lower_trigram.element,
            "quality": h.lower_trigram.quality,
            "binary": h.lower_trigram.binary,
            "helen_mode": h.lower_trigram.helen_mode,
        },
        "name_zh": h.name_zh,
        "name_pinyin": h.name_pinyin,
        "keywords": h.keywords,
        "helen_mode": h.helen_mode,
        "tension": h.tension,
        "tension_note": h.tension_note,
        "yin_count": h.yin_count,
        "yang_count": h.yang_count,
        "yin_yang_ratio": h.yin_yang_ratio,
    }


def save_corrected(corpus: List[Hexagram], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "HEXAGRAM_CORPUS_CORRECTED_V1",
        "authority": "NON_SOVEREIGN",
        "canon": "NO_SHIP",
        "source_policy": {
            "trusted": "unicode_hexagram_glyphs + King_Wen_canonical_sequence",
            "distrusted": "pasted_trigram_pair_annotations",
            "raw_source_status": "DRIFT_DETECTED — see source_policy",
            "correction_method": "deterministic_rebuild_from_king_wen_index",
        },
        "total": len(corpus),
        "trigram_mode_map": {
            t.name_en: t.helen_mode for t in _TRIGRAMS
        },
        "hexagrams": [hexagram_to_dict(h) for h in corpus],
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Markdown scan report ───────────────────────────────────────────────────────

def render_scan_md(corpus: List[Hexagram], scan: PatternScan) -> str:
    lines = []
    lines.append("# HELEN Hexagram Pattern Scan")
    lines.append("")
    lines.append("**Authority:** NON_SOVEREIGN  ")
    lines.append("**Canon:** NO_SHIP  ")
    lines.append("**Source:** `oracle_hexagram_engine.py` — deterministic rebuild  ")
    lines.append("**Raw source annotation:** `DRIFT_DETECTED` — trigram annotations not trusted  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Mode distribution
    lines.append("## HELEN Mode Distribution")
    lines.append("")
    lines.append("| Mode | Count | % | Bar |")
    lines.append("|---|---|---|---|")
    for mode in ["FOCUS", "WITNESS", "ORACLE", "TEMPLE"]:
        count = scan.mode_distribution.get(mode, 0)
        pct = count / scan.total_hexagrams * 100
        bar = "█" * count
        lines.append(f"| {mode} | {count} | {pct:.0f}% | {bar} |")
    lines.append("")
    lines.append(f"- **Pure mode** (upper == lower family): {scan.pure_mode_hexagrams}")
    lines.append(f"- **Tension** (upper ≠ lower family): {scan.tension_hexagrams}")
    lines.append("")

    # Trigram frequency
    lines.append("## Trigram Frequency (upper + lower combined, 128 total positions)")
    lines.append("")
    lines.append("| Trigram | Symbol | Mode | Count | % |")
    lines.append("|---|---|---|---|---|")
    for t in _TRIGRAMS:
        count = scan.trigram_frequency.get(t.name_en, 0)
        pct = count / 128 * 100
        lines.append(f"| {t.name_en} | {t.symbol} | {t.helen_mode} | {count} | {pct:.1f}% |")
    lines.append("")
    lines.append("> Each trigram appears exactly 8 times in upper positions and 8 times in lower positions (64 hexagrams × 2 positions ÷ 8 trigrams = 16 each). Deviation signals encoding error.")
    lines.append("")

    # Yin/yang ratio distribution
    lines.append("## Yin/Yang Ratio Distribution (yang:yin)")
    lines.append("")
    lines.append("| Ratio | Count | Hexagrams |")
    lines.append("|---|---|---|")
    yang_total = {
        "6:0": [], "5:1": [], "4:2": [], "3:3": [],
        "2:4": [], "1:5": [], "0:6": []
    }
    for h in corpus:
        yang_total[h.yin_yang_ratio].append(h.king_wen_id)
    for ratio, ids in yang_total.items():
        if ids:
            lines.append(f"| {ratio} | {len(ids)} | {ids} |")
    lines.append("")

    # Opposition pairs
    lines.append("## Opposition Pairs (bitwise complement — all 6 lines flipped)")
    lines.append("")
    lines.append("| Hex A | Glyph A | Hex B | Glyph B | A name | B name |")
    lines.append("|---|---|---|---|---|---|")
    for (id_a, id_b) in scan.opposition_pairs:
        ha = corpus[id_a - 1]
        hb = corpus[id_b - 1]
        lines.append(f"| {ha.king_wen_id} | {ha.glyph} | {hb.king_wen_id} | {hb.glyph} | {ha.name_pinyin} | {hb.name_pinyin} |")
    lines.append("")

    # Pattern clusters
    lines.append("## Recognised Pattern Clusters")
    lines.append("")
    clusters = [
        ("Boot instability / initiation cycle",
         [3, 4, 5],
         "Difficulty → Youthful Folly → Waiting",
         "System startup uncertainty. Progress requires patience before action."),
        ("Bidirectional equilibrium toggle",
         [11, 12],
         "Peace ⟷ Standstill",
         "Stable states invert. Equilibrium is not permanent — it toggles."),
        ("Decay → source → transformation pipeline",
         [18, 48, 50],
         "Corruption → The Well → The Cauldron",
         "System recovery: repair the source before transforming the output."),
        ("Resource balancing pair",
         [41, 42],
         "Decrease ⟷ Increase",
         "Bounded resource oscillation. Reduction enables growth."),
        ("Completion paradox / loop continuity",
         [63, 64],
         "After Completion → Before Completion",
         "No terminal state. Receipt appended (63) → next intent (64). "
         "Maps to NO_RECEIPT = NO_CLAIM: the loop continues."),
    ]
    for name, ids, sequence_str, note in clusters:
        glyphs = " → ".join(f"{corpus[i-1].glyph} ({i})" for i in ids)
        lines.append(f"### {name}")
        lines.append(f"**Sequence:** {glyphs}")
        lines.append(f"**Pattern:** {sequence_str}")
        lines.append(f"**Signal:** {note}")
        lines.append("")

    # Pure trigram hexagrams (upper == lower)
    lines.append("## Pure Trigram Hexagrams (upper == lower)")
    lines.append("")
    lines.append("| ID | Glyph | Name | Trigram | Mode |")
    lines.append("|---|---|---|---|---|")
    for hid in scan.pure_trigram_hexagrams:
        h = corpus[hid - 1]
        lines.append(f"| {h.king_wen_id} | {h.glyph} | {h.name_pinyin} | {h.upper_trigram.symbol} {h.upper_trigram.name_en} | {h.helen_mode} |")
    lines.append("")

    # Sequence neighbor binary distance (sample: first 16)
    lines.append("## Sequence Neighbor Binary Distance (first 20 pairs)")
    lines.append("")
    lines.append("| Hex N | Hex N+1 | Lines differ | Note |")
    lines.append("|---|---|---|---|")
    for (id_a, bin_a, bin_b, note) in scan.sequence_neighbors[:20]:
        ha = corpus[id_a - 1]
        hb = corpus[id_a]  # N+1
        lines.append(f"| {ha.king_wen_id} {ha.glyph} {ha.name_pinyin} | {hb.king_wen_id} {hb.glyph} {hb.name_pinyin} | {note} | |")
    lines.append("")

    # Receipt table
    lines.append("## Receipt Table")
    lines.append("")
    lines.append("| ID | Glyph | Pinyin | Upper | Lower | Mode | Tension | Binary | Yang:Yin |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for h in corpus:
        tension_flag = "⚡" if h.tension else "·"
        lines.append(
            f"| {h.king_wen_id} | {h.glyph} | {h.name_pinyin} "
            f"| {h.upper_trigram.symbol}{h.upper_trigram.name_en} "
            f"| {h.lower_trigram.symbol}{h.lower_trigram.name_en} "
            f"| {h.helen_mode} | {tension_flag} | {h.binary_str} | {h.yin_yang_ratio} |"
        )
    lines.append("")

    # Final note
    lines.append("---")
    lines.append("")
    lines.append("```")
    lines.append("Do not decorate the water.")
    lines.append("Clean the well.")
    lines.append("")
    lines.append("NO_RECEIPT = NO_CLAIM")
    lines.append("Authority: NON_SOVEREIGN")
    lines.append("Canon: NO_SHIP")
    lines.append("```")

    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────────────

def cmd_save(corpus: List[Hexagram]) -> None:
    save_corrected(corpus, _OUT_JSON)
    print(f"\n  {GREEN}◆{RESET}  SAVE_CORRECTED — corpus written")
    print(f"  {DIM}→ {_OUT_JSON}{RESET}")
    print(f"  {DIM}  64 hexagrams · deterministic · King Wen sequence{RESET}")
    print(f"  {DIM}  source_policy: DRIFT_DETECTED on pasted annotations{RESET}\n")


def cmd_scan(corpus: List[Hexagram]) -> None:
    scan = scan_corpus(corpus)
    md = render_scan_md(corpus, scan)
    _OUT_SCAN.parent.mkdir(parents=True, exist_ok=True)
    _OUT_SCAN.write_text(md, encoding="utf-8")

    print(f"\n  {CYAN}◆{RESET}  SCAN COMPLETE")
    print(f"  {DIM}→ {_OUT_SCAN}{RESET}\n")

    print(f"  {DIM}── MODE DISTRIBUTION ────────────────────────────{RESET}")
    for mode in ["FOCUS", "WITNESS", "ORACLE", "TEMPLE"]:
        count = scan.mode_distribution.get(mode, 0)
        color = _MODE_COLOR.get(mode, DIM)
        bar = "█" * count
        pct = count / 64 * 100
        print(f"  {color}{mode:<8}{RESET}  {bar}  {count} ({pct:.0f}%)")
    print()

    print(f"  Pure mode hexagrams:    {scan.pure_mode_hexagrams}")
    print(f"  Tension hexagrams:      {scan.tension_hexagrams}")
    print(f"  Opposition pairs:       {len(scan.opposition_pairs)}")
    print(f"  Pure trigram (8 total): {scan.pure_trigram_hexagrams}")
    print()
    print(f"  {DIM}Pattern clusters identified: 5{RESET}")
    print(f"  {DIM}  3→4→5   boot instability cycle{RESET}")
    print(f"  {DIM}  11⟷12   equilibrium toggle{RESET}")
    print(f"  {DIM}  18→48→50 decay→source→transform pipeline{RESET}")
    print(f"  {DIM}  41⟷42   resource balancing pair{RESET}")
    print(f"  {DIM}  63→64   completion paradox (NO_RECEIPT=NO_CLAIM){RESET}")
    print()


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    corpus = build_corpus()
    cmd = args[0].lower()

    if cmd in ("save", "save_corrected"):
        cmd_save(corpus)
        return 0

    if cmd in ("scan",):
        cmd_scan(corpus)
        return 0

    if cmd in ("both", "save_corrected_then_scan"):
        cmd_save(corpus)
        cmd_scan(corpus)
        return 0

    if cmd in ("receipt",):
        # Print receipt table to stdout
        for h in corpus:
            tension = "⚡" if h.tension else "·"
            color = _MODE_COLOR.get(h.helen_mode, DIM)
            print(
                f"  {DIM}[{h.king_wen_id:>2}]{RESET}  {h.glyph}  "
                f"{color}{h.helen_mode:<8}{RESET}  "
                f"{h.upper_trigram.symbol}{h.lower_trigram.symbol}  "
                f"{h.binary_str}  {tension}  {DIM}{h.name_pinyin}{RESET}"
            )
        return 0

    print(f"Unknown command: {cmd}. Use save|scan|both|receipt", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
