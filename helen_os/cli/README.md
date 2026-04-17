# HELEN OS Dialog Box

Non-sovereign conversational interface over the constitutional kernel.

## Quick Start

```bash
# Run interactive dialog
python -m helen_os.cli.helen_dialog

# Run with custom state file
python -m helen_os.cli.helen_dialog --state my_state.json
```

## Commands

- **`state`** — Show current active skill state
- **`help`** — Show available commands
- **`exit` / `quit`** — Close session
- **JSON packet** — Pass skill promotion packet through kernel

## Example Session

```
you > help
helen > Commands:
         'state' — show current active state
         'exit' — close session
         JSON packet — run through reducer

you > state
helen > {
  "schema_name": "SKILL_LIBRARY_STATE_V1",
  "schema_version": "1.0.0",
  "law_surface_version": "v1",
  "active_skills": {}
}

you > {"schema_name": "SKILL_PROMOTION_PACKET_V1", "schema_version": "1.0.0", "packet_id": "P1", "skill_id": "skill.chat", "candidate_version": "1.0.0", "lineage": {"parent_skill_id": "skill.base", "parent_version": "0.9.0", "proposal_sha256": "sha256:1111111111111111111111111111111111111111111111111111111111111111"}, "capability_manifest_sha256": "sha256:2222222222222222222222222222222222222222222222222222222222222222", "doctrine_surface": {"law_surface_version": "v1", "transfer_required": false}, "evaluation": {"threshold_name": "accuracy", "threshold_value": 0.9, "observed_value": 0.95, "passed": true}, "receipts": [{"receipt_id": "R1", "payload": {"data": "valid"}, "sha256": "sha256:3333333333333333333333333333333333333333333333333333333333333333"}]}
helen > Decision: REJECTED (ERR_RECEIPT_HASH_MISMATCH)
helen > Reason: ERR_RECEIPT_HASH_MISMATCH

you > exit
helen > session closed
```

## Architecture

The dialog box implements the non-sovereign layer:

```
User Input (JSON)
    ↓
helen_dialog.py (parse, route)
    ↓
Kernel Path:
  1. validate_schema()
  2. reduce_promotion_packet()
  3. apply_skill_promotion_decision()
    ↓
Human-Readable Response + State Update
```

**Key principle:** Dialog input has no authority. Only reducer-emitted decisions can mutate state.

## State File

State is persisted to JSON:

```bash
helen_state.json
{
  "schema_name": "SKILL_LIBRARY_STATE_V1",
  "schema_version": "1.0.0",
  "law_surface_version": "v1",
  "active_skills": {
    "skill.chat": {
      "active_version": "1.0.0",
      "status": "ACTIVE",
      "last_decision_id": "dialog_P1"
    }
  }
}
```

## Testing

The dialog is non-sovereign — all authority remains in the kernel:

```bash
# All changes must be ADMITTED by reducer
# All state mutations flow through apply_skill_promotion_decision
# Untyped inputs are rejected
# Malformed packets are rejected
```

No tests needed — the kernel tests cover all invariants.
