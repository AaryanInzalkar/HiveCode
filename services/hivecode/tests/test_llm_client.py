"""Tests for the LLM client adapter."""

from hivecode.llm.client import GeminiClient, LLMResult, ReplayClient, Role


class TestGeminiClient:
    def test_initialization(self):
        client = GeminiClient(api_key="test-key", model="gemini-2.0-flash")
        assert client.api_key == "test-key"
        assert client.model == "gemini-2.0-flash"

    def test_role_prompts_defined(self):
        from hivecode.llm.prompts import (
            ANALYST_PROMPT,
            CODER_PROMPT,
            FAILURE_ANALYST_PROMPT,
            REVIEWER_PROMPT,
        )

        assert "analyst" in ANALYST_PROMPT.lower()
        assert "engineer" in CODER_PROMPT.lower()
        assert "reviewer" in REVIEWER_PROMPT.lower()
        assert "failure" in FAILURE_ANALYST_PROMPT.lower()


class TestReplayClient:
    def test_returns_recorded_response(self):
        recorded = LLMResult(content='{"test": true}', model="replay")
        client = ReplayClient(recordings={"analyst:1": recorded})

        result = client.generate(
            role=Role.ANALYST,
            messages=[{"role": "user", "content": "test"}],
        )

        assert result.content == '{"test": true}'
        assert result.model == "replay"

    def test_returns_default_when_no_recording(self):
        client = ReplayClient(recordings={})

        result = client.generate(
            role=Role.ANALYST,
            messages=[{"role": "user", "content": "test"}],
        )

        assert result.content == "{}"
        assert result.model == "replay"
