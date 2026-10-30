# self-improve — ssh-server-core

## Freshness

`config.yml > servers.<name>.menu` là **snapshot** menu tại lúc `explore`. Menu server có
thể đổi (thêm/bớt mục, đổi chữ). Nếu `run`/`menu` cho kết quả không khớp thực tế → chạy lại
`explore <server>` để refresh menu-map.

## Khi nào sửa gì

| Tình huống | Sửa ở đâu |
|---|---|
| Server mới, menu khác chữ prompt | `RETURN_PROMPT`/`SUBPROMPT` trong `ssh_client.py` + ghi chú vào [menu-driving.md](menu-driving.md) |
| Nhãn động từ mới bị phân loại sai | `READ_VERBS`/`SIDE_VERBS` + thêm case vào `_FIXTURE`/`cmd_selftest` |
| Lỗi lặp lại khi lái menu | mục **Common Mistakes** trong [../SKILL.md](../SKILL.md) |

## Nguyên tắc

- Lỗi lặp → sửa vào **skill gốc** (đây), không vá tay một lần.
- Mọi thay đổi heuristic → chạy `uv run ssh_client.py selftest` trước, rồi `doctor` trên một
  server thật, mới coi là xong.
- Giữ *conservative*: mở rộng `READ_VERBS` phải chắc chắn; nghi ngờ thì để `unknown`.
