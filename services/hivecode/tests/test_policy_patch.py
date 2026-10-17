"""Tests for patch application and test-file integrity."""

import tempfile
from pathlib import Path

from hivecode.policy.patch import (
    Edit,
    apply_edits,
    validate_test_integrity,
)


class TestApplyEdits:
    def test_single_edit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("def hello():\n    print('hello')\n")

            edits = [
                Edit(
                    file="test.py",
                    search_text="print('hello')",
                    replacement="print('world')",
                )
            ]

            result = apply_edits(tmpdir, edits)

            assert result.success is True
            assert "test.py" in result.changed_files
            assert "world" in result.diff

    def test_non_matching_edit_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("def hello():\n    pass\n")

            edits = [
                Edit(
                    file="test.py",
                    search_text="nonexistent text",
                    replacement="replacement",
                )
            ]

            result = apply_edits(tmpdir, edits)

            assert result.success is False
            assert "not found" in result.error.lower()

    def test_ambiguous_edit_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("pass\npass\n")

            edits = [
                Edit(
                    file="test.py",
                    search_text="pass",
                    replacement="replaced",
                )
            ]

            result = apply_edits(tmpdir, edits)

            assert result.success is False
            assert "must be unique" in result.error.lower()

    def test_patch_sha256_computed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("original")

            edits = [
                Edit(
                    file="test.py",
                    search_text="original",
                    replacement="modified",
                )
            ]

            result = apply_edits(tmpdir, edits)

            assert result.success is True
            assert len(result.patch_sha256) == 64


class TestTestFileIntegrity:
    def test_detects_deleted_test(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_content = {"tests/test_example.py": "def test_pass(): pass"}
            violations = validate_test_integrity(
                tmpdir,
                test_files=["tests/test_example.py"],
                base_content=base_content,
            )
            assert len(violations) > 0
            assert "deleted" in violations[0].lower()

    def test_detects_modified_test(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "tests"
            test_dir.mkdir()
            (test_dir / "test_example.py").write_text("def test_modified(): pass")

            base_content = {"tests/test_example.py": "def test_pass(): pass"}
            violations = validate_test_integrity(
                tmpdir,
                test_files=["tests/test_example.py"],
                base_content=base_content,
            )
            assert len(violations) > 0
            assert "modified" in violations[0].lower()

    def test_no_violations_when_unchanged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "tests"
            test_dir.mkdir()
            (test_dir / "test_example.py").write_text("def test_pass(): pass")

            base_content = {"tests/test_example.py": "def test_pass(): pass"}
            violations = validate_test_integrity(
                tmpdir,
                test_files=["tests/test_example.py"],
                base_content=base_content,
            )
            assert len(violations) == 0

    def test_approved_changes_ignored(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "tests"
            test_dir.mkdir()
            (test_dir / "test_example.py").write_text("def test_modified(): pass")

            base_content = {"tests/test_example.py": "def test_pass(): pass"}
            violations = validate_test_integrity(
                tmpdir,
                test_files=["tests/test_example.py"],
                base_content=base_content,
                approved_changes=["tests/test_example.py"],
            )
            assert len(violations) == 0
