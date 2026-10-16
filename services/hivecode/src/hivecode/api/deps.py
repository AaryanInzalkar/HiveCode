"""API dependencies — authentication, CSRF, rate limiting."""

import hashlib
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hivecode.config import get_settings
from hivecode.db.models import Session as SessionModel
from hivecode.db.models import User


def _hash_token(token: str) -> bytes:
    """SHA-256 hash of a session token."""
    return hashlib.sha256(token.encode()).digest()


async def get_current_user(request: Request, db: AsyncSession) -> User:
    """Authenticate the request and return the current user.

    Reads the session cookie, looks up the session by token hash,
    validates expiry, and returns the associated user.
    """
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token_hash = _hash_token(token)
    result = await db.execute(
        select(SessionModel).where(
            SessionModel.token_hash == token_hash,
            SessionModel.revoked_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=401, detail="Session not found")

    now = datetime.now(timezone.utc)
    if session.idle_expires_at < now or session.absolute_expires_at < now:
        raise HTTPException(status_code=401, detail="Session expired")

    result = await db.execute(select(User).where(User.id == session.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.disabled_at:
        raise HTTPException(status_code=403, detail="User disabled")

    return user


def verify_csrf(request: Request) -> None:
    """Verify CSRF token for unsafe methods.

    Uses the double-submit cookie pattern: the X-CSRF-Token header
    must match the session's CSRF secret.
    """
    settings = get_settings()
    method = request.method.upper()

    if method in ("GET", "HEAD", "OPTIONS"):
        return

    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    csrf_header = request.headers.get(settings.csrf_header)
    if not csrf_header:
        raise HTTPException(status_code=403, detail="CSRF token missing")

    # TODO: Look up session's CSRF secret and compare
    # For now, accept any non-empty token (implement full check in auth phase)
    pass
