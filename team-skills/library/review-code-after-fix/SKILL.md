---
name: review-code-after-fix
description: Use when dev đã fix comment review và cần review vòng tiếp theo — "dev fix xong rồi, review lại", "review lần 2/vòng 2", "kiểm chứng dev fix đúng chưa", "review code sau khi fix comment", hoặc user đưa link Jira/MR kèm mốc comment của vòng trước. Không dùng cho lượt review đầu tiên của một MR.
---

# Review Code After Fix

## Overview

Review vòng N+1 của một MR: dev đã đọc comment vòng trước và báo "đã fix". Skill này làm **hai việc tách bạch**:

1. **Kiểm chứng lời khai** — từng comment vòng trước có thật sự được xử lý không, và xử lý đúng chỗ không.
2. **Soi code mới** — phần code dev vừa thêm/sửa để fix có sinh lỗi mới không.

**Nguyên tắc cốt lõi:**
1. **Lời khai không phải bằng chứng.** "đã fix" trong reply/commit message không tính. Mỗi verdict phải neo vào code hiện tại (`file:line`) hoặc kết quả một lệnh đã chạy.
2. **Không tự review lại từ đầu.** Việc soi code là của skill `review-code` — gọi nó với range được truyền vào, KHÔNG chép checklist/format sang đây.
3. **Quy trách nhiệm bằng đo, không bằng đoán.** Thấy test/build đỏ thì chạy lại ở commit mốc rồi trừ số, mới biết vòng này gây ra hay hỏng sẵn từ trước.
4. **Read-only trên code.** Được phép chạy build/test/cài deps trong worktree; TUYỆT ĐỐI không sửa code hộ dev.

## When to Use

- Dev reply "đã fix comment" trên MR/Jira và cần soi lại.
- User đưa link kèm mốc: `...?focusedCommentId=13787`, "review từ comment hôm 26/8", "sau vòng trước".
- Vòng thứ 3, 4… — mốc là comment gần nhất của reviewer, cách làm không đổi.

**Không dùng khi:** review lần đầu một MR (→ `review-code`), hoặc chỉ muốn kiểm tra 1 comment lẻ mà không cần bảng đối chiếu.

## ⚠️ Framework Reminder

Review-after-fix requires systematic verification, not trust: [[framework_systematic_problem_solving]] —
- **Verify with data, not words**: "đã fix" in commit message or reply is NOT proof. Mở code hiện tại, hoặc chạy lệnh để xác nhận
- **Measure regression across layers**: build/test/lint results từ HEAD và từ mốc trước; so số để xác định "do vòng này hay hỏng sẵn"
- **Trace impact of fix**: nếu fix phía này, quét các chỗ anh em (same pattern, same issue type) để đảm bảo không chỉ vá một lỗi mà bỏ sót các chỗ khác

## Workflow

### Bước 1 — Chốt mốc vòng trước và hai range

Xác định `$ROUND_BASE` = trạng thái code **tại thời điểm reviewer comment vòng trước**.

Nguồn mốc, theo thứ tự ưu tiên user đưa:
- **Link Jira có `focusedCommentId`** → Atlassian MCP `getJiraIssue` với `fields: ["comment", ...]`, lấy `created` của đúng comment đó (cloudId + project key lấy từ CLAUDE.md của team).
- **Link/số MR** → `glab api "projects/:id/merge_requests/<iid>/discussions"`, lấy `created_at` của note đầu tiên của reviewer.
- **Chỉ có tên branch** → hỏi user mốc; đừng tự đoán.

```bash
git fetch origin
MOC="2026-08-26T09:28:00+07:00"                                     # mốc comment vòng trước
ROUND_BASE=$(git log --before="$MOC" -1 --format=%H origin/<branch>)
HEAD=origin/<branch>
git log --since="$MOC" --date=iso --pretty='%h %ad %an %s' $HEAD    # đúng các commit cần soi
```

Chốt và **nói ra** hai range:
- `DELTA = $ROUND_BASE..$HEAD` — đối tượng chính của lượt này.
- `FULL = $(git merge-base $HEAD origin/master)..$HEAD` — chỉ dùng để đọc ngữ cảnh khi delta không đủ hiểu.

**Không có commit nào sau mốc** → dừng, báo user "dev chưa push gì sau comment". Đừng review lại code cũ.

