---
name: review-plan
description: Review sâu 1 bản plan/kế hoạch triển khai TRƯỚC KHI code — đối chiếu với requirement Jira, design Figma (nếu có), và code hiện tại để đánh giá tính đầy đủ, khả thi, và an toàn/rủi ro trên mọi khía cạnh. Dùng khi user nói "review sâu plan này", "plan này ổn chưa", "check plan theo jira/design/code", "đánh giá kế hoạch trước khi implement". KHÁC te-dev-review-research (phản biện qua hỏi-đáp để dev TỰ NGHĨ RA giải pháp khi chưa có plan) và te-dev-branch-investigation (soát code ĐÃ VIẾT so với intent, không phải soát plan trước khi code).
---

# Review Plan (sâu, đối chiếu 3 nguồn)

Đóng vai **senior reviewer** chấm 1 bản plan trước khi bắt tay code: plan có phủ đủ requirement, có khớp design, có khả thi/an toàn với code hiện tại không. Không phải brainstorm cùng dev (đó là `te-dev-review-research`) — plan đã có sẵn, việc ở đây là **soi** nó.

## ⚠️ Framework Reminder

Plan review must verify across all system layers: [[framework_systematic_problem_solving]] —
- **Trace end-to-end before approving**: plan that works on paper may fail in practice. Verify proposed changes actually work with current architecture (backend logic, DB schema, API contracts, frontend assumptions)
- **Measure feasibility**: plan looks good doesn't mean "safe to code". Check: migration paths, breaking changes, data integrity risks, backwards compatibility — across all layers (backend → network → frontend)
- **Identify root assumptions**: every plan rests on 2-3 core assumptions (about perf, data structure, user flow). Verify each assumption is grounded in actual code/data, not wishful thinking

## Bước 0 — Nguyên tắc thu thập nguồn

Đọc [`~/.claude/skills/plan-review-core/SKILL.md`](../plan-review-core/SKILL.md) — áp dụng đúng quy tắc tiết kiệm token + cách thu thập Jira/design/code ở đó cho Bước 1-2 dưới đây. Không viết lại logic riêng.

## Bước 1 — Xác định input

Cần tối thiểu **plan** + **1 trong 2** (Jira hoặc code hiện tại để đối chiếu):

1. **Plan cần review**: plan đang có trong conversation (vd vừa thoát Plan Mode), hoặc file/đoạn text user dán. Không có sẵn → hỏi user paste hoặc chỉ đường dẫn file.
2. **Requirement**: mã Jira (vd `OPOS-13`) → dùng project key table, không hỏi lại nếu suy được từ mã. Không có mã → hỏi user có description/AC nào khác không; không có thì bỏ qua trục này và nói rõ trong output là review chỉ dựa vào code, không đối chiếu được requirement gốc.
3. **Design** (tuỳ chọn): link Figma nếu user đưa sẵn. Không hỏi ép buộc — chưa có thì để Bước 2 tự tìm trong Jira trước khi kết luận là "không có".

## Bước 2 — Thu thập 3 nguồn

Làm theo đúng **Cách thu thập (2 đợt)** trong `plan-review-core`: Jira + code-recon song song ở đợt 1, Figma ở đợt 2 nếu có link (từ user hoặc lộ ra trong Jira).

## Bước 3 — Đối chiếu & chấm theo từng trục (main loop, cần judgment)

Chỉ chấm trục có đủ input ở Bước 2; trục thiếu input → ghi rõ "không đánh giá được — thiếu <nguồn>" thay vì đoán.

- **Requirement coverage**: từng acceptance criteria của Jira có được plan cover không? Liệt kê AC nào plan **bỏ sót** hoặc **hiểu sai**.
- **Design fidelity** *(nếu có design)*: plan có đúng flow/state/component trong design không? Field/case nào design có mà plan thiếu?
- **Code feasibility & fit**: plan có khớp kiến trúc hiện tại không — có định viết lại thứ đã có sẵn (helper/module) không, có giả định sai về hệ thống hiện tại không, có chỗ nào code hiện tại **không cho phép** làm như plan đề xuất (constraint kỹ thuật, schema, quyền)?
- **Surface coverage** *(app OPTIS)*: đọc `shopify-app/surfaces.md` (resolve `<repo>` qua `~/.claude/.te-config-repo`) — feature thuộc "cả hai" (in-app + storefront) mà plan chỉ tính một phía → nêu lỗ hổng.
- **Safety & Risk**: liệt kê rủi ro theo mức **P0 (critical)/P1 (high)/P2 (medium)** — tập trung data integrity, migration không reversible, breaking API/contract, billing, webhook/sync, bảo mật (thiếu check quyền, input validation), race condition. Rủi ro phải gắn cụ thể vào **bước nào trong plan**, không nói chung chung.
- **Gaps / Open Questions**: điểm plan còn mơ hồ, chưa quyết (vd chưa nói rõ xử lý edge case nào) — liệt kê thành câu hỏi cụ thể cần làm rõ trước khi code, KHÔNG tự đoán rồi chấm hộ.

## Bước 3.5 — Adversarial verify (phản biện độc lập trước khi chốt verdict)

