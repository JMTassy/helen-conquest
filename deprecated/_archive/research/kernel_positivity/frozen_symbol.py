"""
Module 2: Frozen Symbol Constructor
Implements Protocol 2.1 with high-precision arithmetic

Author: BOT VALIDATOR & IMPLEMENTER
Date: 2026-01-09
"""

import mpmath as mp
from typing import Callable, List
import logging

logger = logging.getLogger(__name__)


class FrozenSymbol:
    """
    Constructs frozen symbol m_w following Protocol 2.1
    """

    def __init__(self, zeros: List[float], weight_func: Callable = None,
                 precision_dps: int = 50):
        """
        Args:
            zeros: List of zero ordinates (symmetric, from Protocol 2.2)
            weight_func: Weight function w(α). If None, uses Gaussian.
            precision_dps: Decimal precision (Protocol 3.2: 50)
        """
        mp.dps = precision_dps
        self.dps = precision_dps

        # Convert zeros to mpmath with high precision
        self.zeros = [mp.mpf(str(g)) for g in zeros]
        self.N_gamma = len(self.zeros)

        # Default: Gaussian weight w(α) = π^{-1/2} exp(-α²)
        if weight_func is None:
            self.w = lambda alpha: mp.exp(-alpha**2) / mp.sqrt(mp.pi)
        else:
            self.w = weight_func

        # Protocol 2.1: Compute counterterm C_w
        self.C_w = self._compute_counterterm()

        logger.info(f"✓ Frozen symbol initialized:")
        logger.info(f"  Precision: {precision_dps} decimal places")
        logger.info(f"  Zeros: {self.N_gamma}")
        logger.info(f"  C_w = {self.C_w}")

    def _compute_counterterm(self) -> mp.mpf:
        """
        Protocol 2.1, Eq 2.2: C_w = Σw(γₖ) / (N_γ · w(0))
        """
        w_zero = self.w(mp.mpf(0))

        if abs(w_zero) < mp.mpf('1e-100'):
            raise ValueError("w(0) is too close to zero")

        # Sum with deterministic ordering (Protocol 3.2)
        # Increasing |γₖ|, negative before positive (already sorted)
        numerator = sum(self.w(gamma) for gamma in self.zeros)
        denominator = self.N_gamma * w_zero

        C_w = numerator / denominator
        return C_w

    def m_w(self, xi: float) -> mp.mpf:
        """
        Frozen symbol (Protocol 2.1, Eq 2.3):
        m_w(ξ) = Σw(ξ - γₖ) - C_w · w(ξ)

        Args:
            xi: Evaluation point

        Returns:
            Value of frozen symbol at ξ
        """
        xi_mp = mp.mpf(str(xi)) if not isinstance(xi, mp.mpf) else xi

        # Sum with deterministic ordering (Protocol 3.2)
        sum_term = sum(self.w(xi_mp - gamma) for gamma in self.zeros)
        counterterm = self.C_w * self.w(xi_mp)

        return sum_term - counterterm

    def validate_remark_2_3(self, test_points: List[float] = None) -> bool:
        """
        Validate Remark 2.3 properties:
        (1) m_w is real-valued (implicit in mpmath.mpf)
        (2) m_w is even: m_w(-ξ) = m_w(ξ)
        (3) m_w(0) = 0

        Returns:
            True if all checks pass
        """
        logger.info("Validating Remark 2.3...")

        tolerance = mp.mpf(10) ** (-self.dps + 5)  # Leave 5 digits slack

        # Check (3): m_w(0) = 0
        m_zero = self.m_w(mp.mpf(0))
        if abs(m_zero) > tolerance:
            logger.error(f"Remark 2.3(3) violation: m_w(0) = {m_zero} (should be 0)")
            return False
        logger.info(f"✓ Remark 2.3(3): m_w(0) = {m_zero:.3e} ≈ 0")

        # Check (2): m_w even
        if test_points is None:
            test_points = [0.1, 0.5, 1.0, 2.0, 5.0]

        max_asymmetry = mp.mpf(0)
        for xi in test_points:
            m_pos = self.m_w(mp.mpf(str(xi)))
            m_neg = self.m_w(mp.mpf(str(-xi)))
            asymmetry = abs(m_pos - m_neg)
            max_asymmetry = max(max_asymmetry, asymmetry)

            if asymmetry > tolerance:
                logger.error(f"Remark 2.3(2) violation at ξ={xi}: |m_w({xi}) - m_w({-xi})| = {asymmetry}")
                return False

        logger.info(f"✓ Remark 2.3(2): max asymmetry = {max_asymmetry:.3e} (even function)")

        # Check (1): real-valued (implicit, but verify no imaginary part)
        test_real = [self.m_w(mp.mpf(str(xi))) for xi in test_points]
        if any(mp.im(val) != 0 for val in test_real):
            logger.error("Remark 2.3(1) violation: imaginary component detected")
            return False
        logger.info("✓ Remark 2.3(1): real-valued")

        logger.info("✓ All Remark 2.3 properties verified")
        return True

    def compute_lipschitz_constant(self, w_prime: Callable = None) -> mp.mpf:
        """
        Lemma 4.1: L_m = (N_γ + |C_w|) ||w'||_∞

        For Gaussian w(α) = π^{-1/2} exp(-α²):
        w'(α) = -2α/√π · exp(-α²)

        Args:
            w_prime: Derivative of weight function. If None, uses Gaussian derivative.

        Returns:
            Lipschitz constant L_m
        """
        if w_prime is None:
            # Gaussian derivative
            w_prime = lambda alpha: -2*alpha/mp.sqrt(mp.pi) * mp.exp(-alpha**2)

        # Estimate ||w'||_∞ numerically over [-10, 10]
        # For Gaussian, max is at α ≈ ±1/√2
        alpha_test = [mp.mpf(a) for a in mp.linspace(-10, 10, 1000)]
        w_prime_values = [abs(w_prime(a)) for a in alpha_test]
        w_prime_max = max(w_prime_values)

        L_m = (self.N_gamma + abs(self.C_w)) * w_prime_max

        logger.info(f"Lipschitz constant (Lemma 4.1):")
        logger.info(f"  ||w'||_∞ ≈ {w_prime_max}")
        logger.info(f"  L_m = (N_γ + |C_w|) ||w'||_∞ = {L_m}")

        return L_m

    def verify_lipschitz_empirically(self, L_m: mp.mpf = None,
                                     test_interval: tuple = (-5, 5),
                                     n_samples: int = 500) -> bool:
        """
        Empirical verification of Lemma 4.1

        Returns:
            True if empirical Lipschitz constant ≤ theoretical L_m
        """
        if L_m is None:
            L_m = self.compute_lipschitz_constant()

        logger.info("Empirically verifying Lemma 4.1...")

        xi_test = [mp.mpf(x) for x in mp.linspace(test_interval[0], test_interval[1], n_samples)]
        lipschitz_ratios = []

        for i in range(len(xi_test) - 1):
            xi1, xi2 = xi_test[i], xi_test[i+1]
            m1, m2 = self.m_w(xi1), self.m_w(xi2)

            if xi2 != xi1:
                ratio = abs(m1 - m2) / abs(xi1 - xi2)
                lipschitz_ratios.append(ratio)

        empirical_L = max(lipschitz_ratios)
        slack = mp.mpf('1e-6')  # Tiny numerical tolerance

        if empirical_L <= L_m * (1 + slack):
            logger.info(f"✓ Lemma 4.1 verified:")
            logger.info(f"  Theoretical L_m = {L_m}")
            logger.info(f"  Empirical max = {empirical_L}")
            return True
        else:
            logger.error(f"Lemma 4.1 violation:")
            logger.error(f"  Theoretical L_m = {L_m}")
            logger.error(f"  Empirical max = {empirical_L}")
            return False


