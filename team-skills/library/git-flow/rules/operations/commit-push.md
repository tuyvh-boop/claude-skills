# Operation — Commit + Push

Trigger: "push lên đi", "push lên branch xx", "commit rồi push", "đẩy code lên"...

Làm tuần tự, KHÔNG nhảy bước. Tuân `rules/safety.md` xuyên suốt.

---

## Step 1 — Gom context + profile

**[Model: haiku — subagent]**

`Agent(model: "haiku")`: chạy `sh <skill>/scripts/git-context.sh` và xác định profile theo `rules/profiles.md`. Trả về: branch hiện tại + default, upstream, ahead/behind, host, status, staged files, **section SECRET SCAN**, staged diff, unstaged diff, recent log, và **profile** (personal/bss).

Nếu project có **CodeGraph** (`codegraph_*`) → có thể dùng `codegraph_impact`/`codegraph_callers` trên symbol đã đổi để đánh giá blast radius (giúp chọn độ phức tạp & phát hiện breaking). Diff vẫn lấy từ git.

---

## Step 2 — Phân tích diff + soạn commit message

**[Model: sonnet — subagent]**

`Agent(model: "sonnet")`, đưa diff + profile + convention:

1. **Secret check:** section SECRET SCAN có `WARN` → đánh dấu để Step 3 dừng hỏi (nêu rõ dòng/file nghi ngờ). Không echo giá trị secret.
2. **Đọc intent:** diff làm gì, giải quyết vấn đề gì. Nhiều mục đích → **mặc định vẫn gộp 1 commit**, viết subject khái quát đủ bao; chỉ chuẩn bị gợi ý tách nếu convention của profile cho phép và diff chạm ngưỡng.
3. **Chọn type + độ phức tạp** theo `_base.md`.
4. **Soạn message** đúng convention của profile:
   - `personal` → `_base.md` (`<type>: <subject>` [+ body]).
   - `bss` → format team `<branch> (<type>) <subject>` [+ body/footer] (theo `company/bss.md`, đọc rule qua con trỏ).

Trả về: message đề xuất (fenced), cờ secret, gợi ý tách (nếu có).

---

## Step 3 — Giải nghĩa branch đích + confirm

**[main loop]**

1. **Target branch (thông minh):**
   - Không nói branch → dùng **branch hiện tại**.
   - Nói "branch xx" **trùng** branch hiện tại → OK, branch hiện tại.
   - Nói "branch xx" **khác** branch hiện tại → **HỎI rõ, không đoán**:
     > "Bạn đang ở `<current>` nhưng nói push lên `<xx>`. Ý bạn là: (a) chuyển sang `<xx>` rồi push, hay (b) push nhánh hiện tại lên remote-ref tên `<xx>`?"
2. **Guard protected branch** (safety §1): current/target ∈ protected → cảnh báo, hỏi trước.
3. **Secret** (safety §4): có cờ từ Step 2 → dừng, cho xem, hỏi.
4. **Staging** (safety §5): chưa stage gì → hỏi stage tất cả / chọn lọc; cảnh báo untracked lạ.
5. Hiện **message** (Step 2) trong fenced block + tóm tắt "sắp commit N file, push lên `origin/<branch>`". Hỏi:
   > `Approve? (yes / edit / cancel)`

   Chỉ khi Step 2 bật cờ gợi ý tách (profile cho phép + chạm ngưỡng) mới thêm lựa chọn `split` vào câu hỏi kèm lý do. Mặc định **không** chào mời `split`.

**NEVER** commit/push trước khi user "yes".

---

## Step 4 — Commit + Push

**[main loop]**

Chỉ sau khi user confirm.

1. **Commit:**
   ```bash
   # 1 dòng
   git commit -m "feat: add export csv"
   # nhiều dòng — dùng heredoc
   git commit -m "$(cat <<'EOF'
   feat: add export csv

   Người dùng cần xuất báo cáo ra CSV để mở bằng Excel.
   EOF
   )"
   ```
   (profile `bss` → subject dạng `feature/OPOS-13 (feat) ...`.)
2. **Push:**
   ```bash
   git push -u origin <branch>      # -u nếu chưa có upstream
   ```
3. **Non-fast-forward** (safety §3) → đề xuất `git pull` (**merge**), xử lý conflict, push lại. KHÔNG force.

---

## Step 5 — Báo cáo kết quả (BẮT BUỘC)

**[main loop]**

Đọc và làm theo `rules/report.md` → **§ Commit + Push**.

> Split (Step 3) → lặp Step 2–4 cho từng nhóm thay đổi (dùng `git add -p`/theo path để stage chọn lọc), rồi báo cáo **một lần** ở Step 5 với đủ các commit.
