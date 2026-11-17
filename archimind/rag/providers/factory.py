"""LLM provider factory."""

import logging
from typing import Optional

from archimind.config import settings
from archimind.rag.providers.anthropic import AnthropicProvider
from archimind.rag.providers.base import LLMProvider
from archimind.rag.providers.gemini import GeminiProvider
from archimind.rag.providers.mock import MockLLMProvider
from archimind.rag.providers.openai import OpenAIProvider

logger = logging.getLogger(__name__)

_provider_instance: Optional[LLMProvider] = None


def get_llm_provider(provider_type: Optional[str] = None, force_new: bool = False) -> LLMProvider:
    """Returns configured LLM provider instance."""
    global _provider_instance
    if _provider_instance is not None and not force_new and provider_type is None:
        return _provider_instance

    p_type = (provider_type or settings.LLM_PROVIDER).lower()

    if p_type == "openai":
        provider = OpenAIProvider()
    elif p_type == "anthropic":
        provider = AnthropicProvider()
    elif p_type == "gemini":
        provider = GeminiProvider()
    elif p_type == "mock":
        provider = MockLLMProvider()
    else:
        logger.warning("Unknown LLM provider '%s', defaulting to MockLLMProvider.", p_type)
        provider = MockLLMProvider()

    if provider_type is None:
        _provider_instance = provider
    return provider
