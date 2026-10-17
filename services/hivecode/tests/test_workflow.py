"""Tests for the workflow graph and router."""

from uuid import uuid4

from hivecode.workflow.graph import create_workflow_graph
from hivecode.workflow.router import route_after_classify, route_after_evaluate, route_after_review
from hivecode.workflow.state import WorkflowState


class TestWorkflowGraph:
    def test_graph_creation(self):
        graph = create_workflow_graph()
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) == 11

    def test_all_nodes_present(self):
        graph = create_workflow_graph()
        expected_nodes = {
            "intake", "prepare", "diagnose", "patch", "scope_gate",
            "validate", "evaluate", "classify", "review", "verdict", "deliver"
        }
        assert set(graph["nodes"].keys()) == expected_nodes


class TestRouteAfterEvaluate:
    def test_all_pass_routes_to_review(self):
        state = WorkflowState(task_id=uuid4())
        checks = [
            {"check_key": "install", "status": "passed", "is_mandatory": True},
            {"check_key": "tests", "status": "passed", "is_mandatory": True},
        ]
        result = route_after_evaluate(state, checks)
        assert result == "review"

    def test_mandatory_fail_routes_to_classify(self):
        state = WorkflowState(task_id=uuid4())
        checks = [
            {"check_key": "install", "status": "passed", "is_mandatory": True},
            {"check_key": "tests", "status": "failed", "is_mandatory": True},
        ]
        result = route_after_evaluate(state, checks)
        assert result == "classify"

    def test_no_mandatory_routes_to_verdict(self):
        state = WorkflowState(task_id=uuid4())
        checks = [
            {"check_key": "lint", "status": "passed", "is_mandatory": False},
        ]
        result = route_after_evaluate(state, checks)
        assert result == "verdict"


class TestRouteAfterClassify:
    def test_pre_existing_routes_to_verdict(self):
        state = WorkflowState(task_id=uuid4())
        classification = {"failure_class": "pre_existing"}
        result = route_after_classify(state, classification, repair_attempts_used=0)
        assert result == "verdict"

    def test_patch_related_routes_to_patch(self):
        state = WorkflowState(task_id=uuid4())
        classification = {"failure_class": "patch_related"}
        result = route_after_classify(state, classification, repair_attempts_used=1)
        assert result == "patch"

    def test_budget_exhausted_routes_to_verdict(self):
        state = WorkflowState(task_id=uuid4())
        classification = {"failure_class": "patch_related"}
        result = route_after_classify(state, classification, repair_attempts_used=3)
        assert result == "verdict"


class TestRouteAfterReview:
    def test_no_blocking_routes_to_verdict(self):
        state = WorkflowState(task_id=uuid4())
        findings = [{"blocks_delivery": False}]
        result = route_after_review(state, findings, repair_attempts_used=1)
        assert result == "verdict"

    def test_blocking_with_budget_routes_to_patch(self):
        state = WorkflowState(task_id=uuid4())
        findings = [{"blocks_delivery": True}]
        result = route_after_review(state, findings, repair_attempts_used=1)
        assert result == "patch"

    def test_blocking_without_budget_routes_to_verdict(self):
        state = WorkflowState(task_id=uuid4())
        findings = [{"blocks_delivery": True}]
        result = route_after_review(state, findings, repair_attempts_used=3)
        assert result == "verdict"
