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

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        raw_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\.\n', text) if s.strip()]
        if not raw_sentences:
            return [text.strip()] if text.strip() else []

        chunks: list[str] = []
        for i in range(0, len(raw_sentences), self.max_sentences_per_chunk):
            group = raw_sentences[i : i + self.max_sentences_per_chunk]
            chunks.append(" ".join(group))
        return chunks


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
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        sep = remaining_separators[0]
        if sep == "":
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        if sep in current_text:
            parts = current_text.split(sep)
            chunks: list[str] = []
            current_group: list[str] = []
            current_len = 0
            for part in parts:
                part_len = len(part) + (len(sep) if current_group else 0)
                if current_len + part_len <= self.chunk_size:
                    current_group.append(part)
                    current_len += part_len
                else:
                    if current_group:
                        joined = sep.join(current_group)
                        if len(joined) <= self.chunk_size:
                            chunks.append(joined)
                        else:
                            chunks.extend(self._split(joined, remaining_separators[1:]))
                        current_group = []
                        current_len = 0
                    if len(part) <= self.chunk_size:
                        current_group.append(part)
                        current_len = len(part)
                    else:
                        chunks.extend(self._split(part, remaining_separators[1:]))
            if current_group:
                joined = sep.join(current_group)
                if len(joined) <= self.chunk_size:
                    chunks.append(joined)
                else:
                    chunks.extend(self._split(joined, remaining_separators[1:]))
            return [c for c in chunks if c]
        else:
            return self._split(current_text, remaining_separators[1:])


class HeaderChunker:
    """
    Split Markdown text into chunks aligned with heading boundaries.

    Each section starts at a heading line ("#" .. "######") and runs until
    the next heading (or end of text); the heading is kept as a prefix on
    every chunk it produces. Regulation articles such as "### Điều 10. Đăng
    ký học phần" lose their meaning once separated from their title, so
    tying chunk boundaries to headings keeps each article self-contained.
    Sections longer than chunk_size are further split on blank-line
    paragraph breaks, then hard-cut as a last resort.
    """

    HEADER_RE = re.compile(r'^(#{1,6})\s+(.*)$', re.MULTILINE)

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        chunks: list[str] = []
        for header, body in self._split_sections(text):
            content = f"{header}\n{body}".strip() if header else body.strip()
            if not content:
                continue
            if len(content) <= self.chunk_size:
                chunks.append(content)
            else:
                chunks.extend(self._split_long_section(header, body))
        return chunks

    def _split_sections(self, text: str) -> list[tuple[str, str]]:
        matches = list(self.HEADER_RE.finditer(text))
        if not matches:
            return [("", text)]

        sections: list[tuple[str, str]] = []
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append(("", preamble))

        for i, match in enumerate(matches):
            header = match.group(0).strip()
            body_start = match.end()
            body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sections.append((header, text[body_start:body_end]))
        return sections

    def _split_long_section(self, header: str, body: str) -> list[str]:
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        chunks: list[str] = []
        buffer = ""
        for para in paragraphs:
            candidate = f"{buffer}\n\n{para}" if buffer else para
            if len(header) + len(candidate) + 1 <= self.chunk_size:
                buffer = candidate
                continue
            if buffer:
                chunks.append(f"{header}\n{buffer}".strip())
                buffer = ""
            if len(header) + len(para) + 1 <= self.chunk_size:
                buffer = para
            else:
                for i in range(0, len(para), self.chunk_size):
                    chunks.append(f"{header}\n{para[i : i + self.chunk_size]}".strip())
        if buffer:
            chunks.append(f"{header}\n{buffer}".strip())
        return chunks


class SlidingSentenceWindowChunker:
    """
    Group sentences into overlapping windows instead of disjoint batches.

    Unlike SentenceChunker (non-overlapping groups of N sentences),
    consecutive windows share `overlap` sentences, so a rule split across a
    sentence boundary (a condition in one sentence, its exception in the
    next) still appears together in at least one chunk.
    """

    def __init__(self, window_size: int = 4, overlap: int = 1) -> None:
        self.window_size = max(1, window_size)
        self.overlap = max(0, min(overlap, self.window_size - 1))

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\.\n', text) if s.strip()]
        if not sentences:
            return [text.strip()] if text.strip() else []

        step = self.window_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(sentences), step):
            window = sentences[start : start + self.window_size]
            if not window:
                break
            chunks.append(" ".join(window))
            if start + self.window_size >= len(sentences):
                break
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(y * y for y in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed_chunks = FixedSizeChunker(chunk_size=chunk_size, overlap=0).chunk(text)
        sentence_chunks = SentenceChunker(max_sentences_per_chunk=3).chunk(text)
        recursive_chunks = RecursiveChunker(chunk_size=chunk_size).chunk(text)

        def _stats(chunks: list[str]) -> dict:
            count = len(chunks)
            avg_len = float(sum(len(c) for c in chunks) / count) if count > 0 else 0.0
            return {
                "count": count,
                "avg_length": avg_len,
                "chunks": chunks,
            }

        return {
            "fixed_size": _stats(fixed_chunks),
            "by_sentences": _stats(sentence_chunks),
            "recursive": _stats(recursive_chunks),
        }

