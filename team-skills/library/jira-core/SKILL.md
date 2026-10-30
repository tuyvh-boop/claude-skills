---
name: jira-core
description: Skill NỀN để thao tác Jira Cloud của team bằng JIRA_PAT (scoped token) — KHÔNG gọi trực tiếp. Chứa toàn bộ kiến thức về API Jira (auth qua gateway api.atlassian.com, cloudId, project, custom field, ADF↔text) và helper CLI jira_client.py (get/search/comments/transitions/comment/transition/assign/edit/raw). CÒN giữ CHUẨN QUY TRÌNH TEAM: luồng status + ai-assign-cho-ai từng mốc + Change Size (reference/workflow.md) và mẫu comment TH1/TH2/TH3 (reference/comment-templates.md) — đọc trước khi đổi status/comment. Mọi skill cần đọc/ghi Jira (sprint-sheet-write, sprint-report, using-git-worktree, review-code-after-fix...) nạp skill này thay vì tự gọi API hay dùng Atlassian MCP. Đọc khi cần lấy issue/comment, search JQL, đổi status, comment, assign, hay bất kỳ thao tác Jira nào.
---

# Jira Core

## Overview

Một chỗ duy nhất giữ "sự thật" về cách nói chuyện với **Jira Cloud của team** (`optis-app.atlassian.net`)
qua **JIRA_PAT** (scoped token). Mọi skill Jira **tái dùng** skill này thay vì tự dựng lại
auth/endpoint hay phụ thuộc Atlassian MCP (OAuth). Cái gì chạy được bằng script → đã đóng
thành hàm/subcommand trong `jira_client.py` để **AI khỏi tốn token suy luận lại**.

**Nguyên tắc cốt lõi:**
1. **Kiến thức ở config, cơ chế ở script.** site/cloudId/project/field/alias **và email cá nhân**
   → `config.yml` (GITIGNORED, không commit; khuôn commit là `config.example.yml`). Logic gọi API
   → `jira_client.py`. Không còn `profile.yml`.
2. **Không bao giờ in token.** Script đọc token từ env `$JIRA_PAT`, trống thì fallback
   `pass show` (capture, không in). **Verify chỉ bằng `doctor`/`myself`** — KHÔNG tự gõ
   `cat`/`echo`/`env`/`pass show` trần (bẫy `${VAR:-...}` bung ra token → lọt transcript).
3. **Đọc luôn qua convert ADF→text.** Không đổ ADF JSON thô vào context (tốn token) — script
   convert sẵn. Ghi thì text→ADF tự động.
4. **Ghi là thao tác thật — mặc định dry-run.** Mọi lệnh GHI in payload trước; chỉ ghi thật
   khi thêm `--commit`. Trước khi `--commit` một thao tác ngoài-nhìn (comment/transition/
   assign/edit) → **hỏi user xác nhận** theo rule an toàn.
5. **Tự lớn dần (self-improve).** Gặp endpoint/field/status chưa có tài liệu → dò bằng `raw`,
   làm xong **ghi bổ sung vào skill** và **báo user** (xem *Self-improve* bên dưới).

## Yêu cầu môi trường (kiểm tra TRƯỚC khi chạy)

- **Token**: env `$JIRA_PAT` có sẵn (terminal đã auto-load), hoặc `pass show personal/JIRA_PAT`
  chạy được (fallback). Không có cả hai → **user chưa dựng PAT/kho token**: đi theo *Lần đầu
  dùng → nhánh A* (giao user tạo PAT trên Atlassian + backup + setup store TRƯỚC), đừng chỉ
  bảo user `export` một token chưa tồn tại.
- **Token admin tạm (sửa cấu hình workflow/status/sprint/board)**: thêm `JIRA_TOKEN_ENV=JIRA_ADMIN_PAT`
  trước lệnh để dùng token khác JIRA_PAT cho riêng lệnh đó (pass entry `personal/<tên biến>`).
  `doctor` in tên biến đang dùng. Cách tạo token + scope: `instructions/jira/jira-admin-config-token.md`.
