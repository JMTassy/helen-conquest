"""
Worktree Isolation: Safe patching in isolated temp directories.

CRITICAL: Prevents contamination of source repository. All patches are applied
in a temporary worktree that is discarded after tool execution.

Invariants:
- Source repo is never modified
- Path traversal is impossible
- Only allowlisted paths can be patched
- Patch application is deterministic (uses GNU patch, not git)
"""
import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass


# Allowlisted paths that can be patched
PATCHABLE_PATHS = {
    "tests/",
    "docs/",
    "examples/",
    "scripts/",
    "oracle_town/creative/",  # Creative extensions only
    "oracle_town/runner/",     # Runner experiments
}

# Forbidden paths (NEVER patch)
FORBIDDEN_PATHS = {
    "oracle_town/core/",
    "oracle_town/policies/",
    "oracle_town/keys/",
    "oracle_town/schemas/",
    ".git/",
    ".github/",
    "venv/",
    ".venv/",
}


@dataclass
class PatchResult:
    """Result of patch application."""
    success: bool
    patch_path: str
    error_message: str = ""
    patched_files: List[str] = None

    def __post_init__(self):
        if self.patched_files is None:
            self.patched_files = []


def make_temp_worktree(src_repo_root: str) -> str:
    """
    Create a temporary copy of the repository.

    Args:
        src_repo_root: Path to source repository root

    Returns:
        Path to temp worktree directory

    Raises:
        ValueError: If src_repo_root doesn't exist or is not readable
    """
    src_path = Path(src_repo_root).resolve()
    if not src_path.exists():
        raise ValueError(f"Source repo not found: {src_repo_root}")
    if not src_path.is_dir():
        raise ValueError(f"Source is not a directory: {src_repo_root}")

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="oracle_town_worktree_")
    temp_path = Path(temp_dir)

    try:
        # Copy repo, excluding unwanted directories
        exclusions = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "*.pyc", ".DS_Store"}

        for src_item in src_path.iterdir():
            # Skip exclusions
            if src_item.name in exclusions:
                continue
            if src_item.suffix == ".pyc":
                continue

            dst_item = temp_path / src_item.name

            if src_item.is_dir():
                shutil.copytree(src_item, dst_item, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
            else:
                shutil.copy2(src_item, dst_item)

        return str(temp_path)

    except Exception as e:
        # Cleanup on failure
        shutil.rmtree(temp_path, ignore_errors=True)
        raise ValueError(f"Failed to create worktree: {e}")


def _is_path_allowed(file_path: str) -> bool:
    """Check if a file path is allowed to be patched."""
    path = Path(file_path)

    # Check for forbidden paths
    for forbidden in FORBIDDEN_PATHS:
        if forbidden.endswith("/"):
            forbidden_path = Path(forbidden.rstrip("/"))
            if forbidden_path in path.parents or str(path).startswith(forbidden):
                return False
        else:
            if path.name == forbidden or str(path) == forbidden:
                return False

    # Check for path traversal
    try:
        path.resolve()
    except (ValueError, RuntimeError):
        return False

    if ".." in path.parts:
        return False

    # Check if in allowlisted paths
    for allowed in PATCHABLE_PATHS:
        allowed_path = Path(allowed.rstrip("/"))
        if allowed_path in path.parents or str(path).startswith(allowed):
            return True

    return False


def apply_patch(workdir: str, diff_text: str) -> PatchResult:
    """
    Apply a unified diff patch to the worktree.

    Args:
        workdir: Path to worktree
        diff_text: Unified diff text

    Returns:
        PatchResult with success status and details

    Safety checks:
        - Validates all patched files are in allowlisted paths
        - Rejects path traversal attempts
        - Uses GNU patch (deterministic, well-defined semantics)
        - Enforces strict patch format
    """
    workdir_path = Path(workdir).resolve()
    if not workdir_path.exists():
        return PatchResult(success=False, patch_path="", error_message=f"Worktree not found: {workdir}")

    # Parse diff to extract file paths (basic validation)
    patched_files = []
    lines = diff_text.split("\n")

    for line in lines:
        if line.startswith("--- ") or line.startswith("+++ "):
            # Extract path: "--- a/path/to/file" -> "path/to/file"
            parts = line.split(None, 1)
            if len(parts) == 2:
                file_path = parts[1]
                # Remove a/ or b/ prefix
                if file_path.startswith("a/") or file_path.startswith("b/"):
                    file_path = file_path[2:]

                # Validate path
                if not _is_path_allowed(file_path):
                    return PatchResult(
                        success=False,
                        patch_path="",
                        error_message=f"Forbidden path in patch: {file_path}",
                        patched_files=[],
                    )

                if file_path not in patched_files:
                    patched_files.append(file_path)

    # Write diff to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".patch", delete=False) as f:
        f.write(diff_text)
        patch_file = f.name

    try:
        # Apply patch using GNU patch
        result = subprocess.run(
            ["patch", "-p1", "--forward", "--batch", "--input=" + patch_file],
            cwd=str(workdir_path),
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return PatchResult(
                success=False,
                patch_path=patch_file,
                error_message=f"Patch failed: {result.stderr}",
                patched_files=patched_files,
            )

        return PatchResult(
            success=True,
            patch_path=patch_file,
            patched_files=patched_files,
        )

    except subprocess.TimeoutExpired:
        return PatchResult(
            success=False,
            patch_path=patch_file,
            error_message="Patch application timed out (>30s)",
            patched_files=patched_files,
        )
    except Exception as e:
        return PatchResult(
            success=False,
            patch_path=patch_file,
            error_message=f"Exception during patch: {e}",
            patched_files=patched_files,
        )
    finally:
        # Cleanup temp patch file
        try:
            os.unlink(patch_file)
        except:
            pass


def cleanup_worktree(workdir: str) -> bool:
    """
    Remove a temporary worktree.

    Args:
        workdir: Path to worktree to remove

    Returns:
        True if cleanup successful
    """
    try:
        workdir_path = Path(workdir).resolve()
        if workdir_path.exists():
            shutil.rmtree(workdir_path)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    """Test worktree isolation."""
    import sys

    # Test 1: Create and cleanup worktree
    print("Test 1: Create and cleanup worktree...")
    try:
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        workdir = make_temp_worktree(repo_root)
        print(f"✓ Created worktree: {workdir}")

        # Verify repo structure
        assert Path(workdir, "oracle_town", "core").exists()
        print(f"✓ Repo structure intact")

        cleanup_worktree(workdir)
        print(f"✓ Cleaned up worktree")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)

    # Test 2: Reject forbidden path
    print("\nTest 2: Reject forbidden path...")
    if not _is_path_allowed("oracle_town/core/crypto.py"):
        print(f"✓ Forbidden path rejected correctly")
    else:
        print(f"✗ Forbidden path was allowed!")
        sys.exit(1)

    # Test 3: Allow patchable path
    print("\nTest 3: Allow patchable path...")
    if _is_path_allowed("tests/test_dummy.py"):
        print(f"✓ Patchable path allowed correctly")
    else:
        print(f"✗ Patchable path was rejected!")
        sys.exit(1)

    # Test 4: Reject path traversal
    print("\nTest 4: Reject path traversal...")
    if not _is_path_allowed("tests/../oracle_town/core/crypto.py"):
        print(f"✓ Path traversal rejected correctly")
    else:
        print(f"✗ Path traversal was allowed!")
        sys.exit(1)

    print("\n✓ All worktree tests passed")
