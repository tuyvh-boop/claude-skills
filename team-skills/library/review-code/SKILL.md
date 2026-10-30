---
name: review-code
description: Use when reviewing code before merging, after finishing a task/feature, or when the user says "review code", "review app X", "soi code này", "review giúp mình". Dispatches a fresh-context reviewer subagent, scoped to only the surfaces the diff actually touches, with layered checklists (base + Shopify + per-app).
---

# Review Code

## Overview

Chạy một lượt code review bằng **subagent context sạch** review đúng phần diff giữa 2 commit, với **checklist xếp lớp** và **chỉ soi những bề mặt diff thực sự động tới**.

**Nguyên tắc cốt lõi:**
1. **Tách cơ chế khỏi tiêu chí.** Cơ chế review (range diff → subagent → phân tier feedback) là một; tiêu chí (soi cái gì) xếp lớp.
2. **Checklist cộng dồn:** `base` (luôn) + `shopify-app` (nếu là shopify app) + `apps/<app>` (nếu biết app đó).
3. **Relevance theo bề mặt bị chạm, KHÔNG theo kích thước diff.** Diff không đụng DB → không soi tiêu chuẩn DB. Nhưng chạm 1 dòng query mà sai vẫn là lỗi nặng.

⚠️ **Framework Reminder:** Áp dụng [[framework_systematic_problem_solving]] — khi review phát hiện vấn đề, đảm bảo:
- Đo lường impact thực tế (không assume): 2s backend > 200ms frontend
- Kiểm tất cả layer (logic, DB, API, UI, network) nếu có liên quan
- Tìm root cause, không chỉ triệu chứng
- Giải thích WHY, không chỉ WHAT

## Workflow

### Bước 1 — Chốt code MR mới nhất trên origin (nguồn sự thật)
**Nguyên tắc: luôn review trên code MR mới nhất đã đẩy lên `origin`, KHÔNG review working tree đang sửa dở** — working tree dở chưa phản ánh đúng MR.

```bash
git fetch origin                          # BẮT BUỘC — kéo trạng thái remote mới nhất
git rev-parse --abbrev-ref HEAD           # tên branch MR hiện tại
git status --porcelain                    # rỗng = working tree sạch; có dòng = đang sửa
git rev-parse --verify origin/<branch>    # xác nhận branch đã được push (có ref remote)
```

Chọn nhánh xử lý theo trạng thái working tree:

- **Sạch** (`git status --porcelain` rỗng): `git pull --ff-only` để local khớp origin, rồi review. Nếu không ff được (đã diverge) → báo user, đừng ép.
- **Đang sửa** (có thay đổi chưa commit/push): **KHÔNG `git pull`** (sẽ đè/xung đột) và **KHÔNG lấy working tree làm đối tượng review** — nó không phản ánh MR trên origin. Review **thẳng trên ref remote** `origin/<branch>` (read-only, không đụng file local) và **báo rõ** cho user là các sửa đổi chưa push đang bị loại khỏi lượt review. Nếu user muốn review đúng phần đang sửa → bảo họ commit & push lên MR trước.
- **Branch chưa push** (không có `origin/<branch>`): không có MR để review → dừng, báo user push trước.

Range diff = từ điểm rẽ nhánh tới đầu MR trên origin:
```bash
BASE=$(git merge-base origin/<branch> origin/master)   # điểm rẽ nhánh
HEAD=origin/<branch>                                    # đầu MR trên origin
```
Xác nhận branch/target với user nếu mơ hồ (không phải MR nào cũng nhắm `master`).

**Range truyền từ ngoài vào:** nếu caller (user, hoặc skill khác — vd `review-code-after-fix` chỉ muốn soi phần code phát sinh sau vòng review trước) đã chốt sẵn `$BASE`, thì **dùng đúng `$BASE` đó**, không tự tính lại `merge-base`. `$HEAD` vẫn là `origin/<branch>` và mọi bước còn lại giữ nguyên. Ghi rõ trong report là đang chấm trên range nào, để người đọc không tưởng đây là review cả MR.

