"""Scope policy — validates file paths and edit boundaries.

Pure functions only. No I/O.
"""

import fnmatch
from dataclasses import dataclass, field


@dataclass
class ScopeConfig:
    """Scope configuration for a task."""

    allowed_paths: list[str] = field(default_factory=lambda: ["**"])
    protected_paths: list[str] = field(
        default_factory=lambda: [
            ".github/**",
            ".env*",
            "*.pem",
            "*.key",
            "id_rsa*",
            "migrations/**",
            "requirements*.txt",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "poetry.lock",
            "Pipfile*",
        ]
    )
    max_files: int = 15
    max_lines: int = 500


@dataclass
class ScopeViolation:
    """A single scope policy violation."""

    path: str
    reason: str


def is_path_allowed(path: str, config: ScopeConfig) -> bool:
    """Check if a path is within the allowed scope.

    A path is allowed if it matches at least one allowed_paths glob
    and does not match any protected_paths glob.
    """
    # Check protected paths first
    for pattern in config.protected_paths:
        if fnmatch.fnmatch(path, pattern):
            return False

    # Check allowed paths
    for pattern in config.allowed_paths:
        if fnmatch.fnmatch(path, pattern):
            return True

    return False


def validate_paths(paths: list[str], config: ScopeConfig) -> list[ScopeViolation]:
    """Validate a list of file paths against the scope config."""
    violations = []
    for path in paths:
        if not is_path_allowed(path, config):
            violations.append(
                ScopeViolation(path=path, reason="Path is outside the allowed scope")
            )
    return violations


def validate_limits(
    file_count: int, line_count: int, config: ScopeConfig
) -> list[ScopeViolation]:
    """Validate file and line count limits."""
    violations = []
    if file_count > config.max_files:
        violations.append(
            ScopeViolation(
                path="*",
                reason=f"Too many files: {file_count} > {config.max_files}",
            )
        )
    if line_count > config.max_lines:
        violations.append(
            ScopeViolation(
                path="*",
                reason=f"Too many changed lines: {line_count} > {config.max_lines}",
            )
        )
    return violations


# Secret patterns to detect in diffs and patches
SECRET_PATTERNS = [
    r"AKIA[0-9A-Z]{16}",  # AWS access key
    r"ghp_[A-Za-z0-9]{36}",  # GitHub PAT
    r"gho_[A-Za-z0-9]{36}",  # GitHub OAuth token
    r"sk-[A-Za-z0-9]{48}",  # OpenAI API key
    r"xoxb-[0-9]+-[0-9]+-[A-Za-z0-9]+",  # Slack bot token
    r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----",  # Private keys
    r"password\s*[=:]\s*\S+",  # password= or password:
    r"api[_-]?key\s*[=:]\s*\S+",  # api_key= or api-key:
    r"secret\s*[=:]\s*\S+",  # secret= or secret:
    r"token\s*[=:]\s*\S+",  # token= or token:
]


def contains_secrets(text: str) -> list[str]:
    """Check if text contains potential secrets. Returns list of matched patterns."""
    import re

    matches = []
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matches.append(pattern)
    return matches
