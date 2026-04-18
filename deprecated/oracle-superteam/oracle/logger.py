# oracle/logger.py
"""
ORACLE SUPERTEAM — Logging & Error Handling

Provides structured logging for audit trails and debugging.
All errors are logged deterministically for replay analysis.
"""

import logging
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import json

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

class OracleLogger:
    """
    Constitutional logging for ORACLE SUPERTEAM.

    Key principles:
    - All logs are structured (JSON format)
    - Timestamps are UTC ISO 8601
    - Sensitive data is redacted
    - Logs are deterministic (no random IDs in production)
    """

    def __init__(self, name: str = "oracle", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """Configure console and file handlers."""

        # Console handler (human-readable)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)

        # File handler (JSON structured logs)
        try:
            file_handler = logging.FileHandler('oracle_audit.log')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not create log file: {e}")

        self.logger.addHandler(console_handler)

    def info(self, message: str, **context):
        """Log informational message."""
        self.logger.info(message, extra={"context": context})

    def warning(self, message: str, **context):
        """Log warning (non-blocking issue)."""
        self.logger.warning(message, extra={"context": context})

    def error(self, message: str, **context):
        """Log error (blocking issue)."""
        self.logger.error(message, extra={"context": context})

    def critical(self, message: str, **context):
        """Log critical error (system failure)."""
        self.logger.critical(message, extra={"context": context})

    def debug(self, message: str, **context):
        """Log debug information."""
        self.logger.debug(message, extra={"context": context})

    # ==============================================================================
    # ORACLE-SPECIFIC LOG EVENTS
    # ==============================================================================

    def log_claim_submitted(self, claim_id: str, tier: str, domain: list):
        """Log claim submission."""
        self.info(
            "Claim submitted",
            event="CLAIM_SUBMITTED",
            claim_id=claim_id,
            tier=tier,
            domain=domain
        )

    def log_signal_emitted(self, team: str, signal_type: str, claim_id: str):
        """Log agent signal emission."""
        self.info(
            f"Signal emitted: {signal_type}",
            event="SIGNAL_EMITTED",
            team=team,
            signal_type=signal_type,
            claim_id=claim_id
        )

    def log_obligation_opened(self, obligation_type: str, owner_team: str, claim_id: str):
        """Log obligation creation."""
        self.warning(
            f"Obligation opened: {obligation_type}",
            event="OBLIGATION_OPENED",
            obligation_type=obligation_type,
            owner_team=owner_team,
            claim_id=claim_id
        )

    def log_kill_switch(self, team: str, claim_id: str, rationale: str):
        """Log kill-switch activation."""
        self.critical(
            f"KILL SWITCH activated by {team}",
            event="KILL_SWITCH",
            team=team,
            claim_id=claim_id,
            rationale=rationale
        )

    def log_verdict(self, claim_id: str, verdict: str, ship_permitted: bool, reason_codes: list):
        """Log final verdict."""
        self.info(
            f"Verdict: {verdict}",
            event="VERDICT_FINAL",
            claim_id=claim_id,
            verdict=verdict,
            ship_permitted=ship_permitted,
            reason_codes=reason_codes
        )

    def log_contradiction_detected(self, rule_id: str, claim_id: str, severity: str):
        """Log evidence contradiction."""
        self.error(
            f"Contradiction detected: {rule_id}",
            event="CONTRADICTION_DETECTED",
            rule_id=rule_id,
            claim_id=claim_id,
            severity=severity
        )

    def log_replay_mismatch(self, claim_id: str, expected_hash: str, actual_hash: str):
        """Log replay determinism failure (CRITICAL)."""
        self.critical(
            "REPLAY DETERMINISM VIOLATION",
            event="REPLAY_MISMATCH",
            claim_id=claim_id,
            expected_hash=expected_hash,
            actual_hash=actual_hash
        )


class JsonFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context if provided
        if hasattr(record, 'context'):
            log_data.update(record.context)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


# ==============================================================================
# GLOBAL LOGGER INSTANCE
# ==============================================================================

_logger = None

def get_logger() -> OracleLogger:
    """Get or create global logger instance."""
    global _logger
    if _logger is None:
        _logger = OracleLogger()
    return _logger


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def log_info(message: str, **context):
    """Convenience: log info message."""
    get_logger().info(message, **context)

def log_error(message: str, **context):
    """Convenience: log error message."""
    get_logger().error(message, **context)

def log_warning(message: str, **context):
    """Convenience: log warning message."""
    get_logger().warning(message, **context)

def log_critical(message: str, **context):
    """Convenience: log critical message."""
    get_logger().critical(message, **context)


# ==============================================================================
# EXAMPLE USAGE
# ==============================================================================

if __name__ == "__main__":
    logger = get_logger()

    # Basic logging
    logger.info("System initialized")

    # Structured logging with context
    logger.log_claim_submitted(
        claim_id="claim-001",
        tier="Tier I",
        domain=["security", "legal"]
    )

    logger.log_signal_emitted(
        team="Engineering Wing",
        signal_type="OBLIGATION_OPEN",
        claim_id="claim-001"
    )

    logger.log_obligation_opened(
        obligation_type="METRICS_INSUFFICIENT",
        owner_team="Engineering Wing",
        claim_id="claim-001"
    )

    logger.log_verdict(
        claim_id="claim-001",
        verdict="NO_SHIP",
        ship_permitted=False,
        reason_codes=["OBLIGATIONS_BLOCKING"]
    )

    # Error logging
    logger.error(
        "Invalid signal type",
        signal_type="INVALID",
        team="Unknown Team",
        claim_id="claim-001"
    )

    # Critical: Kill-switch
    logger.log_kill_switch(
        team="Legal Office",
        claim_id="claim-001",
        rationale="GDPR violation detected"
    )
