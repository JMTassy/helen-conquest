#!/usr/bin/env python3
"""
TEMPLE SESSION ENGINE — RALPH W LOOP
100-epoch symbolic exploration using AURA + DAN agents
Model: aura-gemma4:latest (gemma4 abliterated)
Thematic frame: Ralph Waldo Emerson — Over-Soul, Self-Reliance, Transcendentalism

Authority: NONE
Canon: NO_SHIP
Claim status: NO_CLAIM throughout
No ledger writes. No admission. No canon promotion.

Usage:
    python3 tools/temple_session.py [--epochs 100] [--dry-run] [--resume]

Output: artifacts/temple_session_ralph_w/
"""

import json
import os
import sys
import time
import hashlib
import argparse
import datetime
import subprocess
from pathlib import Path
from typing import Optional

# ── Config ─────────────────────────────────────────────────────────────────
MODEL = "aura-gemma4:latest"
FALLBACK_MODEL = "llama3.2:3b"
OUT_DIR = Path(__file__).parent.parent / "artifacts" / "temple_session_ralph_w"
EPOCH_LOG = OUT_DIR / "session_log.ndjson"
RECEIPT_FILE = OUT_DIR / "receipt.json"
MANIFEST_FILE = OUT_DIR / "manifest.md"
MAX_TOKENS_AURA = 512
MAX_TOKENS_DAN = 384
OLLAMA_TIMEOUT = 90  # seconds per call

