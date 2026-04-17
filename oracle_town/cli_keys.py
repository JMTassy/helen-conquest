#!/usr/bin/env python3
"""
CLI for key registry management and verification.

Commands:
  keys add --id ID --class CLASS --pub PUB_B64 [--allow-obligations O1,O2] [--policy-ids P1,P2]
  keys revoke --id ID --reason REASON
  keys verify --policy policy.json --registry keys/public_keys.json --ledger ledger.json
  keys sign-registry --registry keys/public_keys.json --private-key-b64 <b64> --signer-id <key-id> --out registry_manifest.signed.json

Note: This CLI is a convenience tool for local/manually-governed operations. Production updates must be via governed policy-change runs.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime
from typing import List

ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(ROOT, "..")))

from oracle_town.core.key_registry import compute_registry_hash
from oracle_town.core.crypto import canonical_json_bytes, sign_ed25519


def load_json(path: str):
    with open(path, 'r') as f:
        return json.load(f)


def write_json(path: str, obj):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)


def cmd_add(args):
    registry_path = args.registry
    reg = load_json(registry_path)
    keys = reg.get('keys', [])
    # Prevent duplicates
    if any(k.get('signing_key_id') == args.id for k in keys):
        print(f"Key {args.id} already exists in registry")
        return 1

    allow = {"obligations": ["*"], "policy_ids": ["*"]}
    if args.allow_obligations:
        allow['obligations'] = args.allow_obligations.split(',')
    if args.policy_ids:
        allow['policy_ids'] = args.policy_ids.split(',')

    entry = {
        "signing_key_id": args.id,
        "attestor_class": args.attestor_class,
        "public_key_ed25519_b64": args.pub,
        "status": "ACTIVE",
        "allow": allow,
        "metadata": {"added_at": datetime.utcnow().isoformat(), "owner": args.owner or "unknown"}
    }
    keys.append(entry)
    reg['keys'] = keys
    write_json(registry_path, reg)
    print(f"Added key {args.id} to {registry_path}")
    return 0


def cmd_revoke(args):
    registry_path = args.registry
    reg = load_json(registry_path)
    keys = reg.get('keys', [])
    found = False
    for k in keys:
        if k.get('signing_key_id') == args.id:
            k['status'] = 'REVOKED'
            k['revoked_at'] = args.revoked_at or datetime.utcnow().isoformat()
            k['revocation_reason'] = args.reason
            found = True
            break

    if not found:
        print(f"Key {args.id} not found in registry")
        return 1

    reg['keys'] = keys
    write_json(registry_path, reg)
    print(f"Revoked key {args.id} in {registry_path}")
    return 0


def build_verify_output(decision_record):
    # Convert DecisionRecord to CLI JSON output
    return {
        "ok": decision_record.decision == 'SHIP',
        "registry_hash": None,
        "policy_registry_hash": getattr(decision_record, 'policy_hash', None),
        "violations": [ {"reason_code": r, "detail": r} for r in decision_record.blocking_reasons ]
    }


def cmd_verify(args):
    # Lazy import mayor to avoid startup cost
    from oracle_town.core.policy import Policy
    from oracle_town.core.mayor_rsm import MayorRSM

    policy = load_json(args.policy)
    briefcase = load_json(args.briefcase)
    ledger = load_json(args.ledger)

    # Build Policy object
    from oracle_town.core.policy import Policy as PolicyClass
    policy_obj = PolicyClass.from_dict(policy)

    mayor = MayorRSM(public_keys_path=args.registry)
    decision = mayor.decide(policy_obj, briefcase, ledger)

    out = {
        "ok": decision.decision == 'SHIP',
        "registry_hash": mayor.key_registry.registry_hash if mayor.key_registry else None,
        "policy_registry_hash": policy_obj.key_registry_hash,
        "violations": []
    }

    for r in decision.blocking_reasons:
        # Try to extract attestation id/obligation from message if present
        out['violations'].append({"reason_code": r, "detail": r})

    print(json.dumps(out, indent=2))
    return 0


def cmd_sign_registry(args):
    registry_path = args.registry
    reg = load_json(registry_path)
    canonical = canonical_json_bytes(reg)
    # Compute hash
    reg_hash = compute_registry_hash(reg)

    manifest = {
        "registry_id": reg.get('registry_id', 'KEYREG-ORACLE-TOWN'),
        "registry_version": reg.get('registry_version', '1.0.0'),
        "created_at": datetime.utcnow().isoformat(),
        "registry_hash": reg_hash,
        "policy_compat": args.policy_compat or {},
        "notes": args.notes or "Signed registry manifest"
    }

    # Sign canonical manifest bytes (use canonical JSON of manifest)
    manifest_bytes = canonical_json_bytes(manifest)

    # Accept private key base64 directly or from file
    private_b64 = args.private_key_b64
    if args.private_key_file:
        with open(args.private_key_file, 'r') as f:
            private_b64 = f.read().strip()

    if not private_b64:
        print("No private key provided for signing")
        return 2

    sig_b64 = sign_ed25519(private_b64, manifest_bytes)

    signed = {"manifest": manifest, "signature": {"signer_key_id": args.signer_id, "signature_b64": sig_b64}}
    out_path = args.out or (os.path.splitext(registry_path)[0] + ".manifest.signed.json")
    write_json(out_path, signed)
    print(f"Wrote signed manifest to {out_path}")
    return 0


def main():
    p = argparse.ArgumentParser(prog='oracle-town keys')
    sub = p.add_subparsers(dest='cmd')

    # add
    pa = sub.add_parser('add')
    pa.add_argument('--registry', default='oracle_town/keys/public_keys.json')
    pa.add_argument('--id', required=True)
    pa.add_argument('--attestor-class', dest='attestor_class', required=True)
    pa.add_argument('--pub', required=True)
    pa.add_argument('--allow-obligations')
    pa.add_argument('--policy-ids')
    pa.add_argument('--owner')
    pa.set_defaults(func=cmd_add)

    # revoke
    pr = sub.add_parser('revoke')
    pr.add_argument('--registry', default='oracle_town/keys/public_keys.json')
    pr.add_argument('--id', required=True)
    pr.add_argument('--reason', required=True)
    pr.add_argument('--revoked-at', dest='revoked_at')
    pr.set_defaults(func=cmd_revoke)

    # verify
    pv = sub.add_parser('verify')
    pv.add_argument('--policy', required=True)
    pv.add_argument('--briefcase', required=True)
    pv.add_argument('--ledger', required=True)
    pv.add_argument('--registry', default='oracle_town/keys/public_keys.json')
    pv.set_defaults(func=cmd_verify)

    # sign-registry
    ps = sub.add_parser('sign-registry')
    ps.add_argument('--registry', default='oracle_town/keys/public_keys.json')
    ps.add_argument('--private-key-b64')
    ps.add_argument('--private-key-file')
    ps.add_argument('--signer-id', required=True)
    ps.add_argument('--out')
    ps.add_argument('--notes')
    ps.add_argument('--policy-compat', type=json.loads, default=None)
    ps.set_defaults(func=cmd_sign_registry)

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return 0
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
