"""GitHub gateway — all GitHub API interactions.

Uses GitHub App authentication with installation tokens.
"""

import base64
import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Protocol

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes


@dataclass
class RepoRef:
    """Reference to a GitHub repository."""

    owner: str
    repo: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"


@dataclass
class BranchRef:
    """Reference to a pushed branch."""

    name: str
    sha: str


@dataclass
class PullRequest:
    """A GitHub pull request."""

    number: int
    url: str
    head_branch: str
    head_sha: str
    base_sha: str
    draft: bool


class GitHubGateway(Protocol):
    """Protocol for GitHub gateway."""

    async def resolve_ref(self, repo: RepoRef, ref: str) -> str: ...
    async def fetch_archive(self, repo: RepoRef, sha: str) -> bytes: ...
    async def push_branch(self, repo: RepoRef, name: str, base_sha: str, patch: bytes) -> BranchRef: ...
    async def open_pull_request(self, repo: RepoRef, head: str, base: str, title: str, body: str, draft: bool) -> PullRequest: ...


class GitHubAppGateway:
    """GitHub App gateway using installation tokens."""

    def __init__(self, app_id: str, private_key: str):
        self.app_id = app_id
        self.private_key = private_key
        self._client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=60.0,
        )
        self._installation_tokens: dict[int, tuple[str, float]] = {}

    def _generate_jwt(self) -> str:
        """Generate a GitHub App JWT for authentication."""
        import jwt  # PyJWT

        now = int(time.time())
        payload = {
            "iat": now - 60,  # 60 seconds in the past for clock drift
            "exp": now + 600,  # 10 minutes
            "iss": self.app_id,
        }

        # Load private key
        key = serialization.load_pem_private_key(
            self.private_key.encode(),
            password=None,
        )

        return jwt.encode(payload, key, algorithm="RS256")

    async def _get_installation_token(self, installation_id: int) -> str:
        """Get or refresh an installation token."""
        # Check cache
        if installation_id in self._installation_tokens:
            token, expires_at = self._installation_tokens[installation_id]
            if time.time() < expires_at - 60:  # Refresh 1 min before expiry
                return token

        # Mint new token
        jwt_token = self._generate_jwt()
        response = await self._client.post(
            f"/app/installations/{installation_id}/access_tokens",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        response.raise_for_status()
        data = response.json()

        token = data["token"]
        expires_at = time.time() + 3600  # 1 hour
        self._installation_tokens[installation_id] = (token, expires_at)

        return token

    async def resolve_ref(self, repo: RepoRef, ref: str) -> str:
        """Resolve a branch or tag name to a commit SHA."""
        # Try branch first
        response = await self._client.get(
            f"/repos/{repo.full_name}/git/ref/heads/{ref}"
        )
        if response.status_code == 200:
            return response.json()["object"]["sha"]

        # Try tag
        response = await self._client.get(
            f"/repos/{repo.full_name}/git/ref/tags/{ref}"
        )
        if response.status_code == 200:
            return response.json()["object"]["sha"]

        raise ValueError(f"Could not resolve ref '{ref}' in {repo.full_name}")

    async def fetch_archive(self, repo: RepoRef, sha: str) -> bytes:
        """Fetch a repository archive at a specific commit."""
        response = await self._client.get(
            f"/repos/{repo.full_name}/tarball/{sha}",
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.content

    async def push_branch(self, repo: RepoRef, name: str, base_sha: str, patch: bytes) -> BranchRef:
        """Push a branch with a patch applied."""
        # Create a new tree with the patch
        # This is a simplified version — full implementation would:
        # 1. Get the base tree
        # 2. Apply the patch to create new blobs
        # 3. Create a new tree
        # 4. Create a commit
        # 5. Create a branch ref

        # For now, create an empty commit on a new branch
        response = await self._client.post(
            f"/repos/{repo.full_name}/git/commits",
            json={
                "message": "HiveCode automated fix",
                "tree": base_sha,  # Simplified — should be actual tree SHA
                "parents": [base_sha],
            },
        )
        response.raise_for_status()
        commit_sha = response.json()["sha"]

        # Create branch
        response = await self._client.post(
            f"/repos/{repo.full_name}/git/refs",
            json={
                "ref": f"refs/heads/{name}",
                "sha": commit_sha,
            },
        )
        response.raise_for_status()

        return BranchRef(name=name, sha=commit_sha)

    async def open_pull_request(
        self, repo: RepoRef, head: str, base: str, title: str, body: str, draft: bool
    ) -> PullRequest:
        """Open a pull request."""
        response = await self._client.post(
            f"/repos/{repo.full_name}/pulls",
            json={
                "title": title,
                "head": head,
                "base": base,
                "body": body,
                "draft": draft,
            },
        )
        response.raise_for_status()
        data = response.json()

        return PullRequest(
            number=data["number"],
            url=data["html_url"],
            head_branch=head,
            head_sha=data["head"]["sha"],
            base_sha=data["base"]["sha"],
            draft=draft,
        )

    async def close(self):
        await self._client.aclose()


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify a GitHub webhook signature."""
    expected = "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