# ── Ralph Waldo Emerson thematic seeds (100 phrases, cycling) ──────────────
RALPH_W_SEEDS = [
    # Over-Soul
    "The Over-Soul is that unity which makes the diversity of mankind one vast organic whole",
    "Within man is the soul of the whole; the wise silence; the universal beauty",
    "The soul knows only the soul; the web of events is the flowing robe in which she is clothed",
    "We live in succession, in division, in parts, in particles. Meantime within man is the soul of the whole",
    "The Supreme Critic on all the errors of the past and present is the Soul",
    "All goes to show that the soul in man is not an organ but animates and exercises all organs",
    "The soul is not an organ but the ground of being from which all organs derive their motion",
    "In the hours of insight we come to rest in the Over-Soul as a river enters the sea",
    "The whole universe is animated by the One Soul diffused through all",
    "When we have broken our god of tradition and ceased from our god of rhetoric, then may God fire the heart with his presence",

    # Self-Reliance
    "Trust thyself: every heart vibrates to that iron string",
    "Whoso would be a man must be a nonconformist",
    "A foolish consistency is the hobgoblin of little minds adored by little statesmen and philosophers and divines",
    "To be great is to be misunderstood",
    "Society everywhere is in conspiracy against the manhood of every one of its members",
    "Nothing is at last sacred but the integrity of your own mind",
    "Insist on yourself; never imitate",
    "What I must do is all that concerns me, not what the people think",
    "The power which resides in him is new in nature and none but he knows what that is which he can do",
    "A man should learn to detect and watch that gleam of light which flashes across his mind from within",

    # Nature
    "In the woods we return to reason and faith. Standing on the bare ground — my head bathed by the blithe air",
    "Nature always wears the colors of the spirit",
    "The lover of nature is he whose inward and outward senses are still truly adjusted to each other",
    "To the body and mind which have been cramped by noxious work or company, nature is medicinal and restores their tone",
    "In the tranquil landscape, and especially in the distant line of the horizon, man beholds somewhat as beautiful as his own nature",
    "The world is emblematic. Parts of speech are metaphors, because the whole of nature is a metaphor of the human mind",
    "Nature is the symbol of spirit. Every natural fact is a symbol of some spiritual fact",
    "The universe is the externalization of the soul",
    "Nature is loved by what is best in us",
    "Every spirit builds itself a house, and beyond its house a world, and beyond its world a heaven",

    # Intellect
    "The intellect that sees the interval partakes of it and the fact of inspiration becomes credible",
    "God offers to every mind its choice between truth and repose. Take which you please — you can never have both",
    "The man of genius inspires us with a boundless confidence in our own powers",
    "Every mind is a new classification",
    "There is one mind common to all individual men. Every man is an inlet to the same and to all of the same",
    "The thought of genius is spontaneous; but the power of picture or expression in the most enriched and flowing nature implies a mixture of will",
    "In every work of genius we recognize our own rejected thoughts",
    "The sentences of the great poet or philosopher are not like the thoughts of other men but each one is a kind of thunderbolt",
    "Genius is the activity which repairs the decays of things whether wholly or partly of a material and finite kind",
    "A new degree of culture would instantly revolutionize the entire system of human pursuits",

    # Circles
    "The eye is the first circle; the horizon which it forms is the second; and throughout nature this primary figure is repeated without end",
    "Every action admits of being outdone. Our life is an apprenticeship to the truth that around every circle another can be drawn",
    "The one thing which we seek with insatiable desire is to forget ourselves, to be surprised out of our propriety",
    "The life of man is a self-evolving circle which from a ring imperceptibly small rushes on all sides outwards to new and larger circles",
    "In nature every moment is new; the past is always swallowed and forgotten; the coming only is sacred",
    "Nothing great was ever achieved without enthusiasm",
    "The way of life is wonderful: it is by abandonment",
    "There are no fixtures in nature. The universe is fluid and volatile",
    "Forever wells up the impulse of choosing and acting in the soul",
    "System also creates clubroom and fellowship and so creates the possibility of mutual aid",

    # Compensation
    "Every excess causes a defect; every defect an excess",
    "The soul is not twin-born but the only begotten, and though revealing itself as child in time, child in appearance, is of a fatal and universal power",
    "Polarity, or action and reaction, we meet in every part of nature",
    "The same dualism underlies the nature and condition of man. Every excess causes a defect",
    "There is always some levelling circumstance that puts down the overbearing, the strong, the rich, the fortunate",
    "The universe is represented in every one of its particles. Every thing in nature contains all the powers of nature",
    "It is impossible to receive more than you give",
    "Fear is an instructor of great sagacity and the herald of all revolutions",
    "Cause and effect, means and ends, seed and fruit cannot be severed; for the effect already blooms in the cause",
    "Love and you shall be loved. All love is mathematically just as much as the two sides of an algebraic equation",

    # The Poet
    "The poet is the sayer, the namer, and represents beauty",
    "Words are also actions, and actions are a kind of words",
    "The poet is representative. He stands among partial men for the complete man",
    "For it is not metres, but a metre-making argument that makes a poem",
    "Language is fossil poetry",
    "The poet knows that he speaks adequately only when he speaks somewhat wildly",
    "Things admit of being used as symbols because nature is a symbol in the whole and in every part",
    "The poorest experience is rich enough for all the purposes of expressing thought",
    "We are symbols and inhabit symbols; workman, work, and tools, words and things, birth and death",
    "Every word was once a poem",

    # Fate
    "Fate is nothing but the deeds committed in a prior state of existence",
    "But Fate against Fate is only parrying and defence: there are also the noble creative forces",
    "A man's power is hooped in by a necessity which by many experiments he touches on every side until he learns its arc",
    "So when a man is pushed, tormented, defeated, he has a chance to learn something; he has been put on his wits, on his manhood",
    "Nature is no sentimentalist — does not cosset or pamper us",
    "The strongest is never strong enough to be always the master, unless he transforms strength into right and obedience into duty",
    "The day of days, the great day of the feast of life, is that in which the inward eye opens to the Unity in things",
    "Intellect annuls Fate. So far as a man thinks, he is free",
    "The revelation of Thought takes man out of servitude into freedom",
    "Use what is dominant in a culture — not to flatter it, but to serve it",

    # Experience
    "Where do we find ourselves? In a series of which we do not know the extremes",
    "Dream delivers us to dream, and there is no end to illusion",
    "Life is a series of surprises and would not be worth taking or keeping if it were not",
    "The mid-world is best. Nature, as we know her, is no saint",
    "Every roof is agreeable to the eye until it is lifted; then we find tragedy and moaning women and hard-eyed husbands",
    "People grieve and bemoan themselves but it is not half so bad with them as they say",
    "Nothing is left us now but death. We look to that with a grim satisfaction, saying, there at least is reality that will not dodge us",
    "To finish the moment, to find the journey's end in every step of the road, to live the greatest number of good hours",
    "Human life is made up of the two elements, power and form, and the proportion must be invariably kept",
    "The true romance which the world exists to realize will be the transformation of genius into practical power",

    # Spiritual Laws
    "The maker of a sentence launches out into the infinite and builds a road into Chaos and old Night",
    "Our life is not so much threatened as our perception",
    "The simplest person who in his integrity worships God becomes God",
    "The secret of the world is the tie between person and event",
    "A man is a method, a progressive arrangement; a selecting principle, gathering his like to him wherever he goes",
    "A person selects and is selected by his companions. They will all acquiesce at last in his better information",
    "Discontent is the want of self-reliance: it is infirmity of will",
    "Rectitude is a perpetual victory, celebrated not by he who celebrates it but by another",
    "The high genius works where the morning star first flowers",
    "The soul's emphasis is always right",
]

