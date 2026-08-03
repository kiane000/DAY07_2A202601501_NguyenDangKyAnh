import os

from ingest import build_knowledge_base
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import LocalEmbedder

DATA_DIR = "data/data_vinuni"

QUESTIONS = [
    (
        "Q1",
        "Để đăng ký học phần thành công trên SIS, sinh viên cần thao tác theo những bước nào và trạng thái nào xác nhận đã đăng ký xong?",
        "vinuni-course-registration-guide",
    ),
    (
        "Q2",
        "Nếu lớp đã đầy, bị trùng lịch hoặc chưa đạt điều kiện tiên quyết khi đăng ký môn, sinh viên nên làm gì?",
        "vinuni-course-registration-guide",
    ),
    (
        "Q3",
        "Sinh viên đại học được mượn tối đa bao nhiêu tài liệu thư viện và trong thời hạn bao lâu?",
        "vinuni-library-borrowing-privileges",
    ),
    (
        "Q4",
        "Thư viện VinUni mở cửa vào giờ nào trong học kỳ, và khu nào mở 24/7?",
        "vinuni-library-access-services",
    ),
    (
        "Q5",
        "Nếu không hoàn thành học phí đúng hạn từ một tuần, sinh viên sẽ bị hạn chế gì?",
        "vinuni-financial-regulation-2023-2024",
    ),
]

# Chọn bằng PowerShell: $env:BENCHMARK_CHUNKER = "fixed" | "sentence" | "recursive"
chunker_name = os.getenv("BENCHMARK_CHUNKER", "sentence").strip().lower()
chunkers = {
    "fixed": FixedSizeChunker(chunk_size=500, overlap=50),
    "sentence": SentenceChunker(max_sentences_per_chunk=3),
    "recursive": RecursiveChunker(chunk_size=500),
}
if chunker_name not in chunkers:
    raise ValueError("BENCHMARK_CHUNKER phải là fixed, sentence hoặc recursive")
chunker = chunkers[chunker_name]

print(f"Đang khởi tạo embedding và nạp dữ liệu ({chunker_name})...")
embedder = LocalEmbedder()
store = build_knowledge_base(DATA_DIR, embedding_fn=embedder, chunker=chunker)
print(f"Đã nạp {store.get_collection_size()} chunks.\n")

for label, question, expected_doc_id in QUESTIONS:
    print("=" * 80)
    print(f"{label}: {question}")
    print(f"Tài liệu kỳ vọng: {expected_doc_id}")

    # Q5 cần thu hẹp về tài liệu tài chính để tránh nhiều điều khoản tài chính khác gây nhiễu.
    metadata_filter = {"department": "finance"} if label == "Q5" else None
    results = store.search_with_filter(question, top_k=3, metadata_filter=metadata_filter)
    if metadata_filter:
        print(f"Bộ lọc metadata: {metadata_filter}")
    for rank, result in enumerate(results, start=1):
        metadata = result["metadata"]
        content = result["content"].replace("\n", " ")
        print(
            f"\nTop-{rank} | score={result['score']:.4f}"
            f" | doc_id={metadata.get('doc_id')}"
            f" | chunk={metadata.get('chunk_index')}"
        )
        print(f"Nội dung: {content[:350]}")

    relevant = any(
        result["metadata"].get("doc_id") == expected_doc_id
        for result in results
    )
    print(f"\nKết quả: tài liệu kỳ vọng có trong Top-3? {'CÓ' if relevant else 'KHÔNG'}")

print("\n" + "=" * 80)
print("KIỂM TRA METADATA FILTER — Q4, chỉ tìm tài liệu của thư viện")
filtered = store.search_with_filter(
    QUESTIONS[3][1],
    top_k=3,
    metadata_filter={"department": "library"},
)

for rank, result in enumerate(filtered, start=1):
    print(
        f"Top-{rank} | score={result['score']:.4f}"
        f" | doc_id={result['metadata'].get('doc_id')}"
    )
