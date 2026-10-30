---
name: setup-use-credential
description: Use when setting up encrypted credential storage (pass/gpg, hoặc gopass trên Windows native) để Claude Code + MCP dùng token/PAT mà không để plaintext trên đĩa. Triggers on "setup lưu token/PAT", "cài pass gpg cho credential", "lưu jira pat cho claude", "setup credential store", "nạp token cho Claude Code an toàn", "mã hoá token cho AI". KHÔNG dùng cho trục B (git-sync store + direnv per-project) — skill này chỉ lo token global (personal/, auto-load).
---

# Setup & Use Credential

## Overview

Chạy trên máy user → dựng **kho token mã hoá tập trung** theo **"Hướng A + cache dài"**
(có passphrase, cache ~400 ngày, auto-load vào shell profile — gõ thẳng `claude`, không
cần lệnh riêng). Skill **chủ động làm giúp mọi step chạy được**, chỉ giao user đúng 3 chỗ
bắt buộc tự tay: (1) nhập passphrase khi tạo key, (2) export key để backup, (3) dán PAT
lúc `insert`.

Skill này tự chứa — toàn bộ chuỗi lệnh đã chưng cất vào `reference/`. Chạy theo reference,
không đọc chéo file nào khác lúc thao tác.

## Nguyên tắc cốt lõi (non-negotiables)

1. **KHÔNG tự chạy step cần passphrase hoặc dán PAT.** `gpg --full-generate-key`,
   `gpg --export-secret-keys`, `gpg --gen-revoke`, `pass insert` → luôn đưa lệnh cho **user tự chạy**.
2. **KHÔNG in giá trị token ra output — của AI lẫn của user.** Không `cat` / `echo $VAR` /
   `pass show` trần. Nhãn "user tự chạy" KHÔNG phải hàng rào: terminal vẫn bị đọc lại được
   (tool đọc màn hình, screen-share, scrollback, log). Verify luôn bằng **độ dài**:
   `pass show personal/X | wc -c` hoặc `echo ${#X}`. Xem `CLAUDE.md` ở gốc repo.
3. **Cổng Passbolt bắt buộc.** Chưa xác nhận đã đưa key backup lên Passbolt → KHÔNG sang
   phần nạp token (Step 8–9).
4. **Backup key ngay sau khi tạo** — chống lockout (rủi ro Kiểu 1), trước khi làm gì tiếp.
5. **Idempotent.** Step đã xong (tool đã cài, key/store/auto-load đã có) → báo & bỏ qua,
   không cài lại, không ghi trùng vào profile/config.
6. **Chỉ lo `personal/` (global).** Per-project isolation = trục B (direnv) — **ngoài phạm
   vi skill này**, chỉ ghi 1 dòng pointer.

## Rule ownership (sửa ở đây, không nơi khác)

| Cần đổi... | Sửa |
|---|---|
| Chuỗi lệnh theo HĐH (Linux/macOS/Win-WSL/Win-gopass), biến thể có/không passphrase | `reference/os-procedures.md` |
| Quy ước đặt tên + cách phân loại token NL→biến + sinh command insert | `reference/naming-and-insert.md` |
| Backup key (export/revoke), cổng Passbolt, rủi ro Kiểu 1/2 | `reference/backup-and-risk.md` |
| Thứ tự bước, non-negotiables, nội dung Step 1 | file này |

## Workflow

Chạy tuần tự. `[Model: X — mode]` theo convention team (`shared/CLAUDE.md`). Phần lớn là
main loop vì có tương tác + chạy lệnh local.

### Step 0 — Detect môi trường & trạng thái  **[Model: — main loop]**

Xác định HĐH + shell (máy này Windows/PowerShell → nhánh gopass native hoặc WSL, xem
`reference/os-procedures.md`). Kiểm tra idempotent, **báo trạng thái từng cái**:

- Đã cài `pass`/`gopass` + `gpg` chưa?
- Đã có GPG key chưa (`gpg --list-secret-keys`)?
- Store `~/.credentials-store` tồn tại chưa?
- Auto-load đã có trong shell profile chưa (grep marker `auto-load credentials cho Claude Code`)?

Step nào đã xong → bỏ qua ở dưới, chỉ làm phần thiếu.

### Step 1 — Vì sao cần setup này  **[Model: — main loop]**

Trình đúng khối dưới đây cho user (đã chốt với user, giữ nguyên đầu mục + icon):

---

#### Tại sao cần lưu trữ tập trung các credentials?
Càng làm với AI và nhiều tool, token càng nhiều (Jira PAT, GitHub PAT, token CRM, API key…).
Nếu nhét rải rác trong `.env`, config từng project, hay note tạm thì: không biết mình có bao
nhiêu, cái nào để đâu; token nằm **chữ thô** ở nhiều chỗ, rò một chỗ là lộ; đổi/thu hồi phải
sửa nhiều nơi. Gom về **một kho mã hoá tập trung** để dứt điểm mấy chuyện đó.

#### Setup này làm gì
Dùng **`pass` + `gpg` (GnuPG)** mã hoá từng token thành một file `.gpg` — mở ra chỉ thấy rác,
chỉ key của bạn giải mã được. Nhờ vậy tránh được:

- ✅ **Không có file plaintext chứa token** trên đĩa (khác hẳn `.env`).
- ✅ **Đọc trúng file `.gpg` cũng vô dụng** — chỉ thấy ký tự mã hoá.
- ✅ **Lỡ backup thiếu / sync nhầm / đẩy nhầm lên git** — thứ lộ ra vẫn là bản mã hoá.
- ✅ **Tool tự index thư mục, hay lỡ share màn hình** — không phơi token trần.
- ✅ **Claude đọc token từ env KHÔNG làm token lên Anthropic.** Đường đi: `pass (.gpg)` →
  giải mã → env `$JIRA_PAT` → MCP server (chạy **local**) → gọi thẳng API Jira/GitHub (token
  tới đúng đích `api.atlassian.com`/`api.github.com`). Biến env không tự vào transcript,
  `.mcp.json` chỉ chứa `${JIRA_PAT}` (placeholder) nên Claude đọc config cũng chỉ thấy tên
  biến — token sống trong RAM và đi tới dịch vụ đích, **không rẽ qua Anthropic**.

⚠️ **Nó KHÔNG làm được — đừng hiểu nhầm:**
- ❌ **Không giấu token khỏi Claude lúc chạy.** Muốn gọi API thì token phải giải mã và nạp vào
  env — Claude *có* token thật ở đó. pass/gpg giấu token **khỏi ổ đĩa**, không giấu khỏi tiến
  trình đang dùng.
- ❌ **Không cứu được khi máy bị chiếm toàn bộ đúng lúc key đang mở khoá** (cache còn sống) —
  lúc đó passphrase không chặn được nữa.

#### Lưu ý khi dùng PAT chung với AI
Token đi qua env thì **không** lên Anthropic (như trên). Rủi ro duy nhất là **gián tiếp** —
token lọt vào **transcript chat** khi nó xuất hiện dưới dạng chữ trong hội thoại. Anthropic
chỉ nhận thứ nằm trong transcript, nên **chỉ cần token thành chữ trong chat là có khả năng
được gửi về server Anthropic.** Vậy nên:

- 🚫 **Tuyệt đối không dán token thẳng vào khung chat** với Claude.
- 🚫 **Không nhờ Claude `cat` / `echo $JIRA_PAT` / đọc file chứa token** để "kiểm tra" hay
  "debug" — output đó lọt transcript.
- 🚫 **Không hard-code token vào `.mcp.json`**; luôn dùng `${JIRA_PAT}` để Claude đọc config
  chỉ thấy tên biến.
- ✅ Để Claude **tự lấy token qua env** (auto-load lo) — bạn không phải đưa token vào chat lần nào.

