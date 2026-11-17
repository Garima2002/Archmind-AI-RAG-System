"""OpenAI LLM provider integration with robust error handling and token usage."""

import logging
from typing import Dict, Optional

import httpx

from archimind.config import settings
from archimind.rag.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI API client using standard chat completions."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self._model_name = model_name or settings.OPENAI_MODEL
        self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip("/")
        self.timeout = timeout

        if not self.api_key:
            logger.warning("OpenAI API key not set; OpenAIProvider calls will fail if invoked.")

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, prompt: str, system_prompt: str) -> LLMResponse:
        """Invokes OpenAI Chat Completion API."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,  # Deterministic factual completions
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(url, json=payload, headers=headers)
                if res.status_code == 429:
                    raise RuntimeError("OpenAI rate limit exceeded (HTTP 429).")
                res.raise_for_status()
                data = res.json()

                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                return LLMResponse(
                    content=content,
                    token_usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                    model_name=self.model_name,
                    provider_name=self.provider_name,
                )
        except httpx.TimeoutException as e:
            logger.error("OpenAI request timed out: %s", e)
            raise TimeoutError("OpenAI API call timed out") from e
        except Exception as e:
            logger.error("OpenAI API call error: %s", e)
            raise
