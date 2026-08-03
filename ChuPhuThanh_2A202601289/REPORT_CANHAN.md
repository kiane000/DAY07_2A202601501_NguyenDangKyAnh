# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Chu Phú Thành
**Nhóm:** Nhóm K3 — Dịch vụ và quy định đại học
**Ngày:** 3/8/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần nhau. Với văn bản, điều này thường cho thấy hai câu có nội dung hoặc ý nghĩa tương tự.

**Ví dụ có độ tương tự CAO:**

- Câu A: Sinh viên có thể mượn sách tại thư viện.
- Câu B: Thư viện cho phép người học mượn tài liệu.
- Tại sao tương đồng: Cả hai câu đều nói về dịch vụ mượn tài liệu của thư viện dành cho người học.

**Ví dụ có độ tương tự THẤP:**

- Câu A: Sinh viên đăng ký học phần trên cổng học vụ.
- Câu B: Trận bóng đá diễn ra vào cuối tuần.
- Tại sao khác: Hai câu nói về hai chủ đề không liên quan: thủ tục học vụ và hoạt động thể thao.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine similarity tập trung so sánh hướng của hai vector, nên phù hợp để đo mức độ giống nhau về ý nghĩa giữa các văn bản. Khoảng cách Euclid chịu ảnh hưởng mạnh hơn bởi độ lớn vector, trong khi độ lớn này thường không quan trọng bằng hướng đối với text embedding.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> *Trình bày phép tính:
> Số chunk = làm tròn lên((10000 - 50) / (500 - 50))
> = làm tròn lên(9950 / 450)
> = làm tròn lên(22,11)*
> *Đáp án: 23 chunks.*

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Số chunk = làm tròn lên((10000 - 100) / (500 - 100)) = làm tròn lên(9900 / 400) = 25 chunks. Overlap lớn hơn giúp giữ lại ngữ cảnh ở ranh giới giữa hai chunk, nhưng đổi lại số chunk, chi phí lưu trữ và chi phí tìm kiếm đều tăng.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Tôi kiểm tra văn bản rỗng trước để trả về danh sách rỗng. Sau đó dùng biểu thức chính quy `r"(?<=[.!?])\s+"` để tách sau dấu kết thúc câu, loại bỏ khoảng trắng thừa và gom tối đa `max_sentences_per_chunk` câu thành một chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Hàm `chunk` xử lý trường hợp text rỗng rồi gọi `_split`. Hàm `_split` ưu tiên tách theo đoạn, xuống dòng, kết thúc câu và khoảng trắng; nếu phần văn bản vẫn quá dài thì gọi đệ quy với separator tiếp theo, cuối cùng cắt cứng theo `chunk_size`. Trường hợp cơ sở là text rỗng hoặc text đã ngắn hơn kích thước chunk.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Tôi dùng store trong bộ nhớ, trong đó mỗi record gồm `id`, `content`, `metadata` và `embedding`. Khi thêm document, hệ thống gọi embedding function để tạo vector. Khi tìm kiếm, hệ thống embed câu hỏi, tính dot product với embedding của từng record, sắp xếp điểm giảm dần và lấy tối đa `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> Với `search_with_filter`, tôi lọc metadata trước rồi mới tính điểm tương tự trên các record còn lại. Với `delete_document`, tôi loại bỏ tất cả record có `metadata["doc_id"]` trùng với ID cần xóa và trả về `True` nếu có ít nhất một record bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Tác tử gọi `store.search(question, top_k)` để lấy các chunk liên quan nhất. Tôi ghép nội dung các chunk này thành phần context, sau đó tạo prompt gồm hướng dẫn, context và câu hỏi. Cuối cùng, agent gọi `llm_fn(prompt)` và trả về chuỗi câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
== 42 passed in 0.15s ==
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A                                                       | Câu B                                                                        | Dự đoán | Điểm thực tế | Đúng? |
| ---- | ------------------------------------------------------------ | ----------------------------------------------------------------------------- | ---------- | ---------------- | ------- |
| 1    | Sinh viên có thể mượn sách tại thư viện.            | Thư viện cho phép người học mượn tài liệu.                          | cao        | -0.0985          | Không  |
| 2    | Học phí được thanh toán theo thời hạn của học kỳ. | Sinh viên cần đóng tiền đúng hạn trong học kỳ.                      | cao        | 0.0221           | Không  |
| 3    | Sinh viên đăng ký học phần trên cổng học vụ.       | Thư viện cung cấp không gian học tập yên tĩnh.                        | thấp      | -0.0734          | Có     |
| 4    | Ký túc xá dành cho sinh viên ở xa.                     | Trận bóng đá diễn ra vào cuối tuần.                                   | thấp      | -0.0180          | Có     |
| 5    | Học bổng hỗ trợ sinh viên có thành tích tốt.        | Sinh viên đạt kết quả học tập cao có thể nhận hỗ trợ tài chính. | cao        | -0.0996          | Không  |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Các cặp 1, 2 và 5 có ý nghĩa gần nhau nhưng điểm của mock embedder lại thấp hoặc gần 0. Điều này cho thấy mock embedding được dùng để kiểm thử kỹ thuật, không biểu diễn ngữ nghĩa tốt. Khi đánh giá retrieval thực tế, cần dùng local multilingual embedder hoặc embedding model thật thay vì mock embedder.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| - | ----------------- | ------------------------------------------ | ------------ | --------------------------------- | ------------------------------------- |
| 1 | Để đăng ký học phần thành công trên SIS, sinh viên cần thao tác theo những bước nào và trạng thái nào xác nhận đã đăng ký xong? | Hướng dẫn SIS: đăng nhập, vào `Academics → Course Registration`, chọn kỳ khi đăng ký mở, chọn môn rồi `Add` và `Register`. | 0.7906 | Có — đúng ở Top-1. | Hoàn tất khi trạng thái môn là **Registered**; `Selected` chưa phải đăng ký thành công. |
| 2 | Nếu lớp đã đầy, bị trùng lịch hoặc chưa đạt điều kiện tiên quyết khi đăng ký môn, sinh viên nên làm gì? | Top-1 nói về việc đổi lớp khi một lớp bị hủy; chunk hướng dẫn đúng xuất hiện ở Top-2. | 0.7535 | Có — tài liệu hướng dẫn SIS ở Top-2. | Kiểm tra điều kiện tiên quyết và lịch; khi lớp đầy, trùng lịch hoặc có lỗi cần liên hệ Phòng Quản lý Đào tạo. SIS không có danh sách chờ. |
| 3 | Sinh viên đại học được mượn tối đa bao nhiêu tài liệu thư viện và trong thời hạn bao lâu? | Quyền mượn của sinh viên đại học: tối đa 3 tài liệu, mỗi tài liệu 2 tuần. | 0.7847 | Có — đúng ở Top-1. | Sinh viên đại học được mượn tối đa **3 tài liệu** trong **2 tuần/tài liệu**. |
| 4 | Thư viện VinUni mở cửa vào giờ nào trong học kỳ, và khu nào mở 24/7? | Giờ cổng chính T2–T6 là 8:00–21:00, T7–CN là 9:00–17:00; khu học tập 24/7 luôn mở. | 0.7641 | Có — đúng ở Top-1. | Cổng chính mở theo giờ nêu trên; khu học tập **24/7** mở liên tục. |
| 5 | Nếu không hoàn thành học phí đúng hạn từ một tuần, sinh viên sẽ bị hạn chế gì? | Top-1 thuộc tài liệu tài chính nhưng là chunk về điều kiện/chính sách khác, không chứa hạn chế đăng ký môn. | 0.8140 | Không — Top-3 của SentenceChunker chưa có chunk chứa điều khoản đúng. | Chưa thể trả lời đáng tin cậy từ Top-3; RecursiveChunker kết hợp filter `department=finance` truy xuất được đúng điều khoản. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **4 / 5**

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> SentenceChunker với tối đa ba câu mỗi chunk cho kết quả tốt với các tài liệu hướng dẫn ngắn, vì một quy trình hoặc một quy định thường được giữ trọn trong cùng chunk. Metadata pre-filtering giúp loại bớt nhiễu giữa các phòng ban: với câu hỏi giờ mở cửa, lọc `department=library` giữ lại các chunk thư viện thay vì cả các quy định học vụ và tài chính. Câu hỏi học phí cho thấy cần bổ sung metadata cho tài liệu PDF và thử chunk nhỏ hơn theo tiêu đề/mục để tránh chunk quá rộng.


---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                               | 5 / 5                 |
| Hướng tiếp cận của tôi (My Approach)           | 10 / 10                |
| Hoàn thiện code (Core Implementation — tests)     | 30 / 30                |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5                  |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10                   |
| **Tổng phần cá nhân**                      | **58 / 60**         |
