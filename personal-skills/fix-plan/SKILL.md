---
name: fix-plan
description: Sửa 1 bản plan theo đúng findings từ `review-plan` — mỗi fix bám lại Jira/design/code hiện tại, rồi tự kiểm tra chéo để đảm bảo fix chỗ này không phá vỡ chỗ khác trong plan. Dùng khi user nói "fix plan theo review vừa rồi", "sửa plan theo mấy lỗi review-plan chỉ ra", "áp findings vào plan". Đây là sửa bản PLAN (văn bản) TRƯỚC KHI CODE — KHÔNG PHẢI sửa code đã viết (sửa code theo review MR/PR dùng `te-dev-address-mr`/`explain-and-fix-mr`).
---

# Fix Plan (áp findings review vào plan, kiểm tra chéo)

Input bắt buộc: **bản plan gốc** + **report của `review-plan`** (finding theo trục + P0/P1/P2 + Gaps/Open Questions). Thiếu 1 trong 2 → hỏi user (report có thể là output vừa chạy trong cùng phiên, hoặc user paste/chỉ file).

## ⚠️ Framework Reminder

Plan fixing is not just edits—it's re-verification across all layers: [[framework_systematic_problem_solving]] —
- **Fix ≠ acknowledge**: don't just rewrite the finding text. Verify the actual fix aligns with Jira AC, Figma design, and current code constraints across backend/DB/API/frontend
- **Cross-check after every change**: fixing one finding often cascades (e.g., adding a field triggers schema/permission/validation updates). Self-audit the full chain
- **Measure completeness**: after all finding-based fixes, independently scan AC sections to catch what review-plan missed. Don't inherit review's blind spots

## Bước 0 — Nguyên tắc thu thập nguồn

Đọc [`~/.claude/skills/plan-review-core/SKILL.md`](../plan-review-core/SKILL.md). Điểm quan trọng nhất ở skill này: **`review-plan` vừa chạy trong cùng phiên ngay trước đó** → dữ liệu Jira/design/code đã fetch còn nguyên trong context, **KHÔNG fetch lại**. Chỉ fetch thêm khi report đến từ phiên khác, hoặc cần verify 1 claim cụ thể mà report không nêu rõ.

## Bước 1 — Ưu tiên finding theo mức độ

Xử lý theo thứ tự: **P0 → P1 → P2 (Safety & Risk)**, song song với **Requirement coverage "Thiếu/Hiểu sai"** (giữ nguyên mức độ nghiêm trọng report gốc đã chấm, không tự hạ thấp), rồi tới **Gaps/Open Questions** thường.

## Bước 2 — Với từng finding: sửa đúng, bám nguồn, viết bằng ngôn ngữ PLAN

- Report đã chỉ rõ hành vi đúng phải là gì (vd "AC yêu cầu X, plan đang Y") → sửa thẳng theo đúng X, không tự nghĩ cách khác.
- Report chỉ nêu "thiếu Z" mà chưa nói cách làm cụ thể → tự đề xuất cách sửa dựa trên Jira/design/code, **đánh dấu rõ đây là đề xuất** (không phải yêu cầu trực tiếp từ report) để user biết chỗ nào cần soát kỹ hơn.
- Finding nằm ở mục "Không đánh giá được — thiếu <nguồn>" → nếu giờ đã có nguồn đó (user bổ sung) thì xử lý; chưa có → giữ nguyên trong Open Questions, không tự bịa để lấp.
- **Quan trọng — đọc kỹ, đây là lỗi hay gặp nhất**: mỗi finding sau khi sửa phải được **viết lại thành 1 câu build-plan** ("thêm X vào Y", "sửa Z để làm W"), gắn vào đúng khu vực tính năng liên quan trong plan (không phải 1 mục riêng đặt tên theo finding). **Cấm** mang nguyên các cụm ngôn ngữ review vào nội dung plan: "đã fix", "đã verify", "xác nhận qua đọc code", "vi phạm AC", nhãn `[P0]`/`[P1]`/`[P2]`, tiêu đề dạng "Gap N — <mô tả vấn đề>". Những cụm đó là ngôn ngữ của report `review-plan`, không phải ngôn ngữ của 1 bản plan để build theo — nếu thấy mình đang viết "hiện tại thiếu X" hay "code đang sai Y", hãy tự hỏi lại: "vậy cần LÀM GÌ?" và chỉ giữ câu trả lời đó trong plan.

## Bước 3 — Kiểm tra chéo (bắt buộc — đây là phần hay bị bỏ qua)

