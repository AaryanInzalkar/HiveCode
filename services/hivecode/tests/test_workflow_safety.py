"""Tests for safety controls."""

from hivecode.workflow.safety import Budget, BudgetEnforcer, KillSwitch, StopReason


class TestBudget:
    def test_remaining_time(self):
        budget = Budget(max_time_s=1800, time_used_s=600)
        assert budget.remaining_time_s == 1200

    def test_remaining_cost(self):
        budget = Budget(max_cost_usd=5.0, cost_used_usd=2.0)
        assert budget.remaining_cost_usd == 3.0

    def test_can_continue(self):
        budget = Budget(max_time_s=1800, max_cost_usd=5.0)
        assert budget.can_continue(min_time_s=180) is True

    def test_cannot_continue_low_time(self):
        budget = Budget(max_time_s=1800, time_used_s=1700)
        assert budget.can_continue(min_time_s=180) is False

    def test_cannot_continue_low_cost(self):
        budget = Budget(max_cost_usd=5.0, cost_used_usd=4.95)
        assert budget.can_continue(min_cost_usd=0.10) is False


class TestKillSwitch:
    def test_activate(self):
        ks = KillSwitch()
        assert ks.active is False
        ks.activate("Emergency maintenance")
        assert ks.active is True
        assert ks.reason == "Emergency maintenance"

    def test_deactivate(self):
        ks = KillSwitch()
        ks.activate("test")
        ks.deactivate()
        assert ks.active is False


class TestBudgetEnforcer:
    def test_can_continue_normal(self):
        enforcer = BudgetEnforcer(Budget())
        can_continue, reason = enforcer.check_can_continue()
        assert can_continue is True
        assert reason is None

    def test_kill_switch_blocks(self):
        enforcer = BudgetEnforcer(Budget())
        enforcer.kill_switch.activate("Emergency")
        can_continue, reason = enforcer.check_can_continue()
        assert can_continue is False
        assert reason == StopReason.SERVICE_SUSPENDED.value

    def test_time_exhausted(self):
        budget = Budget(max_time_s=1800, time_used_s=1800)
        enforcer = BudgetEnforcer(budget)
        can_continue, reason = enforcer.check_can_continue()
        assert can_continue is False

    def test_can_start_repair(self):
        enforcer = BudgetEnforcer(Budget())
        can_start, reason = enforcer.check_can_start_repair(repair_attempts_used=1)
        assert can_start is True

    def test_cannot_start_repair_budget_exhausted(self):
        enforcer = BudgetEnforcer(Budget())
        can_start, reason = enforcer.check_can_start_repair(repair_attempts_used=3)
        assert can_start is False
        assert reason == StopReason.RETRY_BUDGET_EXHAUSTED.value

    def test_record_usage(self):
        budget = Budget()
        enforcer = BudgetEnforcer(budget)
        enforcer.record_usage(time_s=60, cost_usd=0.50, tokens=1000)
        assert budget.time_used_s == 60
        assert budget.cost_used_usd == 0.50
        assert budget.tokens_used == 1000
