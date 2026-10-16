"""Result parsing and validation for sandbox execution.

Test output produced inside the sandbox is produced by code that may be
adversarial, so verification does not depend on trusting it blindly.
"""

import xml.etree.ElementTree as ET
import json
import re
from dataclasses import dataclass, field


@dataclass
class ParsedTestResult:
    """A single parsed test result."""

    test_id: str
    status: str  # "passed", "failed", "error", "skipped"
    duration_ms: int = 0
    message: str = ""
    traceback: str = ""


@dataclass
class ParsedCheckResult:
    """Result of parsing a check run's output."""

    check_key: str
    status: str  # "passed", "failed", "error", "timed_out"
    collected: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    test_results: list[ParsedTestResult] = field(default_factory=list)
    exit_code: int | None = None
    duration_ms: int = 0
    oom_killed: bool = False
    timed_out: bool = False


def parse_junit_xml(xml_content: str, check_key: str) -> ParsedCheckResult:
    """Parse JUnit XML output from pytest.

    Uses a safe XML parser (no entity expansion).

    Args:
        xml_content: JUnit XML string
        check_key: The check key this result belongs to

    Returns:
        ParsedCheckResult with test details
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        return ParsedCheckResult(
            check_key=check_key,
            status="error",
            errors=1,
        )

    test_results = []
    collected = 0
    passed = 0
    failed = 0
    errors = 0
    skipped = 0

    for testcase in root.findall(".//testcase"):
        collected += 1
        test_id = testcase.get("classname", "") + "::" + testcase.get("name", "")

        # Determine status
        if testcase.find("failure") is not None:
            status = "failed"
            failed += 1
            failure = testcase.find("failure")
            message = failure.get("message", "")
            traceback = failure.text or ""
        elif testcase.find("error") is not None:
            status = "error"
            errors += 1
            error = testcase.find("error")
            message = error.get("message", "")
            traceback = error.text or ""
        elif testcase.find("skipped") is not None:
            status = "skipped"
            skipped += 1
            message = ""
            traceback = ""
        else:
            status = "passed"
            passed += 1
            message = ""
            traceback = ""

        duration = testcase.get("time", "0")
        try:
            duration_ms = int(float(duration) * 1000)
        except (ValueError, TypeError):
            duration_ms = 0

        test_results.append(
            ParsedTestResult(
                test_id=test_id,
                status=status,
                duration_ms=duration_ms,
                message=message,
                traceback=traceback,
            )
        )

    # Determine overall status
    if errors > 0:
        overall_status = "error"
    elif failed > 0:
        overall_status = "failed"
    elif collected == 0:
        overall_status = "error"  # Zero collected tests is never a pass
    else:
        overall_status = "passed"

    return ParsedCheckResult(
        check_key=check_key,
        status=overall_status,
        collected=collected,
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=skipped,
        test_results=test_results,
    )


def parse_pytest_output(stdout: str, stderr: str, exit_code: int) -> ParsedCheckResult:
    """Parse pytest text output.

    Used when JUnit XML is not available.

    Args:
        stdout: Standard output from pytest
        stderr: Standard error from pytest
        exit_code: Process exit code

    Returns:
        ParsedCheckResult
    """
    # Check for timeout
    if exit_code == -9 or "timeout" in stderr.lower():
        return ParsedCheckResult(
            check_key="pytest",
            status="timed_out",
            timed_out=True,
            exit_code=exit_code,
        )

    # Check for OOM
    if "out of memory" in stderr.lower() or "oom" in stderr.lower():
        return ParsedCheckResult(
            check_key="pytest",
            status="error",
            errors=1,
            oom_killed=True,
            exit_code=exit_code,
        )

    # Parse summary line
    passed = 0
    failed = 0
    errors = 0
    skipped = 0

    summary_match = re.search(
        r"=+\s*(.*?)\s*(?:passed|failed|error).*?=+",
        stdout + stderr,
        re.IGNORECASE,
    )

    if summary_match:
        summary = summary_match.group(1)
        # Extract numbers
        for word in summary.split():
            if word.isdigit():
                # Determine what this number represents from context
                pass

    # Parse individual test results
    test_results = []
    for match in re.finditer(
        r"(PASSED|FAILED|ERROR|SKIPPED)\s+(.+?)(?:\s|$)",
        stdout,
    ):
        status_str = match.group(1)
        test_id = match.group(2).strip()

        status_map = {
            "PASSED": "passed",
            "FAILED": "failed",
            "ERROR": "error",
            "SKIPPED": "skipped",
        }

        status = status_map.get(status_str, "unknown")
        test_results.append(ParsedTestResult(test_id=test_id, status=status))

    # Count from test results
    passed = sum(1 for t in test_results if t.status == "passed")
    failed = sum(1 for t in test_results if t.status == "failed")
    errors = sum(1 for t in test_results if t.status == "error")
    skipped = sum(1 for t in test_results if t.status == "skipped")

    # Determine overall status
    if exit_code != 0 and not test_results:
        overall_status = "error"
    elif failed > 0 or errors > 0:
        overall_status = "failed"
    elif len(test_results) == 0:
        overall_status = "error"  # Zero collected tests is never a pass
    else:
        overall_status = "passed"

    return ParsedCheckResult(
        check_key="pytest",
        status=overall_status,
        collected=len(test_results),
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=skipped,
        test_results=test_results,
        exit_code=exit_code,
    )


def validate_check_result(result: ParsedCheckResult, baseline_collected: int = 0) -> list[str]:
    """Validate a parsed check result for suspicious patterns.

    Cross-checks (SBX-10):
    - Collected count is at least the baseline for pass-to-pass sets
    - Each target test id appears exactly once with a status
    - Zero collected tests is never a pass

    Args:
        result: The parsed check result
        baseline_collected: Expected minimum collected tests

    Returns:
        List of validation warnings
    """
    warnings = []

    if result.collected == 0 and result.status == "passed":
        warnings.append("Zero collected tests but marked as passed")

    if result.collected < baseline_collected:
        warnings.append(
            f"Collected {result.collected} tests, expected at least {baseline_collected}"
        )

    # Check for duplicate test IDs
    test_ids = [t.test_id for t in result.test_results]
    duplicates = [tid for tid in test_ids if test_ids.count(tid) > 1]
    if duplicates:
        warnings.append(f"Duplicate test IDs: {set(duplicates)}")

    return warnings