### Bước 2 — Scoping pre-pass (chốt bề mặt bị chạm)
Đọc **danh sách file + diff** trong range, phân loại thành các *bề mặt*:

```bash
git diff --stat $BASE..$HEAD      # $BASE, $HEAD = origin refs từ Bước 1
git diff $BASE..$HEAD
```

Gán mỗi thay đổi vào một hoặc nhiều **surface tag** (từ vựng cố định):

| Surface tag | Kích hoạt khi diff động tới |
|---|---|
| `logic` | Bất kỳ thay đổi logic/nhánh/tính toán |
| `db-query` | Query, ORM/query builder, repository, raw SQL |
| `db-schema` | Migration, schema, entity/model definition |
| `api-endpoint` | Route/controller/handler HTTP mới hoặc đổi |
| `external-call` | Gọi API bên thứ 3 (gồm Shopify Admin API) |
| `auth` | Xác thực, phân quyền, session, token |
| `webhook` | Handler/đăng ký webhook |
| `ui` | Component/template/view |
| `async` | Job nền, queue, concurrency, shared state |
| `config` | Env, config, secret, dependency |
| `structure` | Thêm/xoá/đổi tên/di chuyển file, thêm module/folder mới, đổi ranh giới module (kích hoạt soi naming, coupling, vị trí file/folder theo quy ước repo) |
| `test` | File test |

Ghi ra danh sách surface đã chạm. **Bề mặt không có trong danh sách = section tương ứng bị bỏ qua hoàn toàn.**

### Bước 3 — Chọn app profile (routing)
- User nói thẳng "review app X" → nạp `apps/<X>.md`.
- Tự suy: có `shopify.app.toml` hoặc dep `@shopify/*` trong repo → bật lớp shopify. Map thư mục repo → file trong `apps/` nếu có.
- Không match app nào → chạy `base` (+ `shopify-app` nếu là shopify app). Đừng bịa profile.

### Bước 4 — Ghép checklist theo lớp + theo surface
Xây checklist cho lượt này = ghép các mục **có `Áp dụng khi:` khớp surface đã chạm ở Bước 2**, từ các file:
1. `checklists/base.md` (luôn)
2. `checklists/shopify-app.md` (nếu là shopify app)
3. `apps/<app>.md` (nếu có profile)

Bỏ mọi mục mà predicate không khớp. Không nhồi cả file vào prompt.

### Bước 5 — Bung reviewer subagent
Dùng Agent tool (general-purpose, read-only) với template `code-reviewer.md`, điền:
- Mô tả việc đã làm + mục tiêu của diff (lấy từ task/Jira/lời user).
- Range: `$BASE` (merge-base) .. `$HEAD` (`origin/<branch>` — đầu MR trên origin).
- **Checklist đã lọc** ở Bước 4.
- **Danh sách surface bị chạm** + luật chống nhiễu (chỉ review đúng bề mặt này).

**[Model: sonnet — subagent]** cho diff thường; diff lớn/nhạy cảm cân nhắc `opus`.

### Bước 5.5 — Trình kết quả cho user (dễ hiểu, không dump nguyên văn)
Subagent trả kết quả về **luồng chính**; **đừng paste nguyên si** ra cho user. Luồng chính biên tập lại thành báo cáo người đọc hiểu ngay mà không phải mở file đoán:

- **Mỗi Critical/Important viết theo 5 nhịp** của `code-reviewer.md` (Là gì → Vì sao sai + truy vết giá trị → **trích code thật** → kịch bản vỡ → sửa). Đây là thứ làm report "dễ đọc" thay vì một danh sách `file:line` khô khan.
- **Giải thích thuật ngữ ngay lần đầu** (LCP, CLS, hydration, no-op…) — người đọc có thể không rành mảng đó.
- **Nhóm theo severity, xếp nặng trước.** Minor gộp 1 dòng/mục.
- **Có Verified-clean** (đã kiểm & loại) để khỏi bị hỏi lại.
- Nếu user hỏi sâu 1 mục → bung đúng mục đó chi tiết hơn (thêm code xung quanh, ví dụ ngôn ngữ/route khác cùng pattern), vẫn giữ giọng thẳng, cụ thể.

