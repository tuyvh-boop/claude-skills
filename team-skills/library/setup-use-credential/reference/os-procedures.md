# OS procedures — chuỗi lệnh theo hệ điều hành

Chọn ĐÚNG nhánh theo HĐH detect ở Step 0. Mỗi lệnh đánh dấu:
- **[AI chạy]** — không cần password/PAT → AI tự chạy (nếu cần `sudo`/Admin thì đưa user chạy).
- **[USER tự chạy]** — cần passphrase hoặc dán PAT → luôn giao user.

Biến thể **có / không passphrase** chỉ khác ở: (a) ghi `gpg-agent.conf` cache hay không,
(b) khi `gpg --full-generate-key` thì đặt passphrase hay để trống.

Tất cả nhánh đi theo **Hướng A + cache dài**: store đổi tên thành `~/.credentials-store`,
auto-load vào shell profile → gõ thẳng `claude`, không cần wrapper.

> ### 🔴 Bẫy chí mạng: guard non-interactive — ĐỌC TRƯỚC KHI GHI PROFILE
>
> `~/.bashrc` của Debian/Ubuntu có đoạn này ở khoảng **dòng 10**:
> ```bash
> case $- in
>     *i*) ;;
>       *) return;;      # ← shell không tương tác DỪNG Ở ĐÂY
> esac
> ```
> Claude Code (và mọi skill/tool spawn shell) chạy **shell không tương tác** — cờ `$-` không có
> `i`. Nên **mọi dòng nằm SAU guard không bao giờ chạy** trong session của Claude.
>
> `cat >> ~/.bashrc` luôn ghi vào **cuối file**, tức luôn nằm sau guard. Triệu chứng: gõ tay
> trong terminal thì `echo ${#JIRA_PAT}` ra số > 0, nhưng skill báo *"Chưa lấy được token"*.
>
> zsh dính kiểu khác nhưng cùng hậu quả: **`~/.zshrc` chỉ đọc bởi shell tương tác**. File cho
> mọi shell là **`~/.zshenv`**.
>
> → Vì vậy quy trình dưới đây tách khối credential ra **file riêng**
> `~/.config/claude-credentials.sh`, rồi chèn **một dòng `source`** vào đúng chỗ đọc được:
> **đầu `~/.bashrc`** (trước guard) với bash, **`~/.zshenv`** với zsh.

---

## 🐧 Linux (Ubuntu/Debian) — cũng dùng cho WSL

**Cài tool** — [USER tự chạy] (cần sudo)
```bash
sudo apt update && sudo apt install -y pass gnupg git
# Fedora: sudo dnf install pass gnupg2 git   ·   Arch: sudo pacman -S pass gnupg git
```

**Cấu hình môi trường** — [AI chạy]
```bash
export PASSWORD_STORE_DIR="$HOME/.credentials-store"
tty -s && export GPG_TTY="$(tty)"
```
> Chỉ set cho **shell hiện tại**, đủ để chạy `pass init` / `pass insert` ở các step sau.
> KHÔNG `>> ~/.bashrc` ở đây — bản ghi vĩnh viễn nằm trong file credential ở step Auto-load
> (nếu ghi vào cuối `~/.bashrc` sẽ dính guard non-interactive, xem hộp cảnh báo đầu file).

**Cache passphrase ~400 ngày** — [AI chạy] · CHỈ khi chọn có passphrase
```bash
mkdir -p ~/.gnupg && chmod 700 ~/.gnupg
grep -q 'default-cache-ttl' ~/.gnupg/gpg-agent.conf 2>/dev/null || cat >> ~/.gnupg/gpg-agent.conf <<'EOF'
default-cache-ttl 34560000
max-cache-ttl 34560000
EOF
gpgconf --kill gpg-agent
```

**Tạo key** — [USER tự chạy] → xem Step 4 SKILL.md (ECC/RSA-4096 · `2y` · email · passphrase mạnh).

**Backup + cổng Passbolt** — [USER tự chạy] → xem `backup-and-risk.md`.

**Init store** — [AI chạy]
```bash
gpg --list-secret-keys --keyid-format=long   # lấy fingerprint / hoặc email
pass init <email-hoặc-fingerprint>
```

**Nạp token** — [USER tự chạy] → `pass insert personal/<TÊN_BIẾN>` (xem `naming-and-insert.md`).