- **config.yml**: tồn tại + có `email` đúng tài khoản Atlassian. Chưa có → tạo từ
  `config.example.yml` (xem *Lần đầu dùng*). File này đã .gitignore — an toàn để chứa email.
- Chạy Python bằng `uv` (PEP 723, tự cài dep):
  ```bash
  uv run <path>/jira-core/scripts/jira_client.py <command> ...
  ```
- Kiểm tra nhanh toàn chuỗi: **`doctor`** → in config/site/email/nguồn-token/whoami (không in token).

## Lần đầu dùng

Chạy `doctor` trước. Kết quả rẽ 2 nhánh:

### A. Chưa có PAT / kho token (setup lần đầu tuyệt đối) — DỪNG, giao việc cho user rồi quay lại

Dấu hiệu: `doctor` báo **không lấy được token** (cả env `$JIRA_PAT` lẫn `pass show
personal/JIRA_PAT` đều trống) và user xác nhận **chưa từng tạo PAT / chưa dựng kho token**.
Đây KHÔNG phải lỗi để tự sửa bằng `export` — user chưa có token nào để export. **Không chạy
tiếp thao tác Jira.** Trình đúng các bước user phải tự làm TRƯỚC, rồi mới quay lại chạy skill:

1. **Tạo API token (PAT) trên Atlassian** tại
   <https://id.atlassian.com/manage-profile/security/api-tokens>.
   **Nên chọn loại "API token with scopes"** (token có scope) và chỉ cấp đúng scope cần —
   để giới hạn thao tác quan trọng (write/delete), an toàn hơn token full-access.
2. ⚠️ **PAT đại diện cho CHÍNH user thao tác** — ai cầm token là thao tác Jira dưới danh
   nghĩa user. Vì vậy:
   - **Backup PAT ngay** vào một password manager an toàn — **khuyến nghị Passbolt** (kho
     token chỉ nằm trên 1 máy; mất máy/mất key là mất token, Atlassian không cho xem lại
     giá trị sau khi tạo → phải backup nơi khác).
   - **Lưu cẩn thận, không dán vào chat/commit/file thường.** Lộ ra là phải **revoke +
     tạo lại** ngay tại link trên.
3. **Nạp PAT vào kho token mã hoá** để skill đọc được qua env `$JIRA_PAT` (không plaintext
   trên đĩa) — làm theo skill `setup-use-credential` (dựng `pass`/`gpg` + auto-load, `insert`
   entry `personal/JIRA_PAT`). User tự dán PAT lúc `insert`; Claude không cầm giá trị.
4. **Mở terminal mới** (để auto-load nạp `$JIRA_PAT`) rồi **quay lại chạy skill**. Verify
   bằng `doctor` — phải thấy nguồn-token + whoami (không in token).

→ Xong bước 1–4 thì rơi sang nhánh B (setup config). **Không in giá trị token ở bất kỳ bước
nào** — verify chỉ bằng `doctor`/`myself` hoặc độ dài (`echo ${#JIRA_PAT}`).

### B. Đã có PAT + kho token, chỉ thiếu `config.yml` (máy mới clone repo)

1. Copy `config.example.yml` → `config.yml` (đã .gitignore — an toàn).
2. Hỏi user email tài khoản Atlassian + điền `email:`, `site:` thật vào `config.yml`.
3. Chạy `doctor` verify. Tuỳ chọn: chạy `projects` rồi cập nhật mục `projects:` trong
   `config.yml` cho khớp quyền truy cập của user.

## CLI reference (`jira_client.py`)

Chạy: `uv run scripts/jira_client.py <command> [options]`

### Đọc (read-only — chạy thoải mái)

