---
name: explain-and-fix-mr
description: Kích hoạt khi user muốn xử lý comment review của 1 MR trên GitLab và ĐỒNG THỜI hiểu code đang bị sửa trong lúc fix — không phải fix mù theo góp ý mà không rõ code cũ viết để làm gì. Đây là bản nâng cấp cá nhân của lệnh team /te-dev-address-mr, chèn thêm bước giải thích ngắn trước khi trình kế hoạch sửa. Dùng khi user nói "sửa review GitLab nhưng giải thích luôn", "fix comment MR + hiểu code", "address MR feedback có giải thích".
---

# Explain & Fix MR

Nâng cấp cá nhân của `/te-dev-address-mr` (`/home/bss-group-3775/Shopify/ai-config/dev/commands/te-dev-address-mr.md`):
giữ nguyên toàn bộ khung 6 bước (kéo comment → gom checklist → lập kế hoạch → chờ confirm →
sửa → commit), chỉ thêm 1 lớp **giải thích code hiện tại** ngay trong bước lập kế hoạch, để đọc
kế hoạch là hiểu luôn code cũ đang làm gì và tại sao sửa vậy — không cần hỏi lại, không cần
chạy riêng một lượt "explain" rồi mới fix.

Làm tuần tự, KHÔNG nhảy bước. **NEVER sửa code khi user chưa confirm kế hoạch ở Step 4.**

## ⚠️ Framework Reminder

Understanding before fixing prevents tunnel vision: [[framework_systematic_problem_solving]] —
- **Trace the whole execution path**: review comment points to one line; but fix must work across all callers/layers. Before proposing fix, trace how the code flows through backend/network/frontend
- **Verify root cause, not just symptom**: reviewer comment is a symptom. Understanding existing code first reveals whether fix addresses the root cause or just patches the surface
- **Measure fix impact**: proposed change should improve (correctness, performance, clarity, safety), not just satisfy the reviewer. Verify with data before confirming

> **CodeGraph:** nếu project có `.codegraph/`, dùng `codegraph_impact`/`codegraph_callers` khi
> phân tích để không sót caller bị ảnh hưởng. Diff/nội dung file vẫn lấy từ `git`/Read.

## Step 1: Tìm MR của branch

**[Model: Haiku — subagent]**

Dùng `Agent(model: "haiku")`: chạy `git branch --show-current` rồi `glab mr view --comments` để
lấy MR đang mở của branch hiện tại cùng toàn bộ comment/thread (author, file/line, nội dung,
trạng thái resolved/unresolved). Không có `glab`/không tìm thấy MR → hỏi user link MR hoặc nhờ
dán comment thủ công.

## Step 2: Gom feedback thành checklist

**[Model: Sonnet — subagent]**

Dùng `Agent(model: "sonnet")`, kèm dữ liệu comment từ Step 1: lập checklist, bỏ qua thread đã
resolved. Mỗi item gồm: nội dung góp ý tóm gọn + người comment, file/dòng liên quan, phân loại
(sửa code / hỏi lại reviewer / từ chối có lý do).

## Step 3: Giải thích code hiện tại rồi mới lập kế hoạch sửa (CHƯA sửa)

**[Model: Opus — main loop]**

Với mỗi item **sửa code**, đọc đúng vùng code liên quan (CodeGraph nếu có), rồi viết theo đúng
thứ tự sau — đây là điểm khác biệt so với `/te-dev-address-mr` gốc:

1. **Giải thích ngắn code hiện tại (2-4 câu, bắt buộc trước khi nói đến việc sửa):**
   đoạn code này tồn tại để làm gì, luồng chạy hiện tại ra sao (input → biến đổi → output ở mức
   ý nghĩa, không diễn giải lại syntax), và — nếu suy luận được — tại sao nó từng được viết như
   vậy. Đây là phần hay bị bỏ qua khi fix vội theo review: sửa xong mà không thực sự hiểu code
   cũ định làm gì thì dễ sửa sai chỗ hoặc phá hỏng ý đồ ban đầu.
2. **Đối chiếu với góp ý reviewer:** góp ý đó đúng vào điểm nào trong luồng vừa giải thích ở
   trên — nói rõ mối liên hệ, không tách rời hai phần.
3. **Kế hoạch sửa:** sửa file nào, vùng nào, cách sửa (tóm tắt, có thể nêu before/after ngắn),
   và phạm vi ảnh hưởng kéo theo (caller/chỗ liên quan cần sửa đồng bộ).

Với item **hỏi lại / từ chối** → soạn nội dung trả lời cho reviewer (không cần bước giải thích
code, không sửa code).

**Ràng buộc bắt buộc (khi lập kế hoạch và khi sửa ở Step 5):**

- Chỉ đụng đúng phần liên quan tới góp ý. **KHÔNG xoá/ghi đè/refactor code không liên quan.**
- **Giữ nguyên các thay đổi đã có** trên branch và code gốc — không làm mất code, không revert
  nhầm thứ người khác đã viết.
- Nghi ngờ một góp ý sẽ phá vỡ logic hiện có hoặc rủi ro mất code → nêu rõ trong kế hoạch để
  user quyết, đừng tự ý làm.
- Nếu phần giải thích code hiện tại phát hiện luồng phức tạp (>4-5 bước hoặc nhiều file), có
  thể chèn 1 sơ đồ mermaid ngắn (`sequenceDiagram`/`flowchart`) — chỉ khi thực sự cần, đừng vẽ
  cho có.

## Step 4: Trình kế hoạch & chờ confirm

**[Model: Opus — main loop]** _(tiếp tục từ Step 3)_

Hiển thị toàn bộ kế hoạch — mỗi item sửa code có đủ 3 phần (giải thích code cũ → liên hệ góp ý →
kế hoạch sửa), item chỉ trả lời reviewer thì hiện nội dung trả lời — rồi hỏi:

> Đã hiểu code + kế hoạch sửa như trên, ok chưa? Mình sửa nhé? (yes / chọn item / sửa lại kế hoạch)

User yêu cầu chỉnh → cập nhật kế hoạch rồi hỏi lại. **Chỉ sang Step 5 sau khi user confirm.**

## Step 5: Sửa theo kế hoạch đã duyệt

**[Model: Opus — main loop]**

Sau khi user confirm: `Edit` từng item đúng như kế hoạch — **KHÔNG `git add`**. Bám sát ràng
buộc ở Step 3 (chỉ đụng phần liên quan, không làm mất code khác). Ghi chú ngắn đã xử lý thế nào
cho mỗi item (để trả lời reviewer sau).

## Step 6: Commit

**[Model: Sonnet — main loop]**

Tạo commit theo đúng các bước của `/te-dev-commit` (format `<branch> (<type>) <subject>`, phân
tích intent, chọn type...). Vì user đã duyệt kế hoạch ở Step 4 nên **commit luôn, KHÔNG hỏi
lại**. Nhiều nhóm thay đổi không liên quan → tách commit như `/te-dev-commit` hướng dẫn.

Gợi ý cuối: `git push` để cập nhật MR; trả lời/resolve các thread tương ứng trên GitLab (có thể
dùng `glab mr note`). **Không** tự reply/resolve thread khi user chưa duyệt nội dung trả lời.

## Khi nào dùng lệnh gốc thay vì skill này

Nếu chỉ cần fix nhanh, đã quen thuộc sẵn đoạn code đó rồi (không cần giải thích lại), dùng thẳng
`/te-dev-address-mr` cho gọn — skill này thêm 1 bước giải thích nên kế hoạch sẽ dài hơn, đổi lại
là hiểu rõ code trước khi sửa.
