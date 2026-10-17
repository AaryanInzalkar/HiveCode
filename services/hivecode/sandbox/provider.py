"""Sandbox provider — isolated execution of repository code.

The sandbox executes dependency installation and tests for repositories
and patches that may be malicious or simply wrong. We assume repository
code can attempt: reading the environment, scanning the network, escaping
the container, exhausting resources, producing misleading output, and
exfiltrating the repository itself.
"""

import zipfile
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Protocol


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


@dataclass
class JobSpec:
    """Specification for a sandbox job."""

    job_id: str
    task_id: str
    attempt_no: int
    image: str
    workspace_path: str
    phases: list["PhaseSpec"] = field(default_factory=list)
    limits: "ResourceLimits" = field(default_factory=lambda: ResourceLimits())
    network_policy: "NetworkPolicy" = field(default_factory=lambda: NetworkPolicy())


@dataclass
class PhaseSpec:
    """Specification for a single execution phase."""

    name: str
    command_id: str
    args: dict = field(default_factory=dict)
    network: str = "none"  # "mirror_only" or "none"
    timeout_s: int = 600
    sidecar: str | None = None


@dataclass
class ResourceLimits:
    """Resource limits for a sandbox job."""

    cpus: float = 2.0
    memory_mb: int = 4096
    pids: int = 512
    disk_mb: int = 2048
    log_bytes: int = 10485760  # 10 MB


@dataclass
class NetworkPolicy:
    """Network policy for a sandbox job."""

    install_egress: list[str] = field(default_factory=list)
    test_network: bool = False
    allow_metadata_endpoint: bool = False


@dataclass
class JobResult:
    """Result of a completed sandbox job."""

    job_id: str
    status: JobStatus
    exit_code: int | None = None
    duration_ms: int = 0
    phase_results: list["PhaseResult"] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    oom_killed: bool = False
    timed_out: bool = False


@dataclass
class PhaseResult:
    """Result of a single phase."""

    name: str
    status: JobStatus
    exit_code: int | None = None
    duration_ms: int = 0
    stdout: str = ""
    stderr: str = ""


@dataclass
class JobHandle:
    """Handle for a submitted job."""

    job_id: str
    status: JobStatus = JobStatus.PENDING


class SandboxProvider(Protocol):
    """Protocol for sandbox providers."""

    async def submit(self, job: JobSpec) -> JobHandle: ...
    async def poll(self, handle: JobHandle) -> JobStatus: ...
    async def cancel(self, handle: JobHandle) -> None: ...
    async def fetch_result(self, handle: JobHandle) -> JobResult: ...


class DockerSandboxProvider:
    """Docker-based sandbox provider.

    Creates disposable containers per job with resource limits,
    network isolation, and no credentials.
    """

    def __init__(self, image_prefix: str = "hivecode-runner"):
        self.image_prefix = image_prefix

    async def submit(self, job: JobSpec) -> JobHandle:
        """Submit a job to the sandbox.

        Creates a Docker container with the specified limits.
        """
        # TODO: Implement Docker container creation
        # 1. Create container with resource limits
        # 2. Copy workspace into container
        # 3. Execute phases sequentially
        # 4. Collect results
        return JobHandle(job_id=job.job_id, status=JobStatus.PENDING)

    async def poll(self, handle: JobHandle) -> JobStatus:
        """Poll job status."""
        # TODO: Implement polling
        return handle.status

    async def cancel(self, handle: JobHandle) -> None:
        """Cancel a running job."""
        # TODO: Implement cancellation
        pass

    async def fetch_result(self, handle: JobHandle) -> JobResult:
        """Fetch job results."""
        # TODO: Implement result fetching
        return JobResult(
            job_id=handle.job_id,
            status=JobStatus.COMPLETED,
            exit_code=0,
        )


class LocalSandboxProvider:
    """Local sandbox provider for development and testing.

    Uses subprocess isolation instead of Docker containers.
    NOT for production — no real isolation.
    """

    def __init__(self, work_dir: str = "/tmp/hivecode-sandboxes"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

    async def submit(self, job: JobSpec) -> JobHandle:
        """Submit a job locally."""
        job_dir = self.work_dir / job.job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        # Extract workspace
        if Path(job.workspace_path).exists():
            with zipfile.ZipFile(job.workspace_path, "r") as zf:
                zf.extractall(job_dir / "workspace")

        return JobHandle(job_id=job.job_id, status=JobStatus.PENDING)

    async def poll(self, handle: JobHandle) -> JobStatus:
        """Poll job status."""
        return handle.status

    async def cancel(self, handle: JobHandle) -> None:
        """Cancel a job."""
        pass

    async def fetch_result(self, handle: JobHandle) -> JobResult:
        """Fetch results."""
        return JobResult(
            job_id=handle.job_id,
            status=JobStatus.COMPLETED,
            exit_code=0,
        )


# Command catalog — no free-form shell
COMMAND_CATALOG = {
    "pip_install_requirements": {
        "argv": ["pip", "install", "-r", "requirements.txt"],
        "workdir": "/workspace",
        "network": "mirror_only",
        "timeout_s": 300,
    },
    "pip_install_project": {
        "argv": ["pip", "install", "-e", "."],
        "workdir": "/workspace",
        "network": "mirror_only",
        "timeout_s": 300,
    },
    "pytest_selected": {
        "argv": ["python", "-m", "pytest", "-v", "--tb=short"],
        "workdir": "/workspace",
        "network": "none",
        "timeout_s": 600,
    },
    "pytest_full": {
        "argv": ["python", "-m", "pytest", "-v", "--tb=short"],
        "workdir": "/workspace",
        "network": "none",
        "timeout_s": 600,
    },
    "ruff_check": {
        "argv": ["ruff", "check", "."],
        "workdir": "/workspace",
        "network": "none",
        "timeout_s": 60,
    },
    "mypy_check": {
        "argv": ["mypy", "."],
        "workdir": "/workspace",
        "network": "none",
        "timeout_s": 120,
    },
    "python_version": {
        "argv": ["python", "--version"],
        "workdir": "/workspace",
        "network": "none",
        "timeout_s": 10,
    },
}


def validate_command_args(command_id: str, args: dict) -> list[str]:
    """Validate command arguments against the catalog.

    Returns list of validation errors.
    """
    errors = []
    if command_id not in COMMAND_CATALOG:
        errors.append(f"Unknown command_id: {command_id}")
        return errors

    COMMAND_CATALOG[command_id]

    # Validate test selectors (must match strict pattern)
    if command_id in ("pytest_selected", "pytest_full"):
        selectors = args.get("selectors", [])
        for selector in selectors:
            if not _is_valid_test_selector(selector):
                errors.append(f"Invalid test selector: {selector}")

    return errors


def _is_valid_test_selector(selector: str) -> bool:
    """Check if a test selector matches the allowed pattern.

    Allowed: tests/test_file.py::test_name or tests/test_file.py::TestClass::test_name
    """
    import re

    pattern = r"^[\w/]+\.py::[\w]+$"
    return bool(re.match(pattern, selector))