| Lệnh | Việc | Options |
|---|---|---|
| `doctor` | Verify AN TOÀN: config/site/email/nguồn-token/whoami (KHÔNG in token) | — |
| `myself` | User hiện tại (verify token) | — |
| `projects` | List mọi project user truy cập được | `--json` |
| `get <KEY>` | 1 issue gọn (description ADF→text) | `--fields a,b` (tên thân thiện OK) · `--json` · `--raw` (JSON gốc) |
| `comments <KEY>` | List comment (id + created + author + body→text) | `--json` |
| `search "<JQL>"` | JQL search, tự phân trang | `--fields` · `--limit N` · `--json` |
| `changelog KEY [KEY…]` | Lịch sử đổi status (read-only): `{key: [{at, from, to}]}` — dùng tính cycle time / thời gian ở từng status | `--json` |
| `transitions <KEY>` | List transition khả dụng (id + name) | — |

### Ghi (side-effect — mặc định DRY-RUN, thêm `--commit` mới ghi thật)

| Lệnh | Việc | Options |
|---|---|---|
| `comment <KEY> --text "..."` | Thêm comment (text→ADF, markdown tối thiểu) | `--text-file <path>` · `--commit` |
| `comment-edit <KEY> <ID> --text "..."` | Sửa nội dung 1 comment đã có (PUT, giữ id — không tạo comment mới); dry-run in cả nội dung cũ | `--text-file <path>` · `--commit` |
| `attach <KEY> <file>...` | Upload file đính kèm (ảnh bằng chứng, log…) vào issue; in id + link content. Muốn ảnh hiện INLINE trong comment → xem `reference/adf.md` mục "Nhúng ảnh inline" | `--name <tên hiển thị>` (1 file) · `--commit` |
| `description <KEY> --text "..."` | Ghi description cho task (heading **h1–h3**, khác comment h3–h4). **Không đè** description đã có nội dung — cần `--force`. Format: [`reference/description-templates.md`](reference/description-templates.md) | `--text-file <path>` · `--force` · `--commit` |
| `transition <KEY> --to "<name\|alias>"` | Chuyển status (alias trong `status_aliases`) | `--commit` |
| `assign <KEY> --to <email\|me\|accountId>` | Gán người (email→accountId tự tra) | `--commit` |
| `edit <KEY> --field <f> --value <v>` | Sửa 1 field. Tự bọc kiểu: description→ADF, labels tách phẩy, priority→`{name}`, custom select→`{value}`, number→số (đọc schema từ `/field`) | `--value-json '<json>'` (kiểu lạ) · `--commit` |

### Vạn năng

| Lệnh | Việc |
|---|---|
| `raw <METHOD> <path> [--data <json>] [--query k=v]...` | Gọi endpoint Jira REST bất kỳ qua auth+gateway đã đóng gói. GET chạy thẳng; method khác mặc định dry-run, thêm `--commit`. |

`raw` là **nền cho "thao tác mọi thứ"**: endpoint chưa có subcommand riêng vẫn gọi được ngay
mà không phải dựng lại auth. Cũng là công cụ để **dò rồi self-improve**.

## Field thân thiện

`--fields` / `edit --field` chấp nhận **tên thân thiện** khai trong `config.yml > fields`
(vd `change_size`, `sprint`, `story_points`) — script tự map sang `customfield_xxxxx`. Field
chuẩn (`summary`, `status`, `assignee`, `priority`, `issuetype`, `labels`, `parent`,
`description`, `created`, `updated`…) dùng thẳng tên.

## Quy trình & comment chuẩn của team (BẮT BUỘC theo khi đổi status / comment)

Trước khi `transition` (đổi status) hoặc `comment` báo tiến độ một task, **đọc và tuân**:

- [`reference/workflow.md`](reference/workflow.md) — luồng status + **ai chuyển → assign cho ai**
  từng mốc, vòng lặp sửa-review / test-ra-bug, và quy tắc field Change Size theo role. Đổi status
  thì phải kèm **assign đúng người kế tiếp** và **đúng comment** như bảng quy định.
- [`reference/comment-templates.md`](reference/comment-templates.md) — mẫu nội dung comment 4 tình
  huống (**TH0** cập nhật tiến độ: code xong 1 phase/lượt, link commit-trong-MR · **TH1** done dev/gửi review · **TH2** đã fix review · **TH3** đã merge test), kèm **cơ chế
  định dạng** (`text_to_adf` hiểu markdown tối thiểu — xem `reference/adf.md`).
