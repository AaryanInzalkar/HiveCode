"""Failure classification — rule-based first, LLM-assisted for ambiguous cases.

Only failures classified as patch_related consume a repair attempt (RET-02).
Environmental failures get a bounded re-run, not a repair (RET-03).
"""

from dataclasses import dataclass, field

from hivecode.llm.client import LLMClient, Role
from hivecode.llm.prompts import FAILURE_ANALYST_PROMPT
from hivecode.agents.schemas import FailureClassification as FailureClassificationSchema
from hivecode.policy.retry import FailureClass, FailureRecord, classify_failure


@dataclass
class ClassificationResult:
    """Result of failure classification."""

    failure_class: FailureClass
    reason: str
    consumes_repair_attempt: bool
    suggested_action: str  # "repair", "re-run", "stop"
    confidence: str = "high"


class FailureClassifier:
    """Classifies test failures using rules first, LLM for ambiguous cases."""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm_client = llm_client

    async def classify(
        self,
        failure: FailureRecord,
        baseline_failures: list[FailureRecord],
        edited_files: list[str],
    ) -> ClassificationResult:
        """Classify a failure using deterministic rules first.

        Only if the rules classify it as 'unknown' do we ask the LLM.
        The LLM can never reclassify to pre_existing (safety constraint).
        """
        # Rule-based classification
        result = classify_failure(failure, baseline_failures, edited_files)

        if result.failure_class != FailureClass.UNKNOWN:
            return ClassificationResult(
                failure_class=result.failure_class,
                reason=result.reason,
                consumes_repair_attempt=result.consumes_repair_attempt,
                suggested_action=self._action_for_class(result.failure_class),
                confidence="high",
            )

        # LLM-assisted classification for unknown cases
        if self.llm_client:
            llm_result = await self._classify_with_llm(
                failure, baseline_failures, edited_files
            )
            return llm_result

        # Default: unknown → patch_related for repair
        return ClassificationResult(
            failure_class=FailureClass.UNKNOWN,
            reason="Failure could not be classified by rules",
            consumes_repair_attempt=True,
            suggested_action="repair",
            confidence="low",
        )

    async def _classify_with_llm(
        self,
        failure: FailureRecord,
        baseline_failures: list[FailureRecord],
        edited_files: list[str],
    ) -> ClassificationResult:
        """Use the failure analyst LLM to classify an unknown failure."""
        # Build context
        baseline_list = "\n".join(
            f"- {bf.test_id}: {bf.message}" for bf in baseline_failures
        )
        edited_list = "\n".join(f"- {ef}" for ef in edited_files)

        messages = [
            {
                "role": "system",
                "content": FAILURE_ANALYST_PROMPT,
            },
            {
                "role": "user",
                "content": f"""<failure>
Test: {failure.test_id}
Message: {failure.message}
File: {failure.file_path}:{failure.line_number}
</failure>

<baseline>
{baseline_list or "No baseline failures"}
</baseline>

<patch>
Edited files: {edited_list or "No files edited"}
</patch>

Classify this failure.""",
            },
        ]

        result = await self.llm_client.generate(
            role=Role.FAILURE_ANALYST,
            messages=messages,
            response_model=FailureClassificationSchema,
        )

        if result.parsed:
            schema = result.parsed
            failure_class = FailureClass(schema.classification)
            return ClassificationResult(
                failure_class=failure_class,
                reason=schema.reasoning,
                consumes_repair_attempt=failure_class
                in (FailureClass.PATCH_RELATED, FailureClass.UNKNOWN),
                suggested_action=schema.suggested_action,
                confidence=schema.confidence,
            )

        # Fallback if LLM output couldn't be parsed
        return ClassificationResult(
            failure_class=FailureClass.UNKNOWN,
            reason="LLM classification failed",
            consumes_repair_attempt=True,
            suggested_action="repair",
            confidence="low",
        )

    def _action_for_class(self, failure_class: FailureClass) -> str:
        """Map failure class to suggested action."""
        if failure_class == FailureClass.PRE_EXISTING:
            return "stop"
        if failure_class == FailureClass.ENVIRONMENTAL:
            return "re-run"
        if failure_class == FailureClass.PATCH_RELATED:
            return "repair"
        return "repair"  # unknown defaults to repair
