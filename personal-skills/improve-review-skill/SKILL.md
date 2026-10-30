---
name: improve-review-skill
description: Kích hoạt khi user chỉ ra một case cụ thể mà skill review-code đã bỏ sót (bug lọt qua review, hoặc user hỏi kiểu "sao review không bắt được case này") và muốn cập nhật skill review-code để lần sau bắt được. KHÔNG dùng để review code thông thường — việc đó thuộc về skill review-code.
---

# Improve Review Skill

Vòng lặp tự cải thiện cho skill `review-code`: mỗi khi có 1 case cụ thể bị bỏ sót, phân tích nguyên nhân gốc rồi vá đúng chỗ trong `review-code`, không viết lại toàn bộ skill.

## ⚠️ Framework Reminder

Skill improvement requires measured analysis, not gut fixes: [[framework_systematic_problem_solving]] —
- **Understand the full failure context**: before fixing review-code, trace why it missed the bug (missing rule entirely? rule too narrow? different pattern?). Don't assume the fix
- **Measure impact of rule change**: new rule should catch the missed case AND not introduce new false positives. Test mentally against known-good code
- **Avoid tunnel vision on one case**: one skipped bug doesn't mean review-code is broken everywhere. Verify the root cause is actually in review-code's rules, not in how a specific caller used it

## Không phải lúc nào cũng dùng skill này

- Đây **không phải** skill review code. Nếu user muốn review 1 đoạn diff/code bình thường → dùng skill `review-code`, không chạy flow dưới đây.
- Chỉ chạy flow này khi user đưa ra **1 case cụ thể đã bị bỏ sót** (ví dụ: "review lúc nãy không phát hiện memory leak ở dòng X", "sao lỗi race condition này lọt qua review-code") và có ý muốn cập nhật skill để tránh lặp lại.

## Quy trình

### 1. Thu thập case cụ thể
Xác định rõ trước khi sửa bất cứ gì:
- Đoạn code/diff nào bị bỏ sót lỗi.
- Lỗi thực tế là gì (mô tả kỹ thuật chính xác, không chung chung).
- Vì sao review-code không bắt được: thiếu rule hoàn toàn, hay có rule nhưng diễn đạt mơ hồ/phạm vi hẹp không cover case này.

Nếu user mô tả chưa đủ để xác định nguyên nhân gốc, hỏi lại đúng điểm còn thiếu — đừng đoán rule để thêm.

### 2. Đọc toàn bộ skill review-code trước khi sửa
Luôn đọc lại **toàn bộ** nội dung hiện tại trước khi edit, để tránh thêm rule trùng lặp:
- `/home/bss-group-3775/.claude/skills/review-code/SKILL.md`
- Nếu SKILL.md có tham chiếu tới thư mục `references/` (vd. `references/checklist.md`), đọc luôn các file đó — rule cụ thể thường nên nằm ở đây thay vì SKILL.md.

Nếu `/home/bss-group-3775/.claude/skills/review-code/` chưa tồn tại tại thời điểm chạy, báo cho user biết và dừng lại (đợi skill đó được tạo trước) — không tự ý tạo mới file review-code.

### 3. Xác định nguyên nhân gốc (root cause)
So sánh case cụ thể với rule hiện có:
- **Thiếu rule hoàn toàn** → cần thêm rule mới.
- **Có rule nhưng mơ hồ/quá rộng** → cần làm rõ/thu hẹp đúng phần gây bỏ sót, không viết lại cả rule.
- **Có rule đúng nhưng case nằm ngoài phạm vi áp dụng** (vd. rule chỉ áp dụng cho 1 ngôn ngữ/pattern) → mở rộng phạm vi đúng mức, không mở rộng tràn lan.

### 4. Vá đúng chỗ, cụ thể, không phình to
- Viết rule **cụ thể, hành động được**, gắn với case thật (có thể kèm ví dụ code ngắn nếu giúp nhận diện case tương tự sau này).
- KHÔNG thêm rule chung chung dạng "hãy cẩn thận hơn với X" — phải nêu rõ dấu hiệu nhận biết + cách bắt.
- KHÔNG viết lại toàn bộ SKILL.md của review-code mỗi lần — chỉ chỉnh phần liên quan (thêm 1 mục checklist, sửa 1 câu mô tả rule, thêm 1 ví dụ).
- Nếu SKILL.md của review-code đã dài (checklist cồng kềnh, nhiều rule chi tiết), ưu tiên đẩy rule mới/chi tiết vào `references/checklist.md` (tạo file này trong thư mục review-code nếu chưa có) và chỉ để 1 dòng trỏ tới nó trong SKILL.md, giữ SKILL.md súc tích.
- Dùng tool Edit (không phải Write ghi đè toàn file) khi chỉnh sửa file đã tồn tại, để giữ nguyên phần còn lại.

### 5. Xác nhận sau khi sửa
- Đọc lại phần vừa sửa trong review-code để xác nhận rule mới xuất hiện đúng chỗ, không trùng rule cũ, không phá format frontmatter/YAML.
- Tóm tắt ngắn gọn cho user: đã thêm/sửa rule gì, ở file nào, vì sao (root cause), không cần hỏi lại xác nhận trừ khi case ban đầu chưa đủ rõ.

## Ranh giới

- Chỉ sửa file thuộc skill `review-code` (`SKILL.md` và `references/*.md` của nó). Không đụng tới skill khác.
- Không tự thêm rule mang tính suy đoán khi chưa có case cụ thể — skill này phản ứng theo bằng chứng thực tế (lỗi đã lọt), không phải brainstorm rule mới.
- Không review code trong skill này — nếu cần đánh giá code, chuyển sang skill `review-code` ([[review-code]] tại `/home/bss-group-3775/.claude/skills/review-code/SKILL.md`).