Sau khi sửa hết finding, đọc lại **toàn bộ plan đã sửa** (không chỉ phần vừa đổi), và với mỗi chỗ vừa sửa tự hỏi: "sửa chỗ này có làm sai/mâu thuẫn phần nào khác không?" Kiểm tra ở **3 tầng**, không chỉ tầng văn bản:

- **Trong văn bản plan:** Đổi 1 field/behaviour ở Frontend → có ảnh hưởng mô tả API contract/schema ở Backend không, và ngược lại. Đổi 1 giới hạn/rule (vd số ký tự, điều kiện cascade) → có chỗ khác trong plan còn giả định con số/rule cũ không. Thêm phần bị thiếu (vd thêm hẳn 1 feature bị bỏ sót) → có đụng Cross-cutting (pricing/plan-gating, surface coverage, permission) chưa cập nhật tương ứng không.
- **Đối chiếu lại với code thật:** con số/rule vừa chốt theo AC (vd giới hạn ký tự, tên field) có **khớp với constraint đã tồn tại sẵn trong code** (DTO validation, schema, giới hạn platform) không — đây là loại mâu thuẫn dễ bỏ sót nhất vì nó không nằm trong chính văn bản plan mà nằm giữa plan và code. Cần đọc trực tiếp file liên quan (không chỉ tin report gốc), đúng tinh thần "độ sâu verify theo mục đích" trong `plan-review-core`.
- **Đối chiếu MỌI endpoint/field/UI MỚI vừa được thêm vào lúc fix với pattern bảo vệ của sibling code hiện có** (auth/plan-gating, input validation, permission check) — 1 finding được fix xong thường kéo theo phải thêm hẳn 1 route/field mới (vd Gap yêu cầu thêm endpoint để test), và route/field mới đó dễ bị quên áp đúng guard mà các route/field tương tự đã có sẵn (vd toàn bộ route khác trong module đều check `resolveShopWithPlatinumPlan` nhưng route mới lại quên). Tự hỏi: "cái tôi vừa thêm có đi qua đúng lớp bảo vệ mà mọi thứ tương tự nó trong repo đang có không?"

Sửa theo finding A có tạo ra vi phạm AC/design mà finding khác **không** nhắc tới không (report review-plan không nhất thiết bắt hết mọi trường hợp) — phát hiện mâu thuẫn mới phát sinh do chính việc fix → sửa luôn trong vòng này (thêm vào Checklist ở Bước 4 kèm ghi chú "phát sinh khi cross-check"), không để lại cho vòng review sau — đây chính là yêu cầu "fix không được tạo lỗi mới".

## Bước 3.5 — Quét completeness độc lập (bắt buộc — đừng chỉ tin report là đủ)

**Report của `review-plan` không đảm bảo bắt hết mọi thứ ngay lần đầu** — độ sâu review tăng dần qua nhiều lượt soi, không phải 1 lần là exhaustive. `fix-plan` chỉ vá đúng những gì report liệt kê sẽ **kế thừa luôn điểm mù của report đó**. Trước khi coi bản fix là xong, tự làm 1 lượt quét nhanh (không phải review lại từ đầu, chỉ cần lướt) — điểm quan trọng nhất: **đọc lại toàn bộ mục lớn của Jira AC (theo từng heading/section), không chỉ những AC report đã chấm**, và tự hỏi mỗi mục: "mục này có được nhắc tới ở ĐÂU đó trong plan (kể cả phần không phải gap) không, hay hoàn toàn vắng mặt cả ở report lẫn ở plan?" Mục nào vắng mặt hoàn toàn (không phải "đã làm đúng nên không cần gap", mà là **chưa từng được ai kiểm tra**) → thêm vào Checklist với nhãn `[Phát hiện thêm — ngoài report gốc]`, xử lý như 1 finding thường (đề xuất cách sửa, đánh dấu rõ đây là đề xuất).

Quét này chỉ cần ở mức **section-level** (đủ AC lớn nào bị bỏ hoàn toàn), không cần đào sâu từng dòng — đào sâu là việc của `review-plan`, ở đây chỉ để bắt lỗ hổng dạng "cả report lẫn plan đều im lặng" trước khi giao lại cho user.

**Nếu bước này tìm thấy điều gì mới** → coi bản fix lần này **chưa hội tụ**, nói rõ với user trong output rằng bản fix vẫn có thứ mới ngoài report gốc, khuyến nghị chạy lại `review-plan` một vòng nữa (không tự nhận là "xong"). **Nếu không tìm thấy gì mới** → có thể nói rõ điều đó trong output, tăng độ tin cậy rằng vòng fix này đã ổn định.

