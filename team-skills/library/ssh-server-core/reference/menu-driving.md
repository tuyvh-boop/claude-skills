# Lái restricted menu qua pexpect — ghi chú kỹ thuật & tuning

Đọc khi cần chỉnh heuristic phân loại, xử lý một dạng menu mới, hoặc debug khi
`explore`/`run` cho kết quả lạ.

## Luồng quan sát được (mô tả bằng ví dụ HƯ CẤU)

> Menu/host thật chỉ nằm trong `config.yml` (đã gitignore). Ở đây dùng ví dụ hư cấu.

Login → in banner + menu (các dòng `N) nhãn`, kết bằng `0) Thoat`) → chờ nhập số.
Sau khi chọn một mục:

- **Mục không cần input** (vd một mục `Xem trang thai dich vu`): in output rồi dừng ở
  prompt kiểu `-- Nhan Enter de quay lai menu --`. Gửi Enter → menu hiện lại.
- **Mục cần input** (vd một mục `Xem log ung dung`): in prompt kiểu `Chon <muc>:`
  (kết thúc bằng `:`), chờ một giá trị, rồi mới ra output + prompt "nhấn Enter".

→ Vì menu **không tự hiện lại** ngay, KHÔNG được dùng marker `0) Thoat` làm dấu "đã xong".

## Ba regex xương sống (trong `ssh_client.py`)

- `MENU_MARKER` — dòng `0) Thoat` (nhận biết đang ở màn hình menu; dùng lúc `_wait_menu`).
- `RETURN_PROMPT` — `nhan enter de quay lai menu`: mục đã xong, **không cần input**.
- `SUBPROMPT` — dòng có động từ hỏi (`chon|chọn|nhap|nhập|select|enter so`) + kết thúc `:`:
  **cần input thật**.

**Thứ tự khi `expect` phải là `[RETURN_PROMPT, SUBPROMPT, MENU_MARKER, TIMEOUT, EOF]`** —
RETURN_PROMPT trước SUBPROMPT, vì "nhấn Enter" cũng chứa chữ "enter"; đảo thứ tự sẽ bắt nhầm.

## Vì sao mỗi mục một session (`_probe_option`)

Nếu dò nhiều mục trên cùng một session: gặp sub-prompt ở mục A, phải abort (Ctrl-C/Enter),
mà trạng thái sau abort không chắc về đúng menu → mọi mục sau lệch pha, bị gắn nhầm
`needs_input`. Mở **session mới cho mỗi mục** loại bỏ hẳn class lỗi này. Chi phí: N login
ngắn khi explore (chạy 1 lần/server) — chấp nhận được.

## Phân loại nhãn (`classify_option`)

Thiên về an toàn: **không rõ = `unknown`, không tự bấm**.

1. Marker `chi doc / read-only / chi xem` trong nhãn → ép `read` (vd một mục
   `Chay bao cao thong ke (chi doc, khong sua duoc)`).
2. Động từ **ĐẦU** nhãn (đã bỏ dấu) trong `SIDE_VERBS` (restart/reload/edit/sua/xoa/set/
   stop/start/kill/tao/update/drop/truncate/deploy...) → `side-effect`.
3. Động từ đầu trong `READ_VERBS` (xem/list/duyet/inspect/stats/show/view/describe/...) → `read`.
4. `thoat/exit/quit/back` → `exit`. Còn lại → `unknown`.

Không substring toàn nhãn (tránh "khong **sua** duoc" bị nhầm side-effect).

## Tuning cho server mới

- Menu khác chữ (vd prompt "Enter để tiếp tục" thay vì "Nhan Enter de quay lai menu") →
  bổ sung alternation vào `RETURN_PROMPT` / `SUBPROMPT`.
- Nhãn dùng động từ lạ → thêm vào `READ_VERBS`/`SIDE_VERBS`. Ưu tiên vẫn là *conservative*:
  chưa chắc thì để `unknown` cho user chốt, đừng nới `READ_VERBS` liều.
- Sau khi chỉnh regex/verb: cập nhật fixture `_FIXTURE` + kỳ vọng trong `cmd_selftest` nếu
  thêm case mới, rồi `uv run ssh_client.py selftest`.

## Đã kiểm chứng (khi dựng skill)

`doctor / explore / menu / run` đã chạy thật trên một server nội bộ thật (chi tiết trong
`config.yml` đã gitignore), read-only, không side-effect. `selftest` PASS trên fixture hư cấu.
