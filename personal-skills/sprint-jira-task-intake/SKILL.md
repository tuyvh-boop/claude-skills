---
name: sprint-jira-task-intake
description: Kích hoạt khi user có 1 task Jira mới cần lên plan trước khi code — ví dụ "lấy task OPOS-2 rồi lên plan", "task Jira này cần làm gì", "điền plan task X vào sheet planning". Lấy chi tiết task từ đúng project Jira (Product Options / Color Swatch), hỗ trợ breakdown công việc + estimate, rồi điền vào Google Sheet planning của team.
---

# Sprint Jira Task Intake

Skill hỗ trợ luồng: **lấy task Jira → lên plan triển khai → điền vào sheet planning**. Dùng khi có task Jira mới được giao, cần hiểu rõ yêu cầu và breakdown việc trước khi bắt tay code.

## ⚠️ Framework Reminder

Task intake requires measuring scope before planning: [[framework_systematic_problem_solving]] —
- **Understand the full AC before breaking down**: don't assume "simple" until you've read acceptance criteria completely. Scope explosion mid-project often comes from missing AC read
- **Breakdown must span all layers**: "sửa API endpoint" is backend-only. Intake should identify: backend logic changes, DB/schema touches, API contract changes, frontend surface changes, test updates. Missing any layer = incomplete estimate
- **Estimate against current codebase constraints**: rủi ro và estimate come from knowing what pattern/tool already exists in this repo vs what's new. Thời gian estimate là thời gian implement-with-tools-here, không thời gian xây từ đầu

## Bối cảnh Jira của team (dùng thẳng, KHÔNG dò lại)

- Site: `optis-app.atlassian.net`, `cloudId`: `0324d786-4e6b-4cdf-bd05-8d876d21f3a7`
- Project key theo app — dùng đúng bảng này, **KHÔNG** gọi `getVisibleJiraProjects` / `getAccessibleAtlassianResources` để dò lại (tốn token):

  | App | Board | Project key |
  |---|---|---|
  | Product Options | Scrum | OPOS |
  | Product Options | Kanban | OPOK |
  | Color Swatch | Scrum | OPCS |
  | Color Swatch | Kanban | OPSK |

- Mã task dạng `<KEY>-<số>`, ví dụ `OPOS-2`, `OPCS-15`.
- Workflow status (board Scrum): To Do → Research → In Development → In Code Review → Ready for Test → Testing → Done.
  - Lưu ý: trạng thái "review" tên chính xác là **"In Code Review"**, không phải "Review".

## Bước 1 — Lấy task từ Jira

1. Xác định app (Product Options / Color Swatch) và board (Scrum/Kanban) từ mã task hoặc từ ngữ cảnh user cho — suy ra project key từ bảng trên, không hỏi lại nếu đã rõ từ mã task (ví dụ `OPOS-12` → project OPOS).
2. Tìm tool Jira MCP khả dụng qua ToolSearch với từ khoá `"jira"` (tên tool có dạng `mcp__<id>__getJiraIssue`, `mcp__<id>__searchJiraIssuesUsingJql` — id server có thể khác nhau tuỳ session).
3. Dùng `getJiraIssue` (site `optis-app.atlassian.net`, cloudId ở trên, issueIdOrKey = mã task) để lấy: title, description, acceptance criteria, status, assignee, labels, priority, các field liên quan khác.
4. Nếu user chỉ đưa mô tả chung ("task mới nhất của tôi", "task đang To Do") thay vì mã cụ thể — dùng `searchJiraIssuesUsingJql` với JQL đúng project key, ví dụ:
   `project = OPOS AND status = "To Do" AND assignee = currentUser() ORDER BY created DESC`

## Bước 2 — Lên plan triển khai

Từ nội dung task lấy được ở Bước 1, soạn plan gồm:

1. **Breakdown công việc**: chia task thành các đầu việc cụ thể, đủ nhỏ để estimate và code được ngay (vd: "sửa API endpoint X", "thêm field Y vào schema", "viết test cho Z").
2. **Estimate sơ bộ**: ước lượng effort cho từng đầu việc (giờ hoặc story point tuỳ convention team đang dùng — hỏi user nếu chưa rõ đơn vị).
3. **Rủi ro / điểm chưa rõ**: liệt kê những chỗ mô tả task còn mơ hồ, thiếu acceptance criteria, hoặc có rủi ro kỹ thuật (breaking change, phụ thuộc hệ thống khác...).
   - **KHÔNG tự đoán** yêu cầu mơ hồ để lấp đầy plan. Với mỗi điểm chưa rõ, viết thành câu hỏi cụ thể để hỏi lại người giao việc trước khi code.
   - Nếu có điểm chưa rõ quan trọng (ảnh hưởng lớn đến scope/estimate), dừng và hỏi user trước khi chốt plan, thay vì tự ý giả định rồi điền vào sheet.

Trình bày plan dạng bảng/markdown rõ ràng để user review trước khi ghi vào sheet.

## Bước 3 — Điền vào Google Sheet planning

1. **Trước khi ghi bất kỳ cột nào**, đọc file `/home/bss-group-3775/.claude/skills/sprint-sheet-core/references/sheet-schema.md` để biết SHEET_ID, tên tab, và cột nào tương ứng nghĩa gì. Không tự đoán cấu trúc sheet.
2. Nếu file schema đó **không tồn tại**, hoặc còn chứa placeholder dạng `<TODO...>` chưa điền (nghĩa là sheet chưa setup xong):
   - **Dừng lại**, nói rõ cho user rằng schema sheet chưa sẵn sàng.
   - Đề xuất 2 hướng: (a) user tự điền nốt schema rồi chạy lại skill, hoặc (b) xuất plan ở Bước 2 ra bảng markdown ngay trong chat để user tự copy-paste vào sheet tạm thời.
   - Không block toàn bộ luồng chỉ vì thiếu tích hợp sheet — plan vẫn phải được giao cho user dưới dạng markdown.
3. Nếu schema đã đầy đủ: dùng ToolSearch với từ khoá liên quan đến `"sheet"` / `"google sheets"` để kiểm tra có Google Sheets MCP tool khả dụng trong session không, trước khi thử gọi. Nếu không có tool nào, áp dụng fallback markdown như mục 2.
4. Khi ghi sheet, map đúng theo cột đã đọc ở bước 1 (task key, title, breakdown, estimate, rủi ro/câu hỏi mở, status...). Xác nhận lại với user các dòng đã ghi trước khi coi là hoàn tất.

## Ghi chú chung

- Luôn ưu tiên project key có sẵn ở trên, không gọi lại API để tra cứu danh sách project.
- Không tự transition status Jira hay comment vào task trong skill này trừ khi user yêu cầu rõ — phạm vi skill là intake + plan + điền sheet.
- Nếu user chỉ muốn 1 phần (vd chỉ lấy task, chưa cần plan hoặc chưa cần điền sheet), dừng ở đúng bước được yêu cầu, không tự ý làm tiếp các bước sau.
