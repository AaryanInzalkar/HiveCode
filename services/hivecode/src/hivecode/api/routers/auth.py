"""Authentication router — GitHub OAuth, sessions, CSRF."""

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hivecode.config import get_settings
from hivecode.db.base import get_db
from hivecode.db.models import Session as SessionModel
from hivecode.db.models import User
from hivecode.db.repositories import UserRepository
from hivecode.db.uuid7 import uuid7

router = APIRouter()


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: "UserResponse | None" = None
    app_installed: bool = True
    csrf_secret: str | None = None


class UserResponse(BaseModel):
    id: UUID
    github_login: str
    display_name: str | None
    avatar_url: str | None


class MeResponse(BaseModel):
    user: UserResponse
    csrf_secret: str


def _hash_token(token: str) -> bytes:
    """SHA-256 hash of a session token."""
    return hashlib.sha256(token.encode()).digest()


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(request: Request, db: AsyncSession = Depends(get_db)):
    """Check authentication status."""
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)

    if not token:
        return AuthStatusResponse(authenticated=False)

    token_hash = _hash_token(token)
    result = await db.execute(
        select(SessionModel).where(
            SessionModel.token_hash == token_hash,
            SessionModel.revoked_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        return AuthStatusResponse(authenticated=False)

    now = datetime.now(timezone.utc)
    if session.idle_expires_at < now or session.absolute_expires_at < now:
        return AuthStatusResponse(authenticated=False)

    user = await UserRepository.get_by_id(db, session.user_id)
    if not user:
        return AuthStatusResponse(authenticated=False)

    return AuthStatusResponse(
        authenticated=True,
        user=UserResponse(
            id=user.id,
            github_login=user.github_login,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
        ),
    )


@router.get("/me", response_model=MeResponse)
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    """Get current user and CSRF secret."""
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

    user = await UserRepository.get_by_id(db, session.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return MeResponse(
        user=UserResponse(
            id=user.id,
            github_login=user.github_login,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
        ),
        csrf_secret=session.csrf_secret.hex(),
    )


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """Sign out — revoke session and clear cookie."""
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)

    if token:
        token_hash = _hash_token(token)
        result = await db.execute(
            select(SessionModel).where(SessionModel.token_hash == token_hash)
        )
        session = result.scalar_one_or_none()
        if session:
            session.revoked_at = datetime.now(timezone.utc)
            await db.commit()

    response.delete_cookie(
        settings.session_cookie_name,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )
    return {"status": "ok"}