**Auto-load** — [AI chạy] · 2 bước, idempotent

Bước 1 — ghi khối credential ra **file riêng** (ghi đè được, không sợ trùng lặp):
```bash
mkdir -p ~/.config && cat > ~/.config/claude-credentials.sh <<'EOF'
# --- auto-load credentials cho Claude Code --- (sinh bởi skill setup-use-credential)
# Dùng chung cho bash & zsh -> không dùng cú pháp riêng của shell nào.
export PASSWORD_STORE_DIR="$HOME/.credentials-store"
tty -s && export GPG_TTY="$(tty)"
for f in "$PASSWORD_STORE_DIR/personal/"*.gpg; do
    [ -e "$f" ] || continue
    name="$(basename "$f" .gpg)"
    eval "cur=\${$name}"
    [ -n "$cur" ] && continue
    val="$(pass show "personal/$name" 2>/dev/null)" && [ -n "$val" ] && export "$name=$val"
done
unset f name val cur
EOF
```
> 3 khác biệt so với khối cũ, đều có lý do: **(a)** bỏ qua biến đã có sẵn → shell con không
> giải mã gpg lại, đỡ chậm; **(b)** `pass` lỗi thì **không** export chuỗi rỗng (biến rỗng khó
> debug hơn biến không tồn tại); **(c)** `GPG_TTY` chỉ set khi thật sự có tty — `$(tty)` trong
> shell không tương tác trả về chuỗi `not a tty`.

Bước 2 — chèn **1 dòng source lên ĐẦU `~/.bashrc`**, trước guard non-interactive:
```bash
grep -q 'claude-credentials.sh' ~/.bashrc || { printf '%s\n\n' \
  '[ -f "$HOME/.config/claude-credentials.sh" ] && . "$HOME/.config/claude-credentials.sh"' \
  | cat - ~/.bashrc > ~/.bashrc.new && mv ~/.bashrc.new ~/.bashrc; }
```
> Backup trước khi đụng profile: `cp ~/.bashrc ~/.bashrc.bak-$(date +%Y%m%d-%H%M%S)`.

**Verify** — [AI chạy] · bắt buộc, đây là bước bắt được bẫy guard
```bash
bash -c 'source ~/.bashrc; echo "opts=$-"; echo "len=${#JIRA_PAT}"'
```
`opts` phải **không có `i`** (chứng minh đang test đúng shell non-interactive) và `len` phải
**> 0**. Ra `len=0` là khối credential vẫn nằm sau guard → xem lại Bước 2.
In độ dài, **không bao giờ in giá trị token**.

---

## 🍎 macOS (cần Homebrew)

**Cài tool** — [USER tự chạy]
```bash
brew install pass gnupg pinentry-mac
```

**Cấu hình môi trường + cache** — [AI chạy] · phần cache CHỈ khi có passphrase
```bash
mkdir -p ~/.gnupg && chmod 700 ~/.gnupg
grep -q 'pinentry-program' ~/.gnupg/gpg-agent.conf 2>/dev/null || cat >> ~/.gnupg/gpg-agent.conf <<EOF
pinentry-program $(brew --prefix)/bin/pinentry-mac
default-cache-ttl 34560000
max-cache-ttl 34560000
EOF
gpgconf --kill gpg-agent
export PASSWORD_STORE_DIR="$HOME/.credentials-store"
```
> Chỉ set cho shell hiện tại (đủ cho `pass init` / `pass insert`). Bản vĩnh viễn nằm ở step
> Auto-load. KHÔNG ghi vào `~/.zshrc` — file đó chỉ shell tương tác đọc.
> Không passphrase: vẫn cần dòng `pinentry-program`, bỏ 2 dòng `*-cache-ttl`.

**Tạo key / Backup / Init store** — như Linux (Init: [AI chạy] `pass init <email-hoặc-fingerprint>`).

**Auto-load** — [AI chạy] · ghi vào **`~/.zshenv`**, KHÔNG phải `~/.zshrc`

Bước 1 — y hệt Linux: ghi `~/.config/claude-credentials.sh` (khối đó viết portable, chạy cả zsh).

