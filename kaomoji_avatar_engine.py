#!/usr/bin/env python3
"""
KAOMOJI AVATAR ENGINE v1.0
Deterministic avatar rendering for CONQUEST agents.

Per (seed, tick, agent_id) → (face, emotion, color, overlays)
Uses FNV-1a 64-bit hash for reproducibility.
"""

from typing import Dict, List, Tuple

# ============================================================================
# CONSTANTS
# ============================================================================

# 12 canonical emotions
EMOTIONS = ["JOY", "LOVE", "EXCITED", "SHY", "HUG", "TASTY", 
            "MISCHIEVOUS", "FIGHT", "SAD", "PANIC", "NEUTRAL", "ANIMALS"]

# Face pools (exact kaomoji)
FACE_POOLS = {
    "JOY": ["(๑>ᴗ<๑)", "(≧◡≦)", "(✿◕‿◕)"],
    "LOVE": ["(｡♥‿♥｡)", "(•ө•)♡"],
    "EXCITED": ["(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧", "(╯✧▽✧)╯", "(๑˃̵ᴗ˂̵)و", "(つ≧▽≦)つ"],
    "SHY": ["(⁄ ⁄>⁄ ▽ ⁄<⁄ ⁄)", "(｡•́‿•̀｡)"],
    "HUG": ["(づ｡◕‿‿◕｡)づ", "(っ^_^)っ", "(っ´▽`)っ"],
    "TASTY": ["(っ˘ڡ˘ς)"],
    "MISCHIEVOUS": ["(｡•̀ᴗ-)✧", "(￢‿￢)"],
    "FIGHT": ["(ง'̀-'́)ง"],
    "SAD": ["(｡•́︿•̀｡)", "(；ω；)", "(╥﹏╥)", "(；´Д｀)"],
    "PANIC": ["(；´Д｀)", "(╥﹏╥)"],
    "NEUTRAL": ["(￣▽￣)ノ"],
    "ANIMALS": ["ʕ•ᴥ•ʔ", "ʕっ•ᴥ•ʔっ", "(=^･ω･^=)", "(=^･ｪ･^=)", "(ᵔᴥᵔ)", "(•ㅅ•)", "( ͡° ᴥ ͡°)"]
}

# RGB colors per emotion (24-bit)
EMOTION_COLORS = {
    "JOY": (255, 211, 78),           # #FFD34E gold
    "LOVE": (255, 77, 141),          # #FF4D8D hot pink
    "EXCITED": (168, 85, 247),       # #A855F7 purple
    "SHY": (249, 168, 212),          # #F9A8D4 soft pink
    "HUG": (96, 165, 250),           # #60A5FA sky blue
    "TASTY": (52, 211, 153),         # #34D399 mint
    "MISCHIEVOUS": (249, 115, 22),   # #F97316 orange
    "FIGHT": (239, 68, 68),          # #EF4444 red
    "SAD": (59, 130, 246),           # #3B82F6 blue
    "PANIC": (244, 63, 94),          # #F43F5E danger pink-red
    "NEUTRAL": (163, 163, 163),      # #A3A3A3 gray
    "ANIMALS": (34, 197, 94)         # #22C55E green
}

# ANSI fallback colors (standard 16)
ANSI_FALLBACK = {
    "JOY": "\x1b[93m",           # bright yellow
    "LOVE": "\x1b[95m",          # bright magenta
    "EXCITED": "\x1b[95m",       # bright magenta
    "SHY": "\x1b[95m",           # bright magenta
    "HUG": "\x1b[96m",           # bright cyan
    "TASTY": "\x1b[92m",         # bright green
    "MISCHIEVOUS": "\x1b[93m",   # bright yellow
    "FIGHT": "\x1b[91m",         # bright red
    "SAD": "\x1b[94m",           # bright blue
    "PANIC": "\x1b[91m",         # bright red
    "NEUTRAL": "\x1b[90m",       # bright black (gray)
    "ANIMALS": "\x1b[92m"        # bright green
}

