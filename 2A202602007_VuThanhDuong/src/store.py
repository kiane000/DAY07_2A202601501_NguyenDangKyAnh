from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=self._collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata)
        metadata.setdefault("doc_id", doc.id)
        return {
            "id": str(doc.id),
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
            "index": self._next_index,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []

        from heapq import nlargest

        query_embedding = self._embedding_fn(query)
        scored = ((_dot(query_embedding, record["embedding"]), record) for record in records)
        return [dict(record, score=score) for score, record in nlargest(top_k, scored, key=lambda item: item[0])]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        records = []
        for doc in docs:
            records.append(self._make_record(doc))
            self._next_index += 1

        if not records:
            return

        if self._use_chroma and self._collection is not None:
            self._collection.add(
                ids=[record["id"] for record in records],
                documents=[record["content"] for record in records],
                embeddings=[record["embedding"] for record in records],
                metadatas=[
                    {**record["metadata"], "index": record["index"]}
                    for record in records
                ],
            )
        else:
            self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)
        if self._use_chroma and self._collection is not None:
            result = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
            ids = result.get("ids", [[]])[0]
            documents = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]
            return [
                {
                    "id": id_,
                    "content": content,
                    "metadata": metadata or {},
                    "score": -distance,
                }
                for id_, content, metadata, distance in zip(ids, documents, metadatas, distances)
            ]

        scored = ((_dot(query_embedding, record["embedding"]), record) for record in self._store)
        from heapq import nlargest

        return [dict(record, score=score) for score, record in nlargest(top_k, scored, key=lambda item: item[0])]

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return int(self._collection.count())
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self._search_records(query, self._store, top_k)

        filter_items = tuple(metadata_filter.items())
        filtered_records = [
            record
            for record in self._store
            if all(record["metadata"].get(key) == value for key, value in filter_items)
        ]
        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            before = int(self._collection.count())
            self._collection.delete(where={"doc_id": doc_id})
            return int(self._collection.count()) < before

        before = len(self._store)
        self._store = [record for record in self._store if record["metadata"].get("doc_id") != doc_id]
        return len(self._store) < before
