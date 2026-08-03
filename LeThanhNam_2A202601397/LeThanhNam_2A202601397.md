# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Thành Nam (MSSV 2A202601397)
**Nhóm:** A7
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding gần như cùng *hướng* trong không gian nhiều chiều, nghĩa là hai đoạn văn bản nói về cùng chủ đề / cùng ý, bất kể chúng dài ngắn hay dùng từ khác nhau. Cosine chỉ quan tâm hướng, không quan tâm độ lớn của vector.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sinh viên đăng ký học phần trên cổng thông tin học vụ."
- Câu B: "Việc đăng ký môn học được thực hiện qua hệ thống trực tuyến của trường."
- Tại sao tương đồng: cùng một hành động (đăng ký môn học) và cùng một phương tiện (cổng/hệ thống trực tuyến); chỉ khác cách diễn đạt, nên embedding rơi vào cùng vùng ngữ nghĩa.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Học bổng khuyến khích học tập được xét theo điểm trung bình học kỳ."
- Câu B: "Ký túc xá bố trí sáu sinh viên mỗi phòng."
- Tại sao khác: hai dịch vụ khác nhau (học bổng vs. chỗ ở), không chia sẻ chủ thể, hành động hay tiêu chí nào — chỉ trùng bối cảnh "trường đại học" nên điểm thấp.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Độ dài (magnitude) của vector embedding phần lớn phản ánh độ dài / tần suất từ của văn bản, còn *ý nghĩa* nằm ở hướng. Khoảng cách Euclid trộn cả hai yếu tố nên một tài liệu dài sẽ bị coi là "xa" câu truy vấn ngắn dù cùng chủ đề; cosine chuẩn hóa độ lớn đi nên chỉ so sánh ngữ nghĩa. Ngoài ra khi vector đã được chuẩn hóa (như trong `MockEmbedder` và `LocalEmbedder` của lab này) thì `||a-b||² = 2 - 2·cos(a,b)`, tức hai thước đo xếp hạng giống nhau, và cosine rút gọn thành tích vô hướng nên tính nhanh hơn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: bước nhảy (step) = 500 − 50 = 450 ký tự → `ceil((10000 − 50) / (500 − 50)) = ceil(9950 / 450) = ceil(22.11)`
> **Đáp án: 23 chunks.** (Chạy `FixedSizeChunker(chunk_size=500, overlap=50).chunk("a"*10000)` cho đúng 23 chunk — code khớp công thức.)

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> `ceil((10000 − 100) / (500 − 100)) = ceil(24.75) = 25 chunks`, tăng 2 chunk (~+9% chi phí embedding và lưu trữ). Tăng overlap để một câu/một quy định bị cắt ngang ranh giới chunk vẫn còn nguyên vẹn trong ít nhất một chunk — tránh mất ngữ cảnh kiểu "thời hạn là ngày 30/9" bị tách khỏi "đóng học phí học kỳ 1".

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi tách câu bằng regex `(?<=[.!?])\s+`: dùng *lookbehind* nên dấu kết câu được giữ lại trong câu đứng trước, và `\s+` bao trọn cả `". "`, `"! "`, `"? "` lẫn `".\n"` chỉ bằng một biểu thức. Tôi tách phần này ra hàm `split_sentences()` để `ChunkingStrategyComparator` dùng lại được. Edge case đã xử lý: text rỗng hoặc chỉ có khoảng trắng → trả `[]`; các câu rỗng sinh ra do nhiều khoảng trắng liền nhau bị lọc bỏ; mỗi câu được `strip()`; `max_sentences_per_chunk` bị ép tối thiểu là 1 (trong `__init__`) để không chia cho 0. Sau đó nhóm câu theo lô `max_sentences_per_chunk` và nối bằng một dấu cách.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `_split` đi từ dấu phân cách thô đến mịn (`"\n\n" → "\n" → ". " → " " → ""`). Base case: đoạn hiện tại đã `<= chunk_size` thì trả về nguyên đoạn; hết separator (hoặc separator là `""`) thì cắt cứng theo `chunk_size`. Nếu separator hiện tại không xuất hiện trong đoạn (`split` trả về 1 phần tử) thì gọi đệ quy với separator kế tiếp thay vì cắt sớm. Trường hợp còn lại: tôi *gộp tham lam* các mảnh vào một buffer cho tới sát `chunk_size` rồi mới xả buffer — nhờ vậy các đoạn/câu ngắn được ghép lại thành chunk đủ dày, còn mảnh nào tự nó vẫn quá to thì đệ quy tiếp với separator mịn hơn. Khi gộp tôi nối lại đúng separator ban đầu để chunk không bị mất định dạng.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `_make_record()` chuẩn hóa mỗi `Document` thành một record: `key` (khóa nội bộ duy nhất `id#index`, vì test có thêm hai lần cùng `doc_id`), `id`, `content`, `metadata` (luôn `setdefault("doc_id", doc.id)` để lọc/xóa hoạt động cả khi tài liệu không có metadata), `embedding` (nhúng **một lần** lúc thêm vào, không nhúng lại khi search) và `index` để phá thế bằng điểm. `add_documents` chỉ việc tạo record rồi `extend` vào `self._store`. `search` nhúng câu truy vấn rồi gọi `_search_records`, tính **tích vô hướng** với từng embedding đã lưu; vì cả `MockEmbedder` và `LocalEmbedder` đều trả vector đơn vị nên tích vô hướng chính là cosine — rẻ hơn mà xếp hạng không đổi. Kết quả sort giảm dần theo `score` (sort của Python là *stable* nên thứ tự thêm vào giữ nguyên khi bằng điểm) và cắt `top_k`.
>
> Về ChromaDB: `__init__` tạo `EphemeralClient` khi import được `chromadb`, nhưng tôi cố tình để **danh sách trong bộ nhớ là nguồn dữ liệu chính** và Chroma chỉ là bản sao (mirror) trong `add_documents`/`delete_document`, bọc trong `try/except`. Lý do: hành vi của store phải giống nhau ở mọi máy — có hay không có `chromadb` cài đặt — và không bị dữ liệu cũ của lần chạy trước lẫn vào.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc **trước** rồi mới xếp hạng (pre-filter). Tôi giữ những chunk mà *mọi* cặp key/value trong `metadata_filter` đều khớp, sau đó gọi lại chính `_search_records` trên tập ứng viên đó. Pre-filter đúng hơn post-filter vì nếu lọc sau, `top_k` đã bị các chunk sai `audience` chiếm chỗ và có thể trả về ít hơn `top_k` kết quả hợp lệ. Khi `metadata_filter` rỗng/`None` thì hàm gọi thẳng `search()` nên số lượng kết quả bằng đúng search không lọc. `delete_document` chia store thành `kept` / `removed` theo `metadata["doc_id"]` (nhờ `setdefault` ở trên, so sánh này bắt được cả tài liệu nguyên bản lẫn mọi chunk `doc::chunk_i` do `ingest.py` sinh ra), trả `False` nếu không xóa được gì, ngược lại gán lại `self._store` và xóa theo `key` bên Chroma.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Đúng ba bước RAG: `store.search(question, top_k)` → `_build_prompt()` → `llm_fn(prompt)`, và luôn `str()` kết quả để đảm bảo trả về chuỗi. Prompt gồm ba khối rõ ràng: chỉ dẫn hệ thống (chỉ được dùng ngữ cảnh, trích dẫn `[n]`, nói rõ khi không tìm thấy — chống *hallucination*), khối `NGỮ CẢNH` đánh số `[1] [2] [3]` kèm nguồn (`source_url` → `source` → `doc_id`) và điểm số để câu trả lời có thể truy vết, rồi tới `CÂU HỎI`. Tôi tách `_build_prompt` khỏi `answer` để dễ in prompt ra kiểm tra khi phân tích lỗi truy xuất. Trường hợp store rỗng: ngữ cảnh ghi rõ "(không truy xuất được tài liệu liên quan)" thay vì gửi prompt trống cho LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ python -m pytest tests/ -v
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Lab AI in action\DAY07_2A202601397_LeThanhNam
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

