"""
ADHD-Friendly Terminal Colors for HELEN
========================================

Visual hierarchy for clarity. Colors signal meaning, not decoration.

Usage:
    from helen_os.ui.colors import Colors
    print(f"{Colors.HER}[HER]{Colors.RESET} This is HER speaking")
    print(f"{Colors.HAL_VERDICT}[PASS]{Colors.RESET} All gates verified")
"""

class Colors:
    """ANSI color codes for terminal output."""

    # === ACTORS ===
    # HER = cyan (cool, thinking, exploratory)
    HER = "\033[96m"  # Bright cyan

    # HAL = yellow (warm, auditing, critical)
    HAL = "\033[93m"  # Bright yellow

    # HELEN (system) = magenta (authority, sovereign)
    HELEN = "\033[95m"  # Bright magenta

    # === VERDICTS ===
    # PASS = green (all clear)
    PASS = "\033[92m"  # Bright green

    # WARN = orange (caution, needs attention)
    WARN = "\033[38;5;208m"  # Orange (256-color palette)

    # FAIL/BLOCK = red (stop, critical)
    FAIL = "\033[91m"  # Bright red

    # === STRUCTURES ===
    # Receipt = dim blue (verified, historical)
    RECEIPT = "\033[34m"  # Standard blue

    # Gate = purple (constraint, boundary)
    GATE = "\033[35m"  # Magenta

    # Keyword/emphasis = bold white (draw attention)
    BOLD = "\033[1m"  # Bold
    BOLD_WHITE = "\033[1;37m"  # Bold white

    # === SEMANTIC ===
    # Input = white (neutral, listening)
    INPUT = "\033[37m"  # White

    # Output = white (default)
    OUTPUT = "\033[37m"  # White

    # Comment/meta = dark gray (low priority)
    META = "\033[90m"  # Bright black (dark gray)

    # === UTILITY ===
    RESET = "\033[0m"  # Reset all formatting
    CLEAR = "\033c"  # Clear screen

    @classmethod
    def her(cls, text: str) -> str:
        """Format HER output (cyan)."""
        return f"{cls.HER}[HER]{cls.RESET} {text}"

    @classmethod
    def hal(cls, text: str) -> str:
        """Format HAL output (yellow)."""
        return f"{cls.HAL}[HAL]{cls.RESET} {text}"

    @classmethod
    def verdict_pass(cls, text: str) -> str:
        """Format PASS verdict (green)."""
        return f"{cls.PASS}✅ PASS{cls.RESET} {text}"

    @classmethod
    def verdict_warn(cls, text: str) -> str:
        """Format WARN verdict (orange)."""
        return f"{cls.WARN}⚠️  WARN{cls.RESET} {text}"

    @classmethod
    def verdict_fail(cls, text: str) -> str:
        """Format FAIL verdict (red)."""
        return f"{cls.FAIL}❌ FAIL{cls.RESET} {text}"

    @classmethod
    def receipt(cls, text: str) -> str:
        """Format receipt (blue)."""
        return f"{cls.RECEIPT}📋 {text}{cls.RESET}"

    @classmethod
    def gate_result(cls, gate_id: str, passed: bool, message: str) -> str:
        """Format gate result with color."""
        status = cls.verdict_pass("PASS") if passed else cls.verdict_fail("FAIL")
        gate_colored = f"{cls.GATE}{gate_id}{cls.RESET}"
        return f"{status} {gate_colored}: {message}"

    @classmethod
    def section_header(cls, title: str) -> str:
        """Format section header (bold cyan)."""
        return f"{cls.BOLD}{cls.HER}{'='*60}{cls.RESET}\n{cls.BOLD}{cls.HER}{title}{cls.RESET}\n{cls.BOLD}{cls.HER}{'='*60}{cls.RESET}"

    @classmethod
    def subsection_header(cls, title: str) -> str:
        """Format subsection header (cyan)."""
        return f"{cls.HER}→ {title}{cls.RESET}"

    @classmethod
    def meta(cls, text: str) -> str:
        """Format metadata/comment (dark gray)."""
        return f"{cls.META}{text}{cls.RESET}"

    @classmethod
    def disable_all(cls):
        """For non-TTY output (logs, piping), disable colors."""
        cls.HER = ""
        cls.HAL = ""
        cls.HELEN = ""
        cls.PASS = ""
        cls.WARN = ""
        cls.FAIL = ""
        cls.RECEIPT = ""
        cls.GATE = ""
        cls.BOLD = ""
        cls.BOLD_WHITE = ""
        cls.INPUT = ""
        cls.OUTPUT = ""
        cls.META = ""
        cls.RESET = ""


if __name__ == "__main__":
    # Demo: Show all colors
    print(f"\n{Colors.section_header('HELEN Terminal Colors Demo')}\n")

    print(Colors.her("This is HER (cyan) - exploratory and generative"))
    print(Colors.hal("This is HAL (yellow) - auditing and verification"))
    print(f"{Colors.HELEN}[HELEN]{Colors.RESET} This is the sovereign system (magenta)")

    print(f"\n{Colors.subsection_header('Verdicts')}\n")
    print(Colors.verdict_pass("All gates passed"))
    print(Colors.verdict_warn("Manual approval required"))
    print(Colors.verdict_fail("Tool not in allowlist"))

    print(f"\n{Colors.subsection_header('Gate Results')}\n")
    print(Colors.gate_result("G0", True, "Tool 'web_search' is in allowlist"))
    print(Colors.gate_result("G1", False, "Tool 'shell_execute' requires approval"))

    print(f"\n{Colors.subsection_header('Receipts')}\n")
    print(Colors.receipt("entry_hash=abc123... cumulative=def456..."))

    print(f"\n{Colors.subsection_header('Metadata')}\n")
    print(Colors.meta("[timestamp: 2026-03-06T15:30:00Z]"))

    print(f"\n{Colors.RESET}")
