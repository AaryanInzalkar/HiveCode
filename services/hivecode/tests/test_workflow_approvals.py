"""Tests for approvals workflow."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from hivecode.workflow.approvals import (
    ApprovalActionType,
    ApprovalRequest,
    ApprovalStatus,
    check_expiry,
    compute_payload_hash,
    create_approval_request,
    requires_approval,
    validate_approval,
)


class TestComputePayloadHash:
    def test_deterministic(self):
        payload = {"paths": ["migrations/**"]}
        hash1 = compute_payload_hash(payload)
        hash2 = compute_payload_hash(payload)
        assert hash1 == hash2

    def test_order_independent(self):
        payload1 = {"a": 1, "b": 2}
        payload2 = {"b": 2, "a": 1}
        assert compute_payload_hash(payload1) == compute_payload_hash(payload2)

    def test_different_payloads_different_hashes(self):
        payload1 = {"paths": ["migrations/**"]}
        payload2 = {"paths": ["src/**"]}
        assert compute_payload_hash(payload1) != compute_payload_hash(payload2)


class TestCreateApprovalRequest:
    def test_creates_pending_approval(self):
        task_id = uuid4()
        payload = {"paths": ["migrations/**"]}

        approval = create_approval_request(
            task_id=task_id,
            action_type=ApprovalActionType.SCOPE_EXPANSION,
            payload=payload,
        )

        assert approval.task_id == task_id
        assert approval.action_type == ApprovalActionType.SCOPE_EXPANSION
        assert approval.status == ApprovalStatus.PENDING
        assert approval.payload_hash == compute_payload_hash(payload)
        assert approval.expires_at > datetime.now(timezone.utc)


class TestCheckExpiry:
    def test_pending_approval(self):
        approval = create_approval_request(
            task_id=uuid4(),
            action_type=ApprovalActionType.SCOPE_EXPANSION,
            payload={},
        )
        assert check_expiry(approval) == ApprovalStatus.PENDING

    def test_expired_approval(self):
        approval = create_approval_request(
            task_id=uuid4(),
            action_type=ApprovalActionType.SCOPE_EXPANSION,
            payload={},
        )
        # Check 25 hours in the future
        future = datetime.now(timezone.utc) + timedelta(hours=25)
        assert check_expiry(approval, now=future) == ApprovalStatus.EXPIRED


class TestValidateApproval:
    def test_valid_payload(self):
        payload = {"paths": ["migrations/**"]}
        approval = create_approval_request(
            task_id=uuid4(),
            action_type=ApprovalActionType.SCOPE_EXPANSION,
            payload=payload,
        )
        assert validate_approval(approval, payload) is True

    def test_invalid_payload(self):
        approval = create_approval_request(
            task_id=uuid4(),
            action_type=ApprovalActionType.SCOPE_EXPANSION,
            payload={"paths": ["migrations/**"]},
        )
        assert validate_approval(approval, {"paths": ["src/**"]}) is False


class TestRequiresApproval:
    def test_scope_expansion_requires_approval(self):
        assert requires_approval(ApprovalActionType.SCOPE_EXPANSION) is True

    def test_protected_path_requires_approval(self):
        assert requires_approval(ApprovalActionType.PROTECTED_PATH) is True