# Symbol overlays per emotion (3 base, can expand)
OVERLAY_SETS = {
    "JOY": ["✧", "✦", "✪"],
    "LOVE": ["🌹", "✧", "✦"],
    "EXCITED": ["🌀", "✧", "✪"],
    "SHY": ["✧", "🌹", "🜄"],
    "HUG": ["✧", "🜄", "🗝"],
    "TASTY": ["🜃", "✧", "🌹"],
    "MISCHIEVOUS": ["🌀", "✧", "⸸"],
    "FIGHT": ["✝️", "🜂", "💀"],
    "SAD": ["🜄", "⚰️", "✧"],
    "PANIC": ["🌀", "💀", "🜂"],
    "NEUTRAL": ["🜃", "⸸", "✧"],
    "ANIMALS": ["🌹", "🜁", "✧"]
}

# ============================================================================
# FNV-1a 64-bit HASH
# ============================================================================

def fnv1a_64(key: str) -> int:
    """FNV-1a 64-bit hash function (deterministic, stable across languages)."""
    offset_basis = 0xcbf29ce484222325
    fnv_prime = 0x100000001b3
    hash_value = offset_basis
    
    for byte in key.encode('utf-8'):
        hash_value ^= byte
        hash_value = (hash_value * fnv_prime) & 0xffffffffffffffff
    
    return hash_value

# ============================================================================
# AVATAR GENERATION
# ============================================================================

def generate_avatar(seed: int, tick: int, agent_id: str) -> Dict:
    """
    Generate deterministic avatar for an agent at a given tick.
    
    Args:
        seed: Simulation seed
        tick: Current tick/turn
        agent_id: Agent identifier (A, B, C, etc.)
    
    Returns:
        Dict with keys: emotion, face, color_rgb, color_hex, overlays, ansi_code
    """
    
    # Canonical key for hashing
    key = f"CONQUEST|AVATAR|v1|{seed}|{tick}|{agent_id}"
    hash_val = fnv1a_64(key)
    
    # Pick emotion (12 total)
    emo_idx = hash_val % len(EMOTIONS)
    emotion = EMOTIONS[emo_idx]
    
    # Pick face from emotion's pool
    face_pool = FACE_POOLS[emotion]
    face_idx = (hash_val >> 8) % len(face_pool)
    face = face_pool[face_idx]
    
    # Pick overlays (3 distinct symbols)
    overlay_set = OVERLAY_SETS[emotion]
    o1 = overlay_set[(hash_val >> 16) % len(overlay_set)]
    o2_idx = (hash_val >> 24) % len(overlay_set)
    o2 = overlay_set[(o2_idx + 1) % len(overlay_set) if o2_idx == (hash_val >> 16) % len(overlay_set) else o2_idx]
    o3_idx = (hash_val >> 32) % len(overlay_set)
    # Avoid duplicates
    while overlay_set[o3_idx] in [o1, o2]:
        o3_idx = (o3_idx + 1) % len(overlay_set)
    o3 = overlay_set[o3_idx]
    
    # Get color (RGB)
    color_rgb = EMOTION_COLORS[emotion]
    color_hex = f"#{color_rgb[0]:02X}{color_rgb[1]:02X}{color_rgb[2]:02X}"
    
    # Get ANSI fallback
    ansi_code = ANSI_FALLBACK[emotion]
    
    return {
        "emotion": emotion,
        "face": face,
        "color_rgb": color_rgb,
        "color_hex": color_hex,
        "overlays": [o1, o2, o3],
        "ansi_code": ansi_code
    }

# ============================================================================
# RENDERING
# ============================================================================

def render_terminal_truecolor(avatar: Dict, agent_id: str) -> str:
    """Render avatar with 24-bit truecolor ANSI codes."""
    r, g, b = avatar["color_rgb"]
    face = avatar["face"]
    overlays = "".join(avatar["overlays"])
    emotion = avatar["emotion"]
    
    # Truecolor format: \x1b[38;2;R;G;Bm...text...\x1b[0m
    colored_face = f"\x1b[1m\x1b[38;2;{r};{g};{b}m{face}\x1b[0m"
    
    return f"{agent_id}  [{overlays}]  {colored_face}  EMO:{emotion}"

