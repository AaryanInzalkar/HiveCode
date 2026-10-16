"""Patch application — applies structured edits to a workspace.

The coder emits structured edits (path, search_text, replacement).
The backend applies them, rejects non-matching edits, and generates
the diff itself (TD-11, WF-12, WF-13).
"""

import difflib
import hashlib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PatchResult:
    """Result of applying a patch."""

    success: bool
    diff: str = ""
    tree_sha: str = ""
    patch_sha256: str = ""
    changed_files: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class Edit:
    """A single structured edit."""

    file: str
    search_text: str
    replacement: str
    description: str = ""


def apply_edits(workspace: str, edits: list[Edit]) -> PatchResult:
    """Apply structured edits to a workspace.

    Each edit must match exactly once in the target file.
    Non-matching edits are rejected.

    Args:
        workspace: Path to the workspace directory
        edits: List of edits to apply

    Returns:
        PatchResult with diff, tree_sha, and patch_sha256
    """
    workspace_path = Path(workspace)
    changed_files = []
    all_diffs = []

    for edit in edits:
        file_path = workspace_path / edit.file

        if not file_path.exists():
            return PatchResult(
                success=False,
                error=f"File not found: {edit.file}",
            )

        original = file_path.read_text(encoding="utf-8")

        # Count occurrences
        count = original.count(edit.search_text)
        if count == 0:
            return PatchResult(
                success=False,
                error=f"Search text not found in {edit.file}",
            )
        if count > 1:
            return PatchResult(
                success=False,
                error=f"Search text found {count} times in {edit.file} (must be unique)",
            )

        # Apply edit
        modified = original.replace(edit.search_text, edit.replacement, 1)

        # Write modified content
        file_path.write_text(modified, encoding="utf-8")
        changed_files.append(edit.file)

        # Generate diff for this file
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile=f"a/{edit.file}",
            tofile=f"b/{edit.file}",
        )
        all_diffs.append("".join(diff))

    # Combine diffs
    full_diff = "".join(all_diffs)

    # Compute tree SHA (simplified — hash of all file contents)
    tree_sha = _compute_tree_sha(workspace_path)

    # Compute patch SHA-256
    patch_sha256 = hashlib.sha256(full_diff.encode()).hexdigest()

    return PatchResult(
        success=True,
        diff=full_diff,
        tree_sha=tree_sha,
        patch_sha256=patch_sha256,
        changed_files=changed_files,
    )


def _compute_tree_sha(workspace: Path) -> str:
    """Compute a SHA-256 hash representing the workspace tree state."""
    hasher = hashlib.sha256()
    for file_path in sorted(workspace.rglob("*")):
        if file_path.is_file():
            rel_path = file_path.relative_to(workspace)
            hasher.update(str(rel_path).encode())
            hasher.update(file_path.read_bytes())
    return hasher.hexdigest()[:40]


def restore_test_files(workspace: str, test_files: dict[str, str], base_content: dict[str, str]) -> list[str]:
    """Restore test files to their base-commit content.

    Prevents a patch that passes by weakening or deleting tests (WF-14).

    Args:
        workspace: Path to the workspace
        test_files: Dict of test file paths
        base_content: Dict of file paths to their base-commit content

    Returns:
        List of restored file paths
    """
    restored = []
    workspace_path = Path(workspace)

    for file_path, content in base_content.items():
        if file_path in test_files or "test" in file_path or "conftest" in file_path:
            full_path = workspace_path / file_path
            full_path.write_text(content, encoding="utf-8")
            restored.append(file_path)

    return restored


def validate_test_integrity(
    workspace: str,
    test_files: list[str],
    base_content: dict[str, str],
    approved_changes: list[str] | None = None,
) -> list[str]:
    """Validate that test files have not been weakened or deleted.

    Args:
        workspace: Path to the workspace
        test_files: List of test file paths to check
        base_content: Expected base-commit content
        approved_changes: Test files the user approved changing

    Returns:
        List of violations (empty if all tests are intact)
    """
    violations = []
    approved = set(approved_changes or [])
    workspace_path = Path(workspace)

    for file_path in test_files:
        if file_path in approved:
            continue

        full_path = workspace_path / file_path
        if not full_path.exists():
            violations.append(f"Test file deleted: {file_path}")
            continue

        current_content = full_path.read_text(encoding="utf-8")
        expected_content = base_content.get(file_path, "")

        if current_content != expected_content:
            violations.append(f"Test file modified: {file_path}")

    return violations
