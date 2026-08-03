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
        self._client = None
        self._next_index = 0

        try:
            import chromadb  # type: ignore # noqa: F401

            # An ephemeral client keeps every store instance isolated (no state
            # leaking between runs). The in-memory list below stays the source of
            # truth for search/filter/delete; Chroma is a mirror for persistence
            # demos, so behaviour is identical with or without it installed.
            self._client = chromadb.EphemeralClient()
            self._collection = self._client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Normalize one Document into a stored record (embedding computed once)."""
        metadata = dict(doc.metadata or {})
        # Guarantee a doc_id so search_with_filter/delete_document work even for
        # documents that were added without any metadata.
        metadata.setdefault("doc_id", doc.id)

        record = {
            "key": f"{doc.id}#{self._next_index}",  # unique even if doc.id repeats
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
            "index": self._next_index,
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Rank records against query by dot product; embeddings are unit-norm, so this is cosine."""
        if not records or top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)
        scored = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "score": float(_dot(query_embedding, record["embedding"])),
            }
            for record in records
        ]
        # Sort by score desc; insertion order breaks ties so results are stable.
        scored.sort(key=lambda item: -item["score"])
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        records = [self._make_record(doc) for doc in docs or []]
        if not records:
            return

        self._store.extend(records)

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(
                    ids=[r["key"] for r in records],
                    documents=[r["content"] for r in records],
                    embeddings=[r["embedding"] for r in records],
                    metadatas=[r["metadata"] for r in records],
                )
            except Exception:
                self._use_chroma = False  # mirror is best-effort only

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        # Pre-filter: only chunks matching every requested key/value are scored.
        candidates = [
            record
            for record in self._store
            if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
        ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        kept = [record for record in self._store if record["metadata"].get("doc_id") != doc_id]
        removed = [record for record in self._store if record["metadata"].get("doc_id") == doc_id]
        if not removed:
            return False

        self._store = kept
        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(ids=[r["key"] for r in removed])
            except Exception:
                self._use_chroma = False
        return True
