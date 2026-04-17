#!/usr/bin/env python3
"""
Generate a local demo `private_keys_TEST_ONLY.json` for developer testing.
DO NOT COMMIT the generated file. Use secure key provisioning in CI/production.
"""
import json
import base64
import os

try:
    from nacl.signing import SigningKey
except Exception:
    print("PyNaCl not installed. Install with: pip install pynacl")
    raise

KEY_IDS = [
    "key-2025-12-legal-old",
    "key-2026-01-ci",
    "key-2026-01-legal",
]

def main():
    out = {}
    for kid in KEY_IDS:
        sk = SigningKey.generate()
        out[kid] = base64.b64encode(sk.encode()).decode('ascii')

    path = os.path.join(os.path.dirname(__file__), "private_keys_TEST_ONLY.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote demo keys to {path}")
    print("IMPORTANT: Do not commit this file. Use secure provisioning for production keys.")

if __name__ == '__main__':
    main()
