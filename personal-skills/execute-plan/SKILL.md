---
name: execute-plan
description: Implement code grounded in every source that governs a task — Jira AC, a `<mã>-plan.md` (if one exists), OpenSpec specs/changes (if the repo uses OpenSpec), Figma design, the current codebase, and any AI-instruction .md files in the repo (CLAUDE.md/AGENTS.md/rules). For each unit of work it designs the interface first, writes the test first (TDD), then implements to pass it — continuously cross-checking against the sources and fixing drift immediately, and refusing to add any table/column/index/config the sources don't actually call for. Use when the user says "code task X", "implement theo plan này", "code đúng theo spec/design đi". Does NOT commit/push/open a PR (that's `cook-feature`/`te-dev-commit`/`te-dev-create-pr`) and does NOT itself produce a plan (that's `create-plan`) — it consumes whatever sources already exist and implements.
metadata:
  trigger: "user says 'code task X', 'implement task này', 'theo plan này mà code', 'code đúng spec/design' — muốn code chi tiết không phải tạo plan mới"
  model_hint: "main loop (Sonnet/Opus) — code chi tiết cần tư duy, TDD cần logic tốt"
  keywords: ["code", "implement", "task", "plan", "spec", "design"]
---

# Execute Plan

Code theo đúng những gì các nguồn đang nói, không phải theo trí nhớ/thói quen — và tự bắt lỗi lệch nguồn ngay trong lúc viết, không để tích lại "sửa sau".

## ⚠️ Framework Reminder

Implementation without verification breeds bugs. Execute systematically: [[framework_systematic_problem_solving]] —
- **TDD forces constraint discovery**: tests reveal interface limits and edge cases (input ranges, error paths) before implementation hides them. Don't skip TDD even if AC seems "complete"
- **Drift detection happens layer-by-layer**: code → design, backend logic → DB schema, API interface → frontend assumptions. Each unit checks its own layer before moving to the next
- **Measure completeness at the end**: does implemented code actually satisfy AC? Does it work across all layers (backend logic, DB, API, frontend)? Don't just count checkboxes

## Nguồn — dùng cái nào, lấy ở đâu

| Nguồn | Khi nào áp dụng | Cách lấy |
|---|---|---|
| Jira AC | có mã Jira | theo `plan-review-core` |
| `<mã Jira>-plan.md` | file đã tồn tại (đọc `~/.claude/.te-ai-config-memo` key `plan-workflow-output-dir`, hoặc hỏi nếu chưa có key) | `Read` thẳng, main loop — đây là tài liệu chính để bám theo, không giao subagent tóm lược |
| OpenSpec (`openspec/specs/`, `openspec/changes/`) | thư mục `openspec/` tồn tại ở root project hiện tại | `ls`/liệt kê tên các capability trong `openspec/specs/` trước, chỉ **mở file** của capability nào tên rõ ràng khớp scope đang làm — không mở file để "xem thử có liên quan không". Project chưa có `openspec/` → **không tự tạo mới** trừ khi user yêu cầu rõ trong prompt |
| Figma design | có link (Jira/user) | theo `plan-review-core` |
| Codebase hiện tại | luôn | theo `plan-review-core` (CodeGraph ưu tiên, Explore fallback) |
| File hướng dẫn AI trong repo | luôn | `CLAUDE.md`/`AGENTS.md` gần nhất theo cây thư mục của vùng code đang sửa + file rule cụ thể nó trỏ tới — `Read` thẳng, main loop (không qua subagent tóm tắt, dễ mất đúng câu chữ constraint) |

Thiếu nguồn nào (không có plan.md, không có OpenSpec, không có design) → bỏ qua nguồn đó, đừng suy diễn thay.

## Tiết kiệm token

Áp dụng nguyên tắc chung ở [`plan-review-core`](../plan-review-core/SKILL.md) (không fetch lại thứ đã biết trong phiên, fetch song song phần biết trước, subagent lo phần fetch/tóm tắt, main loop lo phần quyết định). Thêm riêng cho skill này:

- Đọc `plan.md` và file hướng dẫn AI **một lần** khi bắt đầu, giữ trong context suốt phiên — chỉ đọc lại nếu nghi ngờ nó đã đổi (user tự sửa giữa chừng, hoặc quay lại sau khi tạm dừng lâu).
- OpenSpec: chỉ mở đúng `specs/<capability>/spec.md` hoặc `changes/<id>/` khớp với tính năng đang code — không duyệt hết `openspec/specs/*`.
- Vòng tự đối chiếu (bên dưới) chỉ so với nguồn **áp dụng cho đúng phần vừa viết** — code UI thì so design+AC, code logic backend thì so AC+plan+convention — không lôi cả 6 nguồn ra so mỗi lần.

## Trình tự mỗi đơn vị việc: interface → test → code → đối chiếu

Chia việc theo đơn vị có ý nghĩa (1 file / 1 component / 1 endpoint — không nhỏ tới từng dòng, không lớn tới cả feature). Với **mỗi đơn vị**, đi đúng thứ tự sau — không nhảy thẳng vào viết implementation trước:

1. **Xác định interface trước.** Từ AC/plan/spec, chốt rõ hàm/method/endpoint sẽ cần: tên, input, output, side effect — **chưa viết logic bên trong**. Đây là lúc quyết định chữ ký hàm, không phải lúc code. Nếu có pattern/helper sẵn làm đúng việc này rồi → dùng lại, không thiết kế interface mới song song.
2. **Viết test trước (TDD).** Dùng đúng framework/vị trí test project đã có sẵn (check `package.json`/thư mục test hiện có — không tự chọn framework khác hay bịa ra nếu project chưa có test nào, lúc đó hỏi user trước). Test bám theo AC/plan/spec, gồm cả edge case đã nêu trong nguồn (vd giá trị âm, input rỗng). Test **sẽ fail** ở bước này — đúng như vậy, chưa có gì sai. Đơn vị không có logic để test thật (JSX thuần không nhánh, config tĩnh, migration chỉ đổi tên cột) → bỏ qua bước này, vẫn giữ bước 1.
3. **Implement để test pass.** Chỉ code đủ thoả interface + test đã viết ở trên, tái dùng pattern/helper có sẵn thay vì viết mới song song.
4. **Đối chiếu với nguồn liên quan tới đúng đơn vị đó** (không phải cả 6 nguồn mỗi lần):
   - **Lệch** (code khác AC/design/plan/OpenSpec spec/convention AI-instruction) → sửa ngay trước khi sang đơn vị tiếp theo. Không để lại "TODO check sau".
   - **Bản thân các nguồn mâu thuẫn nhau** (vd AC nói khác design, plan.md khác OpenSpec spec) → không tự chọn 1 bên rồi đi tiếp. Dừng lại, nêu rõ mâu thuẫn cụ thể, hỏi user ưu tiên nguồn nào trước khi code tiếp phần đó. Đang chạy trong ngữ cảnh không hỏi trực tiếp được (vd subagent không có tool hỏi) → **không tự implement phần đang mâu thuẫn**, trả mô tả mâu thuẫn lên cho nơi gọi mình quyết định, thay vì đoán đại 1 bên.
5. **Soát lại mọi thứ mới thêm trong đơn vị này có thật sự tối ưu không** (xem mục "Đánh giá tối ưu cho bảng/cột/index/config mới" ngay dưới) trước khi coi đơn vị là xong.

Sau khi xong toàn bộ scope: rà lại một lượt tổng — đối chiếu danh sách AC / mục trong plan.md / spec OpenSpec đã cover đủ chưa, không phải đọc lại từng dòng code đã tự đối chiếu ở trên rồi.

## Đánh giá tối ưu cho bảng/cột/index/config mới

Đây **không phải** kiểu tra "nguồn có ghi dòng nào yêu cầu đúng cái này không" — nhiều thứ hợp lý cần thêm mà không nguồn nào viết thẳng ra. Cách đánh giá đúng: **suy luận từ nhu cầu truy vấn/lưu trữ/vận hành thực sự mà các nguồn ngụ ý** (AC, plan, spec, cách UI/flow sẽ dùng dữ liệu này, quy mô dữ liệu nếu biết được) để tự quyết cái gì đáng thêm, cái gì là thói quen/phỏng đoán không cần thiết.

- **Index**: dựa vào các truy vấn (sort/filter/join) mà sources cho thấy **sẽ thực sự chạy** trong scope hiện tại — kể cả khi không câu nào nói thẳng "thêm index" — nếu suy luận ra được truy vấn đó chắc chắn xảy ra thì thêm index là tối ưu. Ngược lại, thêm vì "field kiểu timestamp/id thường hay được index" mà không có truy vấn cụ thể nào trong scope cần → đó là phỏng đoán, bỏ.
- **Bảng/cột mới**: đánh giá theo dữ liệu **thực sự cần lưu và cách nó sẽ được đọc/ghi** theo AC/plan/spec — không phải chỉ "có dòng nào nhắc tới field này chưa". Tách bảng/chuẩn hoá thêm chỉ hợp lý nếu quy mô/quan hệ dữ liệu theo nguồn thật sự cần — nếu chỉ là "để sau này mở rộng" khi chưa có tín hiệu nào cho thấy sẽ cần, đó là over-engineer, bỏ.
- Quyết định không rõ ràng (không chắc có nên thêm hay không dựa trên nguồn hiện có) → nêu rõ lý do cân nhắc và hỏi user, đừng tự chọn 1 bên rồi lờ đi — giống cách xử lý mâu thuẫn nguồn ở trên.

## Ranh giới

Chỉ lo phần **code + tự đối chiếu**. Không tự `git commit`/push/tạo MR — dừng lại và báo đã xong phần implement, để `cook-feature`/`te-dev-commit`/`te-dev-create-pr` tiếp quản phần đó. Không tự soạn `plan.md` mới nếu chưa có — nếu task chưa có plan và scope đủ lớn để cần 1 bản, gợi ý chạy `create-plan` trước, đừng tự bịa plan giữa chừng lúc code.

## Lỗi hay gặp

- **Code mà không TDD**: Viết code trước, không viết test. Sau khi code khó test lại vì không design interface rõ. → Fix: TDD bắt buộc — viết test trước, implement sau, không exception.
  - **Exception trap**: "AC đã specifies toàn bộ logic, không cần discover" — SAI. Kể cả AC rõ ràng, TDD vẫn bắt buộc vì test = verify interface + giới hạn (không phải để khám phá logic). Nếu AC phức tạp → TDD càng quan trọng.

- **Thêm field/index/config chưa có yêu cầu**: Tự suy diễn thêm vì "tốt cho sau này", nhưng AC/plan không có mention. → Fix: đánh giá theo nguyên tắc "suy luận thực tế" ở mục trên — nếu chưa có truy vấn/case cụ thể cần → không thêm.
  - **Pressure trap (schema)**: Under deadline, temptation to add "extensibility fields" (`validation_rules`, `synced_at`, cache columns) to look prepared. Boundary: **audit fields JUSTIFIED** (low risk, high support value); **extensibility fields DEFERRED** (require AC expansion to justify). Criterion: "Does AC or plan mention this behavior?" Yes → add; No → defer.

- **Lệch nguồn mà không sửa ngay**: Phát hiện code khác AC/design/plan nhưng để "sửa sau". Sau lại quên. → Fix: lệch nguồn = sửa **ngay lập tức** trước qua đơn vị tiếp theo, không "TODO".

- **Nguồn mâu thuẫn mà tự chọn 1 bên**: AC nói khác design, không hỏi user → tự pick 1 bên code xong. → Fix: dừng lại, nêu mâu thuẫn cụ thể, hỏi ưu tiên trước code, không tự đoán.

- **Tái dùng code sai pattern**: Dùng component/helper nhưng parameter/signature không match, hay đã deprecated. → Fix: từ create-plan phải cụ thể (tên + path) → code phải verify thực tế.

- **Quên check convention repo**: Code theo convention cũ hoặc convention khác. → Fix: read `CLAUDE.md` + file rule của repo **TRƯỚC** code, giữ trong context.

- **Logic nhiều chiều cấu hình (combinatorial) tự viết test cùng lượt với code → mù cùng một chỗ**: Field/tính năng có N chiều độc lập kết hợp nhau (vd 2 mode × 3 unit × 7 week × 2 range = 84 tổ hợp). Test viết ngay sau code, cùng một luồng suy nghĩ → dễ bỏ sót tổ hợp/biên. **Pressure: "AC specifies all 84 cases, just code them"** — sai. Viết test TRƯỚC không phải để discover, mà để verify interface & giới hạn. (Case thật: 9 lỗi interaction — rollover nửa đêm, unit vô tác dụng, range validate lệch, enum fallback — phải chạy code-review riêng mới bắt.)
  - **Fix**: Trước code, liệt kê ma trận tất cả chiều + case biên (rollover thời gian, giá trị ngoài dải, tổ hợp làm field vô tác dụng). Viết test từng ô/biên (không chỉ happy path). TDD không bỏ qua cho dù AC "đã specifies" — TDD = confidence, không = discovery. Độ phức tạp tổ hợp cao (>30 cases) → chủ động chạy `code-review` ngay sau xong, không chờ user.
  - **Time pressure trap**: "1 hour, 84 cases, no time for 84 tests" — hybrid là SAI nếu "skip test-first". Đúng hybrid: decision-table (5 min) + spot-check tests (15 min) + coverage matrix walk-through (5 min) = 25 min an toàn, không skip TDD.

**Xem thêm:** `references/execute-plan-tdd.md` để chi tiết TDD workflow + cách đánh giá tối ưu.