#### Sau khi chạy xong skill này bạn sẽ có gì
Toàn bộ credentials nằm tập trung, mã hoá, trong `~/.credentials-store/`, cấu trúc như sau:

```
~/.gnupg/                        ← CHÌA KHOÁ (GPG key + cấu hình cache passphrase)
   ├── private key + public key      ↳ thứ giải mã mọi token; KHÔNG bao giờ share private
   └── gpg-agent.conf                ↳ cache passphrase ~400 ngày, đỡ nhập lại

~/.credentials-store/            ← KHO TOKEN (mỗi token = 1 file .gpg mã hoá)
   └── personal/
       ├── JIRA_PAT.gpg               ← tên file = tên biến env
       └── GITHUB_PAT.gpg

~/.bashrc (hoặc .zshrc / $PROFILE)   ← auto-load: tự export token vào env khi mở terminal
```

Và về sau, **thêm một token mới chỉ cần đúng 1 lệnh** — auto-load tự nạp ở lần mở terminal
sau, không phải sửa gì thêm:

```bash
pass insert personal/GITLAB_PAT
```

> Muốn hiểu kỹ cơ chế (vì sao mở `.gpg` ra rác mà Claude vẫn có token qua env, token đi đường
> nào, rủi ro Kiểu 1/Kiểu 2 khi tự giữ GPG key), xem `reference/backup-and-risk.md`.

---

### Step 2 — Hỏi passphrase  **[Model: — main loop, AskUserQuestion]**

Hỏi user muốn đặt passphrase không, dùng AskUserQuestion. Đặt option **khuyến nghị lên đầu**:

- **Có passphrase (khuyến nghị)** — *Đặt 1 mật khẩu bảo vệ key. Nhờ cache ~400 ngày nên gần
  như chỉ nhập 1 lần/năm. Là lớp chặn nếu máy bị chiếm lúc vừa khởi động. Chọn cái này thì
  nhớ **lưu passphrase vào Passbolt** để khỏi quên — quên passphrase là mất luôn kho.*
- **Không passphrase** — *Tiện, không phải nhập gì. Đổi lại mất lớp chặn ở kịch bản nặng nhất:
  ai lấy được file key là giải mã được kho. Token vẫn không nằm plaintext trên đĩa (vẫn hơn
  `.env`).*

Ghi lại lựa chọn → quyết định biến thể lệnh cache + key gen ở Step 3–4.

### Step 3 — Cài tool + cấu hình  **[Model: — main loop / AI chạy]**

Theo nhánh HĐH trong `reference/os-procedures.md`. **AI tự chạy** phần không cần password:

- Cài `pass`+`gnupg` (Linux/mac/WSL) hoặc `gopass`+`gpg` (Win native). Lệnh cần `sudo`/Admin
  → đưa cho user chạy, đừng tự sudo.
- Set `PASSWORD_STORE_DIR="$HOME/.credentials-store"` + `GPG_TTY` vào shell profile.
- Nếu Step 2 chọn **có passphrase**: ghi `gpg-agent.conf` cache ~400 ngày rồi `gpgconf --kill gpg-agent`.
  Chọn **không passphrase**: bỏ qua cache config.

Chạy xong báo rõ đã cài/ghi gì.

### Step 4 — Tạo GPG key  **[Model: — main loop / USER tự chạy]**

Đưa lệnh cho **user tự chạy** (cần passphrase, không tự chạy hộ):

```bash
gpg --full-generate-key
```

Hướng dẫn từng prompt: ECC (sign and encrypt) hoặc RSA-4096 · thời hạn `2y` · real name/email
của user · **passphrase mạnh, không tái sử dụng** (nếu Step 2 chọn không passphrase → để trống).
Chờ user báo tạo xong rồi mới đi tiếp.

### Step 5 — Backup key + CỔNG Passbolt  **[Model: — main loop / USER export → AI gate]**

