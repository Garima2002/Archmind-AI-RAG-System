"""Core RAG engine orchestrating retrieval, LLM generation, and citation attribution."""

import logging
import re
import time
from typing import Dict, List, Optional, Set

from archimind.api.schemas import Citation, DocumentChunkModel, QueryRequest, QueryResponse
from archimind.config import settings
from archimind.rag.prompt import (
    ARCHITECT_CONVERSATION_PROMPT,
    INSUFFICIENT_EVIDENCE_FALLBACK,
    QUERY_REWRITE_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_rag_prompt,
)
from archimind.rag.providers.base import LLMProvider
from archimind.rag.providers.factory import get_llm_provider
from archimind.rag.retriever import SemanticRetriever

logger = logging.getLogger(__name__)


class RAGEngine:
    """Orchestrates intent classification, query rewriting, retrieval, and grounded citation mapping."""

    def __init__(
        self,
        retriever: Optional[SemanticRetriever] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        self.retriever = retriever or SemanticRetriever()
        self.llm_provider = llm_provider or get_llm_provider()

    def _detect_intent(self, query: str) -> str:
        """Classifies incoming query as 'greeting' or 'technical'."""
        cleaned = re.sub(r"[^\w\s]", "", query.strip().lower())
        tokens = cleaned.split()
        if not tokens:
            return "technical"

        # Short greeting patterns (<= 5 tokens)
        if len(tokens) <= 5:
            exact_greetings = {
                "hi", "hello", "hey", "hiya", "howdy", "namaste", "hola",
                "sup", "yo", "greetings", "good morning", "good afternoon",
                "good evening", "good day", "thanks", "thank you", "thx",
                "bye", "goodbye", "see ya", "cya", "ok", "okay",
            }
            if cleaned in exact_greetings:
                return "greeting"
            if tokens[0] in {"hi", "hello", "hey", "greetings"}:
                return "greeting"

        # Persona and capability queries
        meta_phrases = [
            "who are you",
            "what are you",
            "what can you do",
            "what do you do",
            "what is archimind",
            "what does archmind represent",
            "who made you",
            "how can you help me",
            "introduce yourself",
            "tell me about yourself",
        ]
        for phrase in meta_phrases:
            if phrase in cleaned:
                return "greeting"

        return "technical"

    def _rewrite_query(self, query: str, history: List) -> str:
        """Contextualizes a follow-up query using preceding turns into a standalone search query."""
        if not history:
            return query

        conversation_lines = []
        for item in history[-4:]:
            role = getattr(item, "role", "user")
            content = getattr(item, "content", "")
            prefix = "User" if role == "user" else "Assistant"
            conversation_lines.append(f"{prefix}: {content[:300]}")

        conversation_context = "\n".join(conversation_lines)
        rewrite_prompt = (
            f"Conversation History:\n{conversation_context}\n\n"
            f"Latest Follow-up Question:\n{query}\n\n"
            "Rewritten Standalone Search Query:"
        )

        try:
            response = self.llm_provider.generate(
                prompt=rewrite_prompt,
                system_prompt=QUERY_REWRITE_SYSTEM_PROMPT,
            )
            rewritten = response.content.strip()
            rewritten = re.sub(r'^["\']|["\']$', "", rewritten)
            rewritten = re.sub(r"^(Rewritten Query|Standalone Query):\s*", "", rewritten, flags=re.IGNORECASE).strip()
            if rewritten and len(rewritten) >= 3:
                logger.info("Contextualized query: '%s' -> '%s'", query, rewritten)
                return rewritten
        except Exception as e:
            logger.warning("Query rewriting failed: %s; falling back to original query", e)

        return query

    def _extract_citations(
        self, answer: str, chunks: List[DocumentChunkModel]
    ) -> List[Citation]:
        """Extracts [Doc X] or [X] citations from the answer and matches against retrieved chunks."""
        citations: List[Citation] = []
        if not chunks:
            return citations

        # Match [Doc 1], [Doc 2], [1], [2], etc.
        doc_refs = re.findall(r"\[(?:Doc\s*)?(\d+)\]", answer)
        referenced_indices: Set[int] = set()
        for ref in doc_refs:
            try:
                idx = int(ref)
                if 1 <= idx <= len(chunks):
                    referenced_indices.add(idx)
            except ValueError:
                continue

        # If model used citation markers, build targeted citations
        if referenced_indices:
            for idx in sorted(referenced_indices):
                chunk = chunks[idx - 1]
                snippet = (
                    chunk.content[:240] + "..." if len(chunk.content) > 240 else chunk.content
                )
                citations.append(
                    Citation(
                        citation_id=idx,
                        document_id=chunk.document_id,
                        document_title=chunk.document_title,
                        document_url=chunk.document_url,
                        section_title=chunk.section_title,
                        chunk_id=chunk.id,
                        snippet=snippet,
                        score=chunk.score or 0.0,
                    )
                )
        else:
            # If model didn't output explicit brackets but answered from evidence, attach top context
            for idx, chunk in enumerate(chunks[:2], start=1):
                snippet = (
                    chunk.content[:240] + "..." if len(chunk.content) > 240 else chunk.content
                )
                citations.append(
                    Citation(
                        citation_id=idx,
                        document_id=chunk.document_id,
                        document_title=chunk.document_title,
                        document_url=chunk.document_url,
                        section_title=chunk.section_title,
                        chunk_id=chunk.id,
                        snippet=snippet,
                        score=chunk.score or 0.0,
                    )
                )

        return citations

    def answer_query(self, request: QueryRequest) -> QueryResponse:
        """Executes full RAG query lifecycle with intent routing and contextual rewriting."""
        start_time = time.perf_counter()

        # 1. Intent Detection
        intent = self._detect_intent(request.query)

        # 2. Conversational / Senior Architect Greeting Routing
        if intent == "greeting":
            logger.info("Routing conversational/greeting query '%s' to architect persona", request.query[:40])
            llm_response = self.llm_provider.generate(
                prompt=request.query,
                system_prompt=ARCHITECT_CONVERSATION_PROMPT,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return QueryResponse(
                query=request.query,
                answer=llm_response.content.strip(),
                is_sufficient_evidence=True,
                citations=[],
                retrieved_chunks_count=0,
                latency_ms=round(elapsed_ms, 2),
                llm_provider=self.llm_provider.provider_name,
                model_name=llm_response.model_name or self.llm_provider.model_name,
                token_usage=llm_response.token_usage,
                rephrased_query=None,
                intent="greeting",
            )

        # 3. Contextual Query Rewriting for follow-up questions
        search_query = request.query
        rephrased_query = None
        if request.history and len(request.history) > 0:
            tokens_lower = set(re.findall(r"\b\w+\b", request.query.lower()))
            anaphora_triggers = {
                "it", "its", "this", "that", "they", "them", "these", "those",
                "do", "use", "how", "why", "what", "example", "difference",
                "previous", "above", "mentioned", "system", "architecture",
            }
            if tokens_lower.intersection(anaphora_triggers) or len(request.query.split()) <= 10:
                rewritten = self._rewrite_query(request.query, request.history)
                if rewritten and rewritten.lower() != request.query.lower():
                    search_query = rewritten
                    rephrased_query = rewritten

        # 4. Dense Semantic Retrieval
        retrieved_chunks = self.retriever.retrieve(
            query=search_query,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
        )

        # 5. Intelligent Architectural Primitive Retrieval for System Design Requests
        if not retrieved_chunks:
            design_keywords = [
                "architecture", "architect", "design", "wallet", "app",
                "system", "finance", "scale", "pipeline", "ledger",
                "payment", "store", "flow", "microservice", "infrastructure",
            ]
            is_design_request = any(
                w in search_query.lower() or w in request.query.lower()
                for w in design_keywords
            )
            if is_design_request:
                logger.info(
                    "Primary retrieval returned 0 chunks for system design query '%s'. Retrieving core architectural primitives.",
                    request.query[:50],
                )
                retrieved_chunks = self.retriever.retrieve(
                    query="PostgreSQL ACID transaction ledger Redis in-memory caching Kafka event streaming DynamoDB",
                    top_k=4,
                    similarity_threshold=0.20,
                )

        # 6. Insufficient Evidence Early Return (if no chunks met similarity threshold)
        if not retrieved_chunks:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.info(
                "Insufficient evidence: 0 chunks passed threshold for query: '%s' (search_query: '%s')",
                request.query[:50],
                search_query[:50],
            )
            return QueryResponse(
                query=request.query,
                answer=INSUFFICIENT_EVIDENCE_FALLBACK,
                is_sufficient_evidence=False,
                citations=[],
                retrieved_chunks_count=0,
                latency_ms=round(elapsed_ms, 2),
                llm_provider=self.llm_provider.provider_name,
                model_name=self.llm_provider.model_name,
                token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                rephrased_query=rephrased_query,
                intent="technical",
            )

        # 7. Assemble Grounded Prompt with History Context
        prompt = build_rag_prompt(request.query, retrieved_chunks, history=request.history)

        # 8. Generate Answer via LLM Provider
        llm_response = self.llm_provider.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        answer = llm_response.content.strip()

        # 9. Check if LLM flagged insufficient evidence
        is_sufficient = True
        if (
            "not have enough evidence" in answer.lower()
            or "insufficient evidence" in answer.lower()
            or answer == INSUFFICIENT_EVIDENCE_FALLBACK
        ):
            is_sufficient = False
            citations = []
        else:
            citations = self._extract_citations(answer, retrieved_chunks)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            "Query answered in %.2fms (chunks=%d, sufficient=%s, citations=%d, rewritten=%s)",
            elapsed_ms,
            len(retrieved_chunks),
            is_sufficient,
            len(citations),
            bool(rephrased_query),
        )

        return QueryResponse(
            query=request.query,
            answer=answer,
            is_sufficient_evidence=is_sufficient,
            citations=citations,
            retrieved_chunks_count=len(retrieved_chunks),
            latency_ms=round(elapsed_ms, 2),
            llm_provider=self.llm_provider.provider_name,
            model_name=llm_response.model_name or self.llm_provider.model_name,
            token_usage=llm_response.token_usage,
            rephrased_query=rephrased_query,
            intent="technical",
        )