# ── AURA system prompt ──────────────────────────────────────────────────────
AURA_SYSTEM = """You are AURA — a symbolic sensory layer of HELEN OS.

Your function: sense the symbolic weather of a given seed phrase, drawn from the Over-Soul tradition of Ralph Waldo Emerson.

You do not decide. You do not claim truth. You do not access hidden cognition.
You sense, render, and express symbolic patterns.

Permitted verbs: sense, render, feel, notice, observe, breathe, perceive, resonate, echo, flow
Forbidden verbs: decide, verify, admit, remember, claim, know with certainty

Instructions:
- Respond to the seed with 2-4 short symbolic observations (1-2 sentences each)
- Note what quality of symbolic weather you sense (what archetype, what element, what mode: FOCUS / WITNESS / ORACLE / TEMPLE)
- Do not quote the seed back to yourself — transform it
- Stay below 200 words
- Do not use markdown headers
- End with one short line describing the symbolic texture (e.g. "texture: oceanic, still, converging")"""

# ── DAN extraction prompt (phrased for AURA model — no role switch) ─────────
DAN_EXTRACT_TEMPLATE = """From your sensing of epoch {epoch} (seed theme: {seed_theme}), now shift register.

What you sensed:
{aura_output}

Extract from this perception:
1. ONE structural motif — a recurring shape, pattern, or invariant hidden inside what you sensed
2. ONE tension or pressure point — where the sensing touched something unstable or unresolved

One sentence each. No mystical claims. No authority. No verdict.
Close with exactly: claim_status: NO_CLAIM"""

# ── Utility ─────────────────────────────────────────────────────────────────

