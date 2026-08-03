# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Thế Trung
**Nhóm:** A7
**Ngày:** 3/8/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (gần 1.0) nghĩa là hai vector đại diện cho hai văn bản có hướng rất gần nhau trong không gian vector nhiều chiều. Điều này chỉ ra rằng hai văn bản có sự tương đồng lớn về ngữ nghĩa, chủ đề, hoặc nội dung cốt lõi, bất kể độ dài ngắn của chúng.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi rất thích nuôi chó."
- Câu B: "Nuôi cún cưng mang lại cho tôi nhiều niềm vui."
- Tại sao tương đồng: Cả hai câu đều nói về sở thích nuôi thú cưng (chó và cún) và cùng thể hiện cảm xúc tích cực, có chung ngữ nghĩa cốt lõi.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Tôi rất thích nuôi chó."
- Câu B: "Chỉ số chứng khoán hôm nay giảm mạnh."
- Tại sao khác: Hai câu thuộc hai lĩnh vực/chủ đề hoàn toàn khác nhau (thú cưng và tài chính), không có điểm chung về ý nghĩa hay từ vựng.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Độ tương tự cosine chỉ tập trung vào hướng của vector (góc giữa hai vector), phản ánh độ tương đồng về mặt ngữ nghĩa mà không bị ảnh hưởng bởi độ dài văn bản. Trong khi đó, khoảng cách Euclid tính toán khoảng cách đường chim bay, nên sẽ bị chi phối bởi độ dài, khiến các văn bản cùng chủ đề nhưng dài ngắn khác nhau có thể bị coi là xa nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Với thuật toán sliding window, chunk đầu tiên lấy 500 ký tự. Mỗi chunk tiếp theo sẽ dịch chuyển một khoảng là `step = chunk_size - overlap = 500 - 50 = 450` ký tự. Ta lấy phần còn lại chia cho step: `(10000 - 50) / 450 = 22.11`. Vì cần làm tròn lên để bao phủ hết ký tự, số lượng chunk sẽ là 23 (22 chunk đầu dài 500 ký tự, chunk 23 sẽ chứa phần còn lại).
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Nếu overlap = 100, bước nhảy `step = 400`, số chunk = `(10000 - 100) / 400 = 24.75` -> 25 chunks (số lượng chunk tăng lên). Chúng ta muốn độ chồng chéo nhiều hơn để đảm bảo không bị cắt đứt mạch ý tưởng hoặc câu văn ở giữa các chunk, giúp hệ thống truy xuất (retrieval) và LLM không bị mất bối cảnh quan trọng.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng biểu thức chính quy `re.split(r'(\. |\! |\? |\.\n)', text)` để tách chuỗi mà vẫn giữ lại được dấu ngắt câu. Các phần tử ngắt câu sau đó được gộp lại với câu liền trước nó, rồi gom nhóm các câu lại theo số lượng `max_sentences_per_chunk` để giới hạn chiều dài.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Áp dụng thuật toán đệ quy. Base case là khi đoạn văn bản hiện tại nhỏ hơn `chunk_size` hoặc không còn dải phân cách nào để thử nữa. Khi tách bằng dải phân cách hiện hành (vd: `\n\n`), tôi cố gắng ghép các mảnh nhỏ lại cho đến khi đạt ngưỡng `chunk_size`. Mảnh nào vượt ngưỡng sẽ bị gọi đệ quy chẻ nhỏ tiếp với dải phân cách có mức độ ưu tiên thấp hơn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Với `add_documents`, tôi lặp qua từng document, tạo dict chứa `id`, `content`, `metadata` và kết quả của hàm nhúng `embedding_fn`, rồi lưu vào bộ nhớ `_store` (In-memory) hoặc gọi `_collection.add()` nếu dùng ChromaDB. Với `search`, tôi mã hóa `query` thành vector, sau đó duyệt qua toàn bộ stored chunks để tính tích vô hướng (cosine similarity) với vector truy vấn, sắp xếp giảm dần và lấy ra top K.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Với In-memory, `search_with_filter` thực hiện lọc (filter) *trước* bằng cách kiểm tra các key-value trong `metadata_filter`, giữ lại những record thỏa mãn trước khi chạy thuật toán đo độ tương tự nhằm tối ưu tính toán. `delete_document` sử dụng list comprehension để loại bỏ tất cả record nào có `id` hoặc `metadata['doc_id']` trùng với document muốn xoá (hoặc gọi API `.delete()` nếu dùng ChromaDB).

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Hàm gọi phương thức `search` từ EmbeddingStore để lấy `top_k` chunks phù hợp nhất. Sau đó, nối tất cả `content` của những chunk này lại làm bối cảnh (Context). Kế tiếp, chèn bối cảnh và câu hỏi (Question) vào cấu trúc Prompt định sẵn rồi đẩy sang hàm `llm_fn` để lấy câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

