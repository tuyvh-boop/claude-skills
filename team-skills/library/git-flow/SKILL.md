---
name: git-flow
description: Use when the user wants to do everyday git work in natural language — commit & push, create a branch, or open a merge/pull request — in ANY repo (personal or company). Triggers on "push lên đi", "push lên branch xx", "commit rồi push", "commit giúp", "tạo branch mới cho task X", "checkout branch mới", "tạo MR", "mở PR/pull request", "đẩy code lên". Auto-detects the working environment to apply the right commit/branch/PR convention, and enforces safety guards (never commit straight to main/master without asking, always confirm before push, scan for secrets, never force-push, pull uses merge not rebase).
---

# git-flow

Tái hiện kỹ năng dùng git của mình để AI làm thay: **commit + push**, **tạo branch**, **tạo MR/PR** — nói tự nhiên là làm, chạy được ở **mọi repo** (cá nhân hoặc công ty), tự nhận diện môi trường để áp đúng convention, và luôn giữ **guardrail an toàn**.

## ⚠️ Framework Reminder

Git flow executes conventions, which hide crucial decisions: [[framework_systematic_problem_solving]] —
- **Convention is constraint, not speed-up**: reading convention before writing subject line feels slow; skipping it causes silent downstream failures (wrong branch, wrong commit message format, confuses automation). Measure: 30sec reading convention vs 1 hour debugging wrong commit classification
- **Safety guards catch real problems**: never commit to main without asking, always confirm push, scan for secrets — these sound paranoid until they prevent a real incident. Enforce them religiously, never skip
- **Verify result after execution**: commit message formatted right doesn't mean you committed the right code. After push, spot-check: right repo, right branch, right files, nothing sensitive leaked

## Khi nào dùng

- "push lên đi" / "push lên branch xx" / "commit rồi push" / "đẩy code lên" → **commit + push**.
- "tạo branch mới cho task X" / "checkout branch mới từ master" → **tạo branch**.
- "tạo MR" / "mở PR" / "gửi pull request" → **tạo MR/PR**.

**Không dùng cho:** luồng Jira/multi-repo đặc thù công ty (comment ticket, merge-test, đổi status/assignee, tính release) — cái đó thuộc các command team (`/te-dev-commit`, `/te-dev-create-pr`, `/te-dev-merge-test`). Ở repo công ty, skill này sẽ **hỏi hand-off** sang chúng khi cần (xem `company/bss.md`).

## KHÔNG chạy tắt (BẮT BUỘC)

Skill này tồn tại vì thói quen git mặc định của model **không** giống convention của user. Biết cách chạy `git commit`/`git push` không có nghĩa là được tự làm.

- **Cấm** soạn commit message / tên branch / mô tả PR bằng "kiểu thường làm". Phải **đọc file convention của profile** (`rules/conventions/_base.md` + `personal.md` hoặc `company/bss.md`) **trước khi** viết chữ đầu tiên.
- **Cấm** bỏ step. Thấy việc "đơn giản, diff nhỏ, tự làm cũng được" → đó chính là lúc dễ sai convention nhất; vẫn chạy đủ step của operation.
- Trước khi commit, tự kiểm: có `<type>:` đúng loại chưa? subject imperative, ≤72 ký tự chưa? subject đang liệt kê ("and"/"also") thì đã viết khái quát lại chưa? Sai một mục → soạn lại, không commit.
- **Mặc định 1 lần push = 1 commit.** Không tự tách, không mặc định hỏi tách — chỉ gợi ý khi profile cho phép và chạm ngưỡng (xem convention của profile).
- Đã lỡ chạy tắt và commit sai → **nói thẳng với user**, không im lặng cho qua. Không tự amend/force-push để giấu.

## Model & token policy (BẮT BUỘC)

Skill này cố ý **rẻ** — **không bao giờ dùng Opus**, kể cả khi session đang chạy Opus.

- Step gắn `[Model: haiku — subagent]` / `[Model: sonnet — subagent]` → **PHẢI** `Agent(model: "haiku"|"sonnet")` để chạy, đẩy phần đốt token (gom context, đọc diff, soạn message/description) ra khỏi main loop.
- Step gắn `[main loop]` chỉ là *confirm với user + chạy lệnh git* (nhẹ token) → chạy trực tiếp; không cần đổi model.
- Không có step nào dùng Opus.

## Quy trình chung (mọi thao tác)

1. **Gom context** bằng script read-only (1 lần, thay vì gõ nhiều lệnh git rời):
   ```bash
   sh <skill>/scripts/git-context.sh           # commit/push/branch
   sh <skill>/scripts/git-context.sh mr [base] # tạo MR/PR
   ```
   `<skill>` = đường dẫn folder skill này. Script chạy trên Linux/macOS/Windows(Git Bash) không cần cài thêm.
2. **Xác định profile** (môi trường) → nạp đúng convention: đọc `rules/profiles.md`.
3. **Chạy thao tác** theo file tương ứng bên dưới, **luôn tuân** `rules/safety.md`.
4. **Báo cáo kết quả** ở step cuối theo `rules/report.md` — tóm tắt commit/branch/MR **kèm link bấm được** (link sinh bằng `scripts/git-links.sh`, không tự bịa URL).

## Router — thao tác → file rule

| Việc | Đọc file |
|---|---|
| Nhận diện môi trường & chọn convention | `rules/profiles.md` |
| Convention nền chung (mọi repo) | `rules/conventions/_base.md` |
| Convention repo cá nhân | `rules/conventions/personal.md` |
| Convention đặc thù công ty BSS/OPTIS | `company/bss.md` |
| Commit + push | `rules/operations/commit-push.md` |
| Tạo branch | `rules/operations/create-branch.md` |
| Tạo MR/PR | `rules/operations/create-mr.md` |
| Guardrail an toàn (đọc trước mọi lần ghi/push) | `rules/safety.md` |
| Format báo cáo kết quả + link (step cuối mọi operation) | `rules/report.md` |

## Nguyên tắc an toàn (tóm tắt — chi tiết ở `rules/safety.md`)

- **Push luôn phải confirm.** Push là hành động "outward" — không tự động push.
- **Không commit thẳng** `main`/`master`/`develop`/`release/*` — cảnh báo và hỏi trước.
- **Secret scan** diff trước khi commit; nghi ngờ → dừng hỏi.
- **Non-fast-forward** → đề xuất `git pull` (**merge**, không rebase) rồi push lại. **Không** force-push.
- Thao tác phá huỷ (`reset --hard`, discard, xoá branch) → luôn hỏi rõ.