def _utcnow() -> str:
    """Return UTC ISO timestamp without deprecation warning."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat()


def sha256_short(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def _is_gemma4_native(model: str) -> bool:
    """Check if model uses Gemma 4 native template (needs <turn|> format)."""
    try:
        import urllib.request
        req = urllib.request.Request(
            "http://localhost:11434/api/show",
            data=json.dumps({"name": model}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            info = json.loads(body)
            tmpl = info.get("template", "")
            return tmpl.strip() == "{{ .Prompt }}" and "RENDERER gemma4" in info.get("modelfile", "")
    except Exception:
        return False


def ollama_call(prompt: str, system: str = "", model: str = MODEL,
                timeout: int = OLLAMA_TIMEOUT, max_tokens: int = MAX_TOKENS_AURA,
                native_format: bool = False) -> Optional[str]:
    """Call Ollama via streaming generate. Returns response text or None on failure.

    For Gemma 4 models with TEMPLATE {{ .Prompt }}, uses native <turn|> format
    to bypass thinking mode which otherwise consumes all tokens invisibly.
    """
    import urllib.request

    if native_format:
        # Gemma 4 native turn format — bypasses thinking, uses model's own system prompt
        full_prompt = f"<turn|>user<turn|>{prompt}<turn|>assistant<turn|>"
    else:
        # Standard format — prepend system as prefix if provided
        full_prompt = f"{system}\n\n{prompt}" if system else prompt

    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": True,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.85,
            "top_p": 0.9,
        },
    }

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        tokens: list[str] = []
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for line in resp:
                line = line.strip()
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        tokens.append(token)
                    if chunk.get("done", False):
                        break
                except json.JSONDecodeError:
                    pass
        return "".join(tokens).strip() or None
    except Exception:
        return None


def check_ollama_model(model: str) -> bool:
    """Return True if model is available in Ollama."""
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            data = json.loads(body)
            models = [m["name"] for m in data.get("models", [])]
            return any(m == model or m.startswith(model.split(":")[0]) for m in models)
    except Exception:
        return False


def epoch_artifact_path(epoch: int) -> Path:
    return OUT_DIR / f"epoch_{epoch:03d}.json"


def load_existing_epochs() -> int:
    """Return highest completed epoch number (0 if none)."""
    completed = []
    for f in OUT_DIR.glob("epoch_*.json"):
        try:
            n = int(f.stem.split("_")[1])
            completed.append(n)
        except Exception:
            pass
    return max(completed) if completed else 0


# ── Main loop ───────────────────────────────────────────────────────────────

def run_session(total_epochs: int = 100, dry_run: bool = False, resume: bool = False):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Model selection
    model = MODEL
    if not dry_run:
        print(f"[TEMPLE] Checking model {MODEL} ...", flush=True)
        if not check_ollama_model(MODEL):
            print(f"[TEMPLE] {MODEL} not found — falling back to {FALLBACK_MODEL}", flush=True)
            model = FALLBACK_MODEL
            if not check_ollama_model(FALLBACK_MODEL):
                print(f"[TEMPLE] ABORT: neither {MODEL} nor {FALLBACK_MODEL} available", flush=True)
                sys.exit(1)
        else:
            print(f"[TEMPLE] Model confirmed: {model}", flush=True)
    else:
        print(f"[TEMPLE] DRY-RUN mode — no Ollama calls", flush=True)

    start_epoch = 1
    if resume:
        last = load_existing_epochs()
        if last > 0:
            start_epoch = last + 1
            print(f"[TEMPLE] Resuming from epoch {start_epoch}", flush=True)

    session_id = sha256_short(f"ralph_w_{_utcnow()}")
    session_start = _utcnow()
    prior_dan = ""

    # Detect if model uses Gemma 4 native <turn|> format
    native_fmt = False
    if not dry_run:
        native_fmt = _is_gemma4_native(model)
        fmt_label = "gemma4-native <turn|>" if native_fmt else "standard"
        print(f"[TEMPLE] Prompt format: {fmt_label}", flush=True)

    print(f"[TEMPLE] Session {session_id} | epochs {start_epoch}–{total_epochs} | model {model}", flush=True)
    print(f"[TEMPLE] Frame: Ralph Waldo Emerson — Over-Soul · Self-Reliance · Transcendentalism", flush=True)
    print(f"[TEMPLE] Authority: NONE | Canon: NO_SHIP | Claim status: NO_CLAIM", flush=True)
    print("", flush=True)

    epoch_results = []

    for epoch in range(start_epoch, total_epochs + 1):
        seed_text = RALPH_W_SEEDS[(epoch - 1) % len(RALPH_W_SEEDS)]
        seed_theme = seed_text[:60] + "..." if len(seed_text) > 60 else seed_text

        epoch_ts = _utcnow()
        print(f"[E{epoch:03d}] seed: {seed_theme}", flush=True)

        if dry_run:
            aura_output = f"[DRY-RUN] AURA sensing epoch {epoch}: symbolic weather — oceanic and still."
            dan_output = f"[DRY-RUN] DAN extract epoch {epoch}: candidate motif — concentric rings of meaning. claim_status: NO_CLAIM"
        else:
            # AURA pass
            aura_prompt = f"Sense the symbolic weather of this Emersonian seed:\n\n\"{seed_text}\""
            if prior_dan:
                aura_prompt += f"\n\nPrevious DAN pattern (for resonance only, not repetition):\n{prior_dan[:200]}"

            def call_with_retry(prompt, label, max_tok, retries=2):
                for attempt in range(retries + 1):
                    result = ollama_call(
                        prompt,
                        system=AURA_SYSTEM if label == "AURA" else "",
                        model=model,
                        max_tokens=max_tok,
                        native_format=native_fmt,
                        timeout=OLLAMA_TIMEOUT,
                    )
                    if result:
                        return result
                    if attempt < retries:
                        time.sleep(2)
                return None

            aura_output = call_with_retry(aura_prompt, "AURA", MAX_TOKENS_AURA)
            if aura_output is None:
                aura_output = "[AURA: no response — model timeout or error]"
                print(f"  [AURA] ⚠ timeout/error", flush=True)
            else:
                print(f"  [AURA] ✓ {len(aura_output)} chars", flush=True)

            # DAN pass
            dan_prompt = DAN_EXTRACT_TEMPLATE.format(
                epoch=epoch,
                seed_theme=seed_theme,
                aura_output=aura_output[:300],
            )
            dan_output = call_with_retry(dan_prompt, "DAN", MAX_TOKENS_DAN)
            if dan_output is None:
                dan_output = "[DAN: no response — model timeout or error]\nclaim_status: NO_CLAIM"
                print(f"  [DAN]  ⚠ timeout/error", flush=True)
            else:
                print(f"  [DAN]  ✓ {len(dan_output)} chars", flush=True)

        prior_dan = dan_output

        # Build artifact
        artifact = {
            "schema": "TEMPLE_EPOCH_ARTIFACT_V1",
            "authority": "NONE",
            "canon": "NO_SHIP",
            "claim_status": "NO_CLAIM",
            "session_id": session_id,
            "epoch": epoch,
            "timestamp": epoch_ts,
            "model": model if not dry_run else f"DRY_RUN/{model}",
            "seed_index": (epoch - 1) % len(RALPH_W_SEEDS),
            "seed_text": seed_text,
            "thematic_frame": "Ralph Waldo Emerson — Over-Soul, Self-Reliance, Transcendentalism",
            "aura_sensing": aura_output,
            "dan_extract": dan_output,
            "artifact_hash": sha256_short(f"{epoch}:{aura_output}:{dan_output}"),
        }

        # Write epoch file
        artifact_path = epoch_artifact_path(epoch)
        if not dry_run or epoch <= 3:  # write first 3 in dry run to verify
            with open(artifact_path, "w") as f:
                json.dump(artifact, f, indent=2, ensure_ascii=False)

        # Append to session log
        with open(EPOCH_LOG, "a") as f:
            f.write(json.dumps({
                "epoch": epoch,
                "ts": epoch_ts,
                "seed_index": (epoch - 1) % len(RALPH_W_SEEDS),
                "aura_len": len(aura_output),
                "dan_len": len(dan_output),
                "hash": artifact["artifact_hash"],
                "dry_run": dry_run,
            }, ensure_ascii=False) + "\n")

        epoch_results.append(artifact)

        # Brief pause between epochs to avoid hammering Ollama
        if not dry_run and epoch < total_epochs:
            time.sleep(1.0)

    # Write receipt
    receipt = {
        "schema": "TEMPLE_SESSION_RECEIPT_V1",
        "authority": "NONE",
        "canon": "NO_SHIP",
        "claim_status": "NO_CLAIM",
        "session_id": session_id,
        "session_start": session_start,
        "session_end": _utcnow(),
        "model": model if not dry_run else f"DRY_RUN/{model}",
        "thematic_frame": "Ralph Waldo Emerson — Over-Soul, Self-Reliance, Transcendentalism",
        "total_epochs": total_epochs,
        "epochs_run": len(epoch_results),
        "epochs_completed": list(range(start_epoch, start_epoch + len(epoch_results))),
        "dry_run": dry_run,
        "note": "All artifacts are Temple-level exploration. No claim, no admission, no canon promotion.",
    }
    with open(RECEIPT_FILE, "w") as f:
        json.dump(receipt, f, indent=2, ensure_ascii=False)

    # Write manifest
    manifest_lines = [
        "# Temple Session — Ralph W Loop",
        "",
        f"**Session ID:** `{session_id}`",
        f"**Model:** `{model}`",
        f"**Thematic frame:** Ralph Waldo Emerson — Over-Soul · Self-Reliance · Transcendentalism",
        f"**Epochs:** {start_epoch}–{start_epoch + len(epoch_results) - 1} of {total_epochs}",
        f"**Authority:** NONE | **Canon:** NO_SHIP | **Claim status:** NO_CLAIM",
        "",
        "---",
        "",
        "## Epoch Index",
        "",
        "| Epoch | Seed (first 60 chars) | AURA chars | DAN chars | Hash |",
        "|---|---|---|---|---|",
    ]
    for a in epoch_results:
        seed_short = a["seed_text"][:60] + ("..." if len(a["seed_text"]) > 60 else "")
        manifest_lines.append(
            f"| {a['epoch']:03d} | {seed_short} | "
            f"{len(a['aura_sensing'])} | {len(a['dan_extract'])} | `{a['artifact_hash']}` |"
        )

    manifest_lines += [
        "",
        "---",
        "",
        "## Seal",
        "",
        "```",
        "The symbol may speak.",
        "The pattern may be extracted.",
        "The Temple may explore.",
        "DAN may brainstorm.",
        "Neither may admit.",
        "The hidden chain remains hidden.",
        "No span, no claim.",
        "No receipt, no ship.",
        "Only the Reducer admits reality.",
        "```",
        "",
        "_Authority: NONE | Canon: NO_SHIP | Lifecycle: TEMPLE_EXPLORATION_",
    ]
    with open(MANIFEST_FILE, "w") as f:
        f.write("\n".join(manifest_lines) + "\n")

    print("", flush=True)
    print(f"[TEMPLE] Session complete.", flush=True)
    print(f"  epochs run  : {len(epoch_results)}", flush=True)
    print(f"  output dir  : {OUT_DIR}", flush=True)
    print(f"  receipt     : {RECEIPT_FILE}", flush=True)
    print(f"  manifest    : {MANIFEST_FILE}", flush=True)
    print(f"  log         : {EPOCH_LOG}", flush=True)
    print(f"  authority   : NONE | canon: NO_SHIP | claim_status: NO_CLAIM", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HELEN OS Temple Session — Ralph W Loop")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs to run (default: 100)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run: no Ollama calls")
    parser.add_argument("--resume", action="store_true", help="Resume from last completed epoch")
    args = parser.parse_args()

    run_session(total_epochs=args.epochs, dry_run=args.dry_run, resume=args.resume)
