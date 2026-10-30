---
name: ssh-server-core
description: Skill NỀN để Claude nối tới các server nội bộ theo dạng "restricted interactive menu" qua SSH (login vào bị ép vào một menu cố định, quyền hạn chế, hợp để scan log / xem trạng thái dịch vụ, tiến trình, DB). Đọc khi cần xem log/trạng thái một server đã khai trong config, khi cần khám phá (explore) menu của một server mới, hoặc khi một skill khác cần chạy lệnh read-only trên server qua menu này. KHÔNG dùng để thao tác side-effect (restart/reload/sửa/xoá) — những cái đó user tự làm.
---

# ssh-server-core

## Overview

Nhiều server nội bộ cấu hình account đăng nhập vào **bị ép vào một menu cố định**
(`ForceCommand` / login shell là script menu) thay vì shell tự do: chỉ cho vài thao tác
**read-only** (xem log, trạng thái dịch vụ, tiến trình, cấu hình, truy vấn chỉ đọc...) + vài
thao tác restart/reload có giới hạn. Skill này cho Claude **lái menu đó qua SSH** để lấy
dữ liệu, một cách an toàn.

**Giá trị ở config, cơ chế ở skill.** Danh sách server + menu-map nằm ở `config.yml`
(gitignored); kết nối chỉ trỏ tới **alias trong `~/.ssh/config`** (`ssh_alias`), key nằm
nguyên trong `~/.ssh` — skill không đọc/không truyền key, không có secret trong config.

## When to use

- Cần **xem log / trạng thái** một server (dịch vụ, tiến trình, log ứng dụng, cấu hình, DB) mà
  account chỉ có menu hạn chế.
- Gặp một **server mới** cùng dạng menu → chạy `explore` để dựng menu-map lần đầu.
- Một skill khác (vd scan-log) cần **chạy một mục read-only** và lấy output.

**KHÔNG dùng khi:** cần shell tự do / chạy lệnh tuỳ ý (account này không cho), hoặc cần
**side-effect** (restart/reload/deploy/sửa file) — skill chặn cứng, user tự làm qua `raw`.

## Mô hình menu (đọc kỹ — quyết định cách lái)

Sau khi chọn một mục, menu **KHÔNG tự hiện lại**. Có 2 kiểu kết thúc:

| Kiểu | Dấu hiệu | Nghĩa |
|---|---|---|
| Xong, không cần input | prompt kiểu "nhấn Enter để quay lại menu" (khớp bởi `RETURN_PROMPT`) | mục chạy xong, output nằm phía trên; chỉ cần Enter để về menu |
| Hỏi thêm (sub-prompt) | dòng kết thúc `:` kiểu `Chọn <mục>:` (khớp bởi `SUBPROMPT`) | cần **một giá trị** (chọn một mục con / nhập tham số) rồi mới ra output |

→ Mỗi mục read được dò trên **một session riêng** (tránh lệch pha giữa các mục). Gặp
sub-prompt lúc explore thì **không tự bịa input** — chỉ ghi lại `needs_input` + `input_hint`.

## Config

`config.yml` (copy từ `config.example.yml`, đã gitignore):

```yaml
servers:
  <ten-ngan>:                        # tên gọi ngắn dùng trong lệnh
    ssh_alias: <alias-trong-ssh-config>   # alias trong ~/.ssh/config (key tự resolve)
    label: "<mô tả người đọc>"
    explored: false                  # explore xong tự thành true
    menu: []                         # explore tự điền
```

> Giá trị THẬT (alias, tên server, menu) chỉ nằm trong `config.yml` — **đã gitignore**.
> Không viết alias/host/menu thật vào SKILL.md, reference hay bất kỳ file được commit nào.

Mỗi mục trong `menu` sau explore: `{option, label, kind, needs_input, input_hint, user_ok}`.
`kind` ∈ `read | side-effect | exit | unknown` (script tự phân loại). `user_ok` ∈
`true | false | null` là **quyết định của user** (không phải script): `null` = chưa duyệt,
`false` = user cấm, `true` = user cho phép. `run` chỉ chạy khi `user_ok == true`.

## CLI (mọi lệnh chạy bằng `uv run`, KHÔNG `uv run python`)

```bash
uv run scripts/ssh_client.py selftest              # test logic parse/classify, không cần mạng
uv run scripts/ssh_client.py doctor [server]       # verify login (vào menu rồi thoát), không side-effect
uv run scripts/ssh_client.py list-servers          # liệt kê server trong config
uv run scripts/ssh_client.py explore <server>      # LẦN ĐẦU với server mới: dò menu, phân loại
uv run scripts/ssh_client.py menu <server>         # in menu-map + trạng thái user_ok
uv run scripts/ssh_client.py allow <server> N...   # user CHO PHÉP các mục (user_ok=true)
uv run scripts/ssh_client.py block <server> N...   # user CẤM các mục (user_ok=false)
uv run scripts/ssh_client.py run <server> --option N [--input V ...]   # chạy 1 mục, trả output
uv run scripts/ssh_client.py read-file <server> <key>   # đọc file khai trong `files:`, CHỈ in dòng khớp `show`
uv run scripts/ssh_client.py raw <server>          # bàn giao phiên interactive cho USER tự thao tác
```

- **`read-file`** dùng cho file cấu hình cần soi định kỳ (vd `shopify.app.toml` prod — gitignored, chỉ có trên
  server). Duyệt mục "Duyệt/đọc file" **theo tên** từng bước (số thứ tự trên server đổi khi thêm file → không lưu số
  cứng). Chỉ in dòng khớp regex `show` (danh sách trắng). Chặn cứng path dạng `.env*` / `*.pem` / `*.key` / credential,
  thiếu `show` cũng chặn. Vẫn qua gate `kind == read` + `user_ok == true` của mục duyệt file.
