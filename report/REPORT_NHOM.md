# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** A7
**Thành viên:** Nguyễn Đặng Kỳ Anh, Chu Phú Thành, Lê Thành Nam, Vũ Thành Dương, Phạm Thế Trung
**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K3):** Dịch vụ / quy định đại học (đăng ký môn, học phí, học bổng, thư viện, ký túc xá…).

**Phạm vi cụ thể nhóm tập trung:**

> Hướng dẫn và quy định dành cho sinh viên VinUni: đăng ký học phần, dịch vụ thư viện, học phí và quy chế học vụ.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu                                              | Nguồn (Source URL)          | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán                                                                                 |
| - | ------------------------------------------------------------ | ---------------------------- | ------------------------ | ----------- | -------------------------------------------------------------------------------------------------- |
| 1 | Quy định tài chính năm học 2023–2024                  | vinuni.edu.vn (PDF)          | 03/08/2026 · 2023–2024 | 29.974      | `doc_id`, `audience`, `department`, `topic`, `language`, nguồn, ngày lấy, phiên bản |
| 2 | Quy chế đào tạo đại học hệ chính quy theo tín chỉ | Tài liệu được cung cấp | 03/08/2026 · 2024-05-21 | 77.041      | `doc_id`, `audience`, `department`, `topic`, `language`, nguồn, ngày lấy, phiên bản |
| 3 | Hướng dẫn đăng ký học phần trên SIS                 | registrar.vinuni.edu.vn      | 03/08/2026 · 2026       | 1.381       | `doc_id`, `audience`, `department`, `topic`, `language`, nguồn, ngày lấy, phiên bản |
| 4 | Thông báo đăng ký học phần Summer 2026                | registrar.vinuni.edu.vn      | 03/08/2026 · 2026-05-22 | 1.666       | `doc_id`, `audience`, `department`, `topic`, `language`, nguồn, ngày lấy, phiên bản |
| 5 | Đăng ký Summer 2026 trên Student Portal                  | registrar.vinuni.edu.vn      | 03/08/2026 · 2026-06-29 | 1.566       | `doc_id`, `audience`, `department`, `topic`, `language`, nguồn, ngày lấy, phiên bản |
| 6 | Quy định học vụ về đăng ký học phần                | policy.vinuni.edu.vn         | 03/08/2026 · 2024       | 1.025       | `doc_id`, `audience`, `department`, `topic`, `language`, nguồn, ngày lấy, phiên bản |
| 7 | Chính sách truy cập và dịch vụ thư viện              | policy.vinuni.edu.vn         | 03/08/2026 · 2025       | 1.334       | `doc_id`, `audience`, `department`, `topic`, `language`, nguồn, ngày lấy, phiên bản |
| 8 | Quyền mượn tài liệu thư viện                          | library.vinuni.edu.vn        | 03/08/2026 · 2026       | 903         | `doc_id`, `audience`, `department`, `topic`, `language`, nguồn, ngày lấy, phiên bản |
| 9 | Tuyển sinh Chương trình AI Thực chiến                  | vinuni.edu.vn                | 03/08/2026 · 2026-01-29 | 2.602       | `doc_id`, `audience`, `department`, `topic`, `language`, nguồn, ngày lấy, phiên bản |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [X] Tập tài liệu chỉ dùng nguồn công khai/tài liệu được phép dùng; không có thông tin đăng nhập hay dữ liệu cá nhân.
- [X] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` trong YAML front matter và có đối chiếu trong `data/data_vinuni/sources.csv`.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata                       | Kiểu         | Ví dụ giá trị                    | Tại sao hữu ích cho truy xuất (retrieval)?                |
| --------------------------------------- | ------------- | ------------------------------------ | ------------------------------------------------------------- |
| `doc_id`                              | string        | `vinuni-course-registration-guide` | Nhận diện tài liệu và truy vết chunk về đúng nguồn. |
| `department`                          | string        | `registrar`, `library`           | Lọc nhiễu theo đơn vị phụ trách.                       |
| `topic`                               | string        | `course_registration`              | Thu hẹp truy vấn vào chủ đề.                            |
| `audience`                            | string        | `student`, `all`                 | Phân biệt đối tượng áp dụng quy định.               |
| `language`                            | string        | `vi`                               | Hỗ trợ bộ lọc/ngôn ngữ truy vấn.                       |
| `source_url`                          | string        | URL trang nguồn                     | Cho phép kiểm chứng thông tin.                            |
| `retrieved_at` / `document_version` | date / string | `2026-08-03` / `2026`            | Đánh giá độ mới của quy định.                        |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu                  | Chiến lược (Strategy)           | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không?                                    |
| --------------------------- | ---------------------------------- | ----------------- | --------------------- | ------------------------------------------------------------------ |
| Hướng dẫn đăng ký SIS | FixedSizeChunker (`fixed_size`)  | 7                 | 197,3                 | Có thể cắt giữa một bước thao tác.                         |
| Hướng dẫn đăng ký SIS | SentenceChunker (`by_sentences`) | 4                 | 342,0                 | Tốt; mỗi chunk giữ trọn một nhóm hướng dẫn.               |
| Hướng dẫn đăng ký SIS | RecursiveChunker (`recursive`)   | 11                | 123,8                 | Giữ ranh giới tốt nhưng chunk khá ngắn.                      |
| Chính sách thư viện     | FixedSizeChunker (`fixed_size`)  | 7                 | 190,6                 | Có nguy cơ cắt rời giờ mở cửa và điều kiện sử dụng.   |
| Chính sách thư viện     | SentenceChunker (`by_sentences`) | 5                 | 264,0                 | Tốt; giờ mở cửa nằm cùng một chunk.                         |
| Chính sách thư viện     | RecursiveChunker (`recursive`)   | 11                | 119,5                 | Mạch lạc nhưng tạo nhiều chunk nhỏ.                          |
| Quy định tài chính      | FixedSizeChunker (`fixed_size`)  | 150               | 199,8                 | Ổn định kích thước nhưng làm vỡ ngữ cảnh điều khoản. |
| Quy định tài chính      | SentenceChunker (`by_sentences`) | 62                | 479,6                 | Ít chunk hơn, nhưng một số chunk còn dài.                   |
| Quy định tài chính      | RecursiveChunker (`recursive`)   | 198               | 150,3                 | Bám cấu trúc tốt hơn, đổi lại số chunk lớn.              |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Cấu hình A — FixedSizeChunker (đường cơ sở)**

- **Loại chiến lược:** `FixedSizeChunker(chunk_size=500, overlap=50)`.
- **Mô tả & lý do chọn:** Đây là đường cơ sở đơn giản, đảm bảo giới hạn kích thước và có overlap để giảm mất ngữ cảnh ở ranh giới. Nó là mốc đối chiếu cho các chiến lược nhận biết cấu trúc văn bản.

**Cấu hình B — SentenceChunker**

- **Loại chiến lược:** `SentenceChunker(max_sentences_per_chunk=3)`.
- **Mô tả & lý do chọn:** Các hướng dẫn SIS và quy định thư viện thường thể hiện trọn ý trong 1–3 câu. Gom theo câu giúp giữ bước thao tác, ngoại lệ và thời gian trong cùng một chunk dễ đọc.

**Cấu hình C — RecursiveChunker**

- **Loại chiến lược:** `RecursiveChunker(chunk_size=500)`.
- **Mô tả & lý do chọn:** Phù hợp văn bản quy định dài có tiêu đề, đoạn và câu. Thuật toán ưu tiên tách theo cấu trúc rồi mới cắt cứng, nên giảm khả năng chia giữa ý.

### So Sánh Giữa Các Thành Viên

| Thành viên                   | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh                                                 | Điểm yếu                                                    |
| ------------------------------ | ------------------------ | ----------------------- | ------------------------------------------------------------ | -------------------------------------------------------------- |
| Fixed-size baseline | FixedSize 500/50 | 7 / 10 | Q1, Q3, Q4 đúng Top-1; kích thước ổn định và có overlap. | Q2 chỉ liên quan một phần ở Top-3; Q5 chưa có điều khoản đúng. |
| Sentence 3 câu | Sentence 3 câu | 7 / 10 | Q1, Q3, Q4 đúng Top-1; Q2 có chunk hướng dẫn đúng ở Top-2. | Không lấy được điều khoản Q5 trong Top-3, dù đã lọc tài chính. |
| Recursive 500 + filter | Recursive 500 | 9 / 10 | Q1, Q3, Q4, Q5 đúng Top-1; Q5 dùng `department=finance` lấy đúng điều khoản. | Q2 ở Top-1 mới trả lời một phần, chưa đầy đủ hướng dẫn liên hệ Phòng Quản lý Đào tạo. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> RecursiveChunker (`chunk_size=500`) là cấu hình tốt nhất trong phép chạy chung: 4 câu trả về đúng thông tin ở Top-1 và Q2 trả về thông tin liên quan nhưng thiếu một phần chi tiết, tương đương 9/10. So với SentenceChunker, RecursiveChunker tách quy định tài chính theo ranh giới đoạn tốt hơn; kết hợp filter `department=finance` đưa đúng điều khoản hạn chế đăng ký môn của Q5 lên Top-1.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query)                                                                            | Câu trả lời chuẩn (Gold Answer)                                                                                                   | Chunk nào chứa thông tin?                     |
| - | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| 1 | Để đăng ký học phần thành công trên SIS, sinh viên cần thao tác theo những bước nào và trạng thái nào xác nhận đã đăng ký xong? | Vào `Academics → Course Registration`, chọn kỳ mở đăng ký, `Add` rồi `Register`; trạng thái phải là `Registered`. | `vinuni-course-registration-guide`, chunk 0 |
| 2 | Nếu lớp đã đầy, bị trùng lịch hoặc chưa đạt điều kiện tiên quyết khi đăng ký môn, sinh viên nên làm gì? | Kiểm tra điều kiện/lịch và liên hệ Phòng Quản lý Đào tạo; SIS không có danh sách chờ. | `vinuni-course-registration-guide`, chunk 2 |
| 3 | Sinh viên đại học được mượn tối đa bao nhiêu tài liệu thư viện và trong thời hạn bao lâu? | Tối đa 3 tài liệu, mỗi tài liệu 2 tuần. | `vinuni-library-borrowing-privileges`, chunk 0 |
| 4 | Thư viện VinUni mở cửa vào giờ nào trong học kỳ, và khu nào mở 24/7? | Cổng chính T2–T6 8:00–21:00, T7–CN 9:00–17:00; khu học tập 24/7 mở liên tục. | `vinuni-library-access-services`, chunk 0 |
| 5 | Nếu không hoàn thành học phí đúng hạn từ một tuần, sinh viên sẽ bị hạn chế gì? | Sinh viên có thể bị tạm đình chỉ học và không được đăng ký môn kỳ tiếp theo cho đến khi hoàn thành nghĩa vụ. | Điều khoản thanh toán chậm trong `vinuni-financial-regulation-2023-2024` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi                | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú                                                                                         |
| - | ------------------------ | -------------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------ |
| 1 | Đăng ký SIS | Recursive 500 | Có, Top-1 | Score Top-1: 0,7915. |
| 2 | Sự cố đăng ký môn | Recursive 500 | Có, Top-1 (một phần) | Score Top-1: 0,7518; thiếu chi tiết liên hệ Phòng Quản lý Đào tạo. |
| 3 | Quyền mượn thư viện | Recursive 500 | Có, Top-1 | Score Top-1: 0,7923. |
| 4 | Giờ thư viện | Recursive 500 | Có, Top-1 | Score Top-1: 0,7844. |
| 5 | Hạn chế do chậm học phí | Recursive 500 + filter finance | Có, Top-1 | Score Top-1: 0,7919; nêu đúng tạm đình chỉ và hạn chế đăng ký môn. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

> Có. Với Q4, filter `{"department": "library"}` giữ lại các kết quả thư viện: Top-1 là `vinuni-library-access-services` (0,7844), tiếp theo là các chunk thư viện thay vì tài chính. Với Q5, filter `{"department": "finance"}` giới hạn truy vấn vào quy định tài chính; kết hợp RecursiveChunker, điều khoản tạm đình chỉ và không được đăng ký môn xuất hiện ở Top-1 (0,7919).

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

- Mock embedding chỉ dùng để test; benchmark tiếng Việt phải dùng local multilingual embedder.
- RecursiveChunker giữ tốt quy trình ngắn lẫn các điều khoản dài; đạt 9/10 trên năm câu benchmark.
- Metadata filter theo `department` loại bớt chunk không liên quan; hai tài liệu dài đã được chuẩn hóa front matter để hỗ trợ filter.

**Bài học rút ra khi so sánh trong nhóm:**

> Cùng một bộ dữ liệu, ranh giới chunk quyết định thông tin nào đi cùng nhau. Fixed-size dễ thực hiện nhưng có thể tách một quy trình ở giữa; SentenceChunker mạch lạc hơn với hướng dẫn ngắn; RecursiveChunker phù hợp nhất với quy định dài, dù tạo nhiều vector. Kết quả Q5 cho thấy chất lượng metadata, filter và cấu trúc dữ liệu quan trọng không kém lựa chọn embedder.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

> Nếu làm lại, nhóm sẽ tạo thêm metadata cấp điều khoản (ví dụ `section` hoặc `article`) cho các quy định rất dài. Điều đó giúp filter chính xác hơn tài liệu tài chính mà không cần tăng số lượng chunk quá nhiều; nhóm cũng sẽ bổ sung một câu benchmark cần kết hợp hai nguồn để kiểm tra khả năng tổng hợp của agent.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí                                   | Điểm tự đánh giá |
| -------------------------------------------- | ---------------------- |
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10                |
| Thiết kế chiến lược (Strategy Design)   | 15 / 15                |
| Chất lượng truy xuất (Retrieval Quality) | 9 / 10                 |
| Thuyết trình (Demo)                        | 0 / 5                  |
| **Tổng phần nhóm**                  | **34 / 40**      |
