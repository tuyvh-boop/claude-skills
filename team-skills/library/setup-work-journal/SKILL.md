---
name: setup-work-journal
description: Use when a teammate (dev, tester, BA / PMA) wants their own private work-journal repo — "dựng nhật ký làm việc cho mình", "tạo repo journal", "mình mới vào, muốn có kho lưu tài liệu làm việc", "journal máy mới chưa chặn secret", "clone journal sang máy mới, kiểm tra hook", "kiểm tra journal", "thêm phần sổ học vào journal", "nối journal lên GitHub", "hôm qua chưa tạo repo GitHub, làm tiếp". NOT for saving an artifact into an existing journal (journal-save, dev-journal-save), setting up CLAUDE.md for a code repo (setup-repo-ai), or committing / pushing the journal (git-flow).
---

# setup-work-journal

Dựng cho một người trong team một **repo nhật ký làm việc riêng tư**: khung folder theo vai trò, `CLAUDE.md` quy ước để Claude tự
cất tài liệu đúng chỗ, hook chặn secret, nối GitHub cá nhân private. Người dùng là **người mới, có thể không rành git** — giải
thích bằng lời thường, cho xem trước rồi mới làm.

**Journal là kho thuần:** chỉ quy ước + chỗ lưu. **Không** sinh template nội dung, **không** viết script bắt người dùng gõ lệnh
hằng ngày — người dùng nói với Claude, Claude đọc `CLAUDE.md` của journal rồi lưu.

Script: `S="uv run <skill>/scripts/journal_setup.py"` — mọi bước tất định (dò máy, dựng file, bật hook, tự test) đi qua nó.
`$S --help` xem lệnh.

## Chế độ

| Chế độ | Khi nào | Bước |
|---|---|---|
| **Dựng mới** | chưa có journal | 0 → 9 |
| **Thêm loại** | journal đã có, muốn thêm loại lưu trữ | 0 → 1 → 2 (chỉ câu b) → 3 → 4 → 5 → 9 |
| **Nối GitHub** | journal đã dựng, chưa có remote ("hôm qua chưa tạo repo") | `$S doctor --path P` → 7 → 9 |
| **Kiểm tra** | clone sang máy mới, nghi hook không chạy, "kiểm tra journal" | `$S doctor --path P` → sửa từng dòng ⚠️ |

## Dựng mới

