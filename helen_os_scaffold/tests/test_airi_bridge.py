"""
tests/test_airi_bridge.py

Test suite for AIRI bridge (hardened, non-sovereign integration).

Scenarios:
1. Token sanitization (authority tokens removed)
2. Secret redaction (API keys, passwords redacted)
3. Hash redaction (SHA256 hashes removed)
4. Emotion mapping (correct emotion from text)
5. Error handling (malformed input, empty input)
6. Fail-closed (always return valid output)
"""

import pytest
from helen.utils.redaction import sanitize_output_for_airi, redact_secrets, emotion_map
from helen.integrations.airi_bridge import AIRIBridge


class TestSecretRedaction:
    """Test secret redaction (API keys, passwords, tokens)."""

    def test_redact_api_key_bearer(self):
        """Bearer token redaction."""
        text = "Use Bearer eyJhbGc..."
        result = redact_secrets(text)
        assert "[REDACTED]" in result
        assert "eyJhbGc" not in result

    def test_redact_api_key_simple(self):
        """api_key redaction."""
        text = "Configure api_key=sk-1234567890"
        result = redact_secrets(text)
        assert "[REDACTED]" in result
        assert "sk-1234567890" not in result

    def test_redact_password(self):
        """Password redaction."""
        text = "password: secretpass123"
        result = redact_secrets(text)
        assert "[REDACTED]" in result
        assert "secretpass123" not in result

    def test_no_false_positives(self):
        """Don't redact normal text."""
        text = "The API is working fine"
        result = redact_secrets(text)
        assert result == text


class TestTokenSanitization:
    """Test authority token removal."""

    def test_strip_verdict(self):
        """VERDICT token stripped."""
        text = "The VERDICT is approved."
        safe_text, redactions = sanitize_output_for_airi(text)
        assert "VERDICT" not in safe_text
        assert "[REDACTED]" in safe_text
        assert "authority_token:VERDICT" in redactions

    def test_strip_seal(self):
        """SEAL token stripped."""
        text = "Status: SEALED"
        safe_text, redactions = sanitize_output_for_airi(text)
        assert "SEALED" not in safe_text
        assert "authority_token:SEALED" in redactions

    def test_strip_ship(self):
        """SHIP token stripped."""
        text = "Ready to SHIP"
        safe_text, redactions = sanitize_output_for_airi(text)
        assert "SHIP" not in safe_text

    def test_multiple_tokens(self):
        """Multiple tokens stripped."""
        text = "VERDICT: APPROVED. SEAL: SHIP"
        safe_text, redactions = sanitize_output_for_airi(text)
        assert "VERDICT" not in safe_text
        assert "APPROVED" not in safe_text
        assert "SEAL" not in safe_text
        assert "SHIP" not in safe_text


class TestHashRedaction:
    """Test hash redaction (SHA256, etc.)."""

    def test_strip_sha256_hash(self):
        """SHA256 hash stripped."""
        text = f"Receipt hash: {'a' * 64}"
        safe_text, redactions = sanitize_output_for_airi(text)
        assert "a" * 64 not in safe_text
        assert "[HASH]" in safe_text
        assert "hash:hex64" in redactions

    def test_preserve_non_hex(self):
        """Non-hash strings preserved."""
        text = "Transaction ID: abc123xyz"
        safe_text, redactions = sanitize_output_for_airi(text)
        assert "abc123xyz" in safe_text  # Only 64-char hex removed


class TestPathRedaction:
    """Test filesystem path redaction."""

    def test_strip_town_path(self):
        """Town directory path stripped."""
        text = "Storage: /town/ledger.ndjson"
        safe_text, redactions = sanitize_output_for_airi(text)
        assert "/town/" not in safe_text
        assert "[PATH]" in safe_text
        assert "path:filesystem" in redactions

    def test_strip_db_references(self):
        """Database references stripped."""
        text = "Database: memory.db"
        safe_text, redactions = sanitize_output_for_airi(text)
        assert "memory.db" not in safe_text


class TestEmotionMapping:
    """Test emotion state detection from text."""

    def test_emotion_concerned(self):
        """Error text → concerned."""
        assert emotion_map("An error occurred") == "concerned"
        assert emotion_map("Failed to process") == "concerned"
        assert emotion_map("Warning: conflict detected") == "concerned"

    def test_emotion_happy(self):
        """Success text → happy."""
        assert emotion_map("Task completed successfully") == "happy"
        assert emotion_map("Perfect! All done.") == "happy"
        assert emotion_map("Excellent work.") == "happy"

    def test_emotion_thinking(self):
        """Reflection text → thinking."""
        assert emotion_map("Let me consider this") == "thinking"
        assert emotion_map("I'm puzzled by this") == "thinking"
        assert emotion_map("There's a tension here") == "thinking"

    def test_emotion_neutral(self):
        """Normal text → neutral."""
        assert emotion_map("The weather is nice") == "neutral"
        assert emotion_map("Here's some information") == "neutral"
        assert emotion_map("") == "neutral"


class TestAIRIBridgeErrorHandling:
    """Test bridge error handling (fail-closed)."""

    def test_error_response_structure(self):
        """Error response has correct structure."""
        bridge = AIRIBridge()
        response = bridge._error_response("Test error")

        assert response["type"] == "output"
        assert response["text"] == "Test error"
        assert response["emotion"] == "concerned"

    @pytest.mark.asyncio
    async def test_handle_malformed_input_non_dict(self):
        """Malformed input (not dict) handled gracefully."""
        bridge = AIRIBridge()
        response = await bridge._handle_input("not a dict")

        assert response["type"] == "output"
        assert "Malformed" in response["text"]
        assert response["emotion"] == "concerned"

    @pytest.mark.asyncio
    async def test_handle_missing_type_field(self):
        """Missing 'type' field handled gracefully."""
        bridge = AIRIBridge()
        response = await bridge._handle_input({"text": "hello"})

        assert response["type"] == "output"
        assert "type='input'" in response["text"]
        assert response["emotion"] == "concerned"

    @pytest.mark.asyncio
    async def test_handle_empty_text(self):
        """Empty user text handled gracefully."""
        bridge = AIRIBridge()
        response = await bridge._handle_input({"type": "input", "text": "   "})

        assert response["type"] == "output"
        assert "Empty" in response["text"]
        assert response["emotion"] == "concerned"


class TestComprehensiveFlow:
    """Integration tests for full sanitization flow."""

    def test_full_sanitization_with_multiple_risks(self):
        """Text with multiple security risks fully sanitized."""
        text = (
            "VERDICT: APPROVED. "
            "Receipt: abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789 "
            "Stored at /town/ledger.ndjson. "
            "API Key: sk-secret123"
        )

        safe_text, redactions = sanitize_output_for_airi(text)

        # All risks removed
        assert "VERDICT" not in safe_text
        assert "APPROVED" not in safe_text
        assert "abcdef01" not in safe_text  # Hash truncated
        assert "/town/" not in safe_text
        assert "sk-secret" not in safe_text

        # Redactions recorded
        assert len(redactions) > 0

    def test_safe_output_is_readable(self):
        """Sanitized output remains human-readable."""
        text = (
            "The task VERDICT is APPROVED. "
            "Check receipt abc123def456 for details. "
            "Store results in /town/data.ndjson"
        )

        safe_text, redactions = sanitize_output_for_airi(text)

        # Output is still sensible
        assert len(safe_text) > 10
        assert safe_text  # Not empty
        assert not safe_text.startswith("[")  # Not all redactions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
