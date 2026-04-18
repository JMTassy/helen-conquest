import hashlib
import os
import json
from typing import Dict, Any, List

class BootVerifier:
    """
    Computes environmental hashes to ensure system integrity.
    """
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.monitored_files = [
            "helen_os/kernel.py",
            "helen_os/town/ledger_writer_v2.py",
            "helen_os/tools/redaction.py",
            "helen_os/tools/path_safety.py",
            "helen_os/helen.py"
        ]

    def _hash_file(self, rel_path: str) -> str:
        abs_path = os.path.join(self.base_dir, rel_path)
        if not os.path.exists(abs_path):
            return "MISSING"
        
        sha256 = hashlib.sha256()
        with open(abs_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def compute_env_bundle_hash(self) -> str:
        """
        Computes a single hash representing the entire monitored environment.
        """
        hashes = {f: self._hash_file(f) for f in self.monitored_files}
        # Add requirements.txt if exists
        req_path = os.path.join(self.base_dir, "requirements.txt")
        if os.path.exists(req_path):
            hashes["requirements.txt"] = self._hash_file("requirements.txt")
            
        canon = json.dumps(hashes, sort_keys=True)
        return hashlib.sha256(canon.encode()).hexdigest()

    def verify_against_seal(self, seal_payload: Dict[str, Any]) -> bool:
        """
        Verifies current environment against a SEAL_V2 payload.
        """
        if seal_payload.get("type") != "SEAL_V2":
            return False
            
        current_hash = self.compute_env_bundle_hash()
        pinned_hash = seal_payload.get("env_hash")
        
        return current_hash == pinned_hash

    def get_status(self) -> Dict[str, Any]:
        return {
            "monitored_files": self.monitored_files,
            "bundle_hash": self.compute_env_bundle_hash()
        }
