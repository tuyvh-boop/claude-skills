# Description task trên Jira — format chuẩn

Chuẩn **nội dung + cách trình bày** khi viết description cho một task/bug. AI/skill đọc file này
trước khi ghi description. Khác comment (báo tiến độ, xem [`comment-templates.md`](comment-templates.md)):
description là **tài liệu gốc của task** — người đọc mở ra là hiểu task giải quyết gì, làm ở đâu, deadline nào.

## Cơ chế — ghi qua subcommand `description`

Ghi bằng `jira_client.py description <KEY> --text-file <path>` (hoặc `--text`), mặc định **dry-run**,
thêm `--commit` mới ghi. Subcommand **không ghi đè** description đã có nội dung (rule write-risk 🔴) —
cố ý thay thì thêm `--force`. Nội dung qua `text_to_adf()` với **heading h1–h3** (khác comment ép h3–h4).

## Cách trình bày (khác comment ở heading)

- **Heading dùng h1 / h2 / h3** — description là tài liệu nên header lớn, phân cấp rõ:
  - `#` (h1) = tiêu đề tổng của description (1 dòng đầu, mô tả 1 câu task là gì).
  - `##` (h2) = các mục chính (Chi tiết, Tác động, Việc cần làm, Nguồn…).
  - `###` (h3) = mục con khi cần.
- Inline markdown như comment: `**đậm**` nhãn/điểm chính, `` `code` `` cho tên field/mutation/bảng/lệnh,
  `[nhãn](url)` hoặc URL trần (tự thành link), `- ` bullet, `1. ` numbered, `---` đường kẻ.
- **Một dòng trống** ngắt khối là đủ, không chồng nhiều dòng trống.
- Ngôn ngữ: tiếng Việt; giữ nguyên tên field/scope/repo/mã lỗi/API bằng tiếng Anh.
- **Không để lộ secret**: chỉ ghi tên field/hành động, không dán giá trị token/connection string.

## Khung mục cho BUG (linh hoạt, bỏ mục không có)

```
# <Tiêu đề 1 câu: bug là gì, ở đâu>

<1–2 câu bối cảnh: phát hiện từ đâu, link nguồn/dashboard>

## Chi tiết
- <thông số cụ thể: mutation/endpoint/field, thay đổi, version, thời điểm phát hiện, deadline>

## Tác động
<điều gì hỏng nếu không fix, hỏng với ai>

## Việc cần làm
- <các bước fix, verify>

## Lưu ý / rủi ro
- <giả định cần kiểm chứng, cạm bẫy>

## Nguồn tham khảo
- <official docs / changelog / ticket — link trần>
```

## Khung mục cho FEATURE (tham khảo)

```
# <Tên feature — 1 câu giá trị>

## Mục tiêu / User story
## Phạm vi (in / out)
## Yêu cầu chi tiết
## Ràng buộc & phụ thuộc
## Tiêu chí done (acceptance)
```

> Không bắt buộc đủ mọi mục — giữ mục thực sự có nội dung, bỏ mục trống. Mục tiêu là người đọc mở
> description ra hiểu ngay, không phải điền cho đủ khung.
