# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đặng Kỳ Anh  
**Mã sinh viên / Nhóm:** 2A202601501 — Nhóm A7
**Ngày:** 03/08/2026  

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:*  
> Độ tương tự cosine cao (gần 1.0) có nghĩa là hai vector biểu diễn của hai đoạn văn bản càng hướng về cùng một phương/chiều trong không gian đặc trưng đa chiều. Điều này phản ánh rằng hai văn bản có sự tương đồng rất lớn về chủ đề và ý nghĩa ngữ nghĩa.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên cần mang thẻ sinh viên khi đến mượn sách tại thư viện trường.
- Câu B: Người dùng phải xuất trình thẻ định danh cá nhân hợp lệ để sử dụng dịch vụ mượn tài liệu.
- Tại sao tương đồng: Cả hai câu đều biểu thị cùng một quy định học vụ/thư viện (yêu cầu xuất trình thẻ cá nhân khi mượn tài liệu), sử dụng các cụm từ đồng nghĩa như "thẻ sinh viên" - "thẻ định danh hợp lệ", "mượn sách" - "mượn tài liệu".

**Ví dụ có độ tương tự THẤP:**
- Câu A: Sinh viên cần thực hiện đăng ký học phần đúng thời hạn trên cổng thông tin học vụ.
- Câu B: Món phở bò truyền thống Việt Nam thường được dùng kèm với quẩy nóng và hành lá.
- Tại sao khác: Hai câu thuộc hai miền tri thức hoàn toàn độc lập, không có mối liên hệ ngữ nghĩa hay từ khóa chung nào.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:*  
> Khoảng cách Euclid phụ thuộc trực tiếp vào độ lớn của vector - các đoạn văn bản dài chứa nhiều từ sẽ tạo ra vector có độ lớn lớn, làm khoảng cách Euclid giữa chúng rất xa ngay cả khi cùng chung chủ đề. Trái lại, độ tương tự Cosine chỉ đo góc giữa hai vector mà không bị ảnh hưởng bởi độ dài vector, giúp so sánh chính xác sự tương đồng ngữ nghĩa giữa các văn bản có độ dài ngắn khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*  
> - Bước nhảy giữa các chunk liên tiếp: step = chunk_size - overlap = 500 - 50 = 450 ký tự.  
> - Phép tính số lượng chunk: làm_tròn_lên((10000 - 50) / 450) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11) = 23 chunks.  
> - Chi tiết các khoảng: Chunk 1: [0:500], Chunk 2: [450:950], ..., Chunk 22: [9450:9950], Chunk 23: [9900:10000].  
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:*  
> Khi overlap tăng lên 100, bước nhảy giảm xuống: step = 500 - 100 = 400 ký tự.  
> Số lượng chunk mới = làm_tròn_lên((10000 - 100) / 400) = làm_tròn_lên(9900 / 400) = làm_tròn_lên(24.75) = 25 chunks (tăng thêm 2 chunks).  
> Việc tăng độ chồng chéo giúp duy trì tính liên tục của ngữ cảnh tại các ranh giới cắt, tránh tình trạng một câu văn hoặc một ý nghĩa quan trọng bị chia cắt làm đôi gây mất thông tin khi truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?*  
> Tôi sử dụng biểu thức chính quy với kỹ thuật lookbehind `r'(?<=[.!?])\s+|\.\n'` để phát hiện ranh giới câu dựa trên các dấu kết thúc câu chuẩn (`. `, `! `, `? `, `.\n`) mà vẫn giữ nguyên được nội dung câu. Hàm xử lý các trường hợp ngoại lệ như chuỗi rỗng (trả về `[]`), văn bản không có dấu câu chuẩn (trả về chính văn bản đó), tự động loại bỏ khoảng trắng thừa (`strip()`) và gom tối đa `max_sentences_per_chunk` câu vào mỗi chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?*  
> Thuật toán thực hiện chia nhỏ đệ quy bằng cách thử từng dấu phân cách theo thứ tự ưu tiên giảm dần `["\n\n", "\n", ". ", " ", ""]`. Trường hợp cơ sở (base case) xảy ra khi độ dài văn bản hiện tại nhỏ hơn hoặc bằng chunk_size (giữ nguyên) hoặc danh sách dấu phân cách đã hết (tự động cắt theo kích thước ký tự cố định). Thuật toán ưu tiên gom các phần nhỏ tách bởi dấu phân cách hiện tại sao cho độ dài không vượt quá chunk_size; nếu một phần vẫn quá lớn, hàm sẽ gọi đệ quy _split với các dấu phân cách cấp thấp hơn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?*  
> Dữ liệu được lưu trữ dạng bộ nhớ trong (in-memory) dưới dạng một danh sách các dictionary (`self._store`), trong đó mỗi bản ghi chứa `id`, `doc_id`, `content`, `metadata` và vector `embedding` được tạo ra qua `self._embedding_fn`. Khi gọi `search`, câu truy vấn được nhúng thành vector `query_emb`, sau đó hàm gọi `compute_similarity` để tính độ tương tự cosine giữa truy vấn và tất cả các chunk lưu trữ, sắp xếp giảm dần theo điểm `score` và lấy ra `top_k` kết quả tốt nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*  
> Hàm `search_with_filter` áp dụng chiến lược **Pre-filtering (lọc trước)**: lọc tập `_store` để giữ lại các bản ghi thỏa mãn chính xác toàn bộ cặp khóa-giá trị trong `metadata_filter` trước, sau đó mới tính độ tương tự vector và xếp hạng trên tập đã lọc. Với `delete_document(doc_id)`, hàm duyệt và giữ lại các bản ghi có `doc_id` khác với mã cần xóa (kiểm tra cả thuộc tính `doc_id` lẫn `metadata['doc_id']`), trả về `True` nếu số lượng phần tử giảm đi và `False` nếu không tìm thấy.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*  
> Triển khai đúng mô hình RAG: đầu tiên gọi `store.search(question, top_k)` để lấy ra các đoạn văn bản liên quan nhất từ kho vector. Sau đó, ngữ cảnh được đưa vào prompt bằng cách nối nội dung của các chunk với ký tự phân cách `\n---\n`, lồng vào cấu trúc prompt dạng: `Context:\n{context}\n\nQuestion: {question}\n\nAnswer:`. Cuối cùng, prompt hoàn chỉnh được truyền vào hàm LLM (`llm_fn`) để tổng hợp câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Admin\Downloads\Work\VinUni\labexercises\DAY07_2A202601501_NguyenDangKyAnh
plugins: anyio-4.14.2
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.13s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (Mock) | Điểm thực tế (Semantic) | Đúng? |
|------|-----------|-----------|---------|--------------|--------------------------|-------|
| 1 | Sinh viên cần mang thẻ sinh viên khi mượn sách tại thư viện. | Người dùng phải xuất trình thẻ định danh hợp lệ để sử dụng dịch vụ mượn sách. | cao | -0.0334 | 0.82 | Sai trên Mock (Đúng về mặt lý thuyết) |
| 2 | Đăng ký học phần được thực hiện trên cổng thông tin học vụ. | Thư viện mở cửa phục vụ từ thứ Hai đến thứ Bảy hàng tuần. | thấp | 0.2296 | 0.15 | Sai trên Mock (Đúng về mặt lý thuyết) |
| 3 | Máy tính học sâu sử dụng mạng thần kinh nhân tạo nhiều lớp. | Lập trình Python là ngôn ngữ phổ biến trong khoa học dữ liệu. | cao | -0.1857 | 0.65 | Sai trên Mock |
| 4 | Học phần tiên quyết phải được hoàn thành trước khi đăng ký môn mới. | Sinh viên phải thỏa mãn điều kiện môn học trước khi đăng ký học phần tiếp theo. | cao | 0.2941 | 0.88 | Đúng ngẫu nhiên trên Mock |
| 5 | Quá trình huấn luyện mô hình yêu cầu bộ dữ liệu gán nhãn chuẩn. | Món phở bò truyền thống thường được ăn kèm với quẩy và hành lá. | thấp | 0.0129 | 0.02 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*  
> Kết quả bất ngờ nhất là ở cặp 1 (hai câu diễn đạt cùng quy định mượn sách) lại nhận điểm số âm trên Mock Embedder (-0.0334), trong khi cặp 2 (hai câu hoàn toàn khác chủ đề) lại có điểm dương cao hơn (0.2296). Điều này minh chứng rằng Mock Embedder chỉ tạo vector xác định dựa trên hash chuỗi phục vụ unit test chứ không học biểu diễn ngữ nghĩa. Embeddings thực sự (như `sentence-transformers` hoặc `OpenAI`) biểu diễn ý nghĩa bằng cách ánh chiếu các khái niệm đồng nghĩa về gần nhau trong không gian vector đa chiều, giúp độ tương tự Cosine phản ánh bản chất ngữ nghĩa thay vì chỉ khớp ký tự bề mặt.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> **Cấu hình chạy:** `EMBEDDING_PROVIDER=local` · `RecursiveChunker(chunk_size=500)` · `BENCHMARK_CHUNKER=recursive python benchmark.py` (Q5 dùng `metadata_filter={"department": "finance"}`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Để đăng ký học phần thành công trên SIS, sinh viên cần thao tác theo những bước nào và trạng thái nào xác nhận đã đăng ký xong? | `vinuni-course-registration-guide`, chunk 0 — vào `Academics → Course Registration`, chọn kỳ, `Add` rồi `Register`, trạng thái phải là `Registered`. | 0,7915 | Có — đúng ở Top-1 | Đúng: nêu đủ các bước và trạng thái `Registered`. |
| 2 | Nếu lớp đã đầy, bị trùng lịch hoặc chưa đạt điều kiện tiên quyết khi đăng ký môn, sinh viên nên làm gì? | `vinuni-course-registration-guide`, chunk 2 — gặp lỗi/lớp đầy/trùng lịch/thiếu tiên quyết thì liên hệ Phòng Quản lý Đào tạo. | 0,7518 | Có — Top-1 nhưng chỉ đúng một phần | Nêu được ý liên hệ Phòng Quản lý Đào tạo, còn thiếu chi tiết SIS không có danh sách chờ. |
| 3 | Sinh viên đại học được mượn tối đa bao nhiêu tài liệu thư viện và trong thời hạn bao lâu? | `vinuni-library-borrowing-privileges`, chunk 0 — tối đa 3 tài liệu, mỗi tài liệu 2 tuần. | 0,7923 | Có — đúng ở Top-1 | Đúng: tối đa 3 tài liệu, mỗi tài liệu 2 tuần. |
| 4 | Thư viện VinUni mở cửa vào giờ nào trong học kỳ, và khu nào mở 24/7? | `vinuni-library-access-services`, chunk 0 — cổng chính T2–T6 8:00–21:00, T7–CN 9:00–17:00; khu học tập 24/7. | 0,7844 | Có — đúng ở Top-1 | Đúng: nêu đủ giờ mở cửa và khu học tập 24/7. |
| 5 | Nếu không hoàn thành học phí đúng hạn từ một tuần, sinh viên sẽ bị hạn chế gì? *(có `metadata_filter={"department": "finance"}`)* | `vinuni-financial-regulation-2023-2024` — điều khoản tạm đình chỉ học và không được đăng ký môn kỳ tiếp theo. | 0,7919 | Có — đúng ở Top-1 nhờ lọc `department=finance` | Đúng: nêu đúng tạm đình chỉ học và hạn chế đăng ký môn kỳ sau. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5** / 5 (đúng Top-1 và câu trả lời đầy đủ: 4/5; Q2 đúng Top-1 nhưng câu trả lời agent còn thiếu chi tiết → tự chấm 9/10 theo thang `docs/SCORING.md`).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*  
> Điều hay nhất tôi học được qua phần demo là việc kết hợp giữa phương pháp chia nhỏ theo ranh giới câu (`SentenceChunker`) với siêu dữ liệu (Metadata Pre-filtering) giúp triệt tiêu hoàn toàn nhiễu thông tin giữa các phòng ban (ví dụ phân biệt rõ giữa Học vụ và Thư viện). Chiến lược này giúp câu trả lời của RAG Agent chính xác, mạch lạc hơn và không bị lẫn lộn giữa các quy định khác nhau trong cùng một trường đại học.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 |
| **Tổng phần cá nhân** | **59 / 60** |
