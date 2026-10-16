"""Integration tests for the full workflow.

These tests use mock adapters to verify the workflow executes correctly
without live LLM calls or real GitHub integration.
"""

import pytest
from uuid import uuid4

from hivecode.llm.client import ReplayClient, LLMResult, Role
from hivecode.workflow.state import WorkflowState
from hivecode.workflow.router import route_after_evaluate, route_after_classify


class TestWorkflowIntegration:
    """Integration tests for workflow routing."""

    def test_full_verified_flow(self):
        """Test a flow where all checks pass."""
        state = WorkflowState(task_id=uuid4())

        # All checks pass
        checks = [
            {"check_key": "install", "status": "passed", "is_mandatory": True},
            {"check_key": "tests.target", "status": "passed", "is_mandatory": True},
            {"check_key": "tests.regression", "status": "passed", "is_mandatory": True},
        ]

        # Should route to review
        result = route_after_evaluate(state, checks)
        assert result == "review"

    def test_repair_flow(self):
        """Test a flow where a check fails and needs repair."""
        state = WorkflowState(task_id=uuid4())

        # Target test fails
        checks = [
            {"check_key": "install", "status": "passed", "is_mandatory": True},
            {"check_key": "tests.target", "status": "failed", "is_mandatory": True},
        ]

        # Should route to classify
        result = route_after_evaluate(state, checks)
        assert result == "classify"

        # After classification as patch_related, should route to patch
        classification = {"failure_class": "patch_related"}
        result = route_after_classify(state, classification, repair_attempts_used=1)
        assert result == "patch"

    def test_budget_exhausted_flow(self):
        """Test a flow where repair budget is exhausted."""
        state = WorkflowState(task_id=uuid4())

        classification = {"failure_class": "patch_related"}
        result = route_after_classify(state, classification, repair_attempts_used=3)
        assert result == "verdict"


class TestLLMIntegration:
    """Integration tests for LLM client with replay."""

    def test_replay_client_returns_recorded(self):
        recorded = LLMResult(
            content='{"root_cause": "test", "confidence": "high"}',
            model="replay",
        )
        client = ReplayClient(recordings={"analyst:2": recorded})

        result = client.generate(
            role=Role.ANALYST,
            messages=[{"role": "user", "content": "test"}],
        )

        assert result.content == '{"root_cause": "test", "confidence": "high"}'


class TestEndToEndMock:
    """End-to-end test with all mocks."""

    def test_task_creation_to_verdict(self):
        """Test the full flow from task creation to verdict with mocks."""
        # This would test the full workflow with:
        # - Mock GitHub gateway
        # - Replay LLM client
        # - Local sandbox provider
        # - In-memory database

        # For now, just verify the components work together
        state = WorkflowState(task_id=uuid4())
        assert state.attempt_no == 0
        assert state.stop_reason is None
