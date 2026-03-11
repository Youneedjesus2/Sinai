from pathlib import Path

from src.integrations.vector_store import VectorStoreClient
from src.schemas.llm import RetrievalResult

KNOWLEDGE_DIR = Path(__file__).parents[4] / 'knowledge'

CONFIDENCE_THRESHOLD = 0.65


class RetrievalService:
    def retrieve(self, query: str, agency_id: str) -> RetrievalResult:
        try:
            client = VectorStoreClient()
            index = client.get_or_create_index(str(KNOWLEDGE_DIR))
            nodes = client.query(index, query)

            if not nodes:
                return RetrievalResult(
                    context_chunks=[],
                    confidence_score=0.0,
                    sources=[],
                    context_found=False,
                )

            scores = [n.score if n.score is not None else 0.0 for n in nodes]
            confidence_score = sum(scores) / len(scores)
            context_chunks = [n.node.get_content() for n in nodes]
            sources = [n.node.metadata.get('file_name', 'unknown') for n in nodes]
            context_found = confidence_score >= CONFIDENCE_THRESHOLD

            return RetrievalResult(
                context_chunks=context_chunks if context_found else [],
                confidence_score=confidence_score,
                sources=sources,
                context_found=context_found,
            )
        except Exception:
            return RetrievalResult(
                context_chunks=[],
                confidence_score=0.0,
                sources=[],
                context_found=False,
            )