## Bước 4 — Output: 2 phần TÁCH BIỆT, không trộn

**Phần A — Plan** (nội dung chính, đây là thứ dev đọc để code theo):

```markdown
# Plan — <mã Jira>: <tên feature>

<Toàn bộ plan, viết bằng ngôn ngữ build (xem Bước 2), tổ chức theo khu vực tính năng
— KHÔNG theo "Gap N"/finding, KHÔNG chứa nhãn P0/P1/P2, KHÔNG chữ "đã fix"/"đã verify".
Nếu plan gốc đã lỡ tổ chức theo Gap-N (vd do dev tự viết vậy), fix-plan vẫn PHẢI
tổ chức lại theo khu vực tính năng khi viết ra bản mới — không kế thừa cấu trúc audit
chỉ vì plan gốc có cấu trúc đó.>

## Quyết định đã chốt
<Các điểm trước đây là Open Question, giờ đã có quyết định — 1 câu mỗi điểm, không cần giải thích dài dòng như 1 lập luận review.>

## Việc nên làm thêm nếu tiện (không block)
<Nếu có.>
```

**Trước khi coi Phần A là xong — chống rớt nội dung khi viết lại gọn hơn**: việc chuyển từ giọng "Gap N/finding" sang giọng build (Bước 2) và tổ chức lại theo khu vực tính năng rất dễ **vô tình bỏ sót 1 câu hành động cụ thể** trong lúc gộp/rút gọn câu chữ (khác với Bước 3.5 — vốn chỉ bắt "cả section AC nào bị bỏ hoàn toàn", không bắt được kiểu mất mát này ở mức từng chi tiết nhỏ trong 1 section đã có mặt). Sau khi viết xong Phần A, đọc lại **song song** bản nháp mới với (a) bản plan trước khi viết lại và (b) từng dòng AC Jira thuộc các phần đã đụng tới — với mỗi câu hành động/chi tiết cụ thể ở 2 nguồn đó (không chỉ tiêu đề section), tự hỏi "câu này còn xuất hiện ở đâu đó trong bản mới không, hay đã biến mất khi mình rút gọn?" Mất 1 chi tiết nhỏ (1 biến template, 1 trạng thái UI, 1 empty-state...) dễ xảy ra hơn mất cả section, và cũng khó nhận ra hơn — nên đây là bước rà soát riêng, làm sau khi Phần A đã có bản nháp, không gộp chung với Bước 3.5.

**Phần B — Ghi chú xử lý** (chat only, KHÔNG lưu vào file plan — đây là vết tích audit, thuộc về file review nếu cần lưu):

```markdown
Trạng thái hội tụ: ✅ Không phát hiện gì mới ngoài report / ⚠️ Phát hiện thêm <N> điểm ngoài report gốc (Bước 3.5) — bản này CHƯA hội tụ

Checklist finding đã xử lý:
- [Đã áp dụng / Đề xuất mới / Cần user quyết / Phát hiện thêm ngoài report] <finding, ngắn gọn> → <đã sửa ở khu vực nào trong plan>

Điểm cần user quyết (không tự fix được):
<Finding mà 3 nguồn không đủ để tự chọn cách sửa — câu hỏi cụ thể.>
```

Kết thúc Phần B bằng gợi ý chạy lại `review-plan` — đổi giọng theo trạng thái hội tụ: **có phát hiện thêm** → khuyến nghị mạnh chạy lại trước khi đưa cho ai code; **không phát hiện gì mới** → hỏi nhẹ có muốn chạy thêm 1 vòng cho chắc không.

### Lưu file

Mặc định trả trong chat (cả 2 phần), không tự ý xuất file. User muốn lưu → đọc `~/.claude/.te-ai-config-memo` tìm key `plan-workflow-output-dir` (có sẵn thì dùng luôn, chưa có thì hỏi thư mục rồi ghi vào file đó, giữ nguyên key khác — dùng chung với `create-plan`).

- **Phần A** → ghi đè `<MÃ-JIRA>-plan.md` (file plan sạch, không đổi tên dù đã fix nhiều vòng).
- **Phần B** (nếu user muốn giữ vết tích) → append vào `<MÃ-JIRA>-plan-review.md` (file review của `review-plan`, không phải file plan) dưới 1 heading mới `## Fix áp dụng — <ngày>`; không tạo file thứ 3 riêng cho việc này.