**App nhiều repo** (api/cms/tae…): chạy Bước 1 cho **từng** repo. Repo không có commit sau mốc → ghi rõ trong report là "không đổi", đừng bỏ im lặng.

### Bước 2 — Dựng chỗ làm việc

Branch MR thường không được checkout ở clone chính → dùng skill **`create-worktree`** (đừng tự chế lệnh). Mặc định code-only; chỉ cài deps khi Bước 6 thực sự chạy.

Local branch trong worktree có thể **chậm nhiều commit** so với origin → luôn `git merge --ff-only origin/<branch>` rồi mới đọc. Kiểm tra `git status` trước.

### Bước 3 — Kéo toàn bộ yêu cầu của vòng trước

Yêu cầu nằm ở **hai nơi**, gom cả hai:

```bash
glab api "projects/:id/merge_requests/<iid>/discussions?per_page=100"
```

- Dùng endpoint **`discussions`** (không dùng `mr view --comments`): chỉ nó mới có `position.new_path`/`new_line` và ghép được cặp comment ↔ reply.
- Bỏ note có `system: true`.
- **KHÔNG lọc theo `resolved`.** Trường này team không dùng — thread đã được trả lời đầy đủ vẫn về `resolved=false`. Lọc theo nó là mất sạch thread.
- Comment trên **Jira** cũng là yêu cầu (thường là ý bổ sung sau khi comment MR). Kéo luôn các comment của reviewer sau mốc.
- Không có `glab` / không tìm được MR → hỏi user link hoặc nhờ dán comment. Đừng suy diễn từ commit message.

**Tách sub-point:** một comment nhiều gạch đầu dòng = **nhiều dòng verdict riêng**. Đây là chỗ hay lọt nhất — dev trả lời ý to, ý nhỏ chìm luôn.

### Bước 4 — Kiểm chứng từng dòng verdict (trái tim của skill)

Mỗi dòng nhận đúng một trạng thái:

| Verdict | Nghĩa |
|---|---|
| ✅ Đã fix | Code hiện tại đáp ứng, đã mở xem tận mắt |
| 🟡 Fix một phần | Làm ý chính, còn ý phụ/trường hợp khác chưa |
| 💬 Chỉ trả lời | Dev phản biện / defer sang phase khác, code không đổi |
| ❌ Bỏ sót | Không thấy dấu vết xử lý, cũng không thấy trả lời |
| ⚠️ Fix sai chỗ | Có sửa, nhưng không trúng thứ comment nói tới |

Luật kiểm chứng:

- **Neo vào hiện tại.** Mở file hiện tại ở `file:line`, hoặc dẫn kết quả lệnh. Commit message không phải bằng chứng.
- **Line number trong comment trỏ vào file CŨ.** File có thể đã bị move/cắt/đổi tên giữa hai vòng. Trước khi kết luận, giải mã dòng đó bằng `git show $ROUND_BASE:<path> | sed -n '<n-4>,<n+4>p'` để biết comment đang chỉ vào **cái gì**. Bỏ bước này là kết luận sai đối tượng.
- **Quét anh em cùng bệnh.** Comment chỉ ra một chỗ, nhưng bệnh thường có nhiều chỗ (nhiều key Redis cùng loại, nhiều query cùng thiếu scope). Grep pattern tương tự; nếu chỉ một chỗ được vá → verdict 🟡 kèm tên chỗ còn lại, không phải ✅.
- **Lời khai chạm ngoài repo đang đứng thì mở ra xem.** Dev khai "CMS đã debounce 3s/15s/100" → mở file CMS xác nhận con số. Khai "đã thêm command dedupe" → grep command đó. Khai đúng thì ghi ✅ kèm đường dẫn đã kiểm.
- **💬 không phải là lỗi.** Tóm lý lẽ của dev trong 1–2 câu, đánh dấu **"cần bạn quyết"**, và không tự kết luận thay reviewer.
- **Không sửa code.** Thấy chỗ chưa xong thì viết ra, không tự vá.

### Bước 5 — Soi code mới trong delta

Gọi skill **`review-code`** với range đã chốt: `$BASE = $ROUND_BASE`, `$HEAD = origin/<branch>`.

- **Không** định nghĩa lại checklist, surface tag, prompt reviewer hay format 5 nhịp ở đây — dùng nguyên của `review-code`.
- Fix chạm vùng code cũ mà delta không đủ ngữ cảnh → đọc thêm ở range `FULL` cho **đúng vùng đó**, nhưng chỉ raise lỗi thuộc delta. Ngoại lệ: lỗi cũ **bị fix mới kích hoạt** thì vẫn raise, nói rõ "code cũ, nhưng thay đổi vòng này làm nó chạm tới".

