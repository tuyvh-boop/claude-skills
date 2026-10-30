# Tự cải thiện — setup-work-journal

last reviewed: 2026-10-16 · assumed versions: betterleaks v1.9 (v2 đang rc), git ≥ 2.36

## Khi nào sửa, sửa ở đâu

| Loại insight | File đích | Trigger | Gate |
|---|---|---|---|
| Loại lưu trữ mới / đổi tick sẵn theo vai trò | `MODULES` trong `scripts/journal_setup.py` + `templates/claude-modules/<id>.md` | Người dùng xin loại chưa có, hoặc bỏ tick mặc định nhiều lần | Đề xuất diff, chờ confirm |
| Đổi cờ scanner (betterleaks v2 stable) | hàm `scan_*` trong `templates/githooks/scan.sh` + header file này | Release mới, hoặc quá 6 tháng từ `last reviewed` | Đề xuất diff + chạy selftest với betterleaks v1, v2 và khi không có scanner |
| Lỗi cài đặt theo OS, bẫy hook mới | SKILL.md (Cài đặt / Common Mistakes) + `cmd_doctor` | `doctor` báo ⚠️ chưa có cách sửa | Đề xuất diff |
| Câu chữ cảnh báo / ranh giới | SKILL.md | Người dùng vẫn làm sai sau khi đã đọc | Confirm + chạy lại kịch bản baseline |
| Skill `journal-save` đi kèm lưu sai chỗ / sai tên | `templates/companion-skill/SKILL.md.tmpl` | Teammate báo, hoặc thấy file sai tên trong journal | Đề xuất diff |

**Khi nào thêm script tính path cho `journal-save`** (hiện cố ý không có — bảng loại của team ngắn, một bản script copy vào mỗi journal
sẽ trôi version): thêm lệnh lint tên file vào `doctor` trước; chỉ khi lint ra file sai tên lặp ở ≥ 2 teammate, hoặc team có workflow
tự động cần tra "file loại X mới nhất", mới thêm `dest` / `find-task` vào `scripts/` của skill này (một bản), kèm selftest ngay từ đầu.

## Kỷ luật

- Chỉ sửa ở repo nguồn của skill, không sửa bản đã cài / symlink.
- Journal đã dựng của người dùng **không** tự cập nhật theo template mới — muốn áp thì chạy chế độ Thêm loại / Kiểm tra.
- Sau mỗi lần sửa: `uv run scripts/journal_setup.py apply` vào thư mục tạm → `hooks` → `selftest` phải `passed: true`; sửa
  `CLAUDE.md` merge thì thử trên một `CLAUDE.md` tự viết (phải giữ nguyên phần cũ).
