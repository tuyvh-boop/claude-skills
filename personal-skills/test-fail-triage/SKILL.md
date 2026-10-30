---
name: test-fail-triage
description: Đọc Google Sheet kết quả test mà tester đã điền (pass/fail) sau khi test 1 task, lọc case FAIL, điều tra code tìm nguyên nhân, rồi báo cáo lại cho dev và CHỜ xác nhận trước khi fix. Kích hoạt khi user nói "đọc sheet test kết quả", "xem tester test fail chỗ nào", "check fail trong sheet rồi fix", hoặc đưa mã Jira/link sheet kèm ý muốn xử lý kết quả test. KHÔNG dùng để tạo test case mới (đó là công cụ của tester, `te-tester-gen-testcases`) và KHÔNG dùng để xử lý comment review MR trên GitLab (đó là `te-dev-address-mr`/`explain-and-fix-mr`).
---

# Test Fail Triage

Đọc kết quả test tester đã trả về trên Google Sheet, điều tra từng case FAIL, báo cáo nguyên nhân cho dev, và **dừng lại chờ xác nhận** trước khi đụng vào code — không tự ý fix.

## ⚠️ Framework Reminder

Test failure diagnosis requires data, not guessing: [[framework_systematic_problem_solving]] —
- **Distinguish test failure from code bug**: test framework outdated? Environment issue? Or actual code logic wrong? Measure by running test in different contexts (isolated vs full suite, old code vs new code)
- **Measure impact across layers**: fail in UI test might trace back to API change, schema migration, or permission logic. Don't assume the failure's layer; trace through all of them
- **Root cause before fixing**: "test fails" is symptom. Developer must confirm root cause before fixing, not guess. Report findings; wait for developer acknowledgment. Prevents fixing wrong thing

## Nguyên tắc bắt buộc

**Không bao giờ tự fix khi chưa được user xác nhận rõ ràng ở Step 5.** Kể cả khi nguyên nhân đã rõ 100%, vẫn phải trình bày và chờ — đây là ranh giới cứng của skill này, không phải gợi ý.

**Không đoán bừa nguyên nhân.** Case nào Note của tester không đủ để xác định lỗi thì báo "chưa đủ thông tin", không suy diễn cho có.

## Step 1 — Xác định sheet & tab

**Bỏ qua bước này nếu user đã paste sẵn bảng kết quả trực tiếp trong tin nhắn** (không nhắc tới sheet nào cả) — nhảy thẳng xuống Step 3 với dữ liệu đó, không cần SHEET_ID vì không có sheet nào để đọc.

Ngược lại, nếu cần đọc 1 sheet thật (user đưa link/tên task mà chưa kèm dữ liệu): cần Sheet ID (hoặc URL) + tên tab chứa kết quả test của task đang xử lý.

Đọc `references/sheet-schema.md` trước khi làm gì khác.

- Nếu file còn placeholder `<TODO...>` cho SHEET_ID → **dừng lại, hỏi user điền** trước khi tiếp tục. Không tự đoán SHEET_ID, không bịa cấu trúc tab để "chạy tạm".
- Nếu user chỉ đưa mã Jira (vd `OPCS-44`) → suy ra tên tab theo quy tắc đặt tên đã ghi trong `sheet-schema.md`; nếu không khớp rõ ràng, hỏi lại user tên tab chính xác thay vì đoán.

## Step 2 — Đọc dữ liệu

`ToolSearch` với từ khoá `"sheet"` / `"spreadsheet"` để tìm tool đọc Google Sheet khả dụng trong session hiện tại (vd MCP server `autosheet`).

- **Có tool** → đọc toàn bộ range của tab đó.
- **Không có tool** → đây là tình huống bình thường (MCP mới add cần phiên `claude` mới mới thấy được), không phải lỗi. Báo user 1 trong 2 cách:
  - Mở phiên `claude` mới nếu vừa connect MCP xong, hoặc
  - Export sheet ra CSV / copy-paste bảng kết quả vào chat để dùng ngay, không cần chờ MCP.

## Step 3 — Lọc & phân loại case FAIL

- Chỉ lấy row có cột Status khớp fail (chấp nhận biến thể viết hoa/thường/emoji: `fail`, `FAILED`, `Fail ❌`...).
- Với mỗi case fail, đọc đủ: Steps, Expected result, Actual result/Note tester ghi lúc fail.
- Gộp các case rõ ràng cùng chung 1 nguyên nhân (vd 3 test case khác nhau đều fail vì cùng 1 bug) thành 1 mục báo cáo — tránh liệt kê lặp.

## Step 4 — Điều tra nguyên nhân

Với từng case (hoặc nhóm case) fail: dùng CodeGraph (nếu repo có, xem `.codegraph/`) hoặc grep/Read để tìm code liên quan tới hành vi mô tả ở Steps + Expected result. Repo có nhiều hơn 1 (api/cms/tae) thì xác định đúng repo trước khi tìm.

Phân loại mỗi case vào đúng 1 trong 4 nhóm:

1. **Bug thật** — có `file:line` cụ thể, giải thích được tại sao code hiện tại ra kết quả sai so với Expected result.
2. **Không phải bug** — hành vi đúng theo code/spec hiện tại; nhiều khả năng tester hiểu sai expected result hoặc dùng sai data test.
3. **Chưa đủ thông tin** — Note của tester không đủ để xác định nguyên nhân (thiếu bước lặp lại, thiếu ảnh/log, thiếu chi tiết môi trường).
4. **Ngoài phạm vi task này** — nghi ngờ do task/PR khác, do dữ liệu môi trường test, hoặc do bên thứ ba (Shopify, network...).

## Step 5 — Báo cáo & chờ xác nhận (bắt buộc dừng)

Trình bày danh sách case fail đã điều tra, mỗi case gồm: ID test case, tóm tắt lỗi, phân loại (1 trong 4 nhóm ở Step 4), `file:line` nếu có, đề xuất hướng fix nếu là bug thật.

Sắp xếp: **bug thật có file:line rõ ràng lên đầu**, case "chưa đủ thông tin"/"ngoài phạm vi" xuống cuối.

Hỏi user rõ ràng: case nào fix ngay, case nào bỏ qua, case nào cần hỏi lại tester trước khi kết luận. Dùng `AskUserQuestion` nếu danh sách có nhiều lựa chọn rời rạc cần user chốt từng cái.

## Step 6 — Fix (chỉ sau khi user confirm)

- Chỉ fix đúng những case user đã confirm ở Step 5 — không tự mở rộng sang case khác dù thấy "tiện thể".
- Sửa theo đúng convention của repo đang đứng (naming, test coverage...).
- Sau khi fix xong, gợi ý bước tiếp theo (`/te-dev-commit` để commit) — không tự động commit nếu user không yêu cầu thêm.
