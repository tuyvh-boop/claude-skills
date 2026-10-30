---
name: symlink-skills
description: Use when the user asks to symlink, link, or install skills from a source folder or repo into the global Claude skills directory (~/.claude/skills) — all of them or only the ones they pick. Handles "symlink các skill trong folder X vào claude", "link skills from repo Y", "cài skill vào global", "cài skill trong ai-hub cho mình", "liệt kê skill cho mình chọn để cài", "cài thêm skill trong ai-hub".
---

# Symlink Skills

## Overview

Symlink **từng skill một** từ một folder nguồn vào `~/.claude/skills/`, giữ đúng convention 1 cấp để Claude discover được.

**Nguyên tắc cốt lõi:** Claude nhận diện skill theo `~/.claude/skills/<ten-skill>/SKILL.md` — tên folder cha **trực tiếp** của `SKILL.md` là tên skill. Vì vậy symlink phải ở **cấp thư mục skill**, KHÔNG phải cấp thư mục cha chứa nhiều skill.

## The Trap (đọc trước khi làm)

Người dùng nói "symlink các skill trong folder X" → dễ làm sai thành 1 symlink cấp folder:

```
# ❌ SAI: symlink cả folder cha
ln -s /path/X  ~/.claude/skills/X
# → SKILL.md nằm ở ~/.claude/skills/X/<skill>/SKILL.md (2 cấp) → Claude KHÔNG discover
```

Phải symlink từng skill:

```
# ✅ ĐÚNG: mỗi skill 1 symlink
ln -s /path/X/skillA  ~/.claude/skills/skillA
ln -s /path/X/skillB  ~/.claude/skills/skillB
# → ~/.claude/skills/skillA/SKILL.md (1 cấp) → discover chuẩn
```

## Steps

1. **Xác định folder nguồn.** Nếu user chỉ đưa tên repo, tìm nó rồi dùng thư mục `skills/` bên trong (nếu có). Hỏi lại nếu mơ hồ.

2. **Liệt kê các skill = mỗi subdir có `SKILL.md`:**
   ```bash
   SRC=/path/to/source-folder
   find "$SRC" -maxdepth 2 -name SKILL.md -printf '%h\n' | sort -u
   ```
   Mỗi dòng kết quả là 1 thư mục skill cần symlink. Bỏ qua subdir không có `SKILL.md`.

   **Chế độ chọn** (user nói "cho mình chọn", "cài skill trong ai-hub", hoặc nguồn có nhiều skill mà user chưa nói lấy hết):
   in danh sách đánh số, mỗi dòng `tên — description rút 1 câu` (đọc frontmatter từng `SKILL.md`), đánh dấu skill **đã có**
   trong `~/.claude/skills/`, rồi để user trả lời số / tên muốn cài. Chỉ symlink những skill được chọn ở Step 4. Không dùng
   hộp chọn nhiều lựa chọn (tối đa 4 lựa chọn, không đủ cho cả thư viện). Repo ai-hub: nguồn là `skills/library/` và
   `skills/roles/<role của user>/` (hỏi role nếu chưa biết).

3. **Kiểm tra trùng tên** trong `~/.claude/skills/` trước khi tạo. Nếu đã tồn tại: báo user, KHÔNG ghi đè im lặng. Nếu là symlink cũ đã hỏng (dangling) thì có thể thay.

4. **Tạo symlink từng skill (cross-platform):**
   ```bash
   D=~/.claude/skills
   mkdir -p "$D"
   # Chế độ chọn: thay vòng find bằng danh sách thư mục skill user đã chọn
   for skill_dir in $(find "$SRC" -maxdepth 2 -name SKILL.md -printf '%h\n' | sort -u); do
     name=$(basename "$skill_dir")
     if [ -e "$D/$name" ] || [ -L "$D/$name" ]; then
       echo "SKIP (trùng): $name"
       continue
     fi
     ln -s "$skill_dir" "$D/$name" 2>/dev/null
     if [ -L "$D/$name" ]; then
       echo "LINK (symlink): $name -> $skill_dir"       # Linux/macOS, hoặc Windows có Dev Mode
     else
       # Windows: ln -s COPY chứ không link (khác ổ đĩa / không Dev Mode) → dùng JUNCTION (không cần admin)
       rm -rf "$D/$name"
       powershell.exe -NoProfile -Command "New-Item -ItemType Junction -Path '$(cygpath -w "$D/$name")' -Target '$(cygpath -w "$skill_dir")'" >/dev/null 2>&1 \
         && echo "LINK (junction): $name -> $skill_dir" \
         || echo "FAIL: $name (không tạo được link)"
     fi
   done
   ```

   > **Windows:** `ln -s` trong Git Bash thường **copy** thay vì link (nhất là khác ổ đĩa, hoặc chưa bật Developer Mode) → skill sẽ bị "đóng băng", sửa ở repo không cập nhật. Đoạn trên tự phát hiện (`[ -L ]` sai) và fallback sang **directory junction** (`mklink /J`, không cần quyền admin, chạy được cả khác ổ đĩa cùng máy).

5. **Verify** đọc được `SKILL.md` qua symlink:
   ```bash
   for l in "$D"/*/; do
     n=$(basename "$l")
     [ -f "$l/SKILL.md" ] && echo "OK  $n" || echo "FAIL $n"
   done
   ```

6. **Báo user:** liệt kê skill đã link, và nhắc **skill mới chỉ hiện sau khi khởi động lại session** Claude Code.

## Quick Reference

| Việc | Lệnh |
|---|---|
| Tìm skill trong folder | `find "$SRC" -maxdepth 2 -name SKILL.md -printf '%h\n'` |
| Tên skill | `basename "$skill_dir"` |
| Tạo symlink | `ln -s "$skill_dir" ~/.claude/skills/<name>` |
| Kiểm tra tồn tại | `[ -e path ] \|\| [ -L path ]` (cả `-L` để bắt symlink hỏng) |
| Xem symlink hiện có | `ls -la ~/.claude/skills` |

## Common Mistakes

- **Symlink cấp folder cha** thay vì từng skill → skill không hiện (xem The Trap).
- **Copy thay vì link** → sửa trong repo không tự cập nhật. Trên Windows `ln -s` có thể âm thầm copy → luôn verify `[ -L ]`; sai thì fallback junction (xem Step 4).
- **Đường dẫn tương đối** với `ln -s`: dùng đường dẫn **tuyệt đối** cho target để symlink không phụ thuộc cwd.
- **Ghi đè skill trùng tên** không hỏi → có thể phá skill/nguồn khác. Luôn SKIP + báo khi trùng.
- **Quên `-L` khi check tồn tại** → bỏ sót symlink đã hỏng trỏ tới file gốc không còn.

## Notes

- Skill ở `~/.claude/skills/` là **global** — mọi repo/session đều thấy. Nếu user muốn skill chỉ dùng cho 1 repo, symlink vào `<repo>/.claude/skills/` (project scope) thay vì global.
- Symlink không tự bắt skill mới thêm sau này vào folder nguồn — chạy lại skill này để sync thêm.