- [`reference/description-templates.md`](reference/description-templates.md) — format viết
  **description** cho task/bug: heading **h1–h3** (khác comment), khung mục cho bug/feature. Đọc
  trước khi ghi description bằng subcommand `description`.

Không tự chế luồng/nội dung: đổi status mà quên assign người kế / dùng sai template là sai chuẩn
team. Vẫn giữ rule an toàn — mọi `--commit` thao tác ghi phải hỏi user trước.

## Self-improve (BẮT BUỘC làm khi gặp cái mới)

Khi user hỏi/nhờ một thao tác Jira mà **chưa có** subcommand/field/endpoint tương ứng:

1. **Dò** bằng `raw` (vd `raw GET /rest/api/3/field` để tìm custom field id, thử endpoint
   trong Jira REST v3).
2. **Làm xong việc cho user** bằng `raw` (hoặc subcommand nếu hợp).
3. **Ghi bổ sung vào skill** đúng chỗ:
   - Endpoint mới → thêm dòng vào `reference/api-map.md` (bảng *Endpoint đã dùng*).
   - Custom field id mới → thêm vào `config.yml > fields`.
   - Status/transition mới hay dùng → thêm alias vào `config.yml > status_aliases`.
   - Thao tác lặp lại / vừa phải dùng `raw` cho việc hay gặp → **tự thêm hẳn subcommand** vào
     `jira_client.py` (lệnh ghi thì mặc định dry-run) + cập nhật bảng CLI, **không cần hỏi**
     user (user cho phép 24-09-2026). Chỉ báo lại sau khi thêm.
   - Node ADF hiển thị sai → sửa `adf_to_text()` + ghi chú `reference/adf.md`.
4. **Báo user** một dòng: *"Đã bổ sung `<X>` vào jira-core (`<file>`) để lần sau khỏi dò lại."*

→ Nhờ vậy tài liệu skill lớn dần theo thực tế, không lạc hậu.

## Files

- `config.yml` — **GITIGNORED** (human/self-improve chỉnh): email cá nhân, site, cloud_id,
  browse_url, auth (token_env + pass_entry), `projects` (scan được), `fields` (tên↔customfield id),
  `status_aliases`. Tạo từ `config.example.yml`.
- `config.example.yml` — **commit**: khuôn placeholder của config.yml (không chứa giá trị thật).
- `scripts/jira_client.py` — helper + CLI. Auth env→pass fallback, ADF↔text, tất cả subcommand
  + `raw`. Import được: `load_ctx`, `jira_get`, `jira_search`, `jira_raw`, `adf_to_text`, `text_to_adf`.
- `reference/api-map.md` — auth, bảng endpoint đã biết, JQL cheatsheet, ghi chú custom field.
- `reference/adf.md` — vì sao convert ADF, node đã hỗ trợ, quy ước text→ADF.
- `reference/workflow.md` — chuẩn team: luồng status, ai→assign cho ai từng mốc, Change Size theo role.
- `reference/comment-templates.md` — mẫu comment TH0–TH3 + cơ chế link (URL trần, luôn là link MR / commit-trong-MR).
- `reference/description-templates.md` — format description task/bug (heading h1–h3, khung mục).
- `reference/write-risk.md` — phân loại thao tác ghi: 🔴 dry-run + hỏi (xoá, ghi đè description/field có nội dung…) vs 🟢 tự ghi (field chọn, status, assignee, link…). Skill gọi tự chọn có áp hay không.

## Common Mistakes

- **Gọi thẳng `https://optis-app.atlassian.net/rest/api/3/...` với scoped token** → 401/403.
  Phải qua gateway `api.atlassian.com/ex/jira/<cloudId>/...` (script đã lo — đừng tự curl site).