============================= 42 passed in 0.12s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

Ngoài `pytest`, tôi cũng kiểm tra pipeline end-to-end: `python ingest.py` (self-check parser front matter) và `python main.py "<câu hỏi>"` chạy trọn đường `nạp dữ liệu → search → KnowledgeBaseAgent`.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Chạy với embedder thật (`EMBEDDING_PROVIDER=local` → `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`),
tính điểm từng cặp bằng `compute_similarity(embedder(cau_a), embedder(cau_b))`.
Dự đoán được ghi **trước** khi chạy.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên đăng ký học phần trên cổng thông tin học vụ. | Việc đăng ký môn học được thực hiện qua hệ thống trực tuyến của trường. | cao | **0.631** | Đúng |
| 2 | Thời hạn đóng học phí học kỳ 1 là ngày 30/9. | Học phí kỳ một phải hoàn tất trước 30 tháng 9. | cao | **0.720** | Đúng |
| 3 | Thư viện mở cửa từ 7h30 đến 21h các ngày trong tuần. | Sinh viên được gia hạn sách mượn tối đa hai lần. | trung bình | **0.291** | Thấp hơn dự đoán |
| 4 | Học bổng khuyến khích học tập được xét theo điểm trung bình học kỳ. | Ký túc xá bố trí sáu sinh viên mỗi phòng. | thấp | **0.323** | Cao hơn cặp 3 (ngoài dự đoán) |
| 5 | Sinh viên **được phép** rút học phần sau tuần thứ ba. | Sinh viên **không được phép** rút học phần sau tuần thứ ba. | thấp (nghĩa trái ngược) | **0.767** | Sai hoàn toàn — cao nhất bảng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 5: hai câu **trái nghĩa nhau** lại đạt điểm cao nhất (0.767), cao hơn cả hai cặp diễn giải cùng ý (0.631 và 0.720). Chỉ một chữ "không" làm đảo ngược quy định nhưng gần như không làm lệch vector — embedding nắm *chủ đề và từ vựng*, không nắm *giá trị chân lý* hay phủ định. Hệ quả thực tế cho RAG: retrieval sẽ vui vẻ đưa lên top-1 một chunk nói ngược hẳn quy định, nên phần sinh câu trả lời buộc phải đọc lại nguyên văn chunk và trích dẫn nguồn — không được suy luận từ điểm số. Bất ngờ thứ hai là cặp 4 (0.323, khác chủ đề hoàn toàn) lại cao hơn cặp 3 (0.291, cùng chủ đề thư viện): mô hình bị hút bởi từ chung "sinh viên/học kỳ" hơn là bởi việc hai câu cùng thuộc miền thư viện — tức là "cùng chủ đề" theo cảm nhận của người đọc không đảm bảo điểm cosine cao.
>
> **Đối chứng mock vs local (cùng 5 cặp, cùng code):** với `EMBEDDING_PROVIDER=mock`, cặp 2 (hai câu gần như đồng nghĩa) nhận **−0.101** còn cặp 1 chỉ **0.163**. Mock băm MD5 nên điểm gần như ngẫu nhiên — nó chỉ hợp cho unit test, mọi kết luận về ngữ nghĩa đều phải chạy trên `local`.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> **Cấu hình chạy:** `EMBEDDING_PROVIDER=local` · `data/data_vinuni` (bộ dữ liệu nhóm, 9 tài liệu, 264 chunk) · `FixedSizeChunker(chunk_size=500, overlap=50)` qua `build_knowledge_base()` · `KnowledgeBaseAgent` + `demo_llm` (LLM giả lập).
> Lệnh: `PYTHONIOENCODING=utf-8 BENCHMARK_CHUNKER=fixed python benchmark.py` cho 5 câu hỏi đánh giá chuẩn của nhóm.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Để đăng ký học phần thành công trên SIS, sinh viên cần thao tác theo những bước nào và trạng thái nào xác nhận đã đăng ký xong? | `vinuni-course-registration-guide::chunk_0` — "Vào mục Academics -> Course Registration... chọn môn rồi Add và Register..." | 0.7792 | Có — đúng ở Top-1 | Vào `Academics → Course Registration`, chọn kỳ, nhấn `Add` rồi `Register`. Trạng thái phải là `Registered` mới thành công. |
| 2 | Nếu lớp đã đầy, bị trùng lịch hoặc chưa đạt điều kiện tiên quyết khi đăng ký môn, sinh viên nên làm gì? | `vinuni-summer-2026-student-portal-registration::chunk_1` — giải thích ý nghĩa trạng thái Available, Full, Conflict | 0.7812 | Có — một phần ở Top-1, chunk hướng dẫn SIS nằm ở Top-3 (0.7550) | Kiểm tra điều kiện/lịch; khi gặp sự cố trùng lịch hoặc thiếu tiên quyết cần đổi lớp hoặc liên hệ Phòng Quản lý Đào tạo. |
| 3 | Sinh viên đại học được mượn tối đa bao nhiêu tài liệu thư viện và trong thời hạn bao lâu? | `vinuni-library-borrowing-privileges::chunk_0` — "Sinh viên đại học được mượn tối đa 3 tài liệu, mỗi tài liệu trong thời hạn 2 tuần." | 0.7963 | Có — đúng ở Top-1 | Tối đa 3 tài liệu, mỗi tài liệu 2 tuần. |
| 4 | Thư viện VinUni mở cửa vào giờ nào trong học kỳ, và khu nào mở 24/7? | `vinuni-library-access-services::chunk_0` — "Cổng chính T2–T6 8:00–21:00, T7–CN 9:00–17:00. Khu học tập 24/7 mở cửa liên tục." | 0.8036 | Có — đúng ở Top-1 | Cổng chính T2–T6 8:00–21:00, T7–CN 9:00–17:00; khu học tập 24/7 mở liên tục. |
| 5 | Nếu không hoàn thành học phí đúng hạn từ một tuần, sinh viên sẽ bị hạn chế gì? *(có `metadata_filter={"department": "finance"}`)* | `vinuni-financial-regulation-2023-2024::chunk_29` — chunk chứa nội dung đặt cọc/hoàn trả, vỡ điều khoản nộp chậm | 0.8132 | Không — Top-3 chưa lấy được chunk chứa điều khoản phạt/tạm đình chỉ | Chưa thể trả lời chính xác từ Top-3 do FixedSize 500 cắt vỡ ngữ cảnh điều khoản. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **4 / 5** (đúng Top-1: 3/5, có ở Top-3: 4/5 → tự chấm 7/10 theo thang `docs/SCORING.md`, khớp với bảng so sánh trong `REPORT_NHOM.md`).

