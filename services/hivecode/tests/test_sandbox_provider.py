"""Tests for the sandbox provider."""

from hivecode.sandbox.provider import (
    COMMAND_CATALOG,
    LocalSandboxProvider,
    ResourceLimits,
    validate_command_args,
)


class TestCommandCatalog:
    def test_all_commands_defined(self):
        expected = {
            "pip_install_requirements",
            "pip_install_project",
            "pytest_selected",
            "pytest_full",
            "ruff_check",
            "mypy_check",
            "python_version",
        }
        assert expected.issubset(set(COMMAND_CATALOG.keys()))

    def test_pytest_network_is_none(self):
        assert COMMAND_CATALOG["pytest_selected"]["network"] == "none"
        assert COMMAND_CATALOG["pytest_full"]["network"] == "none"

    def test_install_network_is_mirror_only(self):
        assert COMMAND_CATALOG["pip_install_requirements"]["network"] == "mirror_only"


class TestValidateCommandArgs:
    def test_valid_test_selector(self):
        errors = validate_command_args("pytest_selected", {
            "selectors": ["tests/test_orders.py::test_list_orders"]
        })
        assert len(errors) == 0

    def test_invalid_test_selector(self):
        errors = validate_command_args("pytest_selected", {
            "selectors": ["invalid-selector"]
        })
        assert len(errors) > 0

    def test_unknown_command(self):
        errors = validate_command_args("unknown_command", {})
        assert len(errors) > 0


class TestLocalSandboxProvider:
    def test_initialization(self):
        provider = LocalSandboxProvider(work_dir="/tmp/test-sandboxes")
        assert provider.work_dir.exists()

    def test_resource_limits_defaults(self):
        limits = ResourceLimits()
        assert limits.cpus == 2.0
        assert limits.memory_mb == 4096
        assert limits.pids == 512
