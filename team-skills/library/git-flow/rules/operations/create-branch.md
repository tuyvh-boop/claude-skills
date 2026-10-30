# Operation — Tạo branch

Trigger: "tạo branch mới cho task X", "checkout branch mới từ master", "làm branch cho việc này"...

Làm tuần tự. Tuân `rules/safety.md`.

---

## Step 1 — Gom context + profile

**[Model: haiku — subagent]**

`Agent(model: "haiku")`: chạy `sh <skill>/scripts/git-context.sh`, xác định profile (`rules/profiles.md`), và chạy thêm:
- `git fetch origin` — cập nhật ref mới nhất.
- `git branch --list` + `git branch -r` — để check trùng tên.

Trả về: nhánh chính (default), status (sạch/dở), danh sách branch, profile.

---

## Step 2 — Đề xuất tên + guard

**[main loop]**

1. **Guard dirty tree** (safety §7): working tree đang dở → cảnh báo, hỏi (commit/stash/mang theo) trước khi tạo.
2. **Đặt tên theo profile:**
   - `personal` → `feat/<slug>` / `fix/<slug>` (slug từ mô tả việc user đưa).
   - `bss` → `feature/<MÃ-JIRA>` (bug → `fix/<MÃ-JIRA>`), kèm slug tuỳ chọn. Chưa có mã Jira → **hỏi**, không bịa.
3. **Chọn base:** mặc định nhánh chính remote mới nhất (`origin/<default>`). User muốn base khác → theo user.
4. **Check trùng** (từ Step 1): tên đã tồn tại (local/remote) → cảnh báo, hỏi switch sang hay đổi tên.
5. Hiện tên branch + base đề xuất, hỏi:
   > `Tạo branch `<name>` từ `origin/<base>`? (yes / đổi tên / cancel)`

---

## Step 3 — Tạo branch

**[main loop]**

Chỉ sau khi confirm:

```bash
git switch -c <name> origin/<base>     # hoặc: git checkout -b <name> origin/<base>
```

Báo cáo (BẮT BUỘC): đọc và làm theo `rules/report.md` → **§ Tạo branch**. Có brief task → thêm 1 dòng tóm tắt việc để user bắt đầu.

> Repo công ty muốn kèm kéo context Jira đầu task → gợi ý hand-off `/te-dev-start` (xem `company/bss.md`). git-flow không tự đụng Jira.
