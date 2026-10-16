"""Approvals workflow — human-in-the-loop approval handling.

Gated actions create an approvals row and pause the task (awaiting_approval).
Approvals expire after 24 hours (P).
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import UUID


class ApprovalActionType(str, Enum):
    SCOPE_EXPANSION = "scope_expansion"
    PR_NONVERIFIED = "pr_nonverified"
    TEST_MODIFICATION = "test_modification"
    PROTECTED_PATH = "protected_path"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    """A pending approval request."""

    id: UUID
    task_id: UUID
    action_type: ApprovalActionType
    payload: dict
    payload_hash: str
    status: ApprovalStatus
    requested_at: datetime
    expires_at: datetime


def compute_payload_hash(payload: dict) -> str:
    """Compute SHA-256 hash of the approval payload.

    The approval is valid only for the exact payload_hash.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def create_approval_request(
    task_id: UUID,
    action_type: ApprovalActionType,
    payload: dict,
) -> ApprovalRequest:
    """Create a new approval request.

    Args:
        task_id: The task this approval is for
        action_type: The type of action being requested
        payload: The exact payload being approved

    Returns:
        ApprovalRequest
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=24)  # 24h expiry (P)

    return ApprovalRequest(
        id=UUID(int=0),  # Will be set by database
        task_id=task_id,
        action_type=action_type,
        payload=payload,
        payload_hash=compute_payload_hash(payload),
        status=ApprovalStatus.PENDING,
        requested_at=now,
        expires_at=expires,
    )


def check_expiry(approval: ApprovalRequest, now: datetime | None = None) -> ApprovalStatus:
    """Check if an approval has expired.

    Returns the current status (PENDING or EXPIRED).
    """
    if now is None:
        now = datetime.now(timezone.utc)

    if now >= approval.expires_at:
        return ApprovalStatus.EXPIRED
    return ApprovalStatus.PENDING


def validate_approval(
    approval: ApprovalRequest,
    provided_payload: dict,
) -> bool:
    """Validate that the provided payload matches the approval.

    Returns True if the payload hash matches.
    """
    provided_hash = compute_payload_hash(provided_payload)
    return provided_hash == approval.payload_hash


# Default gated actions that require approval (P)
GATED_ACTIONS = {
    ApprovalActionType.SCOPE_EXPANSION,
    ApprovalActionType.PR_NONVERIFIED,
    ApprovalActionType.TEST_MODIFICATION,
    ApprovalActionType.PROTECTED_PATH,
}


def requires_approval(action_type: ApprovalActionType) -> bool:
    """Check if an action type requires approval."""
    return action_type in GATED_ACTIONS
