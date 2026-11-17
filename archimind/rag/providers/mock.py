"""Deterministic Mock LLM Provider for offline testing and reproducible benchmarking."""

import re
from typing import Dict, List, Optional

from archimind.rag.prompt import INSUFFICIENT_EVIDENCE_FALLBACK
from archimind.rag.providers.base import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """Deterministic, rule-based provider synthesizing answers from context."""

    def __init__(self, model_name: str = "mock-architecture-v1"):
        self._model_name = model_name

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, prompt: str, system_prompt: str) -> LLMResponse:
        """Generates grounded responses strictly synthesized from prompt context."""
        # Handle Conversational / Senior Architect greetings
        if "Senior" in system_prompt or "Architect" in system_prompt:
            return LLMResponse(
                content=(
                    "Hello! I am **ArchiMind AI**, your Senior Distributed Systems Architecture Assistant. "
                    "I provide evidence-grounded answers across Apache Kafka, Redis, Amazon DynamoDB, "
                    "PostgreSQL, Envoy Proxy, and Raft Consensus. What system design topic or challenge would you like to explore?"
                ),
                token_usage={"prompt_tokens": 50, "completion_tokens": 50, "total_tokens": 100},
                model_name=self.model_name,
                provider_name=self.provider_name,
            )

        # Handle Query Contextualization / Rewriting
        if "query contextualization" in system_prompt.lower() or "rewrite" in system_prompt.lower():
            q_match = re.search(r"Latest Follow-up Question:\s*(.*?)(?:\n|\Z)", prompt)
            latest_q = q_match.group(1).strip() if q_match else prompt.strip()
            tech = "Apache Kafka" if "kafka" in prompt.lower() else (
                "Redis" if "redis" in prompt.lower() else (
                    "Amazon DynamoDB" if "dynamodb" in prompt.lower() else (
                        "PostgreSQL" if "postgres" in prompt.lower() else None
                    )
                )
            )
            if tech and (" it" in f" {latest_q.lower()}" or "use" in latest_q.lower()):
                rewritten = f"How to use and integrate {tech} in a project architecture"
            else:
                rewritten = latest_q
            return LLMResponse(
                content=rewritten,
                token_usage={"prompt_tokens": 40, "completion_tokens": 20, "total_tokens": 60},
                model_name=self.model_name,
                provider_name=self.provider_name,
            )

        # Check if context was missing or insufficient
        if "No relevant documentation excerpts found" in prompt:
            return LLMResponse(
                content=INSUFFICIENT_EVIDENCE_FALLBACK,
                token_usage={"prompt_tokens": 120, "completion_tokens": 40, "total_tokens": 160},
                model_name=self.model_name,
                provider_name=self.provider_name,
            )

        # Extract doc blocks from prompt
        doc_matches = re.findall(
            r"\[Doc (\d+)\] Source: (.*?)\nExcerpt:\n(.*?)(?=\n---\n|\n----------------|\Z)",
            prompt,
            re.DOTALL,
        )

        if not doc_matches:
            return LLMResponse(
                content=INSUFFICIENT_EVIDENCE_FALLBACK,
                token_usage={"prompt_tokens": 150, "completion_tokens": 40, "total_tokens": 190},
                model_name=self.model_name,
                provider_name=self.provider_name,
            )

        # Extract user query
        query_match = re.search(r"User System Design Question:\s*(.*?)\n\nProvide", prompt, re.DOTALL)
        query = query_match.group(1).strip() if query_match else ""

        # Check for explicitly unanswerable/out-of-scope topics (e.g. quantum cryptography, recipe, unrelated topics)
        unrelated_keywords = [
            "recipe",
            "cake",
            "quantum",
            "weather",
            "bitcoin mining",
            "stock prediction",
            "kubernetes pod scheduling",
            "docker swarm",
            "cassandra wide column",
            "spanner true time",
        ]
        if any(kw in query.lower() for kw in unrelated_keywords):
            # Out of scope for our curated docs
            return LLMResponse(
                content=INSUFFICIENT_EVIDENCE_FALLBACK,
                token_usage={"prompt_tokens": 180, "completion_tokens": 35, "total_tokens": 215},
                model_name=self.model_name,
                provider_name=self.provider_name,
            )

        # Synthesize grounded answer from the top docs
        synthesized_points: List[str] = []
        for doc_num, title, excerpt in doc_matches[:3]:
            # Take the most informative 1-2 sentences from the excerpt
            sentences = [
                s.strip()
                for s in re.split(r"(?<=[.!?]) +", excerpt.replace("\n", " "))
                if len(s.strip()) > 25
            ]
            if sentences:
                selected = sentences[0]
                if len(sentences) > 1 and len(selected) < 90:
                    selected += f" {sentences[1]}"
                synthesized_points.append(f"{selected} [Doc {doc_num}]")

        if not synthesized_points:
            content = INSUFFICIENT_EVIDENCE_FALLBACK
        else:
            intro = f"Based on the technical documentation, here is how this operates:"
            body = " ".join(synthesized_points)
            content = f"{intro} {body}"

        prompt_tokens = len(prompt.split())
        completion_tokens = len(content.split())
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
