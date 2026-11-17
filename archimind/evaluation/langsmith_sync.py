"""LangSmith dataset management and run tracking synchronization."""

import logging
import os
from typing import List, Optional, Tuple

from archimind.config import settings
from archimind.evaluation.dataset import BENCHMARK_DATASET, BenchmarkQuestion

logger = logging.getLogger(__name__)


class LangSmithSync:
    """Manages synchronization of benchmark datasets and runs with LangSmith."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_name: Optional[str] = None,
        endpoint: Optional[str] = None,
    ):
        self.api_key = (
            api_key
            or os.environ.get("LANGSMITH_API_KEY")
            or settings.LANGCHAIN_API_KEY
        )
        self.project_name = project_name or settings.LANGCHAIN_PROJECT
        self.endpoint = endpoint or settings.LANGCHAIN_ENDPOINT
        self.dataset_name = "archimind-system-design-benchmark"

    def is_configured(self) -> bool:
        """Returns True if a valid LangSmith API key is available."""
        return bool(self.api_key and self.api_key.strip())

    def sync_benchmark_dataset(self) -> Tuple[bool, Optional[str], str]:
        """Creates or syncs the 30-question benchmark dataset in LangSmith."""
        if not self.is_configured():
            msg = "LangSmith API key not configured. Set LANGCHAIN_API_KEY in .env to enable remote tracing."
            logger.info(msg)
            return False, None, msg

        try:
            from langsmith import Client

            client = Client(api_key=self.api_key, api_url=self.endpoint)

            # Check if dataset already exists
            datasets = list(client.list_datasets(dataset_name=self.dataset_name))
            if datasets:
                dataset = datasets[0]
                logger.info("Existing LangSmith dataset found: %s (id=%s)", self.dataset_name, dataset.id)
                return True, str(dataset.id), f"Dataset already exists with ID: {dataset.id}"

            # Create new dataset
            dataset = client.create_dataset(
                dataset_name=self.dataset_name,
                description="ArchiMind AI 30-Question System Design Benchmark Dataset with Evidence Grounding",
            )

            # Upload benchmark questions as examples
            for item in BENCHMARK_DATASET:
                client.create_example(
                    inputs={"question": item.question, "topic": item.topic},
                    outputs={
                        "ground_truth_answer": item.ground_truth_answer,
                        "expected_doc_urls": item.expected_doc_urls,
                        "expected_keywords": item.expected_keywords,
                        "is_answerable": item.is_answerable,
                        "difficulty": item.difficulty,
                    },
                    dataset_id=dataset.id,
                )

            logger.info("Successfully created LangSmith dataset '%s' with %d examples", self.dataset_name, len(BENCHMARK_DATASET))
            return True, str(dataset.id), f"Created LangSmith dataset with ID: {dataset.id}"

        except Exception as e:
            logger.error("Failed to sync dataset to LangSmith: %s", e)
            return False, None, f"LangSmith sync failed: {str(e)}"
