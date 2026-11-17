"""Anthropic Claude LLM provider integration."""

import logging
from typing import Dict, Optional

import httpx

from archimind.config import settings
from archimind.rag.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude Messages API client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self._model_name = model_name or settings.ANTHROPIC_MODEL
        self.timeout = timeout
        self.base_url = "https://api.anthropic.com/v1"

        if not self.api_key:
            logger.warning("Anthropic API key not set; AnthropicProvider calls will fail if invoked.")

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, prompt: str, system_prompt: str) -> LLMResponse:
        """Invokes Anthropic Messages API."""
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured.")

        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
            "temperature": 0.0,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(url, json=payload, headers=headers)
                if res.status_code == 429:
                    raise RuntimeError("Anthropic rate limit exceeded (HTTP 429).")
                res.raise_for_status()
                data = res.json()

                content = ""
                for part in data.get("content", []):
                    if part.get("type") == "text":
                        content += part.get("text", "")

                usage = data.get("usage", {})
                return LLMResponse(
                    content=content,
                    token_usage={
                        "prompt_tokens": usage.get("input_tokens", 0),
                        "completion_tokens": usage.get("output_tokens", 0),
                        "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                    },
                    model_name=self.model_name,
                    provider_name=self.provider_name,
                )
        except httpx.TimeoutException as e:
            logger.error("Anthropic request timed out: %s", e)
            raise TimeoutError("Anthropic API call timed out") from e
        except Exception as e:
            logger.error("Anthropic API call error: %s", e)
            raise
