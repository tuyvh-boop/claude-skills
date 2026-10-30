# Operation — Tạo MR / PR

Trigger: "tạo MR", "mở PR", "gửi pull request", "tạo merge request"...

Làm tuần tự. Tuân `rules/safety.md`.

---

## Step 1 — Gom context (mr mode) + profile

**[Model: haiku — subagent]**

`Agent(model: "haiku")`: chạy `sh <skill>/scripts/git-context.sh mr [<base>]` (base mặc định = nhánh chính) và xác định profile (`rules/profiles.md`). Trả về: branch hiện tại, **host** (github/gitlab), platform_cli, commits `base..HEAD`, diff stat, **số dòng diff**, profile.

- Branch hiện tại là protected (main/master) → **dừng**, không tạo MR từ nhánh chính (safety §1).
- Chưa có commit nào so với base → báo "không có gì để tạo MR".

**Chọn CLI theo HOST, không theo CLI nào cài sẵn:**
- host `github` → dùng `gh` (nếu thiếu `gh` → push rồi mở link PR GitHub in ra).
- host `gitlab` → dùng `glab` (nếu thiếu → push rồi mở link MR GitLab in ra).

---

## Step 2 — Soạn title + description

**[Model: sonnet — subagent]**

`Agent(model: "sonnet")`, đưa commits + diff stat + profile:

1. **Cảnh báo PR lớn:** chỉ khi số dòng diff > **~1000** → nêu "PR này ~X dòng, khó review; cân nhắc tách?" (để Step 3 hỏi user). Dưới ngưỡng → **không nhắc gì**. Số file không phải tiêu chí.
2. **Title:** ngắn gọn; profile `bss` có mã Jira → prefix mã (`OPOS-13: Add bulk delete`).
3. **Description:** theo `_base.md` — dòng tóm tắt mệnh lệnh + thân (vấn đề / cách tiếp cận / trade-off / link). Có CodeGraph → thêm phạm vi ảnh hưởng cho reviewer.

Trả về: title + description (fenced), cờ PR-lớn.

---

## Step 3 — Guard, confirm, tạo MR/PR

**[main loop]**

1. **Profile `bss` → hỏi hand-off trước (company/bss.md):**
   > "Repo công ty. (a) tạo MR gọn với `master` ở đây, hay (b) chạy `/te-dev-create-pr` (rà tài liệu + comment Jira + đổi status)?"
   Chọn (b) → dừng, nhường command team. Chọn (a) → tiếp.
2. PR lớn (cờ Step 2) → hỏi có tách không; user muốn tách → dừng, gợi ý cách chia.
3. Có commit chưa push / thay đổi chưa commit → xử lý qua luồng `commit-push.md` trước (hoặc nhắc user).
4. Hiện title + description, hỏi:
   > `Thông tin MR đã ổn? Tạo MR target `<base>`? (yes / sửa / cancel)`

**NEVER** tạo MR trước khi user confirm.

---

## Step 4 — Push + tạo MR/PR

**[main loop]**

Chỉ sau khi confirm.

1. Push branch nếu chưa có trên remote: `git push -u origin <branch>` (theo guard push — safety §2,§3).
2. Tạo theo host:
   ```bash
   # GitHub
   gh pr create --base <base> --head <branch> --title "<title>" --body "<description>"
   # GitLab
   glab mr create --target-branch <base> --source-branch <branch> --title "<title>" --description "<description>"
   ```
   Thiếu CLI tương ứng → push rồi lấy link tạo MR/PR mà remote in ra trong output push, đưa user.
3. **Giữ lại URL MR/PR do CLI in ra** — Step 5 cần dùng nguyên văn.

---

## Step 5 — Báo cáo kết quả (BẮT BUỘC)

**[main loop]**

Đọc và làm theo `rules/report.md` → **§ Tạo MR/PR**.
