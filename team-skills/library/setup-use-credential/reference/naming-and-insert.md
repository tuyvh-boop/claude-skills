# Naming convention + phân loại token + sinh command insert

Auto-load export **tên biến = tên entry trong kho**. Nên tên entry **phải là một tên biến
môi trường hợp lệ**, và **trùng đúng tên mà `.mcp.json` tham chiếu** qua `${...}`.

## Format khung: `<TÊN_TOOL>_<LOẠI>`

`<TÊN_TOOL>` = tên dịch vụ/công cụ, CHỮ HOA, ngắn: `JIRA`, `GITHUB`, `GITLAB`, `CRM`, `SWATCH`…

`<LOẠI>` **ưu tiên** 1 trong 3 (đủ cho phần lớn trường hợp):

| Hậu tố | Dùng cho | Ví dụ |
|---|---|---|
| `_PAT` | Personal Access Token (Jira, GitHub, GitLab…) | `JIRA_PAT`, `GITHUB_PAT`, `GITLAB_PAT` |
| `_TOKEN` | token khác: API token, session/secret token | `CRM_TOKEN`, `SLACK_TOKEN`, `XYZ_TOKEN` |
| `_PASS` | mật khẩu (DB password, service password…) | `DB_PASS` |

**Không đóng khung ở 3 loại này.** Trường hợp khác (client secret OAuth, webhook signing
key, API key…) đặt hậu tố mô tả đúng bản chất, miễn theo Luật đặt tên:
```
personal/OPENAI_API_KEY
personal/STRIPE_WEBHOOK_SECRET
```

## Luật đặt tên entry (áp dụng MỌI trường hợp)

- **CHỮ HOA + gạch dưới**, dạng `<TÊN_TOOL>_<LOẠI>`.
- **Bắt đầu bằng chữ cái**; chỉ gồm `A–Z`, `0–9`, `_`.
- **KHÔNG**: chữ thường, dấu cách, gạch ngang `-`, dấu chấm, dấu tiếng Việt.
  (`jira-pat`, `jira pat`, `Jira.Pat` → SAI, shell không nhận làm tên biến.)
- **Trùng đúng tên `.mcp.json` tham chiếu** — auto-load export nguyên tên này ra env,
  `.mcp.json` đọc lại qua `${JIRA_PAT}`.

## Cách phân loại token từ mô tả tự nhiên của user

User liệt kê bằng lời → map từng cái sang `<TÊN_TOOL>_<LOẠI>`:

1. **Tách tên tool** (danh từ đầu): "jira" → `JIRA`, "crm" → `CRM`, "github" → `GITHUB`.
2. **Chọn hậu tố** theo từ khoá user dùng:
   - có chữ "pat" / "personal access token" → `_PAT`
   - "token" / "api token" / "key" chung chung → `_TOKEN` (hoặc `_API_KEY` nếu user nói "api key")
   - "password" / "mật khẩu" → `_PASS`
3. **Ghép + viết hoa + thay khoảng trắng/gạch ngang bằng `_`.**

Ví dụ: *"tôi có jira pat, crm pat, xyz token"* →

| User nói | Tên biến | Namespace |
|---|---|---|
| jira pat | `JIRA_PAT` | `personal/` |
| crm pat | `CRM_PAT` | `personal/` |
| xyz token | `XYZ_TOKEN` | `personal/` |

**Luôn trình bảng cho user chốt/sửa** trước khi sinh command. Không tự quyết tên gây khó hiểu.

## Namespace

- Skill này chỉ dùng **`personal/`** (global, auto-load vào mọi phiên).
- `projects/<app>/...` (per-project, direnv nạp riêng) = **trục B — ngoài phạm vi skill này**.
  User có token thật sự chỉ dùng cho 1 repo → vẫn đặt tạm ở `personal/` (nạp global) và ghi
  chú isolation theo repo để sau; đừng tự dựng direnv ở đây.

## Sinh command insert (để user tự chạy, dán PAT)

Với mỗi tên đã chốt, sinh 1 dòng — mỗi token 1 block dán-thẳng-terminal:
```bash
pass insert personal/JIRA_PAT
pass insert personal/CRM_PAT
pass insert personal/XYZ_TOKEN
```
(Win native: đổi `pass` → `gopass`.)

Nhắc user: lần `insert` **đầu tiên** hỏi passphrase (nhập đúng passphrase lúc tạo key, cache
lại ~400 ngày); token dán vào **không hiện màn hình**. Token thật **không** đưa vào chat.

## ⚠️ Đổi tên entry = đổi tên biến

Tên entry chính là tên biến → đổi tên file `.gpg` sẽ đổi tên biến env → phải sửa `${TÊN}`
tương ứng trong `.mcp.json`. Ghép nối này là có chủ đích: kho ↔ biến luôn khớp.
