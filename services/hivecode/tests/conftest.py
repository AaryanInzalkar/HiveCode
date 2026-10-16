"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_scope_config():
    """Default scope config for testing."""
    from hivecode.policy.scope import ScopeConfig

    return ScopeConfig(
        allowed_paths=["src/**"],
        protected_paths=[".github/**", "migrations/**"],
        max_files=15,
        max_lines=500,
    )


@pytest.fixture
def sample_evidence():
    """Default evidence for verdict testing."""
    from hivecode.policy.verdict import CheckResult, CheckStatus, Evidence

    return Evidence(
        check_results=[
            CheckResult("install", CheckStatus.PASSED, True, "abc123"),
            CheckResult("tests.target", CheckStatus.PASSED, True, "abc123"),
            CheckResult("tests.regression", CheckStatus.PASSED, True, "abc123"),
        ],
        policy_version="v1.0.0",
    )