# Self-test
if __name__ == "__main__":
    print("=" * 80)
    print("MODULE 2: FROZEN SYMBOL CONSTRUCTOR - SELF TEST")
    print("=" * 80)

    # Import Module 1 for zero data
    from zero_data import ZeroDataHandler

    handler = ZeroDataHandler()
    zeros, file_hash = handler.load_zeros(H=100.0)

    print(f"\nLoaded {len(zeros)} zeros (H=100)")
    print(f"File hash: {file_hash[:16]}...")

    # Initialize frozen symbol
    print("\n" + "-" * 80)
    print("Initializing frozen symbol (Protocol 2.1)...")
    print("-" * 80)

    fs = FrozenSymbol(zeros, precision_dps=50)

    print(f"\nC_w = {fs.C_w}")
    print(f"Expected (Example 6.1): C_w ≈ 32.85")
    print(f"Match: {abs(float(fs.C_w) - 32.85) < 0.1}")

    # Validate Remark 2.3
    print("\n" + "-" * 80)
    print("Validating Remark 2.3...")
    print("-" * 80)

    remark_valid = fs.validate_remark_2_3()

    # Test Lemma 4.1
    print("\n" + "-" * 80)
    print("Testing Lemma 4.1 (Lipschitz constant)...")
    print("-" * 80)

    L_m = fs.compute_lipschitz_constant()
    lipschitz_valid = fs.verify_lipschitz_empirically(L_m)

    # Evaluate at some points
    print("\n" + "-" * 80)
    print("Sample evaluations of m_w(ξ):")
    print("-" * 80)

    test_xi = [0.0, 0.5, 1.0, 2.0]
    for xi in test_xi:
        m_val = fs.m_w(xi)
        print(f"  m_w({xi:4.1f}) = {float(m_val):12.6e}")

    # Final verdict
    print("\n" + "=" * 80)
    if remark_valid and lipschitz_valid:
        print("✓ MODULE 2 SELF-TEST PASSED")
    else:
        print("✗ MODULE 2 SELF-TEST FAILED")
    print("=" * 80)
