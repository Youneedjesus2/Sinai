from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.core.config import get_settings

if TYPE_CHECKING:
    from llama_index.core import VectorStoreIndex
    from llama_index.core.schema import NodeWithScore


class VectorStoreClient:
    def get_or_create_index(self, documents_path: str) -> VectorStoreIndex:
        from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex

        docs_path = Path(documents_path)
        if not docs_path.exists():
            return VectorStoreIndex.from_documents([])

        try:
            documents = SimpleDirectoryReader(str(docs_path)).load_data()
        except Exception:
            documents = []

        if not documents:
            return VectorStoreIndex.from_documents([])

        db_url = get_settings().database_url
        if db_url.startswith('postgresql'):
            from llama_index.vector_stores.postgres import PGVectorStore
            from sqlalchemy.engine import make_url

            parsed = make_url(db_url)
            vector_store = PGVectorStore.from_params(
                host=parsed.host or 'localhost',
                port=str(parsed.port or 5432),
                database=parsed.database or 'sinai',
                user=parsed.username or '',
                password=str(parsed.password or ''),
                table_name='knowledge_vectors',
                embed_dim=1536,
            )
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            return VectorStoreIndex.from_documents(documents, storage_context=storage_context)

        return VectorStoreIndex.from_documents(documents)

    def query(self, index: VectorStoreIndex, query_text: str, top_k: int = 5) -> list[NodeWithScore]:
        retriever = index.as_retriever(similarity_top_k=top_k)
        return retriever.retrieve(query_text)