> Thước đo: user đọc xong **không phải hỏi "chỗ này nghĩa là gì"**. Nếu phải giải thích lại sau khi trình, tức là report đầu ra chưa đạt.

### Bước 5.6 — Tự đúc & cập nhật `apps/<app>.md` sau mỗi lượt review (working tree)
Sau khi có kết quả review, **luôn** chắt lọc hiểu biết bền vững về app rồi ghi/cập nhật `apps/<app>.md`. Chưa có file → **tạo từ `apps/_template.md`**. Ghi vào **repo gốc** (`readlink -f ~/.claude/skills/review-code`), **chỉ chạm working tree** — TUYỆT ĐỐI không `git add`, không commit. **`git add` của user là cửa xác nhận duy nhất** — nên bước này viết đề xuất vào working tree rồi báo, không hỏi chặn.

**Nguồn tri thức để đúc (cả 2 loại đều ghi):**
1. **User chủ động cung cấp** giữa lúc review — quy ước bắt buộc, kiến trúc/luồng, vùng nóng, chỗ "đừng đụng", cách tra tài liệu riêng của app.
2. **Tự đúc từ chính lượt review này** — kiến trúc/luồng reviewer đã dựng được khi đọc code, quy ước suy ra từ **file anh em** (naming, vị trí file/folder lặp lại), vùng nóng vừa đụng, **bẫy tái diễn** vừa phát hiện.

**Kỷ luật (git-add là bộ lọc, KHÔNG phải giấy phép đổ rác — profile phải sạch):**
- **Đọc file hiện tại trước khi ghi.** Mỗi lượt chỉ thêm cái **mới so với những gì file đã có**; **ưu tiên siết/gộp mục sẵn có** hơn chồng thêm mục trùng.
- **Ghi pattern/luật, KHÔNG ghi nhật ký sự cố** — theo schema `_template.md`, route vào đúng mục (Kiến trúc / Quy ước bắt buộc / Vùng nóng / Bẫy tái diễn / Trọng tâm / Không áp dụng). Gắn `Áp dụng khi: <surface>` cho mục cần. ✅ "mọi query option phải scope `shop_id`; hay quên ở tầng service" ❌ "hôm nay bug ở OptionService dòng 42".
- **Chỉ ghi thứ bền vững, tái dùng được** cho review sau. Chi tiết đúng-một-lần (bug lẻ, câu hỏi một lần) → bỏ.
- **Tách FACT khỏi suy luận.** Điều thấy tận mắt trong code → ghi thẳng. Điều **suy ra** (quy ước đoán từ file anh em) → phrase rõ là quan sát ("theo các route cùng thư mục…"), đừng khẳng định như luật đã chốt. KHÔNG ghi "biết đâu sau này cần".

**Báo lại gọn:** đã thêm/sửa **mục nào ở file nào, nội dung gì**; nhắc user xem `git diff` rồi `git add` nếu hợp lý (không hợp thì `git checkout -- <file>` để bỏ).

> Ranh giới với `improve-review-skill`: bước này lo **tri thức về app** và chạy **tự động mỗi lượt** (cửa xác nhận = `git add`). Còn **cải thiện chính cơ chế review** (sửa `checklists/base|shopify-app.md`, prompt reviewer, scoping/surface tag) vẫn thuộc `improve-review-skill`, **chỉ khi user gọi** và cần confirm trước khi ghi. Đừng gộp hai việc.

### Bước 5.7 — (TÙY CHỌN, có gate) Đăng feedback lên MR dưới dạng thread resolvable
Sau khi trình kết quả (Bước 5.5), **hỏi user** có muốn comment các điểm lên MR không — **đừng tự post**. Nếu user đồng ý → làm theo `post-to-mr.md`:
- Mỗi Critical/Important/Minor đã trình = **một thread neo đúng `file:line`** (line-anchored, resolvable). Không neo được dòng (dòng ngoài diff) → fallback thread MR thường, vẫn resolvable.
- Body giữ nguyên format đã trình cho user (emoji severity + tiêu đề + vì sao + sửa gọn).
- **App nhiều repo** (cms/tae…): finding của repo nào post vào MR repo đó. Không suy ra được số MR → hỏi user (chi tiết trong `post-to-mr.md`).
- Xong → **báo cáo lại** đã tạo thread nào + link MR (contract trong `post-to-mr.md`).

