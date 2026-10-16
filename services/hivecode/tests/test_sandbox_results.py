"""Tests for sandbox result parsing and validation."""

from hivecode.sandbox.results import (
    parse_junit_xml,
    parse_pytest_output,
    validate_check_result,
)


class TestParseJUnitXml:
    def test_parse_passing_tests(self):
        xml = """<?xml version="1.0"?>
        <testsuites>
            <testsuite name="pytest" tests="2" failures="0" errors="0">
                <testcase classname="tests.test_orders" name="test_list" time="0.1"/>
                <testcase classname="tests.test_orders" name="test_create" time="0.2"/>
            </testsuite>
        </testsuites>"""

        result = parse_junit_xml(xml, "tests.target")

        assert result.status == "passed"
        assert result.collected == 2
        assert result.passed == 2
        assert result.failed == 0

    def test_parse_failing_test(self):
        xml = """<?xml version="1.0"?>
        <testsuites>
            <testsuite name="pytest" tests="2" failures="1" errors="0">
                <testcase classname="tests.test_orders" name="test_list" time="0.1"/>
                <testcase classname="tests.test_orders" name="test_create" time="0.2">
                    <failure message="AssertionError">assert 1 == 2</failure>
                </testcase>
            </testsuite>
        </testsuites>"""

        result = parse_junit_xml(xml, "tests.target")

        assert result.status == "failed"
        assert result.collected == 2
        assert result.passed == 1
        assert result.failed == 1

    def test_parse_zero_tests_is_error(self):
        xml = """<?xml version="1.0"?>
        <testsuites>
            <testsuite name="pytest" tests="0" failures="0" errors="0">
            </testsuite>
        </testsuites>"""

        result = parse_junit_xml(xml, "tests.target")

        assert result.status == "error"
        assert result.collected == 0


class TestParsePytestOutput:
    def test_parse_passing_output(self):
        stdout = """
        ================= test session starts =================
        collected 2 items
        tests/test_orders.py ..                              [100%]
        ================= 2 passed in 0.42s ==================
        """
        result = parse_pytest_output(stdout, "", 0)

        assert result.status == "passed"
        assert result.passed == 2

    def test_parse_failing_output(self):
        stdout = """
        ================= test session starts =================
        collected 2 items
        tests/test_orders.py .F                              [100%]
        ================= 1 failed, 1 passed in 0.42s ==================
        """
        result = parse_pytest_output(stdout, "", 1)

        assert result.status == "failed"
        assert result.failed == 1
        assert result.passed == 1

    def test_parse_timeout(self):
        result = parse_pytest_output("", "Command timed out", -9)

        assert result.status == "timed_out"
        assert result.timed_out is True


class TestValidateCheckResult:
    def test_zero_collected_passed_is_warning(self):
        from hivecode.sandbox.results import ParsedCheckResult

        result = ParsedCheckResult(
            check_key="tests",
            status="passed",
            collected=0,
        )
        warnings = validate_check_result(result)
        assert len(warnings) > 0
        assert "Zero collected tests" in warnings[0]

    def test_below_baseline_is_warning(self):
        from hivecode.sandbox.results import ParsedCheckResult

        result = ParsedCheckResult(
            check_key="tests",
            status="passed",
            collected=5,
        )
        warnings = validate_check_result(result, baseline_collected=10)
        assert len(warnings) > 0
        assert "expected at least 10" in warnings[0]

    def test_no_warnings_for_valid_result(self):
        from hivecode.sandbox.results import ParsedCheckResult

        result = ParsedCheckResult(
            check_key="tests",
            status="passed",
            collected=10,
            passed=10,
        )
        warnings = validate_check_result(result, baseline_collected=10)
        assert len(warnings) == 0
