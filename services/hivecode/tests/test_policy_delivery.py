"""Tests for delivery policy."""

from hivecode.policy.delivery import (
    DeliveryConfig,
    DeliveryDecision,
    DeliveryMode,
    compute_delivery_decision,
    should_create_pr,
)


class TestComputeDeliveryDecision:
    def test_verified_with_pr_mode(self):
        config = DeliveryConfig(mode=DeliveryMode.PR)
        result = compute_delivery_decision("verified", config, pr_eligible=True)
        assert result == DeliveryDecision.CREATE_PR

    def test_verified_without_pr_eligible(self):
        config = DeliveryConfig(mode=DeliveryMode.PR)
        result = compute_delivery_decision("verified", config, pr_eligible=False)
        assert result == DeliveryDecision.REPORT_ONLY

    def test_failed_no_pr(self):
        config = DeliveryConfig(mode=DeliveryMode.PR)
        result = compute_delivery_decision("failed", config, pr_eligible=True)
        assert result == DeliveryDecision.NO_DELIVERY

    def test_blocked_no_pr(self):
        config = DeliveryConfig(mode=DeliveryMode.PR)
        result = compute_delivery_decision("blocked", config, pr_eligible=True)
        assert result == DeliveryDecision.NO_DELIVERY

    def test_report_mode(self):
        config = DeliveryConfig(mode=DeliveryMode.REPORT)
        result = compute_delivery_decision("verified", config)
        assert result == DeliveryDecision.REPORT_ONLY

    def test_partially_verified_with_approval(self):
        config = DeliveryConfig(mode=DeliveryMode.PR, create_pr_for_non_verified=True)
        result = compute_delivery_decision("partially_verified", config, pr_eligible=True)
        assert result == DeliveryDecision.CREATE_DRAFT

    def test_partially_verified_without_approval(self):
        config = DeliveryConfig(mode=DeliveryMode.PR, create_pr_for_non_verified=False)
        result = compute_delivery_decision("partially_verified", config, pr_eligible=True)
        assert result == DeliveryDecision.REPORT_ONLY

    def test_no_duplicate_pr(self):
        config = DeliveryConfig(mode=DeliveryMode.PR)
        result = compute_delivery_decision("verified", config, has_pr=True)
        assert result == DeliveryDecision.NO_DELIVERY


class TestShouldCreatePR:
    def test_verified_creates_pr(self):
        config = DeliveryConfig(mode=DeliveryMode.PR)
        assert should_create_pr("verified", config) is True

    def test_failed_no_pr(self):
        config = DeliveryConfig(mode=DeliveryMode.PR)
        assert should_create_pr("failed", config) is False

    def test_scope_violation_blocks_pr(self):
        config = DeliveryConfig(mode=DeliveryMode.PR)
        assert should_create_pr("verified", config, has_scope_violation=True) is False

    def test_blocking_finding_blocks_pr(self):
        config = DeliveryConfig(mode=DeliveryMode.PR)
        assert should_create_pr("verified", config, has_blocking_finding=True) is False

    def test_blocking_finding_with_approval(self):
        config = DeliveryConfig(mode=DeliveryMode.PR)
        assert should_create_pr("verified", config, has_blocking_finding=True, approval_granted=True) is True