### Bước 6 — Xử lý feedback (port từ receiving-code-review)
1. **READ** hết feedback, chưa phản ứng.
2. **UNDERSTAND** — nói lại yêu cầu bằng lời mình.
3. **VERIFY** với codebase thực tế.
4. **EVALUATE** đúng ngữ cảnh của mình.
5. **RESPOND** bằng lý lẽ kỹ thuật, không lời khách sáo.
6. **IMPLEMENT** từng item một, test từng cái.

Ưu tiên: **Critical** sửa ngay → **Important** xử lý trước khi đi tiếp → **Minor** ghi lại. Được phép **phản biện** reviewer bằng bằng chứng (YAGNI, phá tính năng đang chạy, sai ngữ cảnh) — "technical correctness over social comfort". Không nói "You're absolutely right"; sai thì sửa, đúng thì nêu lý do.

### Sau review — cải thiện CƠ CHẾ review (TÙY CHỌN, KHÔNG tự chạy)
Việc **cập nhật tri thức app** (`apps/<app>.md`) đã tự động ở Bước 5.6 (working tree, user tự `git add`). Riêng việc **rút kinh nghiệm về chính cách review** — bỏ sót loại lỗi, báo nhiễu, sửa `checklists/base|shopify-app.md`, prompt reviewer, scoping/surface tag — thì **KHÔNG** tự chạy sau mỗi lượt (phiền).

Khi user **chủ động** muốn cải thiện cơ chế review → dùng skill riêng **`improve-review-skill`**: tự soi lượt review, đề xuất, **chờ confirm**, rồi ghi vào repo gốc.

## Quick Reference

| Việc | Cách |
|---|---|
| Nguồn code review | `origin/<branch>` (MR mới nhất). Working tree sạch → `git pull --ff-only`; đang sửa → review thẳng ref remote, KHÔNG dùng local dở |
| Range diff | `git merge-base origin/<branch> origin/master` .. `origin/<branch>`; caller truyền sẵn `$BASE` thì dùng đúng cái đó |
| Bề mặt bị chạm | Bước 2, gán surface tag |
| Lớp checklist | base (+shopify) (+app), lọc theo surface |
| Reviewer | subagent read-only, template `code-reviewer.md` |
| Trình kết quả | Bước 5.5 — biên tập lại, Critical/Important theo 5 nhịp + trích code, không dump nguyên văn |
| Đăng lên MR | Bước 5.7 — TÙY CHỌN, hỏi user trước; thread neo dòng resolvable theo `post-to-mr.md`, xong báo cáo link |
| Cập nhật profile app | Bước 5.6 — **tự động mỗi lượt**, đúc từ (info user cung cấp + tự học từ review) vào `apps/<app>.md` (working tree), user tự `git add` |
| Cải thiện cơ chế review | TÙY CHỌN, chỉ khi user gọi → skill `improve-review-skill` |

## Common Mistakes