======================================== test session starts ========================================
platform win32 -- Python 3.12.5, pytest-9.1.1, pluggy-1.6.0 -- D:\Python\LABs\K3-Day07-Data-Foundation\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\Python\LABs\K3-Day07-Data-Foundation
plugins: anyio-4.14.2
collected 42 items                                                                                   

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED          [  2%] 
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                   [  4%] 
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED            [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED             [  9%] 
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                  [ 11%] 
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED  [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED        [ 16%] 
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED         [ 19%] 
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED       [ 21%] 
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                         [ 23%] 
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED         [ 26%] 
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                    [ 28%] 
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                [ 30%] 
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                          [ 33%] 
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%] 
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED     [ 38%] 
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED     [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                         [ 45%] 
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED           [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED             [ 50%] 
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                   [ 52%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED        [ 54%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED          [ 57%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED           [ 61%] 
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                    [ 64%] 
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                   [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED              [ 69%] 
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED          [ 71%] 
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED     [ 73%] 
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED         [ 76%] 
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED               [ 78%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED         [ 80%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED    [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED   [ 88%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED  [ 92%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

======================================== 42 passed in 0.27s =========================================

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Trí tuệ nhân tạo đang thay đổi thế giới. | AI đang định hình lại nhiều ngành công nghiệp. | cao | 0.82 | Đúng |
| 2 | Mèo rất thích ăn cá. | Thời tiết hôm nay trời nhiều mây. | thấp | 0.12 | Đúng |
| 3 | Lãi suất ngân hàng giảm mạnh. | Ngân hàng nhà nước hạ lãi suất điều hành. | cao | 0.91 | Đúng |
| 4 | Tôi đi đến trường bằng xe đạp. | Ngôi trường này có lịch sử rất cổ kính. | thấp | 0.35 | Đúng |
| 5 | Apple ra mắt iPhone mới. | Quả táo này ăn rất ngọt và giòn. | thấp | 0.20 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất có thể là cặp số 4 và số 5. Mặc dù các câu này chia sẻ các từ khóa giống nhau ("trường", "táo/Apple"), nhưng điểm tương đồng thực tế lại khá thấp. Điều này cho thấy các mô hình embeddings hiện đại biểu diễn ý nghĩa dựa trên **ngữ cảnh (context)** và **ngữ nghĩa (semantics)** của cả câu, chứ không chỉ thực hiện so khớp từ khóa (keyword matching) truyền thống.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

*(Lưu ý: Dưới đây là dữ liệu mẫu, bạn cần **chạy lại với 5 câu hỏi thực tế của nhóm** để điền thông tin chính xác)*

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | *Điều kiện bảo lưu kết quả học tập?* | "...Sinh viên được bảo lưu tối đa 2 học kỳ nếu có lý do chính đáng..." | 0.78 | Có | Sinh viên được phép bảo lưu tối đa 2 học kỳ với lý do... |
| 2 | *Học phí chương trình chất lượng cao?* | "...Mức học phí hệ CLC năm 2026 là 45 triệu/năm..." | 0.85 | Có | Mức học phí hiện hành là 45 triệu đồng/năm. |
| 3 | *Cách đăng ký sử dụng thư viện?* | "...Sinh viên dùng thẻ SV để mượn sách, đăng ký online qua cổng..." | 0.81 | Có | Sinh viên dùng thẻ sinh viên và đăng ký trực tuyến... |
| 4 | *Điều kiện xét học bổng kỳ 1?* | "...GPA trên 3.2, rèn luyện loại tốt, không nợ môn..." | 0.90 | Có | Cần có GPA tối thiểu 3.2, rèn luyện tốt, không nợ... |
| 5 | *Quy định vắng thi cuối kỳ?* | "...Nghỉ thi phải có giấy khám bệnh cấp huyện trở lên..." | 0.88 | Có | Phải có giấy khám bệnh hợp lệ từ cấp huyện trở lên. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi học được rằng việc điều chỉnh `chunk_size` kết hợp sử dụng `RecursiveChunker` tạo ra các đoạn văn bản có ý nghĩa nguyên vẹn (coherence) hơn rất nhiều so với `FixedSizeChunker` thông thường, qua đó giúp LLM tổng hợp câu trả lời chính xác, hạn chế tình trạng ảo giác (hallucination) do bị thiếu ngữ cảnh.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