| Bước | Việc |
|---|---|
| **0. Dò máy** | `$S detect --path <path gợi ý, mặc định ~/work-journal>`. Thiếu `uv` → đưa lệnh cài (bảng Cài đặt), chờ user cài rồi chạy lại. Có journal ở path đó → chuyển chế độ Thêm loại / Kiểm tra / Nối GitHub. |
| **1. Vai trò + giải thích** | Vai trò chưa rõ từ câu của user → **hỏi trước tiên** (AskUserQuestion 1 câu: Dev / Tester / BA-PMA, lưu `pma`); rõ rồi → chỉ xác nhận. Rồi in mode brief (`reference/mode-briefs.md`, điền theo bước 0, bỏ dòng không áp dụng) + "Journal giúp gì cho bạn": 2 mục đích (**ghi chép, lưu trữ** · **quan sát kết quả AI** qua `retro.md` / `implement-retro.md` để tối ưu prompt, skill) + `$S benefits --role R`. User đòi nhanh / "khỏi hỏi" → gộp brief + lợi ích còn 3–4 dòng, không bỏ hẳn. |
| **2. Hỏi** | AskUserQuestion 1 lượt, 3 câu: **(b) cần lưu gì** — multi-select từ `$S modules --role R`: 1 lựa chọn "Bộ khuyên dùng (<liệt kê id>)" tick sẵn + mỗi loại **Có thể thêm** 1 lựa chọn (mô tả 1 dòng để làm gì); `build-skills` + `build-workflow` luôn gộp 1 lựa chọn "Dựng skill / workflow AI" → tối đa 4 lựa chọn / câu cho mọi vai trò; nhóm **Loại khác** ghi 1 dòng chữ trong câu hỏi ("chọn Other nếu cần: …"). User hỏi "X là gì" → trả lời từ `templates/claude-modules/<id>.md` (đích lưu + luật), kèm 1 ví dụ dùng; hỏi về data khách / thông tin nhạy cảm → trả lời theo khối 🔴 Bắt buộc của `templates/CLAUDE.md.tmpl` (thay `[redacted]` / mô tả chung; bản thật cần giữ → `_local/` của task); **(c) đặt ở đâu** — **tên folder cũng là tên repo GitHub** (gợi ý `~/work-journal`); **(d) nối với Claude** — nói đúng ý mẫu rồi hỏi A / B / không (để biết có sinh `journal-save` trước commit đầu): *"Mặc định Claude chỉ biết journal khi bạn mở Claude **trong** folder journal. Muốn đang ở repo app mà nói 'lưu cái này vào journal' được thì chọn: **A** — một skill nhỏ `journal-save` nằm trong journal, link vào Claude, chỉ nạp khi cần lưu (khuyên dùng); **B** — 2 dòng trỏ trong cấu hình Claude cá nhân, luôn nạp mọi session; **Không** — làm việc chủ yếu trong journal (vd tester ghi kết quả test) thì không cần."* Tên chủ journal: `git_user_name` của bước 0 → **xác nhận** "ghi tên chủ là <tên> nhé?" (có thể chỉ là username) — **kể cả nhánh "khỏi hỏi"**, gộp vào bước 3. User sửa tên → hỏi thêm: commit đang ký tên `<git_user_name>`, máy **riêng** hay **dùng chung**? (chỉ hỏi, **chưa đưa lệnh** — journal chưa `git init`; làm ở bước 5); `null` → hỏi tên + email công ty, đưa 2 lệnh `git config --global user.name / user.email` cho user tự chạy **ngay** (commit bước 6 cần). User nói "khỏi hỏi" → dùng mặc định (bộ khuyên dùng, `~/work-journal`, A) và ở bước 3 **liệt kê đủ**: đã chọn gì, nhóm Có thể thêm còn gì, tên folder đổi được, cách nối Claude (A, đổi B / không được), tên chủ. |
| **3. Xem trước** | `$S plan --path P --role R --modules … --owner O --connect A|B|none --git-identity keep|own|shared` (theo câu d + việc sửa tên) → trình **cây folder + bảng file + bảng các bước sắp chạy** (script in sẵn, có cột ra ngoài máy / cần hỏi lại) + **khối cảnh báo** (bên dưới). **Dừng chờ "oke"** — kể cả khi user nói "gấp, khỏi hỏi". "oke" / "cứ làm đi" sau khi thấy preview = đồng ý **bước 4–6 kể cả commit đầu**, không hỏi lại; bước 7–8 vẫn hỏi lúc tới. Journal có `CLAUDE.md` tự viết (detect `enabled_modules: []`): đặt quy ước đang có cạnh khối sắp thêm, lệch nhau thì hỏi giữ bên nào. |
| **4. Tạo khung** | `$S apply …` (muốn chắc thì `--dry-run` trước). Có file `differs` (hook khác bản chuẩn) → cho xem diff, hỏi, không đè. |
| **5. Chặn secret** | `$S hooks --path P` (git init + bật hook) → `$S selftest --path P`. `passed: false` → sửa tới khi pass, không đi tiếp. `scanner: none` → đưa lệnh cài betterleaks (bảng Cài đặt), user tự cài, chạy lại selftest. Câu (d) chọn A → `$S companion --path P --owner O` **ngay sau selftest** (skill vào commit đầu, clone sang máy khác là có). User đã sửa tên ở bước 2 → chỉnh tên ký commit **trước bước 6**: máy dùng chung → Claude chạy `git -C P config user.name "<tên>"` + `git -C P config user.email "<email công ty>"` (config riêng của journal, hỏi email nếu chưa biết); máy riêng → đưa 2 lệnh `git config --global user.name / user.email` cho user tự chạy, chờ user báo xong rồi kiểm **cả** `git -C P config user.name` và `user.email` (hỏi email từ trước nếu chưa biết). User không muốn đổi → nói rõ commit sẽ ký tên `<git_user_name>`, rồi mới commit. |
| **6. Commit đầu** | Nói 1 câu thường (commit = chụp lại một mốc, sau này xem lại / khôi phục được) rồi `git add -A && git commit -m "chore: init work journal"` — đã được oke ở bước 3. Hook in banner + log màu của betterleaks → **diễn giải**: "no leaks found" = sạch, commit thành công; đừng để user tưởng là lỗi. |
| **7. GitHub private** | Lặp lại cảnh báo. `gh` đã đăng nhập → đề xuất `gh repo create <tên folder> --private --source . --push`, **confirm rồi mới chạy**. Chưa đăng nhập → user tự chạy `gh auth login` (Claude không chạy hộ), dặn trước cách trả lời: **GitHub.com → HTTPS → Yes (authenticate Git) → Login with a web browser** → copy mã 8 ký tự, dán vào trang mở ra. Chưa có tài khoản GitHub → tạo ở github.com (email cá nhân hoặc công ty theo quy định team) rồi quay lại. Không cài được `gh` → tạo repo trên web, **tick Private**, Claude chạy `git remote add origin <url>` + `git push -u origin main` khi user dán URL. User chưa làm được ngay → ghi ⚠️ và nói câu quay lại: *"nối journal lên GitHub"*. Có remote rồi **luôn** `$S remote-check --path P`: khác `PRIVATE` → dừng, hướng dẫn đổi sang Private ngay. User đòi public → **lần đầu** giải thích vì sao không (repo ngoài hạ tầng công ty, không thu hồi được bản đã bị xem / fork) + muốn team cùng xem thì chọn bài, gỡ data nhạy cảm, đưa vào kênh chung của team; đề xuất private 1 lần. Vẫn đòi public → đưa lệnh private để tự chạy khi đổi ý, **kết thúc bước 7** (không tạo gì, không hỏi lại), ghi ⚠️. |
| **8. Nối với Claude** | Làm theo câu (d). **(A) `journal-save`** (đã sinh ở bước 5) → `$S link-companion --path P` link vào `~/.claude/skills/` để dùng ở mọi repo; trả `conflict` → hỏi, không đè. **(B) Khối trỏ trong `~/.claude/CLAUDE.md`** (khối dưới): file chưa có → tạo mới chỉ với khối đó; đã có khối `## Nhật ký làm việc` → cho xem khối cũ, hỏi thay hay giữ; chưa có → nối cuối file. Cả hai ghi vào cấu hình cá nhân → **cho xem nội dung / diff, chờ confirm** rồi mới chạy. Không chọn gì → nhắc: chỉ dùng được khi mở Claude **bên trong** folder journal (đủ cho người làm việc chủ yếu trong journal, vd tester ghi kết quả test). |
| **9. Chốt** | Bảng ✅ / ⚠️ những gì đã làm + mục "Dùng hằng ngày" trong README journal (sinh theo đúng loại đã chọn). Nói rõ: **lưu = ghi file trên máy; lên GitHub khi bạn bảo "commit và push journal"** (vd cuối ngày). Bước 7 còn ⚠️ (chưa có remote) → câu chốt thay bằng: *"journal chưa lên GitHub — khi sẵn sàng, nói 'nối journal lên GitHub'; trước đó đừng bảo push."* Nhắc **mở session Claude mới** — trong folder journal nếu không chọn A/B, vì chỉ session mới mới nạp `CLAUDE.md` / skill vừa tạo — kèm cách mở: terminal `cd <path journal> && claude`; app desktop → chọn folder journal khi tạo session mới; VS Code → File › Open Folder rồi mở Claude Code. |

