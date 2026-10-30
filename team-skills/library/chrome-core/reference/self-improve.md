# Tự cải thiện — luật kỹ thuật khi đúc vào chrome-core

**Khi nào đúc:** `chrome.py learn` báo một ứng viên đã lặp (≥ 2 lần). File này là luật kỹ thuật khi đúc vào tầng
core / shopify: ghi vào file nào, kiểm gì.

## Ghi ứng viên

- Thao tác (code) lặp → `chrome.py learn <id> --desc "…"`, sổ
  `candidates.md`. Script báo lặp → đúc theo bảng dưới, rồi xoá dòng.
- Bẫy / kiến thức → ghi thẳng `pitfalls.md` (mọi web) hoặc `sites/<nền tảng>.md`, không qua sổ.
- Thứ chỉ một case dùng (data, bước nghiệp vụ, selector riêng) → runbook của task, không vào skill.

## Loại insight → file đích

| Insight | File | Gate |
|---|---|---|
| Thao tác lặp, mọi web | `scripts/chrome_lib/session.py` (hoặc `devices.py`) + 1 dòng Quick Reference ở SKILL.md | Ghi working tree + case `selftest`, báo 1 dòng; không `git add` |
| Thao tác lặp, một nền tảng | `scripts/chrome_lib/sites/<nền tảng>.py` (chưa có thì tạo, đăng ký vào `SITES` của chrome.py) | Như trên |
| Bẫy chung | `reference/pitfalls.md` | Ghi thẳng, báo 1 dòng |
| Bẫy một nền tảng | `reference/sites/<nền tảng>.md` | Ghi thẳng, báo 1 dòng |
| Đặc thù một app (origin, frame host, tunnel, bẫy môi trường) | Tài liệu của app (vd `CLAUDE.md` repo app) | Theo quy ước tài liệu của app |
| Cách vào / đọc một màn của app, helper steps + lệnh harness dùng lại mọi task | Runbook dùng chung của app (`steps.py` + ghi chú, đặt chỗ team thống nhất) | Theo quy ước runbook của team |
| Đặc thù một case | runbook của task | Theo skill gọi |
| Cơ chế, câu chữ SKILL.md | `SKILL.md` | Đề xuất diff, chờ user confirm |

## Kỷ luật ghi

1. Đọc file đích trước; siết mục có sẵn hơn thêm mục mới.
2. Ghi **pattern**, không nhật ký sự cố; không mã task, không ngày sự cố, không URL / tên store thật (dùng placeholder).
3. Tách fact (đã chạy thấy) khỏi suy luận (`[suy]`).
4. Sửa ở repo gốc (`readlink -f` thư mục skill), không sửa bản symlink.
5. Đụng `chrome_lib` → `uv run scripts/chrome.py selftest` phải xanh trước khi báo xong.
6. Bẫy đã có helper lo → rút còn 1 dòng ở `pitfalls.md`.