### Bước 6 — Kiểm chứng bằng thực thi + quy trách nhiệm

**Gate — chỉ chạy khi** delta chạm code chạy được (không phải chỉ doc/comment) **và** repo có script build/test. Không chạy thì nói thẳng trong report là đã bỏ qua và vì sao.

1. Ở `$HEAD`: chạy build → lint → test. Ghi số liệu thật.
2. **Có fail → phải đo ở mốc.** Dựng worktree tạm detached ở `$ROUND_BASE`, chạy đúng bộ lệnh đó, so số:

```bash
git worktree add --detach <tmp>/base $ROUND_BASE
ln -s <worktree-chính>/node_modules <tmp>/base/node_modules   # dùng lại deps, đừng cài 2 lần
# chạy cùng bộ test, so con số fail
git worktree remove --force <tmp>/base                        # LUÔN dọn
```

3. Chia kết quả làm hai nhóm trong report: **do vòng này** (chênh lệch) vs **hỏng sẵn từ trước** (có ở cả hai).
4. **Test vỡ chưa chắc code sai.** Nếu thứ vỡ là mock/spec cũ, tra API thật (typings trong `node_modules`, source thư viện) xem code production có đúng không, rồi mới kết luận "chỉ là nợ test" hay "bug thật".
5. Đọc config CI xem test có phải job **chặn merge** không — quyết định severity của nợ test (chặn merge = Critical, không thì Important).

`node_modules` của clone chính có thể **thiếu dependency mới của branch** → nếu import lỗi, cài deps thẳng trong worktree của branch.

### Bước 7 — Report (contract cố định, đúng thứ tự này)

1. **Worktree & phạm vi** — đường dẫn, repo nào có/không có commit sau mốc, danh sách commit trong delta.
2. **Bảng đối chiếu** — mỗi dòng: nguồn (thread id / Jira comment) · yêu cầu tóm gọn · verdict · bằng chứng. **Phải đủ mọi dòng, kể cả ✅**, để user không phải hỏi lại cái nào đã xong.
3. **Vấn đề mới** — theo format của `review-code` (5 nhịp, nhóm severity, nặng trước).
4. **Hỏng sẵn từ trước** — tách hẳn mục riêng, ghi rõ không do vòng này nhưng vẫn chặn MR nếu chặn.
5. **Đã verify** — build/lint/test kèm số liệu; những giả thuyết đã kiểm và loại.

Bảng đối chiếu **đứng trước** danh sách lỗi mới: câu hỏi đầu tiên của reviewer luôn là "nó fix chưa". Ghi cả điểm dev làm tốt, thật lòng, ngắn.

### Bước 7.5 — (TÙY CHỌN, có gate) Đăng kết quả vòng này lên MR
Sau khi trình Bảng đối chiếu + Vấn đề mới (Bước 7), **hỏi user** có muốn cập nhật lên MR không — đừng tự post. Nếu user đồng ý → theo `../review-code/post-to-mr.md`, xử lý theo verdict của **từng dòng** trong bảng đối chiếu (mỗi dòng đã neo về `discussion_id` nguồn từ Bước 3):

| Verdict dòng | Hành động trên MR |
|---|---|
| ✅ Đã fix | **Resolve** thread cũ (`PUT discussions/<id>?resolved=true`). Kèm reply một câu xác nhận nếu muốn để lại dấu vết. |
| 🟡 một phần / ❌ bỏ sót / ⚠️ sai chỗ | **Reply vào chính thread cũ** (`POST discussions/<id>/notes`), nêu rõ còn tồn đọng gì. **Không** tạo thread mới, **không** resolve. |
| 💬 chỉ trả lời | Để user quyết — mặc định không đụng (không resolve, không reply hộ). |
| Vấn đề **mới** (mục "Vấn đề mới") | Tạo **thread mới neo dòng** như review lần đầu (Bước 5.7 của `review-code`). |

- App nhiều repo: xử lý từng repo với đúng MR của nó. Repo không có commit sau mốc thì không có gì để post.
- Xong → **báo cáo lại**: đã resolve thread nào, reply thread nào, tạo mới thread nào + link MR (contract trong `post-to-mr.md`).

### Bước 8 — Đúc tri thức app