- Khai file mới: thêm entry vào `files:` của server (khuôn ở `config.example.yml`), path **tương đối với gốc** của mục
  duyệt; file nằm ngoài vùng menu cho duyệt thì không khai được (ghi chú trong config, đừng lùi thư mục cha để lách).

- `run` chạy được chỉ khi **cả hai**: `kind == read` **và** `user_ok == true`. `side-effect`
  bị chặn cứng; `user_ok` `false`/`null` cũng bị chặn (kèm lý do "user cấm" / "chưa duyệt").
- Mục cần input: truyền theo đúng thứ tự menu hỏi, vd trả lời sub-prompt bằng giá trị `2`:
  `run <server> --option N --input 2`. Xem `input_hint` trong `menu` để biết nó hỏi gì.

## Explore một server mới — quy trình

1. Khai server vào `config.yml` (`ssh_alias` trỏ alias `~/.ssh/config` đã login được).
2. `doctor <server>` — chắc chắn login vào tới menu.
3. `explore <server>` — nó tự bấm thử **chỉ mục read** (mỗi mục 1 session), bỏ qua
   side-effect, **không đụng** mục unknown. Lưu menu-map vào config.yml (mọi mục `user_ok=null`).
4. **Mục `unknown`** (script không tự phân loại được) → **hỏi user** từng mục là read hay
   side-effect, rồi sửa `kind` tay trong `config.yml`. Không tự đoán rồi bấm.
5. **GATE BẮT BUỘC — user duyệt quyền.** Sau explore, **trình menu cho user và HỎI mục nào
   Claude được dùng, mục nào cấm** — kể cả mục `read` hợp lệ user vẫn có thể cấm (vd ở một
   server, các mục đụng DB bị cấm dù chỉ đọc). Ghi lại bằng `allow`/`block`. Chưa duyệt
   (`user_ok=null`) thì `run` từ chối. **Không tự cho phép mục nào — phải hỏi user.**

## An toàn (theo rule của user — bắt buộc)

- **Read-only mặc định.** Không bao giờ tự chạy mục `side-effect`/`unknown`.
- **Gate quyền của user.** Kể cả mục `read` hợp lệ, chỉ chạy khi user đã `allow`. User có
  quyền cấm bất kỳ mục nào (`block`) dù script cho là read — tôn trọng tuyệt đối, không lách.
- **Không bịa input** khi gặp sub-prompt lúc explore.
- Prod → chỉ đọc. Side-effect (restart/reload...) là việc **user tự làm** qua `raw`, không
  phải Claude.
- Key không rời `~/.ssh`; `config.yml` không chứa secret; không in gì nhạy cảm ra transcript.

## Skill khác nạp lại

```python
from ssh_client import load_ctx, run_option, explore_server, parse_menu, classify_option
```
Ưu tiên `cmd_run` (đã bao gồm cả 2 gate `kind==read` + `user_ok==true`) thay vì gọi
`run_option` trực tiếp. Nếu buộc phải dùng `run_option`, tự kiểm `kind == "read"` **và**
`user_ok is True` từ menu-map trước — đừng gọi mù, đừng bỏ qua gate quyền của user.

## Common Mistakes

- **Chờ menu `0) Thoat` hiện lại sau khi chọn mục** → sai, menu dừng ở `-- Nhan Enter --`.
  Dùng `RETURN_PROMPT` để nhận "đã xong, không cần input". (Đây là bug thật gặp khi dựng skill.)
- **Dò nhiều mục trên một session** → lệch pha dây chuyền, mọi mục sau bị gắn nhầm
  `needs_input`. Fix: **mỗi mục một session** (`_probe_option`).
- **Substring keyword để phân loại** → "khong sua duoc" (chỉ đọc) bị dính "sua" → nhầm
  side-effect. Fix: phân loại theo **động từ ĐẦU nhãn** + marker "chi doc" ép read.
- **Token đầu có dấu phân cách** (`Duyet/doc file...`) mà chỉ xoá ký tự lạ rồi ghép → `duyetdoc`
  không khớp verb nào → `unknown` dù `duyet` đã có trong `READ_VERBS`. Fix: xét cả dạng ghép
  (`khoidong`) lẫn từ đầu trước dấu phân cách (`duyet`). Thấy `unknown` lạ → thử `classify_option`
  trên nhãn trước khi kết luận thiếu verb.
- **Đọc file config qua `run --option <duyệt> --input <số>...` rồi in cả output** → số thứ tự lệch khi server có
  file mới, và in cả file vi phạm luật danh sách trắng. Dùng `read-file` (duyệt theo tên + lọc `show`).
- **Regex `show` trong YAML escape 2 lớp** (`'\\s'` trong chuỗi single-quote) → regex hỏng, `read-file` lỗi
  `unterminated character set`. Single-quote YAML chỉ cần một `\` (`'^\s*\['`).
- **`ssh -tt` bơm stdin trực tiếp** hay bị auto-mode classifier chặn; chạy qua script
  `uv run` thì không (đã kiểm chứng). Bị chặn → nhờ user chạy tay hoặc thêm permission rule
  hẹp `Bash(uv run*ssh_client.py*)`.

## Self-improve

Menu mỗi server có thể đổi theo thời gian / khác nhau giữa server. Xem
[reference/menu-driving.md](reference/menu-driving.md) khi cần chỉnh heuristic phân loại hay
xử lý một dạng menu mới, và [reference/self-improve.md](reference/self-improve.md) cho quy tắc
cập nhật.