Khối trỏ global (bước 8, cách B):
```markdown
## Nhật ký làm việc
Nhật ký làm việc của mình ở `<path tuyệt đối>`. Tài liệu quá trình của task (research, plan, review, testcase…) → lưu vào đó
theo quy ước trong `<path tuyệt đối>/CLAUDE.md`; đọc file đó trước mỗi lần lưu.
```

**Hỏi hay gặp** (trả lời thẳng, không đoán):
- *Hook có làm commit chậm không?* — Không đáng kể: pre-commit chỉ quét phần vừa `git add`, pre-push chỉ quét các commit sắp đẩy; journal
  mới quét ~20 KB mất dưới 0,1 giây. Hook chỉ chặn khi thấy thứ giống secret, kèm hướng dẫn sửa.
- *Ảnh chụp bug để đâu?* — trong folder `tests/` của task (vd `tests/runs/<lượt>/evidence/`): ảnh / video trong `tests/` không lên
  git (ảnh hay dính email khách, scanner không đọc được ảnh). Để chỗ khác thì **có lên git** → đừng để ảnh có data khách ngoài
  `tests/` hoặc `_local/`.
- *Câu (d) bằng lời thường* — "Claude chỉ nhớ journal khi bạn mở Claude trong folder journal. Muốn đang làm ở chỗ khác mà vẫn
  bảo 'lưu vào journal' được thì cần nối thêm; làm việc chủ yếu trong journal thì không cần."