Áp dụng Bước 5.6 của `review-code` (ghi `apps/<app>.md` ở working tree, **không** `git add`). Vòng re-review hay lộ thêm tri thức bền vững mà vòng đầu không thấy: CI có job nào chặn merge, deploy có tự chạy migration không, quy ước thư mục suy từ file anh em, bẫy tái diễn vừa phát hiện.

## Quick Reference

| Việc | Cách |
|---|---|
| Mốc vòng trước | Jira `focusedCommentId` → `created`; hoặc note đầu của reviewer trong `discussions` |
| `$ROUND_BASE` | `git log --before="$MOC" -1 --format=%H origin/<branch>` |
| Range chính | `$ROUND_BASE..origin/<branch>` (KHÔNG phải merge-base) |
| Kéo comment | `glab api "projects/:id/merge_requests/<iid>/discussions?per_page=100"` + comment Jira sau mốc |
| Lọc resolved | KHÔNG lọc — team không dùng trường này |
| Verdict | ✅ đã fix · 🟡 một phần · 💬 chỉ trả lời · ❌ bỏ sót · ⚠️ sai chỗ |
| Soi code mới | Gọi `review-code` với range truyền vào |
| Đăng lên MR | Bước 7.5 — TÙY CHỌN, hỏi trước: ✅→resolve · 🟡/❌/⚠️→reply thread cũ · mới→thread mới. Cơ chế: `../review-code/post-to-mr.md` |
| Quy trách nhiệm regression | Chạy cùng bộ test ở `$HEAD` và `$ROUND_BASE`, trừ số |
| Chỗ làm việc | Skill `create-worktree`; ff-only về origin trước khi đọc |

## Common Mistakes

- **Tin chữ "đã fix"** — reply và commit message không phải bằng chứng. Mở code hiện tại, hoặc chạy lệnh.
- **Lọc thread theo `resolved`** → mất sạch, vì team này không set. Lấy hết rồi tự đối chiếu.
- **Nuốt sub-point** — comment 3 gạch đầu dòng, dev trả lời 1, verdict ghi ✅. Tách mỗi ý một dòng ngay từ Bước 3.
- **Coi "trả lời" là "đã sửa"** — phản biện/defer là 💬 kèm "cần bạn quyết", không phải ✅.
- **Fix đúng loại nhưng sai đối tượng mà vẫn cho ✅** — comment nói "key này không có TTL", dev vá key hàng xóm. Luôn quét anh em cùng bệnh trước khi chốt.
- **Đọc line number của comment theo file hiện tại** → chỉ vào nhầm code, vì file đã move/cắt giữa hai vòng. Giải mã bằng `git show $ROUND_BASE:<path>`.
- **Lấy merge-base làm base** → kéo cả code vòng trước vào, không tách nổi "lỗi mới" khỏi "lỗi cũ đã comment rồi".
- **Kết luận "vòng này làm vỡ test" mà chưa chạy ở mốc** → rất hay oan; branch có thể đã đỏ sẵn từ commit merge master.
- **Kết luận "code sai" khi chỉ mock cũ không khớp** → tra API thật trong typings/source trước; phân biệt nợ test với bug production.
- **Quên dọn worktree tạm** ở Bước 6 → rác đĩa, `git worktree list` bẩn.
- **Đăng lên MR mà tạo thread mới cho điểm tồn đọng / quên resolve điểm đã fix** → sai contract Bước 7.5. ✅→resolve thread cũ, 🟡/❌/⚠️→reply chính thread cũ, chỉ vấn đề MỚI mới mở thread mới. Và luôn hỏi user trước khi post.
- **Chép checklist/format của `review-code` sang đây** → hai bản trôi lệch. Gọi skill đó, đừng nhân bản nó.
- **Tự sửa code hộ dev** → skill này chỉ kết luận và báo cáo. Sửa là việc của dev ở vòng sau.
- **Report chỉ có danh sách lỗi mới, không có bảng đối chiếu** → hụt đúng thứ reviewer cần nhất.

## Ranh giới

- **`review-code`** — lượt review đầu của một MR, và là nơi duy nhất định nghĩa checklist/surface tag/format lỗi. Skill này *gọi* nó.
- **`improve-review-skill`** — cải thiện chính cơ chế review, chỉ khi user gọi.
- **`create-worktree`** — dựng chỗ làm việc; đừng viết lại lệnh `git worktree` ở đây.
