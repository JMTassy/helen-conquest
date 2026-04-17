Developer keys and secure provisioning

This folder previously contained `private_keys_TEST_ONLY.json` with demo private keys. That file has been removed from the repository and replaced with `private_keys_TEST_ONLY.json.example` to avoid committing secrets.

To generate a local demo private-keys file for development (DO NOT COMMIT):

```bash
python3 oracle_town/keys/generate_demo_keys.py
```

This will write `oracle_town/keys/private_keys_TEST_ONLY.json` locally. The generated file is intended for local development only; CI and production must use secure secret provisioning (vaults, HSMs, or environment secrets). Add any CI-specific setup to your pipeline to provide private keys at runtime.

Rotation plan (short):
- Remove any committed private keys from the repo (done).
- Provide public-key registry as a signed, versioned artifact.
- Use an HSM or secret manager for production private keys and implement rotation policies.
