# Profiles — nhận diện môi trường & chọn convention

Quyết định **áp convention nào** cho repo hiện tại. Chạy 1 lần đầu mỗi thao tác.

**[Model: haiku — subagent]** _(gộp chung với bước gom context của thao tác)_

## Cách nhận diện (ưu tiên từ trên xuống, dừng ở dòng khớp đầu tiên)

| # | Tín hiệu (kiểm tra theo thứ tự) | Profile |
|---|---|---|
| 0 | User **nói rõ** ("dùng profile bss", "đây là repo cá nhân") | Theo user |
| 1 | Có file override `~/.claude/.gitflow-profile` chứa tên profile | Theo file |
| 2 | `remote.origin.url` là host GitLab công ty **hoặc** đường dẫn repo nằm trong `E:/JOB/BSS/` (hay path công ty tương đương) | **bss** |
| 3 | `remote.origin.url` chứa `github.com` (repo cá nhân) | **personal** |
| 4 | Không khớp gì rõ ràng | Hỏi user 1 câu; mặc định **personal** |

> Lưu ý: **host** (từ `git-context.sh` → `=== REMOTE === host:`) mới là tín hiệu chính, KHÔNG phải "máy có `gh`/`glab` nào". Máy có thể cài `glab` nhưng repo lại trên GitHub — vẫn là profile personal.

## Mỗi profile trỏ tới đâu

| Profile | Convention nạp |
|---|---|
| `personal` | `rules/conventions/_base.md` + `rules/conventions/personal.md` |
| `bss` | `rules/conventions/_base.md` + `company/bss.md` (file này sẽ đọc rule team qua con trỏ) |

`_base.md` luôn là nền; file profile chỉ **ghi đè/bổ sung** phần khác biệt (format tên branch, format commit, footer, hand-off...).

## Cho phép override thủ công

Nếu auto-detect sai, user gõ ép profile (vd "commit theo profile personal"). Muốn cố định lâu dài cho một máy: tạo file `~/.claude/.gitflow-profile` với nội dung 1 dòng là tên profile (`personal` hoặc `bss`). Skill đọc ở bước #1.

## Thêm môi trường/công ty mới (mở rộng)

1. Tạo file convention mới (công ty → đặt trong `company/<tên>.md`; môi trường cá nhân khác → `rules/conventions/<tên>.md`).
2. Thêm 1 dòng nhận diện vào bảng trên.
Không cần sửa `SKILL.md` hay các file `operations/*`.
