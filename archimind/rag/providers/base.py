"""Abstract base class and response container for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""

    content: str
    token_usage: Optional[Dict[str, int]] = None
    model_name: str = ""
    provider_name: str = ""


class LLMProvider(ABC):
    """Abstract interface for LLM completions."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str) -> LLMResponse:
        """Generates a text completion based on prompt and system instructions."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider service."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Active model identifier."""
        pass
