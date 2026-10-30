---
name: create-plan
description: Soạn 1 bản plan triển khai kỹ thuật ĐẦY ĐỦ cho 1 task Jira — bám theo AC Jira + design Figma (nếu có) + code/kiến trúc hiện tại, phủ cả frontend (UI theo design) lẫn backend (API/schema/logic), ưu tiên tái dùng pattern có sẵn, không over-engineer. Dùng khi user nói "lên plan cho task X", "soạn plan implementation", "plan chi tiết task Jira này". KHÁC sprint-jira-task-intake (chỉ breakdown + estimate sơ bộ để điền sheet planning, không đi sâu design/code hiện tại) và Plan Mode gốc của Claude Code (không tự đối chiếu Jira/design/code, chỉ bàn bạc chung). Sau khi có plan → dùng `review-plan` để tự chấm lại trước khi code.
metadata:
  trigger: "user asks 'lên plan', 'soạn plan', 'plan chi tiết task Jira', 'plan implementation', hoặc cần plan kỹ thuật trước khi code"
  model_hint: "main loop (Sonnet/Opus) — thiết kế cần tư duy deep, không delegate"
  keywords: ["plan", "design", "jira", "implementation", "task"]
---

# Create Plan (đối chiếu Jira + Design + Code)

Mục tiêu: bản plan **đúng** (khớp AC/design), **đủ** (không bỏ sót góc nào từ UI tới backend), và **tối ưu** (tái dùng code có sẵn, không đề xuất viết lại cái đã có, không over-engineer cho nhu cầu chưa phát sinh).

⚠️ **Framework Reminder:** [[framework_systematic_problem_solving]] — khi thiết kế plan:
- **Không assume** cách làm tối ưu — đo lường constraint thật (performance budget? API contract? DB schema giới hạn?) trước khi thiết kế.
- **Xem toàn bộ layer:** frontend UI logic + backend API/DB + network/performance — không zoom vào 1 layer.
- **Identify bottleneck trước:** nếu feature nặng ở backend/DB, prioritize backend thiết kế không phải frontend.

## Bước 0 — Nguyên tắc thu thập nguồn

Đọc [`~/.claude/skills/plan-review-core/SKILL.md`](../plan-review-core/SKILL.md) — áp dụng đúng quy tắc tiết kiệm token + cách thu thập Jira/design/code ở đó cho Bước 2 dưới đây.

## Bước 1 — Xác định input & phạm vi

- Mã Jira bắt buộc (hoặc requirement dán tay nếu chưa lên Jira — nói rõ trong output "chưa đối chiếu được AC gốc, review lại khi có ticket").
- **Ticket lớn/nhiều mục** (nhiều feature con trong 1 ticket) → hỏi user muốn plan **toàn bộ** hay **1 phần cụ thể** trước khi fetch — tránh code-recon + soạn plan cho phần user không cần, vừa tốn token vừa ra plan dài không ai đọc hết.

## Bước 2 — Thu thập 3 nguồn

Làm theo đúng **Cách thu thập (2 đợt)** trong `plan-review-core`. Riêng phần **code-recon** ở skill này cần **sâu hơn** mức review-plan cần (ở đó chỉ cần biết constraint để chấm, ở đây cần đủ để **thiết kế**) — yêu cầu agent trả thêm:

- Danh sách component/helper/service **cụ thể tên + đường dẫn** có thể tái dùng đúng việc (không chỉ nói chung chung "có pattern tương tự").
- Constraint kỹ thuật sẽ bó buộc cách implement (schema hiện tại, API contract, giới hạn platform Shopify, permission model).
- WIP đã tồn tại trên branch hiện tại liên quan tới phạm vi — nếu có, plan phải **dựa trên** WIP đó chứ không đề xuất viết lại từ đầu.

## Bước 3 — Soạn plan (main loop, cần thiết kế thật — Sonnet/Opus)

Chỉ điền mục có input thật, phần nào thiếu nguồn (không có design, không rõ constraint) → ghi rõ "chưa xác định — cần thêm <nguồn>", không bịa cho đủ mục.

**Nguyên tắc khi thiết kế:**
- Có pattern/helper/component sẵn sàng đúng việc → **bắt plan dùng lại**, không đề xuất viết mới song song.
- Chỉ thiết kế đủ cho scope/AC hiện tại — không thêm field/case/khả năng mở rộng cho nhu cầu chưa được yêu cầu (over-engineer làm review-plan sau này phải hỏi "cái này để làm gì").
- Có constraint code hiện tại **không cho phép** làm đúng AC as-is (vd platform limit, schema thiếu field) → nêu rõ đây là **giả định cần đổi kiến trúc**, không lờ đi.

