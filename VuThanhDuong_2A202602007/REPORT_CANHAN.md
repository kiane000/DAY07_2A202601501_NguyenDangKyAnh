# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Vũ Thành Dương
**Nhóm:** A7
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Độ tương tự cosine cao nghĩa là 2 vector có hướng rất giống nhau. Trong AI nghĩa là hai đoạn văn hoặc tài liệu có ý nghĩa giống nhau

**Ví dụ có độ tương tự CAO:**

- Câu A: Cách nấu cơm
- Câu B: Làm sao để gạo biến thành cơm
- Tại sao tương đồng: Ở đây ý nghĩa 2 câu đều muốn hỏi về cách thức để nấu cơm

**Ví dụ có độ tương tự THẤP:**

- Câu A: Cách nấu cơm
- Câu B: Cách ăn phở
- Tại sao khác: 2 câu có ý nghĩa khác nhau 1 câu là cách nấu cơm, 1 câu là cách ăn phở

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Vì cosine similarity chỉ quan tâm hướng, còn euclidean distance quan tâm tới cả hướng và độ dài, trong khi độ dài không phản ánh ngữ nghĩa của câu nói

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> *Trình bày phép tính: 500, 950, 1400, ... 10000. Cách tính: ()10000 - 500)/450  + 1*
> *Đáp án: 23*

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Số lượng chuncks sẽ tăng lên 25. Độ chồng chéo nhiều hơn để giúp giữ ngữ cảnh câu nói, và để tăng khả năng tìm kiếm document.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Dùng regex `.+?(?:[.!?](?=\s)|[.!?]$)|.+$` để tách văn bản theo dấu kết thúc câu như `.`, `!`, `?`, đồng thời vẫn giữ lại phần câu cuối nếu không có dấu câu rõ ràng. Sau khi tách, loại bỏ khoảng trắng thừa và gom các câu theo `max_sentences_per_chunk`. Với chuỗi rỗng, hàm trả về danh sách rỗng để tránh tạo chunk không có nội dung.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Chia văn bản theo danh sách separator ưu tiên từ lớn đến nhỏ: đoạn văn, dòng, câu, từ, rồi cuối cùng là cắt theo ký tự. Hàm `_split` cố gắng gom các phần nhỏ vào một chunk miễn là không vượt `chunk_size`; nếu một phần vẫn quá dài thì tiếp tục đệ quy với separator tiếp theo. Base case là khi văn bản đã ngắn hơn hoặc bằng `chunk_size`, hoặc khi không còn separator phù hợp thì cắt trực tiếp theo kích thước cố định.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Trong `add_documents`, chuyển mỗi `Document` thành một record gồm `id`, `content`, `metadata`, embedding và thứ tự thêm vào store. Nếu có ChromaDB thì lưu vào collection, còn nếu không có thì dùng danh sách `_store` trong bộ nhớ. Khi `search`, tạo embedding cho query, tính điểm tương tự bằng dot product giữa query embedding và embedding của từng record, sau đó lấy top-k kết quả có điểm cao nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> Với `search_with_filter`, lọc metadata trước để chỉ giữ lại các record thỏa điều kiện, rồi mới tính similarity trên tập đã lọc. Nếu không truyền filter thì hàm tìm kiếm trên toàn bộ dữ liệu giống `search`. Với `delete_document`, tôi xóa tất cả record có `metadata["doc_id"]` trùng với `doc_id` cần xóa và trả về `True` nếu số lượng record giảm.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Trong `answer`, truy xuất top-k chunk liên quan bằng `store.search(question, top_k)`, sau đó nối nội dung các chunk thành phần `Context` trong prompt. Prompt yêu cầu mô hình trả lời chỉ dựa trên ngữ cảnh được cung cấp, rồi đặt câu hỏi ở cuối để LLM sinh câu trả lời. Cuối cùng, gọi `llm_fn(prompt)` để tách phần truy xuất dữ liệu khỏi phần sinh ngôn ngữ.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# D:\DAY07_2A202602007_VuThanhDuong>python -m pytest tests -v

==================================================== test session starts =====================================================

platform win32 -- Python 3.14.4, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\duong\AppData\Local\Python\pythoncore-3.14-64\python.exe

cachedir: .pytest_cache

rootdir: D:\DAY07_2A202602007_VuThanhDuong

plugins: anyio-4.13.0

collected 42 items                                                                                                          



tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                   [  2%]

tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                            [  4%]

tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                     [  7%]

tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                      [  9%]

tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                           [ 11%]

tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                           [ 14%]

tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                 [ 16%]

tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                  [ 19%]

tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                [ 21%]

tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                  [ 23%]

tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                  [ 26%]

tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                             [ 28%]

tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                         [ 30%]

tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                   [ 33%]

tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                          [ 35%]

tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                              [ 38%]

tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                        [ 40%]

tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                              [ 42%]

tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                  [ 45%]

tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                    [ 47%]

tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                      [ 50%]

tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                            [ 52%]

tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                 [ 54%]

tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                   [ 57%]

tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                       [ 59%]

tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                    [ 61%]

tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                             [ 64%]

tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                            [ 66%]

tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                       [ 69%]

tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                   [ 71%]

tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                              [ 73%]

tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                  [ 76%]

tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                        [ 78%]

tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                  [ 80%]

tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED               [ 83%]

tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                             [ 85%]

tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                            [ 88%]

tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                [ 90%]

tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                           [ 92%]

tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                    [ 95%]

tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED          [ 97%]

tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED              [100%]



===================================================== 42 passed in 0.23s =====================================================



D:\DAY07_2A202602007_VuThanhDuong>
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán  | Điểm thực tế | Đúng? |
| ---- | ------ | ------ | ----------- | ---------------- | ------- |
| 1    | Sinh viên đăng ký học phần trong cổng học vụ. | Người học chọn môn trên hệ thống học vụ. | cao | 0.055 | Sai |
| 2    | Thư viện cung cấp mượn tài liệu. | Người dùng có thể mượn sách tại thư viện. | cao | 0.153 | Sai |
| 3    | Sinh viên gặp lỗi trùng lịch khi đăng ký. | Người dùng cần mang thẻ định danh khi mượn tài liệu. | thấp | 0.021 | Đúng |
| 4    | Học phần có thể yêu cầu học phần tiên quyết. | Trước khi đăng ký cần kiểm tra điều kiện môn học. | cao | -0.054 | Sai |
| 5    | Thư viện có không gian học tập. | Yêu cầu ngoại lệ gửi qua kênh hỗ trợ học vụ. | thấp | 0.014 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Kết quả bất ngờ nhất là các cặp có ý nghĩa gần nhau như "đăng ký học phần" và "chọn môn" lại có điểm thấp khi dùng `_mock_embed`. Điều này cho thấy mock embeddings trong bài lab chủ yếu dùng để kiểm thử luồng chương trình, không phản ánh tốt quan hệ ngữ nghĩa thật giữa các câu. Nếu muốn đánh giá semantic similarity chính xác hơn, cần dùng embedding model thật như local sentence-transformers hoặc OpenAI embeddings.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| - | ----------------- | ------------------------------------------ | ------------ | --------------------------------- | ------------------------------------- |
| 1 | Sinh vien dang ky hoc phan o dau? | Top-1 là `Dịch vụ thư viện` score 0.034; chunk liên quan `Đăng ký học phần` xuất hiện ở Top-2/Top-3. | 0.034 | Có trong top-3 | Agent demo chỉ in preview prompt, chưa sinh câu trả lời thật. |
| 2 | Can kiem tra gi truoc khi xac nhan dang ky hoc phan? | Top-1 là `Đăng ký học phần` score 0.214, có nội dung về điều kiện trước khi xác nhận đăng ký. | 0.214 | Có | Agent demo chỉ in preview prompt, chưa sinh câu trả lời thật. |
| 3 | Khi bi trung lich hoc phan thi sinh vien lam gi? | Top-1 là `Đăng ký học phần` score 0.167, có nội dung sinh viên điều chỉnh lớp học phần trước thời hạn công bố. | 0.167 | Có | Agent demo chỉ in preview prompt, chưa sinh câu trả lời thật. |
| 4 | Ai co the su dung dich vu thu vien? | Top-1 là `Đăng ký học phần` score 0.081; chunk liên quan `Dịch vụ thư viện` xuất hiện ở Top-3. | 0.081 | Có trong top-3 | Agent demo chỉ in preview prompt, chưa sinh câu trả lời thật. |
| 5 | Khi muon tai lieu o thu vien can mang gi? | Top-1 là `Đăng ký học phần` score 0.002; chunk liên quan `Dịch vụ thư viện` xuất hiện ở Top-2. | 0.002 | Có trong top-3 | Agent demo chỉ in preview prompt, chưa sinh câu trả lời thật. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Khi dùng `_mock_embed`, kết quả truy xuất chưa phản ánh đúng ngữ nghĩa: một số câu hỏi về thư viện lại trả về chunk đăng ký học phần. Điều này cho thấy mock embeddings phù hợp để kiểm thử pipeline nhưng không phù hợp để đánh giá chất lượng truy xuất thật. Để cải thiện, nên dùng embedding model thật và có thể lọc metadata theo `department` khi câu hỏi thuộc một phạm vi rõ như thư viện hoặc học vụ.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                               | 5 / 5                    |
| Hướng tiếp cận của tôi (My Approach)           | 10 / 10                   |
| Hoàn thiện code (Core Implementation — tests)     | 30 / 30                   |
| Dự đoán độ tương tự (Similarity Predictions) | 2 / 5                    |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10                   |
| **Tổng phần cá nhân**                      | **57 / 60**         |
