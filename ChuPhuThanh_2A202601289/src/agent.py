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

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)

        context = "\n\n".join(
            f"[Nguồn {index}]\n{result['content']}"
            for index, result in enumerate(results, start=1)
        )

        prompt = f"""Bạn là trợ lý trả lời câu hỏi dựa trên ngữ cảnh được cung cấp.
        Chỉ dùng thông tin trong ngữ cảnh. Nếu không có đủ thông tin, hãy nói rõ điều đó.

        Ngữ cảnh:
        {context}

        Câu hỏi: {question}

        Trả lời:"""

        return self.llm_fn(prompt)