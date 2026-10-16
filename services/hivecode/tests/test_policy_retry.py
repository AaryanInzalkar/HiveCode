"""Tests for retry policy — failure classification and repair routing."""

from hivecode.policy.retry import (
    FailureClass,
    FailureRecord,
    can_start_repair,
    classify_failure,
    should_stop_no_progress,
)


class TestClassifyFailure:
    def test_pre_existing_failure(self):
        baseline = [FailureRecord("test_a", "assertion error")]
        failure = FailureRecord("test_a", "assertion error")
        result = classify_failure(failure, baseline, [])
        assert result.failure_class == FailureClass.PRE_EXISTING
        assert result.consumes_repair_attempt is False

    def test_environmental_failure(self):
        failure = FailureRecord("test_a", "could not find a version that satisfies")
        result = classify_failure(failure, [], [])
        assert result.failure_class == FailureClass.ENVIRONMENTAL
        assert result.consumes_repair_attempt is False

    def test_patch_related_in_edited_file(self):
        failure = FailureRecord("test_a", "assertion error", file_path="src/orders/service.py")
        result = classify_failure(failure, [], ["src/orders/service.py"])
        assert result.failure_class == FailureClass.PATCH_RELATED
        assert result.consumes_repair_attempt is True

    def test_patch_related_syntax_error(self):
        failure = FailureRecord("test_a", "SyntaxError: invalid syntax")
        result = classify_failure(failure, [], [])
        assert result.failure_class == FailureClass.PATCH_RELATED
        assert result.consumes_repair_attempt is True

    def test_unknown_defaults_to_repair(self):
        failure = FailureRecord("test_a", "something weird happened")
        result = classify_failure(failure, [], [])
        assert result.failure_class == FailureClass.UNKNOWN
        assert result.consumes_repair_attempt is True


class TestShouldStopNoProgress:
    def test_same_patch_hash(self):
        assert should_stop_no_progress("abc123", "abc123", ["a"], ["a"]) is True

    def test_same_failures(self):
        assert should_stop_no_progress("def456", "abc123", ["a", "b"], ["a", "b"]) is True

    def test_different_patch(self):
        assert should_stop_no_progress("def456", "abc123", ["a"], ["a"]) is False

    def test_first_attempt(self):
        assert should_stop_no_progress("abc123", None, ["a"], []) is False


class TestCanStartRepair:
    def test_can_start(self):
        can, reason = can_start_repair(0, 3, 600, 2.0)
        assert can is True
        assert reason == ""

    def test_budget_exhausted(self):
        can, reason = can_start_repair(3, 3, 600, 2.0)
        assert can is False
        assert reason == "RETRY_BUDGET_EXHAUSTED"

    def test_insufficient_time(self):
        can, reason = can_start_repair(1, 3, 60, 2.0, min_time_s=180)
        assert can is False
        assert reason == "INSUFFICIENT_TIME_BUDGET"
