"""
Compatibility shim.

Tests import:
  from helen.utils.redaction import sanitize_output_for_airi, redact_secrets, emotion_map

Real implementation lives in:
  helen_os.utils.redaction
"""
from helen_os.utils.redaction import sanitize_output_for_airi, redact_secrets, emotion_map  # noqa: F401
