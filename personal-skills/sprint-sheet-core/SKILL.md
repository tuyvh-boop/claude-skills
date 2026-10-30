---
name: sprint-sheet-core
description: Skill "core/reference" lưu quy định cấu trúc Google Sheet planning sprint của team (SHEET_ID, tên tab, tên cột, quy tắc điền dữ liệu). Kích hoạt khi có tác vụ nào đó cần đọc/ghi Google Sheet sprint planning (jira intake, daily standup, hoặc bất kỳ tác vụ nào khác động tới sheet này) — luôn đọc references/sheet-schema.md của skill này TRƯỚC KHI thao tác sheet.
---

# sprint-sheet-core

## Skill này là gì

Đây là skill **passive reference** — bản thân nó KHÔNG tự động đọc/ghi sheet, KHÔNG tự chạy hành động nào cả. Nhiệm vụ duy nhất của nó là làm **nguồn sự thật duy nhất (single source of truth)** cho cấu trúc Google Sheet planning sprint của team: sheet ID, danh sách tab, tên cột, ý nghĩa cột, quy tắc điền dữ liệu.

Các skill khác trong hệ thống — ví dụ `sprint-jira-task-intake`, `sprint-daily-standup` — cần **đọc file `references/sheet-schema.md` của skill này TRƯỚC KHI đọc/ghi bất kỳ dữ liệu nào lên sheet**, thay vì mỗi skill tự đoán cấu trúc sheet riêng. Điều này tránh tình trạng mỗi skill hiểu cột khác nhau, ghi sai vị trí, hoặc dùng nhầm SHEET_ID.

## Quy tắc bắt buộc khi có tác vụ cần đọc/ghi sheet thật

1. **Luôn đọc `references/sheet-schema.md` trước.** Đây là bước bắt buộc, không được bỏ qua dù tác vụ trông đơn giản.
2. **Kiểm tra placeholder chưa điền.** Nếu file `references/sheet-schema.md` còn bất kỳ chỗ nào dạng `<TODO: ...>` chưa được điền, và tác vụ hiện tại cần đọc/ghi sheet thật:
   - **DỪNG LẠI ngay**, không tự suy đoán SHEET_ID, tên tab, tên cột, hay bất kỳ giá trị nào thay cho placeholder.
   - Hỏi user điền các mục còn thiếu trước khi tiếp tục.
   - Không tạo dữ liệu giả (mock SHEET_ID, mock tên cột) để "chạy tạm" — vì user chưa cấu hình Google Sheets API/MCP, làm vậy sẽ gây sai lệch dữ liệu thật sau này.
3. **Kiểm tra MCP tool khả dụng.** Trước khi thao tác sheet thật, dùng `ToolSearch` với từ khoá `"sheet"` hoặc `"google sheets"` để xem session hiện tại có Google Sheets MCP tool nào khả dụng không.
   - Nếu **có** tool phù hợp: dùng tool đó theo đúng cách xác thực/kết nối đã ghi trong `references/sheet-schema.md` (mục "Cách xác thực/kết nối").
   - Nếu **không có**: báo user rằng cần cấu hình Google Sheets MCP server (hoặc Google Sheets API) trước, không tự bịa cách kết nối khác.

## Khi nào coi là "đã sẵn sàng" để thao tác sheet thật

Chỉ khi đồng thời thỏa:
- `references/sheet-schema.md` không còn placeholder `<TODO...>` nào (đã được user điền đầy đủ: SHEET_ID, danh sách tab, tên cột từng tab, quy tắc điền dữ liệu, cách xác thực).
- Có ít nhất một Google Sheets MCP tool khả dụng trong session (xác nhận qua `ToolSearch`).

Nếu thiếu 1 trong 2 điều kiện trên, dừng lại và hỏi/báo user — không tự chế dữ liệu hay đoán cấu hình.

## Cách skill khác nên dùng skill này

Skill khác (vd `sprint-jira-task-intake`, `sprint-daily-standup`) khi cần biết "cột nào là status", "tab nào chứa backlog", "SHEET_ID là gì"... thì đọc trực tiếp file `references/sheet-schema.md` của skill này, không nên hard-code lại thông tin sheet ở nơi khác. Nếu skill khác phát hiện schema đã lỗi thời (vd tab đổi tên), nên báo user cập nhật lại `references/sheet-schema.md` thay vì tự sửa theo suy đoán riêng.
