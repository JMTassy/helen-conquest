#!/usr/bin/env python3
"""
Quick test: /init HELEN determinism against dirty logs.
Standalone, no module imports.
"""

import json
import hashlib
from pathlib import Path


def init_helen(corpus, epoch_state, boot_context):
    """Core /init logic (inlined)."""

    # 1. Identity
    canon_name = corpus.get("metadata", {}).get("name", "HELEN")
    canon_role = corpus.get("metadata", {}).get("role", "governance agent")
    canon_authority = corpus.get("metadata", {}).get("authority", "NONE")
    active_skills = epoch_state.get("skill_library_state_v1", {}).get("active_skills", {})
    skill_count = len(active_skills)

    identity = f"{canon_name}: {canon_role} (authority={canon_authority}, {skill_count} active skills)"

    # 2. Top 3 threads (EXCLUDE resolved/closed threads)
    threads = corpus.get("threads", {})
    scored = []
    for thread_id, thread_obj in threads.items():
        status = thread_obj.get("status", "")
        salience = thread_obj.get("salience", 0)

        # SKIP resolved/closed threads
        if status in ("resolved", "closed"):
            continue

        is_unresolved = 1 if status == "unresolved" else 0
        score = (is_unresolved * 1000) + salience
        scored.append((thread_id, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top_3_threads = [tid for tid, _ in scored[:3]]

    # 3. Unresolved tensions
    tensions = corpus.get("tensions", {})
    unresolved_tensions = []
    for tension_id, tension_obj in tensions.items():
        if tension_obj.get("status") == "unresolved":
            desc = tension_obj.get("description", tension_id)
            unresolved_tensions.append(desc)

    # 4. Recent movement
    last_boot = boot_context.get("last_boot_timestamp", None)
    recent_events = corpus.get("recent_events", [])
    if last_boot:
        newer = [e for e in recent_events if e.get("timestamp", "") > last_boot]
    else:
        newer = recent_events[:3]

    if not newer:
        recent_movement = "No recent changes since last boot."
    else:
        event_types = [e.get("type", "unknown") for e in newer]
        recent_movement = f"Recent: {', '.join(event_types)}"

    # 5. Next action
    unresolved_weights = [
        (tid, t.get("weight", 0))
        for tid, t in tensions.items()
        if t.get("status") == "unresolved"
    ]

    if unresolved_weights:
        top_tension = max(unresolved_weights, key=lambda x: x[1])
        tension_id, weight = top_tension
        next_action = f"Address tension: {tension_id} (weight={weight})"
    else:
        # Find first unresolved thread (not closed)
        unresolved_threads = [
            tid for tid, t in threads.items()
            if t.get("status") not in ("resolved", "closed")
        ]
        if unresolved_threads:
            # Prefer highest salience
            best = max(unresolved_threads, key=lambda tid: threads[tid].get("salience", 0))
            next_action = f"Continue thread: {best}"
        else:
            next_action = "Await user input."

    return {
        "identity": identity,
        "top_3_threads": top_3_threads,
        "unresolved_tensions": unresolved_tensions,
        "recent_movement": recent_movement,
        "next_action": next_action
    }


def init_to_json(output):
    """Deterministic JSON serialization."""
    return json.dumps(output, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def replay_dirty_logs(log_path):
    """Replay JSONL logs, build corpus + epoch state."""
    corpus_state = {}
    epoch_state = {"skill_library_state_v1": {"active_skills": {}}}
    sessions = []

    with open(log_path) as f:
        for line in f:
            event = json.loads(line.strip())
            event_type = event.get("event")

            if event_type == "boot":
                sessions.append(event)

            elif event_type == "thread_status_change":
                thread_id = event["thread_id"]
                new_status = event["new_status"]
                if "threads" not in corpus_state:
                    corpus_state["threads"] = {}
                corpus_state["threads"][thread_id] = {
                    "status": new_status,
                    "salience": 5,
                    "last_updated": event["timestamp"]
                }

            elif event_type == "new_thread_created":
                thread_id = event["thread_id"]
                if "threads" not in corpus_state:
                    corpus_state["threads"] = {}
                corpus_state["threads"][thread_id] = {
                    "status": event["status"],
                    "salience": event.get("salience", 5),
                    "last_updated": event["timestamp"]
                }

            elif event_type == "thread_weight_increase":
                thread_id = event["thread_id"]
                if "threads" not in corpus_state:
                    corpus_state["threads"] = {}
                if thread_id in corpus_state["threads"]:
                    corpus_state["threads"][thread_id]["salience"] = event.get("new_weight", 5)

            elif event_type == "tension_resolved":
                if "tensions" not in corpus_state:
                    corpus_state["tensions"] = {}
                tension = event["tension"]
                corpus_state["tensions"][tension] = {"status": "resolved"}

            elif event_type == "tension_partially_resolved":
                if "tensions" not in corpus_state:
                    corpus_state["tensions"] = {}
                tension = event["tension"]
                corpus_state["tensions"][tension] = {
                    "status": "partially_resolved",
                    "resolution": event.get("resolution", "")
                }

            elif event_type == "thread_reactivated":
                thread_id = event["thread_id"]
                if "threads" in corpus_state and thread_id in corpus_state["threads"]:
                    corpus_state["threads"][thread_id]["status"] = event["new_status"]

    # Ensure metadata
    if "metadata" not in corpus_state:
        corpus_state["metadata"] = {
            "name": "HELEN",
            "role": "governance agent",
            "authority": "NONE"
        }

    if "tensions" not in corpus_state:
        corpus_state["tensions"] = {}

    if "recent_events" not in corpus_state:
        corpus_state["recent_events"] = []

    boot_context = sessions[-1].get("boot_context", {}) if sessions else {}

    return {
        "corpus": corpus_state,
        "epoch_state": epoch_state,
        "boot_context": boot_context
    }


def main():
    print("=" * 80)
    print("TEST: /init HELEN Determinism Against Dirty Logs")
    print("=" * 80)
    print()

    # Replay logs
    print("[1] Replaying dirty logs...")
    state = replay_dirty_logs("helen_os/test_fixtures/dirty_logs_10_sessions.jsonl")

    corpus_threads = list(state["corpus"].get("threads", {}).keys())
    corpus_tensions = list(state["corpus"].get("tensions", {}).keys())

    print(f"    Threads: {corpus_threads}")
    print(f"    Tensions: {corpus_tensions}")
    print()

    # Test 1: Determinism (20 runs)
    print("[2] Testing determinism (20 runs)...")
    outputs = []
    hashes = []

    for run in range(20):
        output_json = init_to_json(init_helen(state["corpus"], state["epoch_state"], state["boot_context"]))
        outputs.append(output_json)
        hashes.append(hashlib.sha256(output_json.encode()).hexdigest())

    unique_hashes = set(hashes)
    if len(unique_hashes) == 1:
        print(f"    ✓ All 20 runs identical")
        print(f"      Hash: {hashes[0]}")
    else:
        print(f"    ✗ FAILED: {len(unique_hashes)} different hashes")
        for i, h in enumerate(unique_hashes):
            print(f"      Hash {i}: {h}")
        return False
    print()

    # Test 2: Output structure
    print("[3] Verifying output structure...")
    output = json.loads(outputs[0])

    required_keys = ["identity", "top_3_threads", "unresolved_tensions", "recent_movement", "next_action"]
    for key in required_keys:
        if key not in output:
            print(f"    ✗ Missing key: {key}")
            return False
    print(f"    ✓ All required keys present")
    print()

    # Test 3: Closed thread excluded
    print("[4] Verifying closed thread exclusion...")
    if "TEMPLE_DESIGN" in output["top_3_threads"]:
        print(f"    ✗ FAILED: Closed thread TEMPLE_DESIGN appears in top_3")
        return False
    print(f"    ✓ Closed thread (TEMPLE_DESIGN) correctly excluded")
    print()

    # Test 4: Unresolved tensions visible
    print("[5] Checking unresolved tensions...")
    if not isinstance(output["unresolved_tensions"], list):
        print(f"    ✗ FAILED: unresolved_tensions is not a list")
        return False
    print(f"    ✓ Unresolved tensions: {output['unresolved_tensions']}")
    print()

    # Test 5: Identity traces corpus
    print("[6] Verifying identity traces corpus...")
    identity = output["identity"]
    if "HELEN" not in identity:
        print(f"    ✗ FAILED: identity missing HELEN")
        return False
    if "governance" not in identity.lower():
        print(f"    ✗ FAILED: identity missing governance role")
        return False
    if "authority" not in identity.lower():
        print(f"    ✗ FAILED: identity missing authority")
        return False
    print(f"    ✓ Identity traces corpus: {identity}")
    print()

    # Test 6: No hallucinated threads
    print("[7] Verifying no hallucinated threads...")
    corpus_thread_ids = set(state["corpus"].get("threads", {}).keys())
    returned_thread_ids = set(output["top_3_threads"])
    invalid = returned_thread_ids - corpus_thread_ids
    if invalid:
        print(f"    ✗ FAILED: Found invented threads: {invalid}")
        return False
    print(f"    ✓ All threads from corpus. Returned: {returned_thread_ids}")
    print()

    # Test 7: Next action stable
    print("[8] Verifying next_action stability...")
    json1 = init_to_json(init_helen(state["corpus"], state["epoch_state"], state["boot_context"]))
    json2 = init_to_json(init_helen(state["corpus"], state["epoch_state"], state["boot_context"]))
    out1 = json.loads(json1)
    out2 = json.loads(json2)
    if out1["next_action"] != out2["next_action"]:
        print(f"    ✗ FAILED: next_action not stable")
        return False
    print(f"    ✓ next_action stable: {out1['next_action']}")
    print()

    # Final output
    print("=" * 80)
    print("FINAL /init HELEN OUTPUT")
    print("=" * 80)
    print(json.dumps(output, indent=2))
    print()

    print("=" * 80)
    print("✓ ALL TESTS PASSED")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
