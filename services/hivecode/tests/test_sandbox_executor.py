"""Tests for the sandbox executor."""

import tempfile

from hivecode.sandbox.executor import CheckConfig, SandboxExecutor


class TestCheckConfig:
    def test_default_values(self):
        config = CheckConfig(check_key="tests", command_id="pytest_full")
        assert config.is_mandatory is True
        assert config.timeout_s == 600
        assert config.network == "none"


class TestSandboxExecutor:
    def test_initialization(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(work_dir=tmpdir)
            assert executor.work_dir.exists()

    def test_validate_command_args_integration(self):
        from hivecode.sandbox.provider import validate_command_args

        errors = validate_command_args("pytest_selected", {
            "selectors": ["tests/test_orders.py::test_list"]
        })
        assert len(errors) == 0

        errors = validate_command_args("pytest_selected", {
            "selectors": ["invalid"]
        })
        assert len(errors) > 0
