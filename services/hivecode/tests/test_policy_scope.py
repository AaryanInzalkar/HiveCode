"""Tests for scope policy — path validation and limits."""

from hivecode.policy.scope import (
    ScopeConfig,
    ScopeViolation,
    contains_secrets,
    is_path_allowed,
    validate_limits,
    validate_paths,
)


class TestIsPathAllowed:
    def test_allowed_path(self):
        config = ScopeConfig(allowed_paths=["src/**"])
        assert is_path_allowed("src/orders/service.py", config) is True

    def test_protected_path(self):
        config = ScopeConfig(allowed_paths=["**"], protected_paths=[".github/**"])
        assert is_path_allowed(".github/workflows/ci.yml", config) is False

    def test_outside_allowed(self):
        config = ScopeConfig(allowed_paths=["src/**"])
        assert is_path_allowed("tests/test_orders.py", config) is False

    def test_default_protected(self):
        config = ScopeConfig()
        assert is_path_allowed(".env", config) is False
        assert is_path_allowed("requirements.txt", config) is False
        assert is_path_allowed("migrations/001_initial.py", config) is False

    def test_wildcard_allowed(self):
        config = ScopeConfig(allowed_paths=["**"])
        assert is_path_allowed("any/file.py", config) is True


class TestValidatePaths:
    def test_no_violations(self):
        config = ScopeConfig(allowed_paths=["src/**"])
        violations = validate_paths(["src/a.py", "src/b.py"], config)
        assert len(violations) == 0

    def test_with_violations(self):
        config = ScopeConfig(allowed_paths=["src/**"])
        violations = validate_paths(["src/a.py", ".github/ci.yml"], config)
        assert len(violations) == 1
        assert violations[0].path == ".github/ci.yml"


class TestValidateLimits:
    def test_within_limits(self):
        config = ScopeConfig(max_files=15, max_lines=500)
        violations = validate_limits(10, 400, config)
        assert len(violations) == 0

    def test_too_many_files(self):
        config = ScopeConfig(max_files=15, max_lines=500)
        violations = validate_limits(20, 100, config)
        assert len(violations) == 1
        assert "Too many files" in violations[0].reason

    def test_too_many_lines(self):
        config = ScopeConfig(max_files=15, max_lines=500)
        violations = validate_limits(5, 600, config)
        assert len(violations) == 1
        assert "Too many changed lines" in violations[0].reason


class TestContainsSecrets:
    def test_aws_key(self):
        matches = contains_secrets("aws_access_key_id = AKIAIOSFODNN7EXAMPLE")
        assert len(matches) > 0

    def test_github_pat(self):
        matches = contains_secrets("token = ghp_1234567890abcdefghijklmnopqrstuvwxyz")
        assert len(matches) > 0

    def test_no_secrets(self):
        matches = contains_secrets("print('hello world')")
        assert len(matches) == 0

    def test_private_key(self):
        matches = contains_secrets("-----BEGIN RSA PRIVATE KEY-----")
        assert len(matches) > 0