Bước 2 — chèn dòng source vào `~/.zshenv`:
```bash
grep -q 'claude-credentials.sh' ~/.zshenv 2>/dev/null || \
  echo '[ -f "$HOME/.config/claude-credentials.sh" ] && . "$HOME/.config/claude-credentials.sh"' >> ~/.zshenv
```
> `~/.zshenv` được zsh đọc cho **mọi** loại shell (tương tác hay không), nên ở đây append vào
> cuối file là an toàn — không có guard nào để né. Ghi vào `~/.zshrc` thì Claude Code không
> thấy token.

**Verify** — [AI chạy]
```bash
zsh -c 'echo "len=${#JIRA_PAT}"'    # phải > 0
```

---

## 🪟 Windows — 2 hướng, đọc rồi chọn

### Hướng 1 (KHUYẾN NGHỊ): WSL2 → làm y hệt Linux
`pass` gốc là script bash, chạy mượt nhất trong WSL, **giữ đúng tên `~/.credentials-store`**.

**Cài WSL** — [USER tự chạy] (PowerShell Admin)
```powershell
wsl --install -d Ubuntu
```
Rồi mở "Ubuntu" từ Start Menu, làm **toàn bộ nhánh 🐧 Linux** bên trong. Cài luôn Claude Code
trong WSL để dùng chung env.

### Hướng 2 (native, KHÔNG WSL): gopass + Gpg4win
`gopass` = bản Go của `pass`, tương thích định dạng store, lệnh gần giống.

> ⚠️ gopass tự quản đường dẫn store qua `gopass.yml`, **không đảm bảo tôn trọng
> `PASSWORD_STORE_DIR`** ở mọi phiên bản. Cần đúng tên `credentials-store` chắc chắn → dùng
> Hướng 1 (WSL). Vẫn muốn native → chấp nhận tên mặc định gopass đặt (step Init), chỉ áp quy
> ước đặt tên cho entry bên trong.

**Cài tool** — [USER tự chạy]
```powershell
scoop install gopass gpg
# hoặc: choco install gopass gpg4win
```

**Cache passphrase ~400 ngày** — [AI chạy] · CHỈ khi có passphrase
```powershell
New-Item -ItemType Directory -Force -Path "$env:APPDATA\gnupg" | Out-Null
Add-Content "$env:APPDATA\gnupg\gpg-agent.conf" "default-cache-ttl 34560000`nmax-cache-ttl 34560000"
gpgconf --kill gpg-agent
```

**Tạo key** — [USER tự chạy]
```powershell
gpg --full-generate-key   # ECC hoặc RSA-4096 · 2y · email · passphrase mạnh (để trống nếu chọn không passphrase)
```

**Backup + cổng Passbolt** — [USER tự chạy] → `backup-and-risk.md`.

**Init store** — [AI chạy]
```powershell
gpg --list-secret-keys --keyid-format=long
gopass init <email-hoặc-fingerprint>   # store ở %LOCALAPPDATA%\gopass\stores\root
```

**Nạp token** — [USER tự chạy]
```powershell
gopass insert personal/JIRA_PAT
```

**Kiểm tra (user tự chạy)** — chỉ đếm ký tự, KHÔNG in value
```powershell
(gopass show -o personal/JIRA_PAT).Length   # ra số khác 0 = token tồn tại & giải mã được
```
> Đừng chạy `gopass show -o personal/JIRA_PAT` trần: nó in nguyên token ra terminal. Terminal
> là thứ có thể bị đọc lại (tool đọc màn hình, screen-share, scrollback, log). Verify bằng độ
> dài là đủ.

**Auto-load** — [AI chạy] · ghi vào PowerShell `$PROFILE`
```powershell
if (!(Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force | Out-Null }
if (!(Select-String -Path $PROFILE -Pattern 'auto-load credentials cho Claude Code' -Quiet)) {
Add-Content $PROFILE @'

# --- auto-load credentials cho Claude Code ---
foreach ($entry in (gopass ls --flat | Where-Object { $_ -like "personal/*" })) {
  $var = $entry -replace "^personal/",""
  Set-Item -Path "Env:$var" -Value (gopass show -o $entry)
}
'@
}
```
Đóng/mở lại PowerShell (hoặc `. $PROFILE`) rồi gõ `claude`. Thêm token sau chỉ cần
`gopass insert personal/<TÊN>`, không sửa `$PROFILE`.
