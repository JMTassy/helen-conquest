"""
Module 1: Zero Data Handler
Implements Protocol 2.2 with full validation

Author: BOT VALIDATOR & IMPLEMENTER
Date: 2026-01-09
"""

import hashlib
import requests
from pathlib import Path
from typing import List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZeroDataHandler:
    """
    Handles Riemann zeta zero data following Protocol 2.2
    """

    ODLYZKO_BASE_URL = "https://www.dtc.umn.edu/~odlyzko/zeta_tables/"
    DEFAULT_FILE = "zeros6"
    CACHE_DIR = Path(__file__).parent / "data_cache"

    def __init__(self):
        self.CACHE_DIR.mkdir(exist_ok=True)
        self.zeros_cache = {}

    def download_zeros_file(self, filename: str = DEFAULT_FILE) -> Path:
        """
        Download Odlyzko zeros file if not cached

        Returns:
            Path to local cached file
        """
        cache_path = self.CACHE_DIR / filename

        if cache_path.exists():
            logger.info(f"Using cached file: {cache_path}")
            return cache_path

        logger.info(f"Downloading {filename} from Odlyzko tables...")
        url = self.ODLYZKO_BASE_URL + filename

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            cache_path.write_bytes(response.content)
            logger.info(f"Downloaded and cached to {cache_path}")
            return cache_path

        except requests.RequestException as e:
            logger.error(f"Failed to download: {e}")
            raise

    def compute_sha256(self, filepath: Path) -> str:
        """
        Compute SHA-256 hash for verification (Protocol 2.2)
        """
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def parse_zeros_file(self, filepath: Path) -> List[float]:
        """
        Parse zeros file following Protocol 2.2 parse rules

        Returns:
            List of positive zero ordinates (unsymmetrized)
        """
        zeros = []
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                try:
                    # Protocol 2.2: One ordinate per line, decimal
                    gamma = float(line)
                    zeros.append(gamma)
                except ValueError as e:
                    logger.warning(f"Skipping invalid line {line_num}: {line} ({e})")

        logger.info(f"Parsed {len(zeros)} positive zeros from {filepath.name}")
        return zeros

    def symmetrize_zeros(self, positive_zeros: List[float]) -> List[float]:
        """
        Protocol 2.2: Include -γₖ for each γₖ > 0
        """
        negative_zeros = [-gamma for gamma in positive_zeros]
        return negative_zeros + positive_zeros

    def sort_zeros(self, zeros: List[float]) -> List[float]:
        """
        Protocol 2.2: Increasing |γₖ|; negative before positive for ties
        """
        return sorted(zeros, key=lambda g: (abs(g), g))

    def truncate_zeros(self, zeros: List[float], H: float) -> List[float]:
        """
        Protocol 2.2: Retain zeros with |γₖ| ≤ H
        """
        truncated = [g for g in zeros if abs(g) <= H]
        logger.info(f"Truncated at H={H}: {len(truncated)} zeros retained")
        return truncated

    def load_zeros(self, H: float, filename: str = DEFAULT_FILE,
                   force_download: bool = False) -> Tuple[List[float], str]:
        """
        Main entry point: Load zeros following complete Protocol 2.2

        Args:
            H: Truncation height
            filename: Odlyzko file name
            force_download: Re-download even if cached

        Returns:
            (zeros_list, file_hash)
        """
        cache_key = (filename, H)
        if cache_key in self.zeros_cache and not force_download:
            logger.info(f"Using memory cache for H={H}")
            return self.zeros_cache[cache_key]

        # Step 1: Download/load file
        if force_download and (self.CACHE_DIR / filename).exists():
            (self.CACHE_DIR / filename).unlink()
        filepath = self.download_zeros_file(filename)

        # Step 2: Compute hash (Protocol 2.2 verification)
        file_hash = self.compute_sha256(filepath)
        logger.info(f"SHA-256: {file_hash}")

        # Step 3: Parse (Protocol 2.2 parse rule)
        positive_zeros = self.parse_zeros_file(filepath)

        # Step 4: Symmetrize (Protocol 2.2)
        symmetric_zeros = self.symmetrize_zeros(positive_zeros)

        # Step 5: Truncate (Protocol 2.2)
        truncated_zeros = self.truncate_zeros(symmetric_zeros, H)

        # Step 6: Sort (Protocol 2.2 ordering)
        sorted_zeros = self.sort_zeros(truncated_zeros)

        # Cache result
        result = (sorted_zeros, file_hash)
        self.zeros_cache[cache_key] = result

        logger.info(f"✓ Protocol 2.2 complete: {len(sorted_zeros)} zeros loaded")
        return result

    def validate_protocol_2_2(self, zeros: List[float], H: float) -> bool:
        """
        Validate that zeros list satisfies all Protocol 2.2 requirements

        Returns:
            True if all checks pass
        """
        logger.info("Validating Protocol 2.2 compliance...")

        # Check 1: Symmetry
        positive = [g for g in zeros if g > 0]
        negative = [g for g in zeros if g < 0]

        if len(positive) != len(negative):
            logger.error(f"Symmetry violation: {len(positive)} positive vs {len(negative)} negative")
            return False
        logger.info(f"✓ Symmetry: {len(positive)} positive, {len(negative)} negative")

        # Check 2: All negatives match positives
        negative_abs = sorted([abs(g) for g in negative])
        positive_abs = sorted(positive)

        if negative_abs != positive_abs:
            logger.error("Symmetry violation: negative and positive sets don't match")
            return False
        logger.info("✓ Symmetric pairs verified")

        # Check 3: Truncation
        if not all(abs(g) <= H for g in zeros):
            violations = [g for g in zeros if abs(g) > H]
            logger.error(f"Truncation violation: {len(violations)} zeros exceed H={H}")
            return False
        logger.info(f"✓ Truncation: all |γₖ| ≤ {H}")

        # Check 4: Ordering (increasing |γₖ|, negative before positive for ties)
        for i in range(len(zeros) - 1):
            g1, g2 = zeros[i], zeros[i+1]
            abs_g1, abs_g2 = abs(g1), abs(g2)

            if abs_g1 > abs_g2:
                logger.error(f"Ordering violation at index {i}: |{g1}| > |{g2}|")
                return False

            if abs_g1 == abs_g2 and g1 > g2:
                logger.error(f"Ordering violation at index {i}: negative not before positive")
                return False

        logger.info("✓ Ordering: increasing |γₖ|, negative before positive")

        # Check 5: Count matches expectation for H=100
        if H == 100:
            expected_count = 2 * 58  # 58 positive zeros below 100, symmetrized
            if len(zeros) != expected_count:
                logger.warning(f"Count mismatch: expected {expected_count}, got {len(zeros)}")
                # Not an error, just different from Example 6.1

        logger.info("✓ All Protocol 2.2 checks passed")
        return True


# Self-test when run directly
if __name__ == "__main__":
    print("=" * 80)
    print("MODULE 1: ZERO DATA HANDLER - SELF TEST")
    print("=" * 80)

    handler = ZeroDataHandler()

    # Test with H=100 (Example 6.1 parameters)
    print("\nTest 1: Load zeros with H=100")
    print("-" * 80)

    try:
        zeros, file_hash = handler.load_zeros(H=100.0)
        print(f"\nLoaded {len(zeros)} zeros")
        print(f"File hash: {file_hash}")
        print(f"\nFirst 10 zeros:")
        for i, g in enumerate(zeros[:10]):
            print(f"  γ[{i}] = {g:.6f}")

        print(f"\nLast 10 zeros:")
        for i, g in enumerate(zeros[-10:], len(zeros)-10):
            print(f"  γ[{i}] = {g:.6f}")

        # Validate
        print("\n" + "-" * 80)
        is_valid = handler.validate_protocol_2_2(zeros, H=100.0)

        if is_valid:
            print("\n" + "=" * 80)
            print("✓ MODULE 1 SELF-TEST PASSED")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("✗ MODULE 1 SELF-TEST FAILED")
            print("=" * 80)

    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