- **Soi thừa bề mặt không bị chạm** → nhiễu. Section chỉ chạy khi surface khớp (Bước 2 + `Áp dụng khi:`).
- **Đòi thêm thứ ngoài mục tiêu diff** (thêm test cho code không đổi, refactor lạc đề) → vi phạm scope. Review diff theo đúng ý định của nó.
- **Nhét cả file checklist vào prompt** → tốn token + reviewer lan man. Lọc trước ở Bước 4.
- **Bỏ qua lỗi nặng vì "diff nhỏ"** → relevance theo *bề mặt*, không theo *kích thước*. Chạm query mà thiếu shop-scoping vẫn Critical.
- **Chỉ soi Web Vitals khi task tên là "fix LCP/CLS"** → sai. Section *Core Web Vitals* trong `checklists/shopify-app.md` gate theo surface `ui`, nên **task feature bình thường** (thêm banner/ảnh/loading gate/dep) cũng phải soi. Và fix 1 chỉ số thì đòi số đo của **cả** LCP + CLS — hai cái kéo nhau.
- **Trình report kiểu danh sách `file:line` khô khan / dump nguyên văn subagent** → user không hiểu, phải hỏi lại từng cái. Critical/Important phải theo 5 nhịp có trích code (Bước 5.5). Thước đo: đọc xong không phải hỏi "chỗ này nghĩa là gì".
- **Xổ thuật ngữ không giải thích** (LCP/CLS/hydration/no-op) → viết cho dev tầm trung, giải thích ngay lần đầu.
- **Review inline thay vì subagent** → mất tính khách quan + ngốn context luồng chính.
- **Tự post feedback lên MR khi chưa hỏi user** → Bước 5.7 có gate, luôn hỏi trước. Và phải dùng endpoint `discussions` (resolvable), không phải `glab mr note` (comment thường). Chi tiết ở `post-to-mr.md`.
- **Review working tree đang sửa dở như thể là MR** → sai nguồn sự thật. Luôn `git fetch` rồi chấm trên `origin/<branch>`. Sạch thì `git pull --ff-only`; đang sửa thì review ref remote & báo user phần chưa push bị loại (hoặc bảo họ push trước).
- **Quên `git fetch` trước khi lấy range** → chấm trên `origin/<branch>` cũ, bỏ sót commit mới nhất của MR.
- **Bịa "chuẩn naming/thư mục lý tưởng" rồi bắt lỗi** → naming, vị trí file/folder, coupling phải chấm theo **quy ước của chính repo** (surface `structure`; đối chiếu `apps/<app>.md` hoặc suy từ file anh em). Repo không có quy ước rõ thì đừng raise.
- **Nâng mọi mùi bảo trì lên Critical/Important** → trùng lặp/coupling/naming mặc định Minor; chỉ nặng khi đã gây bug, phá quy ước đã ghi, hoặc shotgun surgery cắn ngay diff kế tiếp.
- **`git add`/commit hộ user khi auto ghi info app** → sai. Bước 5.6 chỉ chạm working tree + báo; user tự stage. Đó là cửa xác nhận.
- **Đổ nhật ký sự cố / info dùng-một-lần / suy diễn vô căn cứ vào profile** → `git add` là bộ lọc, KHÔNG phải giấy phép đổ rác. Bước 5.6 chỉ ghi **pattern bền vững**, đọc file trước để siết mục sẵn có thay vì chồng trùng, và **tách FACT khỏi suy luận** (quy ước đoán từ file anh em phải phrase là quan sát, đừng khẳng định như luật đã chốt).
- **Dùng skill này cho lượt review SAU KHI dev đã fix comment vòng trước** → thiếu hẳn phần kiểm chứng "dev khai đã fix, có thật không". Việc đó thuộc `review-code-after-fix`; nó sẽ gọi lại skill này với `$BASE` = commit tại mốc comment vòng trước.
- **Tự chạy retrospective *cơ chế review* sau mỗi lượt** → phiền; cái đó thuộc `improve-review-skill`, chỉ khi user gọi. (Khác với **cập nhật profile app** ở Bước 5.6 — cái đó *có* chạy tự động mỗi lượt, ghi working tree, `git add` là cửa xác nhận.)

## Files

- `code-reviewer.md` — prompt template cho reviewer subagent (điền placeholder rồi bung).
- `checklists/base.md` — tiêu chí phổ quát, mỗi mục có `Áp dụng khi:`.
- `checklists/shopify-app.md` — tiêu chí đặc thù Shopify.
- `apps/_template.md` — khuôn tạo profile app mới.
- `post-to-mr.md` — cơ chế đăng feedback lên GitLab MR (thread resolvable neo dòng / reply / resolve). Dùng chung với `review-code-after-fix`.