- *Hook là gì?* — script git tự chạy trước mỗi commit / push; ở đây nó soi nội dung xem có token / key không, có thì chặn lại.

**Khối cảnh báo** (bước 3 và 7, nguyên ý):
> 🔒 Repo này **bắt buộc Private** trên GitHub cá nhân. Nó nằm ngoài hạ tầng công ty, nên **không đưa vào:** token / mật khẩu /
> key, data khách (domain shop, email, đơn hàng), tài liệu nội bộ nhạy cảm (hợp đồng, số liệu kinh doanh, tài liệu ghi mật,
> nhận xét về đồng nghiệp). Thứ cần giữ tạm → folder `_local/` (không lên git). Hook chặn secret là lưới an toàn, không bắt
> được hết (ảnh, data khách viết tay) — lớp đầu tiên là bạn.

## Cài đặt (user tự chạy — Claude không chạy lệnh cài phần mềm)

| Công cụ | macOS | Linux | Windows |
|---|---|---|---|
| `uv` | `brew install uv` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `winget install --id=astral-sh.uv -e` |
| `betterleaks` | `brew install betterleaks` | Fedora `sudo dnf install betterleaks`; khác: tải binary ở [Releases](https://github.com/betterleaks/betterleaks/releases), giải nén vào `~/.local/bin` | tải binary ở Releases, thêm vào PATH |
| `gh` | `brew install gh` | `sudo apt install gh`; không sudo: binary ở [Releases](https://github.com/cli/cli/releases) vào `~/.local/bin` | `winget install --id GitHub.cli` |

Không có sudo / quyền admin: mọi công cụ trên đều có binary — giải nén vào `~/.local/bin` (Linux / macOS, đảm bảo nằm trong PATH)
hoặc một folder trong PATH (Windows). Không cài được `gh` → tạo repo trên web, tick Private.

Chỉ dùng betterleaks (gitleaks đã đóng băng tính năng, không hỗ trợ). Chưa cài → hook quét bằng pattern (yếu hơn), selftest vẫn pass,
nhưng chốt ở bước 9 phải ghi ⚠️ "nên cài betterleaks".

## Ranh giới — không làm

| Cám dỗ | Thay bằng |
|---|---|
| "User gấp / khỏi hỏi → dựng luôn" | Bước 3 vẫn bắt buộc: người mới phải thấy cây folder trước khi có file trên máy |
| Thêm `templates/`, `scripts/new-day.sh`, mẫu daily | Không. Kho thuần; nội dung do skill / Claude sinh lúc cần |
| User muốn public "để team học hỏi" | **Không bao giờ tạo public.** Muốn chia sẻ → chọn bài, gỡ data khách / tài liệu nội bộ, đưa vào kênh chung của team (wiki, repo team) theo quy định team — việc riêng, ngoài skill này |
| Khuyên bật GitHub secret scanning / push protection | Không miễn phí cho repo private; hook local là lớp chặn của journal |
| Dùng gitleaks / `.gitleaks.toml`, `.pre-commit-config.yaml` | Gitleaks đóng băng tính năng, `[[allowlists]]` bị betterleaks v2 bỏ / framework phải cài thêm. Hook dùng `.githooks/scan.sh` với betterleaks |
| "Hook đã chép, chắc chạy" | `selftest` phải `passed: true` trước khi commit đầu |
| Tự ghi `~/.claude/CLAUDE.md`, tự cài phần mềm, tự push | Hỏi / đưa lệnh cho user |

## Common Mistakes

- **Không có `CLAUDE.md` trong journal** → Claude không biết lưu đâu, journal chỉ còn là folder trống. `apply` luôn tạo / gộp nó.
- **Đè `CLAUDE.md` người dùng tự viết.** `apply` chỉ nối thêm khối `core` + module ở cuối; đừng Write đè tay.
- **Hook không chạy sau khi clone**: git không mang `core.hooksPath` theo. Máy mới → chế độ Kiểm tra.
- **Hook bị CRLF trên Windows** → shebang hỏng, hook im lặng. `.gitattributes` đã ép `eol=lf`; vẫn lỗi thì `doctor`.
- **Báo nhầm secret**: thêm comment `betterleaks:allow` cuối dòng (v1 + v2 đều nhận). Không allowlist cả đuôi `.md` (tắt scan cả journal).

## Tự cải thiện

Danh mục loại lưu trữ, cờ scanner, lỗi cài theo OS lớn dần theo phản hồi. Protocol + gate: `reference/self-improve.md`.
