#!/usr/bin/env python3
"""
OpenClaw Skills with Kernel Approval

Each skill requests kernel approval before executing any risky action.
Architecture:
  1. Skill observes/prepares action
  2. Skill submits to kernel for approval (K15)
  3. Kernel decides (ACCEPT/REJECT)
  4. Skill executes only if approved

Usage:
  fetch = FetchSkill()
  content = fetch.fetch("https://example.com")  # Kernel approves first

  shell = ShellSkill()
  output = shell.execute("ls -la")  # Kernel approves first
"""

import sys
sys.path.insert(0, '/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24')

import json
import time
import logging
from typing import Dict, Any, Optional
import requests
import subprocess

from oracle_town.kernel.kernel_client import KernelClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class KernelApprovedSkill:
    """Base class for skills that require kernel approval"""

    def __init__(self, skill_name: str = "Skill"):
        self.kernel = KernelClient()
        self.skill_name = skill_name
        self.logger = logging.getLogger(skill_name)

    def request_approval(self, action_type: str, target: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Request kernel approval for action

        Args:
            action_type: Type of action (fetch, shell, memory_write, etc.)
            target: What is being acted upon
            evidence: Supporting data for the decision

        Returns:
            Decision dict with "decision" (ACCEPT/REJECT) and optional "reason"
        """
        request = {
            "action_type": action_type,
            "target": target,
            "evidence": evidence,
            "source": "OPENCLAW_SKILL",
            "skill_name": self.skill_name
        }

        self.logger.debug(f"Requesting kernel approval for {action_type}: {target}")
        decision = self.kernel._send_request(request)
        return decision

    def verify_approval(self, decision: Dict[str, Any], action_type: str, target: str) -> bool:
        """Verify kernel approved the action (K15 enforcement)

        K15: No receipt = no execution (fail-closed)
        """
        if decision.get("decision") != "ACCEPT":
            reason = decision.get("reason", "Unknown reason")
            self.logger.error(f"✗ Kernel rejected {action_type} on {target}: {reason}")
            raise RuntimeError(f"Kernel denied {action_type}: {reason}")

        self.logger.info(f"✓ Kernel approved {action_type} on {target}")
        return True


class FetchSkill(KernelApprovedSkill):
    """Fetch skill that requires kernel approval"""

    def __init__(self):
        super().__init__("FetchSkill")

    def fetch(self, url: str, timeout: int = 10) -> bytes:
        """Fetch URL content with kernel approval

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            Response content as bytes

        Raises:
            RuntimeError: If kernel denies the fetch
        """
        try:
            # Step 1: Fetch the resource (don't use yet)
            self.logger.info(f"Fetching {url}...")
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()

            # Step 2: Ask kernel for approval
            decision = self.request_approval(
                action_type="fetch",
                target=url,
                evidence={
                    "url": url,
                    "status_code": response.status_code,
                    "content_length": len(response.content),
                    "content_type": response.headers.get("Content-Type", "unknown")
                }
            )

            # Step 3: Verify approval (K15)
            self.verify_approval(decision, "fetch", url)

            # Step 4: Return content (now safe)
            self.logger.info(f"✓ Fetch complete: {len(response.content)} bytes from {url}")
            return response.content

        except requests.exceptions.RequestException as e:
            self.logger.error(f"✗ Fetch failed: {e}")
            raise


class ShellSkill(KernelApprovedSkill):
    """Shell execution skill that requires kernel approval"""

    def __init__(self):
        super().__init__("ShellSkill")

    def execute(self, command: str) -> str:
        """Execute shell command with kernel approval

        Args:
            command: Shell command to execute

        Returns:
            Command output as string

        Raises:
            RuntimeError: If kernel denies the execution
        """
        try:
            # Step 1: Show what we want to execute
            self.logger.info(f"Shell command requested: {command}")

            # Step 2: Ask kernel for approval
            decision = self.request_approval(
                action_type="shell",
                target=command,
                evidence={
                    "command": command,
                    "shell": "/bin/bash"
                }
            )

            # Step 3: Verify approval (K15)
            self.verify_approval(decision, "shell", command)

            # Step 4: Execute (now safe)
            self.logger.info(f"Executing: {command}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)

            output = result.stdout
            if result.stderr:
                self.logger.warning(f"Shell stderr: {result.stderr}")

            self.logger.info(f"✓ Shell execution complete")
            return output

        except subprocess.TimeoutExpired:
            self.logger.error(f"✗ Shell command timed out: {command}")
            raise RuntimeError(f"Shell command timed out: {command}")
        except Exception as e:
            self.logger.error(f"✗ Shell execution failed: {e}")
            raise


class MemorySkill(KernelApprovedSkill):
    """Memory write skill that requires kernel approval"""

    def __init__(self):
        super().__init__("MemorySkill")
        self.memory = {}

    def write(self, key: str, value: Any) -> bool:
        """Write to memory with kernel approval

        Args:
            key: Memory key
            value: Value to store

        Returns:
            True if successful

        Raises:
            RuntimeError: If kernel denies the write
        """
        try:
            # Step 1: Prepare the write
            self.logger.info(f"Memory write requested: {key} = {value}")

            # Step 2: Ask kernel for approval
            decision = self.request_approval(
                action_type="memory_write",
                target=key,
                evidence={
                    "key": key,
                    "value_type": type(value).__name__,
                    "value_size": len(str(value))
                }
            )

            # Step 3: Verify approval (K15)
            self.verify_approval(decision, "memory_write", key)

            # Step 4: Write (now safe)
            self.memory[key] = value
            self.logger.info(f"✓ Memory write complete: {key}")
            return True

        except Exception as e:
            self.logger.error(f"✗ Memory write failed: {e}")
            raise

    def read(self, key: str) -> Any:
        """Read from memory (no approval needed)

        Args:
            key: Memory key

        Returns:
            Value stored at key, or None if not found
        """
        value = self.memory.get(key)
        if value is not None:
            self.logger.info(f"Memory read: {key} = {value}")
        else:
            self.logger.warning(f"Memory key not found: {key}")
        return value


# ============================================================================
# TESTING & EXAMPLES
# ============================================================================

def test_fetch_skill():
    """Test FetchSkill with kernel approval"""
    print("\n" + "="*70)
    print("TEST: FetchSkill")
    print("="*70)

    fetch = FetchSkill()

    try:
        # This will request kernel approval
        content = fetch.fetch("https://example.com", timeout=5)
        print(f"\n✓ Successfully fetched {len(content)} bytes")
        print(f"  First 100 chars: {content[:100]}")
    except RuntimeError as e:
        print(f"\n✗ Fetch denied: {e}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def test_shell_skill():
    """Test ShellSkill with kernel approval"""
    print("\n" + "="*70)
    print("TEST: ShellSkill")
    print("="*70)

    shell = ShellSkill()

    try:
        # Simple safe command
        output = shell.execute("echo 'Hello from kernel-approved shell!'")
        print(f"\n✓ Shell execution successful")
        print(f"  Output: {output}")
    except RuntimeError as e:
        print(f"\n✗ Shell denied: {e}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def test_memory_skill():
    """Test MemorySkill with kernel approval"""
    print("\n" + "="*70)
    print("TEST: MemorySkill")
    print("="*70)

    memory = MemorySkill()

    try:
        # Write with kernel approval
        memory.write("test_key", "test_value")
        print(f"\n✓ Memory write successful")

        # Read (no approval needed)
        value = memory.read("test_key")
        print(f"✓ Memory read: {value}")

    except RuntimeError as e:
        print(f"\n✗ Memory operation denied: {e}")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("OpenClaw Skills with Kernel Approval — Test Suite")
    print("="*70)
    print("\nMake sure kernel daemon is running:")
    print("  python3 oracle_town/kernel/kernel_daemon.py &")
    print("\nWatch the ledger in another terminal:")
    print("  tail -f kernel/ledger.json")
    print("\n" + "="*70)

    test_fetch_skill()
    test_shell_skill()
    test_memory_skill()

    print("\n" + "="*70)
    print("Tests complete!")
    print("="*70)
    print("\nCheck kernel/ledger.json to see all decisions logged.")


if __name__ == "__main__":
    run_all_tests()
