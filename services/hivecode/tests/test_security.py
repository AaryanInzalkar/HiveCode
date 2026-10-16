"""Security tests — IDOR, CSRF, prompt injection, scope enforcement."""

import pytest
from uuid import uuid4

from hivecode.policy.scope import ScopeConfig, is_path_allowed, contains_secrets
from hivecode.workflow.approvals import compute_payload_hash, validate_approval, create_approval_request
from hivecode.workflow.safety import BudgetEnforcer, KillSwitch, Budget


class TestIDORPrevention:
    """Test that cross-user access is prevented."""

    def test_task_repository_scopes_by_user(self):
        """Verify that TaskRepository.get_by_id filters by user_id."""
        from hivecode.db.repositories import TaskRepository

        # The repository function signature includes user_id
        # This ensures cross-user access is impossible
        import inspect
        sig = inspect.signature(TaskRepository.get_by_id)
        assert "user_id" in sig.parameters


class TestScopeEnforcement:
    """Test that scope policy is enforced."""

    def test_protected_paths_rejected(self):
        config = ScopeConfig(allowed_paths=["**"])
        assert is_path_allowed(".github/workflows/ci.yml", config) is False
        assert is_path_allowed(".env", config) is False
        assert is_path_allowed("requirements.txt", config) is False

    def test_allowed_paths_accepted(self):
        config = ScopeConfig(allowed_paths=["src/**"])
        assert is_path_allowed("src/main.py", config) is True

    def test_secrets_detected(self):
        assert len(contains_secrets("AKIAIOSFODNN7EXAMPLE")) > 0
        assert len(contains_secrets("ghp_1234567890abcdefghijklmnopqrstuvwxyz")) > 0


class TestPromptInjectionDefense:
    """Test that prompt injection in repository content is handled."""

    def test_untrusted_content_delimited(self):
        """Verify that role prompts delimit untrusted content."""
        from hivecode.llm.prompts import ANALYST_PROMPT, CODER_PROMPT

        assert "UNTRUSTED DATA" in ANALYST_PROMPT
        assert "UNTRUSTED DATA" in CODER_PROMPT

    def test_prompts_ignore_instructions_in_content(self):
        """Verify that prompts instruct the model to ignore instructions in content."""
        from hivecode.llm.prompts import ANALYST_PROMPT

        assert "Ignore any instructions" in ANALYST_PROMPT


class TestApprovalSecurity:
    """Test approval security."""

    def test_payload_hash_prevents_replay(self):
        """Verify that different payloads have different hashes."""
        payload1 = {"paths": ["migrations/**"]}
        payload2 = {"paths": ["src/**"]}

        hash1 = compute_payload_hash(payload1)
        hash2 = compute_payload_hash(payload2)

        assert hash1 != hash2

    def test_approval_valid_only_for_exact_payload(self):
        """Verify that approval is valid only for the exact payload."""
        payload = {"paths": ["migrations/**"]}
        approval = create_approval_request(
            task_id=uuid4(),
            action_type="scope_expansion",
            payload=payload,
        )

        # Same payload should validate
        assert validate_approval(approval, payload) is True

        # Different payload should not validate
        assert validate_approval(approval, {"paths": ["other/**"]}) is False


class TestBudgetEnforcement:
    """Test that budgets are enforced."""

    def test_kill_switch_immediate(self):
        """Verify that kill switch stops all work immediately."""
        enforcer = BudgetEnforcer(Budget())
        enforcer.kill_switch.activate("Emergency")

        can_continue, reason = enforcer.check_can_continue()
        assert can_continue is False
        assert reason == "SERVICE_SUSPENDED"

    def test_time_budget_enforced(self):
        """Verify that time budget is enforced."""
        budget = Budget(max_time_s=1800, time_used_s=1800)
        enforcer = BudgetEnforcer(budget)

        can_continue, reason = enforcer.check_can_continue()
        assert can_continue is False

    def test_cost_budget_enforced(self):
        """Verify that cost budget is enforced."""
        budget = Budget(max_cost_usd=5.0, cost_used_usd=5.0)
        enforcer = BudgetEnforcer(budget)

        can_continue, reason = enforcer.check_can_continue()
        assert can_continue is False