Mục đích: bắt sai sót trong CHÍNH kết luận ở Bước 3 trước khi đưa cho user — rẻ hơn nhiều so với để sai lọt tới lúc code xong mới phát hiện (xem thực tế đã xảy ra với `cook-task-gated`, task OPOS-176: lỗi bắt được ở bước code tốn hẳn 1 vòng code→test→fix→test lại, bắt sớm ở plan thì chỉ tốn sửa vài dòng plan).

**Nạp known-issues trước** (đóng vòng lặp — xem app từ prefix mã Jira: OPOS/OPOK→option, OPCS/OPSK→swatch, OPTCLT→comp):
```bash
python3 ~/Shopify/skill/personal-workspace/dev-journal/scripts/get-known-issues.py --app <ten-app>
```

**Model routing**: gọi `Agent(model: "haiku")` cho cả 2 lượt đầu (vai phản biện không cần model mạnh bằng vai viết plan/code) — agent nào tự báo "không chắc" thì gọi lại đúng agent đó 1 lần với `model: "sonnet"`.

Dùng `Agent` tool, gọi **2 agent độc lập song song** (1 message, nhiều tool call). Mỗi agent nhận: known-issues ở trên, AC gốc, plan đang review, và **verdict + nội dung chấm ở Bước 3** (không phải code — review-plan không có diff).

```
Prompt mỗi agent: "Lỗi đã từng gặp ở task trước (kiểm tra xem plan này có
lặp lại không): <dán output known-issues>. Đây là AC gốc: <dán AC>. Đây là
plan: <dán plan>. Đây là kết quả chấm plan này: <dán toàn bộ output Bước
3>. Hãy CỐ TÌNH tìm ra: (a) AC nào bị plan bỏ sót mà bước chấm trên cũng bỏ
sót theo, (b) giả định nào trong plan có vẻ hợp lý nhưng thực ra sai với
code/kiến trúc hiện tại mà bước chấm chưa chỉ ra, (c) rủi ro bước chấm đã
đánh giá THẤP hơn thực tế, (d) có khớp 1 trong các known-issues ở trên
không. Mặc định nghi ngờ cả plan lẫn bước chấm, không mặc định tin. Nếu
thật sự không tìm ra gì thêm, trả lời KHÔNG CÓ VẤN ĐỀ MỚI kèm lý do đã xem
đủ kỹ — nếu không đủ tự tin, nói rõ 'không chắc' thay vì cố kết luận.
NGÂN SÁCH TOOL-CALL: tối đa khoảng 4 lượt gọi tool (ít hơn bước verify code
vì không có diff thật để đọc). Tới giới hạn mà chưa đủ bằng chứng → dừng,
báo cần thêm gì.
GIỚI HẠN PHẠM VI: chỉ dựa vào AC/plan/kết quả chấm đã đưa — KHÔNG tự ý đọc
thêm code ngoài những gì cần để xác minh 1 claim cụ thể, KHÔNG spawn thêm
sub-agent nào khác, để tránh tốn token lạc đề."
```

- Finding mới, cụ thể (không phải lặp lại ý Bước 3) → **bổ sung vào output Bước 4** trước khi đưa cho user, không âm thầm sửa verdict mà không giải thích vì sao.
- Cả 2 "KHÔNG CÓ VẤN ĐỀ MỚI" → giữ nguyên verdict Bước 3, không cần nhắc tới bước này trong output (tránh làm báo cáo dài không cần thiết với case không có gì mới).
- Bỏ qua bước này khi: plan quá nhỏ/rõ ràng (vd chỉnh 1 dòng cấu hình, review-plan tự thấy không cần), hoặc user chỉ hỏi review nhanh không cần sâu — không áp dụng máy móc cho mọi plan.

## Bước 4 — Output

Mở đầu 1 dòng verdict: `🟢 Plan sẵn sàng` / `🟡 Cần bổ sung trước khi code` / `🔴 Có lỗ hổng nghiêm trọng — không nên code theo plan này`.

```
## Requirement coverage
- [Đủ/Thiếu/Không đánh giá được] <AC> — <ghi chú>

## Design fidelity        <!-- bỏ mục nếu không có design -->
- ...

## Code feasibility & fit
- ...

## Surface coverage        <!-- bỏ mục nếu không phải app OPTIS -->
- ...

## Safety & Risk
- [P0/P1/P2] <bước trong plan> — <rủi ro> — <vì sao>

## Gaps / Open Questions
1. ...
```

Mặc định trả **trong chat**, không tự ý xuất file `.md`. User muốn lưu lại (vd để gửi Lead) → đọc `~/.claude/.te-ai-config-memo` tìm key `plan-workflow-output-dir` (key dùng chung với `create-plan`/`fix-plan`, đã có sẵn thì dùng luôn); chưa có → hỏi thư mục rồi ghi/append vào file đó (tạo nếu chưa có, giữ nguyên key khác). Tên file: `<MÃ-JIRA hoặc brief>-plan-review.md` — **khác** file `<MÃ-JIRA>-plan.md` mà `create-plan`/`fix-plan` tạo (xem "tách bạch 2 loại tài liệu" trong `plan-review-core`: đây là bản REVIEW, được phép dùng ngôn ngữ chấm điểm/severity, không phải bản plan để code theo). Nếu file review đã tồn tại từ lần trước → **ghi đè bằng bản mới nhất**.
