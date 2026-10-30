---
name: cook-feature
description: Điều phối (orchestrator) toàn bộ luồng code 1 feature từ đầu đến cuối — lấy context Jira, tạo branch, implement, tự soát rủi ro, commit, tạo PR, comment Jira. Kích hoạt khi user muốn "cook"/"làm trọn"/"code hết" 1 task Jira end-to-end trong 1 lần thay vì tự gọi từng slash-command rời rạc (`/te-dev-start`, `/te-dev-commit`, `/te-dev-create-pr`...).
metadata:
  trigger: "user says 'cook', 'làm trọn', 'code hết', 'end-to-end task này' — muốn code feature từ đầu đến hết PR trong 1 luồng"
  model_hint: "main loop (Sonnet/Opus) — điều phối phức tạp, cần context liên bước"
  keywords: ["cook", "feature", "end-to-end", "task", "jira", "code"]
---

# Cook Feature

Skill **điều phối**: nối các slash-command sẵn có của team thành 1 luồng liền mạch để code trọn 1 feature — từ task Jira tới PR đã gửi review. Skill này **KHÔNG re-implement** logic của các command đó, chỉ gọi đúng thứ tự và chèn checkpoint xác nhận trước các bước có side-effect.

⚠️ **Framework Reminder:** [[framework_systematic_problem_solving]] — khi implement feature ở bước 2:
- **Không assume** cách làm — nếu chưa rõ giải pháp tối ưu, chạy `/te-dev-review-research` trước.
- **Measure impact** trước khi commit: tất cả surface bị chạm? backend/network/frontend phía nào có vấn đề?
- **Root cause verify:** kiểm thực nghiệm trước push, không trust test suite alone.

> ⚠️ **Trạng thái: Thử nghiệm.** Thứ tự bước dưới đây được suy ra từ các slash-command hiện có tại thời điểm viết skill, có thể chưa khớp 100% với thực tế dev hàng ngày. Nếu chạy thấy bước nào thừa/thiếu/sai thứ tự, hãy phản hồi để tinh chỉnh lại skill này.

## Nguyên tắc

- **Không thay thế** `/te-dev-start`, `/te-dev-commit`, `/te-dev-create-pr`, `/te-dev-review-pr-risk`, `/te-dev-address-mr`, `/te-dev-branch-investigation` — mỗi bước dưới đây gọi đúng command đó theo Skill tool hoặc mô phỏng đúng các step của nó, KHÔNG viết lại logic riêng.
- **Bỏ qua bước không cần thiết** với feature nhỏ — vd task tiny không cần branch investigation, không cần review-pr-risk sâu nếu diff rất nhỏ. Tự đánh giá theo Change Size Jira (Tiny/Medium/Major) nếu đọc được.
- **Dừng xác nhận trước side-effect thật**: commit+push, tạo PR, comment Jira. Các bước đọc/phân tích/implement code thì làm liền mạch, không hỏi vụn vặt.
- Project có CodeGraph MCP (`codegraph_*`) → ưu tiên dùng cho hiểu cấu trúc/blast-radius thay vì grep, đúng quy ước chung của team.

## Luồng các bước

### 1. Lấy context Jira + tạo branch

Gọi **`/te-dev-start`** (skill `te-dev-start`): hỏi/lấy mã Jira → fetch ticket qua Atlassian MCP (site `optis-app.atlassian.net`, cloudId `0324d786-4e6b-4cdf-bd05-8d876d21f3a7`) → đặt tên branch `feature/<MÃ-JIRA>` (hoặc `fix/` nếu là bug) → tạo từ `origin/master` mới nhất.

Kết quả cần có trước khi qua bước 2: **mã Jira, tóm tắt yêu cầu/AC, tên branch đã tạo**.

### 2. Implement feature

Code theo yêu cầu/AC đã lấy ở bước 1. Không có slash-command riêng cho bước này — đây là phần việc chính, làm trực tiếp trong main loop.

- **Xác định surface** trước khi code (rule `shopify-app/surfaces.md`, đọc qua con trỏ `~/.claude/.te-config-repo`): feature chỉ in-app (`api`+`cms`), chỉ storefront (`tae`), hay cả hai. Feature "cả hai" mà chỉ code 1 phía là lỗ hổng tích hợp phổ biến — nhớ phủ đủ.
- **Nếu feature nằm trong app CMS** (React Router + Polaris, `cms/`): tham khảo cấu trúc feature module tại `cms/.ai/skills/create-feature/SKILL.md` (skill của hệ thống agent khác, dùng làm THAM KHẢO nội dung — không copy nguyên xi lệnh/format, chỉ lấy đúng cấu trúc `features/<name>/{components,hooks,services,types,pages}`, quy ước barrel export, React Query hook pattern... rồi áp theo convention thật của `cms/CLAUDE.md` và `cms/.claude/CLAUDE.md` hiện có trong repo).
- Feature nằm ở `api` hoặc `tae` → theo convention/CLAUDE.md của repo đó, không áp cấu trúc CMS.
- Task lớn/phức tạp, chưa rõ giải pháp → cân nhắc chạy `/te-dev-review-research` trước khi code (ngoài phạm vi flow mặc định của skill này, chỉ gợi ý nếu thấy cần).

### 3. Tự soát rủi ro trước khi push

Gọi **`/te-dev-review-pr-risk`** (skill `te-dev-review-pr-risk`) trên diff vừa implement: lấy diff theo rule `diff-intake.md`, phân tích theo lăng kính risk (critical risks, business logic concerns, missing edge cases, safe-to-ignore, suggested manual tests).

