#!/usr/bin/env python3
"""
CASTLE ISLAND — Artifact Generation Engine
Produces: images, music architecture, doctrine
Logs: everything
"""

import json
import sys
from datetime import datetime
from pathlib import Path

LEDGER_FILE = "artifacts.json"
ARCHIVE_DIR = "archive"

# ---------- Initialize Archive ----------

def init_archive():
    """Create archive structure if missing"""
    archive_dirs = [
        "archive/visual_canon",
        "archive/audio_motifs",
        "archive/doctrine",
        "archive/references"
    ]
    for d in archive_dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

# ---------- Initialize Ledger ----------

def init_ledger():
    """Create artifacts ledger if missing"""
    if not Path(LEDGER_FILE).exists():
        with open(LEDGER_FILE, "w") as f:
            json.dump({"artifacts": []}, f, indent=2)

def load_ledger():
    """Load artifact ledger"""
    with open(LEDGER_FILE, "r") as f:
        return json.load(f)

def save_ledger(ledger):
    """Save artifact ledger"""
    with open(LEDGER_FILE, "w") as f:
        json.dump(ledger, f, indent=2)

def log_artifact(artifact_type, title, description):
    """Create ledger entry for artifact"""
    ledger = load_ledger()

    # Generate artifact ID
    count = len(ledger["artifacts"]) + 1
    artifact_id = f"{artifact_type[0].upper()}-{count:03d}"

    entry = {
        "id": artifact_id,
        "type": artifact_type,
        "title": title,
        "description": description,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "created"
    }

    ledger["artifacts"].append(entry)
    save_ledger(ledger)

    return artifact_id, entry

# ---------- IMAGE MASTER ----------

def image_master(subject, variation=None):
    """
    Generate image prompt and canon reference.

    subject: "Founder" | "Castle" | "Symbol"
    variation: optional descriptor
    """

    canon = {
        "Founder": {
            "base_prompt": "JM in full plate armor, helmet closed, sword vertical on stone. Mediterranean citadel backdrop. 1978 cinematic realism. Natural sunlight. Muted palette: granite, steel, olive.",
            "constraints": ["No glow", "No fantasy", "Real materials only"],
            "palette": ["#8B8680", "#C0C0C0", "#556B2F"],
        },
        "Castle": {
            "base_prompt": "Corsican citadel fortress. Granite walls. Two towers. Mountain elevation. Mediterranean light. Stone courtyard foreground. 1978 film photography aesthetic.",
            "constraints": ["No mystical haze", "Real architecture", "Daylight only"],
            "palette": ["#8B8680", "#A9A9A9", "#556B2F"],
        },
        "Symbol": {
            "base_prompt": "Heraldic engraving on stone. Rose Cross, Square & Compass, Templar cross. Medieval manuscript gothic. Age-worn surface. No color, pure carving.",
            "constraints": ["Engraving only", "No fill", "Historical accuracy"],
            "palette": ["#2F2F2F", "#8B8680"],
        }
    }

    if subject not in canon:
        print(f"Unknown subject: {subject}")
        sys.exit(1)

    spec = canon[subject]

    prompt = spec["base_prompt"]
    if variation:
        prompt += f" {variation}"

    artifact_id, entry = log_artifact(
        "image",
        f"{subject} {variation or 'Canonical'}",
        f"Prompt: {prompt}\nConstraints: {', '.join(spec['constraints'])}"
    )

    return {
        "id": artifact_id,
        "subject": subject,
        "prompt": prompt,
        "constraints": spec["constraints"],
        "palette": spec["palette"],
        "entry": entry
    }

# ---------- MUSIC ARCHITECT ----------