- **Tự gõ lệnh shell để "kiểm tra token"** (`pass show ... ` trần, `echo "${JIRA_PAT:-x}"`,
  `env`, `cat`) → lộ token. Bẫy kinh điển: `${VAR:-...}`/`${VAR:+..}${VAR:-..}` khi biến CÓ giá trị
  sẽ **bung ra chính token**. Verify chỉ bằng `doctor`/`myself` — chúng không bao giờ in token.
- **Hardcode email/cloudId/field id trong skill khác** → lệch khi đổi người/site. Luôn qua
  `config.yml`/CLI này.
- **Đổ ADF JSON thô vào context** → tốn token vô ích. Luôn dùng `get`/`comments` (đã convert),
  chỉ `--raw` khi thật sự cần JSON gốc.
- **`--commit` một thao tác ghi mà chưa hỏi user** → thao tác ngoài-nhìn (comment/transition/
  assign/edit) phải confirm trước. Mặc định dry-run là để chặn việc này.
- **Đổi status mà không theo `reference/workflow.md`** → sai luồng / quên assign người kế tiếp /
  thiếu comment mốc. Đọc workflow.md trước khi `transition`.
- **Comment bị khoảng hở to giữa các khối** → do `text_to_adf` cũ biến dòng trống thành paragraph rỗng.
  Đã sửa (24-09-2026): giờ hiểu markdown tối thiểu (list, heading h3–h4, `---`, đậm/nghiêng/code,
  `[nhãn](url)`), dòng trống chỉ ngắt khối. Chi tiết `reference/adf.md`.
- **Tạo link Blocks bị ngược chiều** → `inwardIssue` là task ĐI block, không phải task bị block. Xem `reference/api-map.md`, tạo xong đọc lại để chắc.
- **Dán link commit trần (`/-/commit/<sha>`) vào comment** → sai chuẩn. Commit cụ thể thì dùng link
  commit trong MR `.../merge_requests/<N>/diffs?commit_id=<sha>` (xem được cả MR); comment có khối Golive
  thì kèm link MR từng repo. Chỉ dùng commit trần khi chưa có MR (OPTCLT-20 comment 14049, 28-09-2026).
- **Dùng `customfield_10293` cho Change Size** → sai field; issue thật điền `10294`.
- **Gửi chuỗi trần cho field select/priority** (`"Major"`, `"High"`) → Jira trả 400. `edit` đã tự bọc
  `{value}` / `{name}`; kiểu khác thì dùng `--value-json`. Change Size có tên thân thiện `change_size`.
- **Bịa endpoint/field khi không chắc** → dò bằng `raw` trước, rồi self-improve ghi lại. Đừng
  đoán mò rồi để tài liệu sai.
- **Quên self-improve** sau khi dò ra cái mới → lần sau lại tốn token dò lại. Ghi + báo user.
- **Thêm field (nhất là Priority) vào work type của space team-managed trên UI mà API/issue view không thấy**
  → UI hiện field + đã Save nhưng server không ghi. Cách chữa đã kiểm chứng (OPTCLT 24-09-2026): kéo field
  ra panel → Save → kéo vào lại → Save. Verify bằng `createmeta/<KEY>/issuetypes/<id>` (phải thấy `fieldId`),
  đừng tin màn cấu hình.
- **`code` span nằm trong `**đậm**`/`*nghiêng*` → Jira trả 400 `INVALID_INPUT`** khi ghi
  comment/description. Trong ADF mark `code` **loại trừ** mọi mark khác; chồng strong/em lên text
  đã có `code` là payload sai. `_with_mark()` đã bỏ qua node có `code` (25-09-2026) → `**x `y`**`
  ra "x" đậm + "y" code (không đậm). Đừng bọc code trong đậm nếu cần cả hai hiển thị.
- **URL trong comment/description không bấm được** → trong ADF, text thuần KHÔNG tự thành link;
  phải gắn `link` mark. `text_to_adf()` đã tự linkify http/https (từ 22-09-2026). Sửa comment cũ
  bị lỗi này: PUT `/rest/api/3/issue/<KEY>/comment/<ID>` với body dựng lại qua `text_to_adf()`.
