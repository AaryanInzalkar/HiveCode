"""Tests for failure classification."""


from hivecode.policy.retry import FailureClass, FailureRecord
from hivecode.workflow.classification import FailureClassifier


class TestFailureClassifier:
    def test_pre_existing_classification(self):
        classifier = FailureClassifier(llm_client=None)
        baseline = [FailureRecord("test_a", "assertion error")]
        failure = FailureRecord("test_a", "assertion error")

        # Run the async method synchronously for testing
        import asyncio
        result = asyncio.run(classifier.classify(failure, baseline, []))

        assert result.failure_class == FailureClass.PRE_EXISTING
        assert result.consumes_repair_attempt is False

    def test_environmental_classification(self):
        classifier = FailureClassifier(llm_client=None)
        failure = FailureRecord("test_a", "could not find a version")

        import asyncio
        result = asyncio.run(classifier.classify(failure, [], []))

        assert result.failure_class == FailureClass.ENVIRONMENTAL
        assert result.consumes_repair_attempt is False

    def test_patch_related_in_edited_file(self):
        classifier = FailureClassifier(llm_client=None)
        failure = FailureRecord("test_a", "error", file_path="src/orders/service.py")

        import asyncio
        result = asyncio.run(classifier.classify(failure, [], ["src/orders/service.py"]))

        assert result.failure_class == FailureClass.PATCH_RELATED
        assert result.consumes_repair_attempt is True

    def test_unknown_defaults_to_repair(self):
        classifier = FailureClassifier(llm_client=None)
        failure = FailureRecord("test_a", "something weird")

        import asyncio
        result = asyncio.run(classifier.classify(failure, [], []))

        assert result.failure_class == FailureClass.UNKNOWN
        assert result.consumes_repair_attempt is True