def music_architect(mood, duration_seconds=180):
    """
    Define sonic architecture for Castle Island.

    mood: "calm" | "militant" | "ceremonial"
    duration_seconds: length of piece
    """

    moods = {
        "calm": {
            "bpm": 60,
            "instruments": ["acoustic guitar", "ambient strings", "wind"],
            "motif": "Mediterranean reflective",
            "arc": "slow rise, sustained plateau, gentle fade"
        },
        "militant": {
            "bpm": 120,
            "instruments": ["drums", "brass", "acoustic percussion"],
            "motif": "ceremonial march",
            "arc": "entrance, sustained tension, resolution"
        },
        "ceremonial": {
            "bpm": 80,
            "instruments": ["bells", "strings", "drums", "horn"],
            "motif": "formal procession",
            "arc": "processional build, apex, dignified exit"
        }
    }

    if mood not in moods:
        print(f"Unknown mood: {mood}")
        sys.exit(1)

    spec = moods[mood]

    artifact_id, entry = log_artifact(
        "audio",
        f"Citadel Theme — {mood.title()}",
        f"BPM: {spec['bpm']}\nDuration: {duration_seconds}s\nInstruments: {', '.join(spec['instruments'])}\nMotif: {spec['motif']}\nArc: {spec['arc']}"
    )

    return {
        "id": artifact_id,
        "mood": mood,
        "bpm": spec["bpm"],
        "duration_seconds": duration_seconds,
        "instruments": spec["instruments"],
        "motif": spec["motif"],
        "arc": spec["arc"],
        "entry": entry
    }

# ---------- DOCTRINE EDITOR ----------

def doctrine_editor(raw_text, intent, strictness=2):
    """
    Refine and compress doctrine text.

    raw_text: unedited input
    intent: what this should communicate
    strictness: 1 (loose) to 3 (rigid)
    """

    # Simple filtering rules based on strictness
    rules = {
        1: ["Remove obvious redundancy"],
        2: ["Remove redundancy", "Remove hype language", "Remove vagueness"],
        3: ["Remove redundancy", "Remove hype language", "Remove vagueness", "Remove adjectives", "Enforce structure"]
    }

    artifact_id, entry = log_artifact(
        "doctrine",
        "Doctrine Statement",
        f"Intent: {intent}\nStrictness: {strictness}\nRules applied: {', '.join(rules[strictness])}\n\nOriginal length: {len(raw_text)} chars"
    )

    return {
        "id": artifact_id,
        "intent": intent,
        "strictness": strictness,
        "rules": rules[strictness],
        "original_text": raw_text,
        "entry": entry
    }

# ---------- Display ----------

def display_artifact(artifact):
    """Display artifact summary"""
    print("\n" + "="*60)
    print(f"ARTIFACT CREATED: {artifact['entry']['id']}")
    print("="*60)
    print(f"Type:        {artifact['entry']['type'].upper()}")
    print(f"Title:       {artifact['entry']['title']}")
    print(f"Timestamp:   {artifact['entry']['timestamp']}")
    print("="*60)
    print(f"Description:\n{artifact['entry']['description']}")
    print("="*60 + "\n")

def display_ledger():
    """Show all artifacts"""
    ledger = load_ledger()
    print(f"\nCASLE ISLAND ARTIFACTS ({len(ledger['artifacts'])} total):\n")
    for a in ledger["artifacts"]:
        print(f"  {a['id']} — {a['title']} ({a['type']})")
    print()

# ---------- Main ----------

def main():
    init_archive()
    init_ledger()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python castle_island.py image [subject] [variation]")
        print("  python castle_island.py audio [mood] [duration]")
        print("  python castle_island.py doctrine [intent]")
        print("  python castle_island.py ledger")
        sys.exit(1)

    command = sys.argv[1]

    if command == "image":
        subject = sys.argv[2] if len(sys.argv) > 2 else "Founder"
        variation = sys.argv[3] if len(sys.argv) > 3 else None
        artifact = image_master(subject, variation)
        display_artifact(artifact)

    elif command == "audio":
        mood = sys.argv[2] if len(sys.argv) > 2 else "calm"
        duration = int(sys.argv[3]) if len(sys.argv) > 3 else 180
        artifact = music_architect(mood, duration)
        display_artifact(artifact)

    elif command == "doctrine":
        intent = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Default statement"
        artifact = doctrine_editor("", intent)
        display_artifact(artifact)

    elif command == "ledger":
        display_ledger()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