**Nhận xét về lỗi truy xuất tôi quan sát được (để mang sang phần nhóm 3.5):**
> 1. `FixedSizeChunker(500, 50)` hoạt động tốt với các tài liệu hướng dẫn ngắn (Q1, Q3, Q4 đều đạt Top-1 với điểm cosine > 0.77).
> 2. Tuy nhiên với tài liệu dài như Quy định tài chính (150 chunk), kích thước cố định 500 ký tự cắt vỡ ranh giới các điều khoản, làm vỡ điều khoản quy định thanh toán chậm ở Q5 khiến câu hỏi không truy xuất được chunk đúng trong Top-3 dù đã lọc `department=finance`.
> 3. Ở Q2, FixedSizeChunker nhồi ngữ cảnh trạng thái trên Student Portal vào Top-1 (0.7812), đẩy chunk hướng dẫn đăng ký trên SIS xuống Top-3 (0.7550). Chuyển sang `RecursiveChunker` như chiến lược của nhóm sẽ khắc phục được nhược điểm này.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua so sánh chiến lược giữa các thành viên, việc kết hợp `RecursiveChunker(500)` với `metadata_filter` (như `department=finance` ở Q5) giúp giữ đúng cấu trúc các điều khoản pháp lý/quy chế dài, khắc phục triệt để lỗi cắt vỡ câu của `FixedSizeChunker`. Metadata filter loại bỏ nhiễu giữa các khối phòng ban cực kỳ hiệu quả.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 (42/42 test pass) |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 7 / 10 |
| **Tổng phần cá nhân** | **57 / 60** |



