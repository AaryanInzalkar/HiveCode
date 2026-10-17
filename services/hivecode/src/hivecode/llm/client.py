"""LLM client adapter — provider-independent interface.

All model calls go through LLMClient. Each call records provider, model,
prompt version, tokens, cost, and latency.
"""

import contextlib
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

import httpx
from pydantic import BaseModel


class Role(StrEnum):
    ANALYST = "analyst"
    CODER = "coder"
    REVIEWER = "reviewer"
    FAILURE_ANALYST = "failure_analyst"


@dataclass
class CallBudget:
    """Budget for a single LLM call."""

    max_tokens: int = 8192
    max_cost_usd: float = 0.10


@dataclass
class LLMResult:
    """Result of an LLM call."""

    content: str
    parsed: BaseModel | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    model: str = ""
    prompt_version: str = ""


class LLMClient(Protocol):
    """Protocol for LLM clients."""

    async def generate(
        self,
        *,
        role: Role,
        messages: list[dict[str, str]],
        response_model: type[BaseModel] | None = None,
        tools: list[dict] | None = None,
        budget: CallBudget | None = None,
    ) -> LLMResult:
        ...


class GeminiClient:
    """Google Gemini API client."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self._client = httpx.AsyncClient(timeout=120.0)

    async def generate(
        self,
        *,
        role: Role,
        messages: list[dict[str, str]],
        response_model: type[BaseModel] | None = None,
        tools: list[dict] | None = None,
        budget: CallBudget | None = None,
    ) -> LLMResult:
        """Generate a response from Gemini."""
        budget = budget or CallBudget()
        start = time.monotonic()

        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            contents.append({
                "role": "model" if msg["role"] == "assistant" else "user",
                "parts": [{"text": msg["content"]}],
            })

        # Build request body
        body: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": budget.max_tokens,
                "temperature": 0.1,
            },
        }

        # Add system instruction for role
        system_prompts = {
            Role.ANALYST: (
                "You are a software debugging analyst. Analyze code, identify root causes, "
                "and propose fix plans. Be precise and evidence-based."
            ),
            Role.CODER: (
                "You are a software engineer. Generate minimal, focused code fixes. "
                "Only modify files within the authorized scope."
            ),
            Role.REVIEWER: (
                "You are a code reviewer. Review changes for correctness, regressions, "
                "and scope violations. Be thorough and skeptical."
            ),
            Role.FAILURE_ANALYST: (
                "You are a failure analysis expert. Classify test failures as patch_related, "
                "environmental, or pre_existing based on evidence."
            ),
        }

        if role in system_prompts:
            body["systemInstruction"] = {
                "parts": [{"text": system_prompts[role]}]
            }

        # Add response schema if provided
        if response_model:
            body["generationConfig"]["responseMimeType"] = "application/json"
            body["generationConfig"]["responseSchema"] = response_model.model_json_schema()

        # Make API call
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        response = await self._client.post(url, json=body)
        response.raise_for_status()
        data = response.json()

        latency_ms = int((time.monotonic() - start) * 1000)

        # Extract content
        content = ""
        if data.get("candidates"):
            candidate = data["candidates"][0]
            if candidate.get("content", {}).get("parts"):
                content = candidate["content"]["parts"][0].get("text", "")

        # Parse structured output if requested
        parsed = None
        if response_model and content:
            with contextlib.suppress(Exception):
                parsed = response_model.model_validate_json(content)

        # Extract token usage
        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)

        # Estimate cost (Gemini 2.0 Flash: $0.10/1M input, $0.40/1M output)
        cost_usd = (input_tokens / 1_000_000 * 0.10) + (output_tokens / 1_000_000 * 0.40)

        return LLMResult(
            content=content,
            parsed=parsed,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            model=self.model,
            prompt_version="v1",
        )

    async def close(self) -> None:
        await self._client.aclose()


class ReplayClient:
    """Deterministic replay client for testing and CI.

    Returns recorded responses instead of making live API calls.
    """

    def __init__(self, recordings: dict[str, LLMResult]):
        self.recordings = recordings

    def generate(
        self,
        *,
        role: Role,
        messages: list[dict[str, str]],
        response_model: type[BaseModel] | None = None,
        tools: list[dict] | None = None,
        budget: CallBudget | None = None,
    ) -> LLMResult:
        """Return a recorded response."""
        key = f"{role.value}:{len(messages)}"
        if key in self.recordings:
            return self.recordings[key]
        return LLMResult(content="{}", model="replay", prompt_version="replay")