- Verdict 🔴 (đừng push khi chưa xử lý) → quay lại bước 2 sửa trước khi đi tiếp.
- Verdict 🟡/🟢 → tóm tắt nhanh cho user biết rồi đi tiếp bước 4. Không cần hỏi xác nhận riêng ở bước này (chưa phải side-effect).

### 4. Commit theo convention team

Gọi **`/te-dev-commit`** (skill `te-dev-commit`): phân tích intent + độ phức tạp diff → chọn type (`feat`/`fix`/`refactor`/...) → soạn message format `<branch> (<type>) <subject>`.

**Checkpoint bắt buộc — dừng xác nhận với user trước khi commit thật** (đúng quy tắc gốc của `/te-dev-commit`: hiện message trong fenced block, hỏi `Approve? (yes / edit / split)`; nếu đang ở `master`/`ai-configs` phải cảnh báo riêng). Sau khi user approve, `/te-dev-commit` tự commit **và push luôn** (không hỏi lại lần 2) — đây là hành vi gốc của command, giữ nguyên.

### 5. Tạo PR + comment Jira báo review

Gọi **`/te-dev-create-pr`** (skill `te-dev-create-pr`): scan diff cả branch → rà soát tài liệu/CLAUDE.md cần cập nhật (hỏi xác nhận nếu có sửa) → commit phần sửa tài liệu nếu có → soạn title/description PR → **hỏi xác nhận** (`Thông tin PR đã chuẩn chưa? (yes / sửa lại)`) → sau khi user confirm mới push + `glab mr create --target-branch master` → lấy URL MR → comment Jira theo mẫu **TH1** (đọc rule `workflow/jira-comment.md` qua con trỏ repo) → **hỏi xác nhận nội dung comment** trước khi post bằng Atlassian MCP.

Đây là bước có 2 side-effect thật (tạo MR + post comment Jira công khai) — **không được bỏ qua checkpoint xác nhận** dù bước 4 đã được approve trước đó.

## Khi nào bỏ qua bước

- Feature Tiny/rất nhỏ, đã rõ yêu cầu → có thể gộp nhanh bước 1 (không cần hỏi thêm), nhưng vẫn giữ đủ checkpoint ở bước 4–5.
- Không có mã Jira (task nội bộ/ad-hoc) → bỏ qua phần fetch Jira ở bước 1 (vẫn tạo branch, đặt tên hợp lý) và bỏ qua comment Jira ở bước 5 (không có ticket để comment).
- Đã có branch/đã bắt đầu code từ trước khi gọi skill này → bắt đầu thẳng từ bước phù hợp (2, 3, 4, hoặc 5), không bắt ép chạy lại `/te-dev-start`.
- MR đã mở và đang chờ feedback → đó là phạm vi của `/te-dev-address-mr`, nằm ngoài vòng đời `cook-feature` (dùng riêng khi cần).
- Cần tài liệu review sâu cho reviewer (~15 phút hiểu hết feature) → có thể chèn thêm `/te-dev-branch-investigation` sau bước 3, trước bước 4 — không bắt buộc trong flow mặc định, chỉ dùng khi feature đủ phức tạp để cần.

## Lỗi hay gặp

- **Bỏ qua code review trước commit**: Bước 3 (risk-review) fail 🔴 nhưng vẫn commit/push. → Fix: bắt buộc fix tới pass 🟢 trước qua bước 4, không exception.
- **Code đủ 1 surface mà quên surface kia**: Feature cần cả in-app + storefront nhưng chỉ code 1 phía. → Fix: bước 2 kiểm tra `shopify-app/surfaces.md` TRƯỚC code, liệt kê tất cả cần cover.
  - **Transparency trap (multi-surface incomplete ship)**: Áp lực time, chỉ code app block, storefront "tương tự có thể chờ". Nhưng khi ship, user vào app block, không tìm thấy ở storefront → bug report (không phải design). → Fix: **nếu phải defer 1+ surface → ghi rõ "phase 2" trong PR description + commit message**, không dạng "chúng tôi đã code xong, chỉ là storefront không có". User/QA sẽ thấy nó là intentional defer, không missing feature. (RED baseline Scenario 2: agent shipped app block + storefront (bare integration) với explicit phase 2 defer cho admin dashboard.)
- **Checkpoint không xác nhận**: Bỏ qua hỏi xác nhận ở bước 4 (commit) + bước 5 (PR/comment Jira) → commit/push sai, phải revert. → Fix: **không skip** checkpoint dù nhỏ, luôn hỏi user xác nhận side-effect.
- **Quên cập nhật CLAUDE.md / docs**: Đã code xong, tạo PR nhưng bỏ qua phần "cập nhật tài liệu" ở bước 5. → Fix: bước 5 bắt buộc scan diff → rà soát có cần cập nhật tài liệu nào không.
- **Reuse code sai**: Dùng component/helper nhưng không check parameter/behavior match. → Fix: từ create-plan phải cụ thể → code phải kiểm tra thực tế.
- **Branch name sai rule**: Tạo branch không theo `feature/<JIRA>` hoặc `fix/<JIRA>`. → Fix: bước 1 `/te-dev-start` tự format, không tự đặt tên.

**Xem thêm:** `references/cook-feature-checklist.md` để chi tiết từng bước + checkpoint.
