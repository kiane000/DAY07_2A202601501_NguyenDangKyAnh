from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    # Split *after* a sentence-ending mark followed by whitespace, so the
    # punctuation stays attached to the sentence it belongs to.
    SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def split_sentences(self, text: str) -> list[str]:
        """Return non-empty, whitespace-stripped sentences of text."""
        if not text or not text.strip():
            return []
        return [s.strip() for s in self.SENTENCE_BOUNDARY.split(text.strip()) if s.strip()]

    def chunk(self, text: str) -> list[str]:
        sentences = self.split_sentences(text)
        if not sentences:
            return []

        step = self.max_sentences_per_chunk
        return [" ".join(sentences[i : i + step]) for i in range(0, len(sentences), step)]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return self._split(text, list(self.separators))

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        # Base case: the piece already fits the budget.
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Out of separators (or asked to split by ""): fall back to hard slicing.
        if not remaining_separators or remaining_separators[0] == "":
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        rest = remaining_separators[1:]
        pieces = current_text.split(separator)
        if len(pieces) == 1:
            # Separator absent — try the next, coarser-to-finer separator.
            return self._split(current_text, rest)

        chunks: list[str] = []
        buffer = ""
        for piece in pieces:
            if not piece:
                continue
            candidate = f"{buffer}{separator}{piece}" if buffer else piece
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue
            if buffer:
                chunks.append(buffer)
                buffer = ""
            if len(piece) <= self.chunk_size:
                buffer = piece
            else:
                # Piece is still too big on its own: recurse with a finer separator.
                chunks.extend(self._split(piece, rest))
        if buffer:
            chunks.append(buffer)
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    similarity = _dot(vec_a, vec_b) / (norm_a * norm_b)
    # Clamp away floating-point drift so the range stays exactly [-1, 1].
    return max(-1.0, min(1.0, similarity))


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        sentence_chunker = SentenceChunker(
            max_sentences_per_chunk=self._sentences_per_chunk(text, chunk_size)
        )
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=max(0, chunk_size // 10)),
            "by_sentences": sentence_chunker,
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            lengths = [len(c) for c in chunks]
            comparison[name] = {
                "count": len(chunks),
                "avg_length": round(sum(lengths) / len(lengths), 1) if lengths else 0.0,
                "min_length": min(lengths) if lengths else 0,
                "max_length": max(lengths) if lengths else 0,
                "chunks": chunks,
            }
        return comparison

    @staticmethod
    def _sentences_per_chunk(text: str, chunk_size: int) -> int:
        """Pick a sentence budget so all three strategies target a similar chunk size."""
        sentences = SentenceChunker(max_sentences_per_chunk=1).split_sentences(text)
        if not sentences:
            return 1
        avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
        return max(1, round(chunk_size / avg_sentence_length))
