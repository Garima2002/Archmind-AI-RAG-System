"""Google Gemini LLM provider integration with robust Free-Tier Rate Limiting and Retries."""

import logging
import time
from typing import Dict, Optional

import httpx

from archimind.config import settings
from archimind.rag.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini REST API client with exponential backoff and rate limit management."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        min_request_interval_s: float = 2.0,  # Pace requests safely for Free Tier (15 RPM)
        max_output_tokens: int = 4096,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._model_name = model_name or settings.GEMINI_MODEL or "gemini-2.0-flash"
        self.timeout = timeout
        self.max_retries = max_retries
        self.min_request_interval_s = min_request_interval_s
        self.max_output_tokens = max_output_tokens
        self._last_request_time = 0.0
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

        if not self.api_key:
            logger.warning("Gemini API key not set; GeminiProvider calls will fail if invoked.")

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    def _apply_rate_limit_throttle(self):
        """Enforces a safe minimum interval between requests for Gemini Free Tier (15 RPM)."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.min_request_interval_s:
            sleep_time = self.min_request_interval_s - elapsed
            logger.info("Pacing request for Gemini Free Tier: sleeping %.2fs", sleep_time)
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _discover_and_update_model(self) -> bool:
        """Discovers available models for the API key and updates self._model_name and self.base_url."""
        if not self.api_key:
            return False

        headers = {"x-goog-api-key": self.api_key}
        for version in ["v1beta", "v1"]:
            try:
                with httpx.Client(timeout=10.0) as client:
                    res = client.get(
                        f"https://generativelanguage.googleapis.com/{version}/models",
                        headers=headers,
                    )
                    if res.status_code == 200:
                        data = res.json()
                        models = data.get("models", [])
                        valid_models = []
                        for m in models:
                            methods = m.get("supportedGenerationMethods", [])
                            if "generateContent" in methods:
                                name = m.get("name", "").replace("models/", "")
                                valid_models.append(name)

                        if valid_models:
                            priorities = [
                                "gemini-2.5-flash",
                                "gemini-2.0-flash",
                                "gemini-2.0-flash-exp",
                                "gemini-1.5-flash-latest",
                                "gemini-1.5-flash",
                                "gemini-1.5-pro",
                                "gemini-2.5-pro",
                                "gemini-2.0-pro-exp",
                            ]
                            chosen = None
                            for p in priorities:
                                if p in valid_models:
                                    chosen = p
                                    break
                            if not chosen:
                                chosen = valid_models[0]

                            logger.info(
                                "Auto-discovered active Gemini model: '%s' using API version '%s' (available: %s)",
                                chosen,
                                version,
                                valid_models[:5],
                            )
                            self._model_name = chosen
                            self.base_url = f"https://generativelanguage.googleapis.com/{version}"
                            return True
            except Exception as e:
                logger.warning("Failed to discover models from %s: %s", version, e)
        return False

    def generate(self, prompt: str, system_prompt: str) -> LLMResponse:
        """Invokes Gemini GenerateContent API with retry, auto-discovery, and rate-limit guardrails."""
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured. Please add your Gemini API key in the .env file."
            )

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.0,  # Factual, deterministic grounding
                "maxOutputTokens": self.max_output_tokens,
            },
        }

        last_error = None
        attempt = 1
        while attempt <= self.max_retries:
            self._apply_rate_limit_throttle()
            url = f"{self.base_url}/models/{self.model_name}:generateContent"

            try:
                with httpx.Client(timeout=self.timeout) as client:
                    res = client.post(url, json=payload, headers=headers)

                    # Handle 429 Too Many Requests / Resource Exhausted
                    if res.status_code == 429:
                        backoff_seconds = (2 ** attempt) + 1.0
                        logger.warning(
                            "Gemini Free Tier rate limit hit (HTTP 429). Attempt %d/%d. Waiting %.1fs...",
                            attempt,
                            self.max_retries,
                            backoff_seconds,
                        )
                        if attempt < self.max_retries:
                            time.sleep(backoff_seconds)
                            attempt += 1
                            continue
                        raise RuntimeError(
                            f"Gemini Free Tier rate limit exceeded (HTTP 429). You may have hit the 15 RPM or daily free quota. Please wait a minute before retrying."
                        )

                    # Handle 404 Model Not Found / Unsupported version: auto-discover available model
                    if res.status_code == 404 and attempt == 1:
                        logger.warning(
                            "Gemini model '%s' returned 404 at '%s'. Attempting model auto-discovery...",
                            self.model_name,
                            url,
                        )
                        if self._discover_and_update_model():
                            attempt += 1
                            continue

                    # Handle error responses with detailed messages
                    if res.status_code >= 400:
                        try:
                            err_body = res.json().get("error", {})
                            err_msg = err_body.get("message", res.text)
                        except Exception:
                            err_msg = res.text
                        raise ValueError(f"Gemini API Error ({res.status_code}): {err_msg}")

                    data = res.json()

                    candidates = data.get("candidates", [])
                    content = ""
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        content = "".join(p.get("text", "") for p in parts)

                    usage_meta = data.get("usageMetadata", {})
                    prompt_tokens = usage_meta.get("promptTokenCount", len(prompt.split()))
                    completion_tokens = usage_meta.get("candidatesTokenCount", len(content.split()))

                    return LLMResponse(
                        content=content,
                        token_usage={
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": prompt_tokens + completion_tokens,
                        },
                        model_name=self.model_name,
                        provider_name=self.provider_name,
                    )

            except httpx.TimeoutException as e:
                logger.warning("Gemini request timed out on attempt %d/%d: %s", attempt, self.max_retries, e)
                if attempt == self.max_retries:
                    raise TimeoutError("Gemini API call timed out after multiple attempts.") from e
                time.sleep(2.0)
            except Exception as e:
                logger.error("Gemini API call error on attempt %d: %s", attempt, e)
                last_error = e
                if attempt == self.max_retries:
                    raise

        raise last_error or RuntimeError("Gemini API call failed.")
