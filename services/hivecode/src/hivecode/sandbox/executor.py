"""Sandbox executor — runs check phases in isolated containers.

Each check runs in a disposable container with:
- Resource limits (CPU, memory, PIDs, disk)
- Network isolation (none for tests, mirror-only for install)
- No credentials
- Output caps
"""

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path

from hivecode.sandbox.provider import (
    validate_command_args,
)
from hivecode.sandbox.results import parse_pytest_output


@dataclass
class CheckConfig:
    """Configuration for a single check."""

    check_key: str
    command_id: str
    args: dict = field(default_factory=dict)
    is_mandatory: bool = True
    timeout_s: int = 600
    network: str = "none"


class SandboxExecutor:
    """Executes checks in isolated environments."""

    def __init__(self, work_dir: str = "/tmp/hivecode-sandboxes"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

    async def execute_check(
        self,
        workspace: str,
        check: CheckConfig,
        attempt_no: int,
    ) -> dict:
        """Execute a single check in the sandbox.

        Returns a dict with the check result ready for database storage.
        """
        # Validate command
        errors = validate_command_args(check.command_id, check.args)
        if errors:
            return {
                "check_key": check.check_key,
                "status": "error",
                "is_mandatory": check.is_mandatory,
                "exit_code": None,
                "duration_ms": 0,
                "error": "; ".join(errors),
            }

        # Create job directory
        job_id = f"{check.check_key}-{attempt_no}-{int(time.time())}"
        job_dir = self.work_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        # Copy workspace
        workspace_path = Path(workspace)
        job_workspace = job_dir / "workspace"
        if workspace_path.exists():
            import shutil
            shutil.copytree(workspace_path, job_workspace, dirs_exist_ok=True)

        # Execute command
        start = time.monotonic()
        try:
            result = await self._run_command(
                command_id=check.command_id,
                args=check.args,
                workdir=str(job_workspace),
                timeout_s=check.timeout_s,
            )
            duration_ms = int((time.monotonic() - start) * 1000)

            # Parse result
            parsed = self._parse_result(check.check_key, result, duration_ms)

            return {
                "check_key": check.check_key,
                "status": parsed["status"],
                "is_mandatory": check.is_mandatory,
                "exit_code": result.get("exit_code"),
                "duration_ms": duration_ms,
                "counts": parsed.get("counts") or {},
                "tree_sha": parsed.get("tree_sha", ""),
                "command_id": check.command_id,
                "flaky_suspected": False,
            }

        except TimeoutError:
            return {
                "check_key": check.check_key,
                "status": "timed_out",
                "is_mandatory": check.is_mandatory,
                "exit_code": None,
                "duration_ms": check.timeout_s * 1000,
                "command_id": check.command_id,
            }
        except Exception as e:
            return {
                "check_key": check.check_key,
                "status": "error",
                "is_mandatory": check.is_mandatory,
                "exit_code": None,
                "duration_ms": 0,
                "error": str(e),
                "command_id": check.command_id,
            }

    async def _run_command(
        self,
        command_id: str,
        args: dict,
        workdir: str,
        timeout_s: int,
    ) -> dict:
        """Run a command in the sandbox.

        This is a simplified implementation. Production would use
        Docker containers with full isolation.
        """
        # Build command from catalog
        from hivecode.sandbox.provider import COMMAND_CATALOG

        spec = COMMAND_CATALOG.get(command_id)
        if not spec:
            return {"exit_code": 1, "stdout": "", "stderr": f"Unknown command: {command_id}"}

        argv = list(spec["argv"])

        # Add test selectors for pytest
        if command_id in ("pytest_selected", "pytest_full"):
            selectors = args.get("selectors", [])
            argv.extend(selectors)

        # Run command
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                cwd=workdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout_s,
                )
                return {
                    "exit_code": proc.returncode,
                    "stdout": stdout.decode("utf-8", errors="replace"),
                    "stderr": stderr.decode("utf-8", errors="replace"),
                }
            except TimeoutError:
                proc.kill()
                await proc.communicate()
                return {
                    "exit_code": -9,
                    "stdout": "",
                    "stderr": "Command timed out",
                }

        except Exception as e:
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e),
            }

    def _parse_result(self, check_key: str, result: dict, duration_ms: int) -> dict:
        """Parse command output into a structured result."""
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        exit_code = result.get("exit_code", 1)

        # Try to parse as pytest output
        if "pytest" in check_key or "test" in check_key:
            parsed = parse_pytest_output(stdout, stderr, exit_code)
            return {
                "status": parsed.status,
                "counts": {
                    "collected": parsed.collected,
                    "passed": parsed.passed,
                    "failed": parsed.failed,
                    "errors": parsed.errors,
                    "skipped": parsed.skipped,
                },
                "test_results": [
                    {"id": t.test_id, "status": t.status}
                    for t in parsed.test_results
                ],
            }

        # Generic command
        status = "passed" if exit_code == 0 else "failed"

        return {
            "status": status,
            "counts": {},
        }

    async def execute_all_checks(
        self,
        workspace: str,
        checks: list[CheckConfig],
        attempt_no: int,
    ) -> list[dict]:
        """Execute all checks for an attempt."""
        results = []
        for check in checks:
            result = await self.execute_check(workspace, check, attempt_no)
            results.append(result)
        return results