Theo `reference/backup-and-risk.md`. Đưa **user tự chạy** (cần passphrase):

```bash
mkdir -p ~/gpg-backup && gpg --export-secret-keys --armor <email> > ~/gpg-backup/private-key.asc
gpg --gen-revoke <email> > ~/gpg-backup/revoke.asc
```

Nhắc: đưa `private-key.asc` + `revoke.asc` + **passphrase** lên **Passbolt** (chỗ cất "chìa
khoá của chìa khoá"), rồi **xoá `~/gpg-backup`**. Không commit/đẩy key lên nơi công khai.

**🚧 CỔNG BẮT BUỘC:** hỏi user xác nhận *"đã đưa key backup lên Passbolt chưa?"*. **Chưa
xác nhận → DỪNG, không sang Step 6.** Đây là chốt chống lockout (Kiểu 1) trước khi có token
trong kho.

### Step 6 — Khởi tạo store  **[Model: — main loop / AI chạy]**

AI tự chạy: lấy fingerprint rồi init store (đường dẫn nhờ `PASSWORD_STORE_DIR` ở Step 3):

```bash
gpg --list-secret-keys --keyid-format=long   # lấy fingerprint 40 hex / hoặc dùng email
pass init <email-hoặc-fingerprint>            # gopass init trên Win native
```

### Step 7 — Auto-load  **[Model: — main loop / AI chạy]**

AI ghi khối auto-load ra **file riêng `~/.config/claude-credentials.sh`**, rồi chèn **1 dòng
`source`** vào đúng chỗ shell KHÔNG tương tác đọc được — dùng khối trong
`reference/os-procedures.md`, chỉ nạp `personal/`. Idempotent (grep marker trước khi chèn).

> 🔴 **KHÔNG `cat >> ~/.bashrc`.** `~/.bashrc` Debian/Ubuntu `return` ở ~dòng 10 với shell
> không tương tác, mà Claude Code chạy đúng loại shell đó → append vào cuối file = token
> không bao giờ nạp. Bash: chèn lên **đầu** `~/.bashrc`. Zsh: dùng **`~/.zshenv`**, không phải
> `~/.zshrc`. Chi tiết + lý do: hộp cảnh báo đầu `reference/os-procedures.md`.

Chạy **Verify** ngay trong step này (`bash -c 'source ~/.bashrc; echo ${#JIRA_PAT}'` phải ra
số > 0) — đừng đợi tới Step 10, vì đây là bước duy nhất bắt được bẫy guard.

Ghi 1 dòng cho user: **per-project isolation (token riêng theo repo) là trục B/direnv — chưa
nằm trong skill này.**

> **— Hạ tầng xong tới đây. Giờ mới sang phần token. —**

### Step 8 — Hỏi token cần lưu + phân loại tên  **[Model: — main loop, AskUserQuestion]**

Hỏi user liệt kê token họ có. AI **phân loại + đề xuất tên biến** theo
`reference/naming-and-insert.md`. Ví dụ user nói *"jira pat, crm pat, xyz token"* → đề xuất:

| Token user nói | Tên biến đề xuất | Namespace |
|---|---|---|
| jira pat | `JIRA_PAT` | `personal/` |
| crm pat | `CRM_PAT` | `personal/` |
| xyz token | `XYZ_TOKEN` | `personal/` |

Trình bảng cho user **chốt/sửa tên** trước khi sinh command. (Token thật user KHÔNG dán ở đây.)

### Step 9 — Insert token  **[Model: — main loop / USER dán PAT]**

Sau khi qua cổng Step 5 + chốt tên Step 8, đưa **list command dán-thẳng-terminal**, mỗi token
một block, để **user tự chạy + dán PAT**:

```bash
pass insert personal/JIRA_PAT
pass insert personal/CRM_PAT
pass insert personal/XYZ_TOKEN
```

Nhắc: lần `insert` đầu tiên sẽ hỏi passphrase (nhập đúng passphrase Step 4, cache lại ~400
ngày); token dán vào không hiện màn hình. Trên Win native đổi `pass` → `gopass`.

### Step 10 — Verify & báo cáo  **[Model: — main loop]**

- Verify token giải mã được — **đếm ký tự, không in value** (lệnh này an toàn, AI chạy được):
  `pass show personal/JIRA_PAT | wc -c` → ra số khác 0 là OK. Win native:
  `(gopass show -o personal/JIRA_PAT).Length`.
  KHÔNG dùng `pass show personal/JIRA_PAT` trần để "xem có đúng không" — in token ra terminal
  là đã lộ, kể cả khi user tự gõ.
- AI tự chạy kiểm tra auto-load bằng **shell không tương tác** (chỉ in độ dài, không in value):
  `bash -c 'source ~/.bashrc; echo "opts=$-"; echo "len=${#JIRA_PAT}"'` — `opts` không có `i`
  và `len` > 0 thì mới thật sự đạt. Test trong terminal tay không chứng minh được gì.
- Nhắc user: session Claude Code **đang mở** vẫn dùng snapshot shell cũ → phải mở session mới
  thì token mới vào env.
- Tổng kết: đã cài gì, key + backup trạng thái, passphrase có/không, token nào đã nạp,
  auto-load ghi ở file nào, `.mcp.json` cần tham chiếu `${TÊN_BIẾN}` tương ứng.

## Common Mistakes

- **Tự chạy `gpg --full-generate-key`/`pass insert` hộ user** → kẹt vì prompt passphrase/PAT,
  và có nguy cơ chạm token. Luôn giao user.
- **`cat`/`echo`/`pass show` in token** → lọt transcript hoặc scrollback. Verify bằng độ dài
  (`| wc -c`, `${#VAR}`). Giao cho user tự gõ cũng không cứu được — terminal vẫn đọc lại được.
- **Đưa command insert trước khi backup key** → hở cổng Passbolt, lỡ mất key là lockout.
- **Cài lại / ghi trùng auto-load** khi đã có → hỏng profile. Luôn detect trước (Step 0).
- **Append auto-load vào cuối `~/.bashrc`** → nằm sau guard non-interactive, Claude Code không
  bao giờ thấy token, dù terminal tay vẫn chạy ngon. Đây là lỗi đã xảy ra thật. Chèn lên đầu
  `~/.bashrc` (bash) hoặc dùng `~/.zshenv` (zsh) — xem Step 7.
- **Verify bằng `echo $JIRA_PAT` trong terminal tay** → shell tương tác luôn pass, không chứng
  minh được gì. Phải test shell không tương tác: `bash -c 'source ~/.bashrc; echo ${#JIRA_PAT}'`.
- **`export VAR="$(pass show ...)"` mà không chặn lỗi** → `pass` fail thì export chuỗi rỗng,
  script báo lỗi khó hiểu hơn là biến không tồn tại. Chỉ export khi giá trị khác rỗng.
- **Đụng vào trục B** (git-sync store, direnv per-project) → ngoài phạm vi. Chỉ pointer.
- **Bịa tên token** không theo quy ước → shell không nhận làm tên biến. Theo `naming-and-insert.md`.

## Files

- `reference/os-procedures.md` — chuỗi lệnh theo HĐH (Linux/macOS/Win-WSL/Win-gopass), đánh
  dấu [AI chạy] vs [USER tự chạy], biến thể có/không passphrase, khối auto-load từng shell.
- `reference/naming-and-insert.md` — quy ước đặt tên `<TOOL>_<LOẠI>`, luật đặt tên, cách phân
  loại token từ mô tả tự nhiên, sinh command insert.
- `reference/backup-and-risk.md` — backup key (export + revoke), cổng Passbolt, rủi ro Kiểu 1
  (mất key) / Kiểu 2 (lộ key) và cách chặn.
