from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    SYSTEM_INSTRUCTION = (
        "Bạn là trợ lý tra cứu dịch vụ/quy định đại học. "
        "Chỉ trả lời dựa trên NGỮ CẢNH được cung cấp bên dưới. "
        "Trích dẫn số nguồn dạng [1], [2] cho từng thông tin. "
        "Nếu ngữ cảnh không chứa câu trả lời, hãy nói rõ là không tìm thấy trong tài liệu."
    )

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        prompt = self._build_prompt(question, results)
        return str(self.llm_fn(prompt))

    def _build_prompt(self, question: str, results: list[dict]) -> str:
        if not results:
            context = "(không truy xuất được tài liệu liên quan)"
        else:
            blocks = []
            for position, result in enumerate(results, start=1):
                metadata = result.get("metadata") or {}
                source = (
                    metadata.get("source_url")
                    or metadata.get("source")
                    or metadata.get("doc_id")
                    or result.get("id", "unknown")
                )
                blocks.append(
                    f"[{position}] nguồn: {source} (score={result.get('score', 0.0):.3f})\n"
                    f"{result.get('content', '')}"
                )
            context = "\n\n".join(blocks)

        return (
            f"{self.SYSTEM_INSTRUCTION}\n\n"
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI: {question}\n\n"
            "TRẢ LỜI (tiếng Việt, ngắn gọn, kèm trích dẫn [n]):"
        )
