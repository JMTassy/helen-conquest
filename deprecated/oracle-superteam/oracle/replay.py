# oracle/replay.py
from oracle.canonical import sha256_hex

def replay_equivalence(manifest_a: dict, manifest_b: dict) -> dict:
    """
    Verifies determinism: inputs_hash and outputs_hash must match.
    """
    ha_in = manifest_a["hashes"]["inputs_hash"]
    hb_in = manifest_b["hashes"]["inputs_hash"]
    ha_out = manifest_a["hashes"]["outputs_hash"]
    hb_out = manifest_b["hashes"]["outputs_hash"]

    return {
        "inputs_hash_equal": ha_in == hb_in,
        "outputs_hash_equal": ha_out == hb_out,
        "a": {"inputs": ha_in, "outputs": ha_out},
        "b": {"inputs": hb_in, "outputs": hb_out},
    }
