---
name: sql-schema-annotation
description: Kích hoạt khi làm việc với MySQL MCP server để query/join dữ liệu, hoặc khi cần tạo/tra cứu/cập nhật tài liệu annotation mô tả ý nghĩa nghiệp vụ của bảng, cột (đặc biệt cột status/type/flag dạng enum), và quan hệ khoá ngoại ngầm không có constraint thật trong DB — để tránh đoán sai và query/join nhầm.
---

# SQL Schema Annotation

## Mục đích

Claude thấy được tên bảng/cột qua MySQL MCP nhưng KHÔNG biết ý nghĩa nghiệp vụ
đằng sau (vd `status = 2` nghĩa là gì, bảng nào là bảng "chính" khi có nhiều
bảng tên gần giống, cột nào tham chiếu ngầm sang bảng khác mà không có FK
constraint thật). Skill này không phải là MySQL MCP server — nó tạo và duy trì
một **file tài liệu annotation** để Claude tra cứu trước khi đoán, giảm rủi ro
query sai âm thầm (không lỗi rõ ràng để phát hiện).

## Khi nào dùng skill này

- Trước khi viết query/join phức tạp trên DB lạ hoặc DB đã có annotation → đọc
  file annotation trước.
- Khi user yêu cầu tạo/khởi tạo tài liệu mô tả schema cho 1 DB/project.
- Khi trong lúc làm việc phát hiện bảng/cột chưa có trong annotation → dừng lại
  bổ sung ngay, không để tồn đọng.

## File annotation nằm ở đâu

File annotation gắn với **từng project**, không nằm trong thư mục skill này
(vì mỗi project là một DB khác nhau). Thứ tự xử lý:

1. Tìm file đã có trong project theo các tên gợi ý: `schema-annotations.md`,
   `db-annotations.md`, `docs/db-schema.md`, `docs/database.md` — ưu tiên
   `docs/schema-annotations.md` nếu chưa có quy ước nào khác trong repo.
2. Nếu chưa có, hỏi user muốn đặt file ở đâu, gợi ý mặc định
   `docs/schema-annotations.md` tại root project, rồi tạo mới.
3. Từ lúc đó, dùng đúng path đó cho cả session/project — không tạo file trùng
   lặp ở vị trí khác.

Định dạng chi tiết + ví dụ đầy đủ: xem
[references/format-template.md](references/format-template.md).

## Quy trình rút annotation

**a. Lấy cấu trúc thật từ DB**
- Nếu có MySQL MCP server đã kết nối trong session (tool dạng `mcp__*mysql*`
  hoặc tương tự): dùng `DESCRIBE <table>` / `SHOW CREATE TABLE <table>` để lấy
  đúng tên cột, kiểu dữ liệu, index — **không tự bịa tên cột**.
- Nếu session **chưa có** MySQL MCP nào: nói rõ với user là chưa thấy MySQL
  MCP được cấu hình, và hỏi user paste DDL (`CREATE TABLE ...`) hoặc kết quả
  `SHOW CREATE TABLE` thủ công — vẫn tạo được annotation từ đó, không bắt buộc
  phải có MCP.

**b. Hỏi lại ý nghĩa cho cột khó đoán**
- Với cột dạng số/enum không tự rõ nghĩa (`status`, `type`, `flag`, `state`,
  cột tinyint/int có vẻ là code...) → **HỎI LẠI user từng giá trị nghĩa là
  gì**, không tự đoán. Đoán sai loại cột này dẫn tới query/filter sai mà
  không có lỗi nào báo — nguy hiểm hơn nhiều so với dừng lại hỏi.
- Với quan hệ khoá ngoại không có constraint tường minh trong DB (vd
  `order.customer_id` không có FK nhưng rõ ràng trỏ sang `customer.id`) →
  xác nhận lại với user nếu không chắc chắn 100%, đặc biệt khi có nhiều bảng
  tên gần giống nhau (bảng nào là bảng "chính đang dùng" vs bảng cũ/backup).

**c. Ghi vào file annotation**
- Dùng đúng format nhất quán (xem template), append vào file annotation của
  project. Không viết lại toàn bộ file trừ khi cần sắp xếp lại.

## Cập nhật dần trong lúc làm việc

Khi đang query/join mà chạm vào bảng hoặc cột **chưa có** trong file
annotation: dừng lại, áp dụng quy trình a→b→c ở trên để bổ sung ngay, rồi mới
tiếp tục việc chính. Không gom lại làm sau — annotation thiếu sẽ khiến các
lần dùng tiếp theo lại đoán mò.