def render_terminal_fallback(avatar: Dict, agent_id: str) -> str:
    """Render avatar with standard 16-color ANSI codes."""
    face = avatar["face"]
    overlays = "".join(avatar["overlays"])
    emotion = avatar["emotion"]
    ansi = avatar["ansi_code"]
    
    # Fallback format: ANSI code + face + reset
    colored_face = f"{ansi}{face}\x1b[0m"
    
    return f"{agent_id}  [{overlays}]  {colored_face}  EMO:{emotion}"

def render_machine_readable(avatar: Dict, agent_id: str) -> str:
    """Render avatar as machine-readable JSON-like format."""
    overlays = " ".join(avatar["overlays"])
    face = avatar["face"]
    emotion = avatar["emotion"]
    color_hex = avatar["color_hex"]
    
    return f"{agent_id}  EMO:{emotion}  RGB:{color_hex}  OV:[{overlays}]  FACE:{face}"

# ============================================================================
# BANNER & DISPLAY
# ============================================================================

def render_day_banner(seed: int, tick: int, use_truecolor: bool = True) -> str:
    """Render global mood banner for the day/tick."""
    key = f"CONQUEST|GLOBAL|{seed}|{tick}"
    hash_val = fnv1a_64(key)
    emo_idx = hash_val % len(EMOTIONS)
    global_emotion = EMOTIONS[emo_idx]
    
    banner = f"{'='*60}\nDAY {tick}  ✨ CONQUEST CASTLE MOOD ✨  [GLOBAL:{global_emotion}]\n{'='*60}"
    return banner

def render_avatar_table(seed: int, tick: int, agent_ids: List[str], use_truecolor: bool = True) -> str:
    """Render table of avatars for all agents."""
    lines = [render_day_banner(seed, tick, use_truecolor)]
    lines.append("")
    
    for agent_id in agent_ids:
        avatar = generate_avatar(seed, tick, agent_id)
        if use_truecolor:
            rendered = render_terminal_truecolor(avatar, agent_id)
        else:
            rendered = render_terminal_fallback(avatar, agent_id)
        lines.append(rendered)
    
    lines.append("")
    return "\n".join(lines)

# ============================================================================
# MAIN / DEMO
# ============================================================================

if __name__ == "__main__":
    import sys
    
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 9137
    tick = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    agents = ["A", "B", "C"]
    
    print("\n" + "="*60)
    print("KAOMOJI AVATAR ENGINE v1.0 — DETERMINISTIC AVATAR RENDERING")
    print("="*60 + "\n")
    
    print(f"SEED: {seed} | TICK: {tick}\n")
    
    # Try truecolor, fallback if not supported
    try:
        print(render_avatar_table(seed, tick, agents, use_truecolor=True))
    except:
        print(render_avatar_table(seed, tick, agents, use_truecolor=False))
    
    # Also show machine-readable format
    print("\n" + "="*60)
    print("MACHINE-READABLE FORMAT")
    print("="*60 + "\n")
    
    for agent_id in agents:
        avatar = generate_avatar(seed, tick, agent_id)
        print(render_machine_readable(avatar, agent_id))
    
    print("\n" + "="*60)
    print("DETAIL VIEW (One Agent)")
    print("="*60 + "\n")
    
    avatar = generate_avatar(seed, tick, "A")
    print(f"Agent: A")
    print(f"Emotion: {avatar['emotion']}")
    print(f"Face: {avatar['face']}")
    print(f"Color (RGB): {avatar['color_rgb']}")
    print(f"Color (Hex): {avatar['color_hex']}")
    print(f"Overlays: {' '.join(avatar['overlays'])}")
    print(f"ANSI Fallback: {repr(avatar['ansi_code'])}")
