# Cấu trúc Google Sheet kết quả test

Nguồn sự thật duy nhất cho `test-fail-triage`. Điền các mục `<TODO...>` bên dưới trước khi skill có thể đọc sheet thật — thiếu mục nào, skill sẽ dừng lại hỏi thay vì tự đoán.

## Sheet

- **SHEET_ID**: `<TODO: điền Sheet ID hoặc URL sheet kết quả test>`
- **Quy tắc đặt tên tab**: `<TODO: vd "1 tab / task, đặt tên theo mã Jira như OPCS-44">`

## Cột (mỗi tab)

Mặc định theo format `te-tester-gen-testcases` + 3 cột kết quả, trừ khi sheet thật khác đi:

| Cột | Ý nghĩa |
|---|---|
| ID | Mã test case, vd `TC-001` |
| Classification | Smoke / Functional / Validation / Abnormal / Edge Case / Permission / UI State / Integration / Regression... |
| Data Test | Dữ liệu dùng để test |
| Pre-condition | Điều kiện trước khi test |
| Steps | Các bước thực hiện |
| Expected result | Kết quả mong đợi |
| Actual result | Kết quả thực tế tester quan sát được |
| Status | Pass / Fail |
| Note | Ghi chú thêm của tester khi fail (ảnh, log, chi tiết môi trường...) |

`<TODO: nếu sheet thật của team dùng tên cột khác hoặc thêm/bớt cột, sửa lại bảng trên cho khớp>`

## Cách xác thực/kết nối

`<TODO: ghi lại cách connect MCP đọc sheet này nếu khác với autosheet mặc định (vd tên MCP server, scope, tool cần dùng)>`