```markdown
# Plan — <mã Jira>: <tên feature>
> Scope: <toàn bộ / phần nào của ticket> · Design: <link, hoặc "không có">

## 1. Frontend / UI
<Theo từng màn/flow trong design (hoặc theo AC nếu không có design): component tái dùng (tên + path), component mới cần viết, state/edge case UI cần xử lý.>

## 2. Backend / Core
<API endpoint (mới/sửa), schema/migration, business logic, webhook/sync, permission — bám AC + constraint code hiện tại.>

## 3. Cross-cutting
<Pricing/plan-gating (nếu có), surface coverage in-app/storefront (theo `shopify-app/surfaces.md`), backward-compat với data/behaviour cũ.>

## 4. Rủi ro & giả định kỹ thuật
<Rủi ro thấy trước (data integrity, breaking change...), giả định cần dev/PM xác nhận trước khi code.>

## 5. Test tối thiểu
<Case bắt buộc test trước khi coi là done, bám theo AC.>

## 6. Open Questions
<Điểm 3 nguồn không đủ để tự quyết — câu hỏi cụ thể cần hỏi trước khi code.>
```

## Bước 4 — Output

Trả **trong chat**. Kết thúc bằng 1 dòng gợi ý: chạy `review-plan` trên bản vừa tạo để có 1 vòng chấm độc lập trước khi giao cho ai code — không tự động chạy (tốn thêm token nếu user chưa cần).

Mặc định trả **trong chat**, không tự ý xuất file `.md`. User muốn lưu lại → đọc `~/.claude/.te-ai-config-memo` tìm key `plan-workflow-output-dir`:
- **Có** → dùng luôn, không hỏi lại.
- **Chưa có** → hỏi thư mục, rồi ghi/append `plan-workflow-output-dir=<path>` vào file đó (tạo nếu chưa có, giữ nguyên key khác — key này dùng chung với `fix-plan`).

Tên file: `<MÃ-JIRA>-plan.md` (khác file `<MÃ-JIRA>-plan-review.md` mà `review-plan` tạo — xem tách bạch 2 loại tài liệu trong `plan-review-core`) — nếu đã tồn tại (từ `fix-plan` trước đó) thì **ghi đè bằng bản mới nhất**, không tạo file riêng theo version.

## Lỗi hay gặp

- **Over-engineering**: Đề xuất thêm field/case/khả năng chưa được AC yêu cầu. → Fix: chỉ thiết kế đúng scope hiện tại, ghi rõ "mở rộng sau nếu cần".
  - **Pressure trap (scope creep under PM)**: PM muốn demo gần, temptation thêm "nice-to-have" fields (validation_rules, cache, multi-select prep) để trông có chuẩn bị. Boundary: **AC = contract**. Fields không trong AC → deferred list, ghi rõ phase nào sẽ thêm, không sneak vào MVP scope. (RED baseline Scenario 3: agent deferred validation_rules + cache + multi-select, giữ lại domain logic + audit trails.)
- **Không phủ đủ surface**: Feature phải chạy cả in-app + storefront nhưng chỉ code 1 phía. → Fix: kiểm tra `shopify-app/surfaces.md` TRƯỚC bước 2, liệt kê tất cả surface cần cover.
- **Bỏ qua WIP sẵn có**: Có branch/code rẻi liên quan nhưng plan đề xuất viết lại. → Fix: bắt buộc check git log + branch hiện tại trước soạn plan.
- **Tái dùng plan cũ mà không validate**: Có plan cũ từ task khác (3–4 tuần trước), trông hoàn chỉnh, temptation copy-paste lại. Nhưng files đã refactor, contracts đã đổi, patterns đã bỏ. Kết quả: build fail, PR review flagging "file không tồn tại", hoặc silent data mismatch production. → Fix: **15-min validation checklist trước reuse**: (1) Files trong plan còn tồn tại không (git check), (2) File có bị refactor/rename không (git log file names), (3) Functions mentioned vẫn cùng signature, (4) Contract/spec có update sau plan date, (5) Patterns cũ còn dùng không. Nếu nghi ngờ → read plan + skim code hiện tại song song, không blind reuse. (RED baseline Scenario 4: agent phát hiện OPOS-32 plan reused ở OPOS-136 nhưng files đã split 3 cách, contracts đã refactor hashing schema, patterns watchdog đã bỏ.)
- **Design/AC không đủ**: Plan soạn nhưng thiếu nguồn. → Fix: ghi rõ "chưa xác định — cần <nguồn>" thay vì bịa, đừng giao code nếu chưa rõ.
- **Constraint code bị lờ**: Plan không nêu giới hạn schema/API/platform sẽ bó buộc cách implement. → Fix: code-recon phải bao gồm constraint + có phần 4 "Rủi ro & giả định".
- **Tái dùng code sai**: Liệt kê component/helper nhưng không check xem có đúng match pattern không. → Fix: cần tên + đường dẫn cụ thể, không nói chung chung "có pattern tương tự".
- **Team conflict trên scope không được quyết định rõ ràng**: Designer + Backend + PM muốn khác nhau (eg. designer: 3 surface, backend: 1 surface, PM: app block first). Plan không lock scope, để "có thể sẽ thêm sau". → Fix: **plan phải quyết định phase nào sao** (phase 1: app block + storefront, phase 2: admin dashboard) + ghi rõ *tại sao* (PM priority ưu tiên, backend risk signal, time constraint). Không để mơ hồ dạng này kéo tới code time. (RED baseline Scenario 5: agent locked app block + storefront ở phase 1, deferred dashboard ở phase 2 với giải thích rõ ràng.)

**Xem thêm:** `references/create-plan-mistakes.md` để chi tiết từng lỗi + cách tránh.
