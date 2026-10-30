---
name: crm-core
description: Skill NỀN để thao tác CRM/OSSA nội bộ của team (ossa.optis.me) bằng CRM_PAT (personal API key, header X-API-Key) — KHÔNG gọi trực tiếp. Chứa kiến thức API CRM (auth header, gọi thẳng base_url, nhóm route bị chặn với API key, endpoint tasks/contacts/companies/customers/users/roles/task-comments/task-categories/workspaces) và helper CLI crm_client.py (doctor/scan/list/get/comments/search/comment-add/task-create/task-update/raw). Mọi skill cần đọc/ghi CRM nạp skill này thay vì tự curl. Đọc khi cần lấy task/contact/customer/user, list/search, thêm comment, tạo/sửa task, hay bất kỳ thao tác CRM/OSSA nào.
---

# CRM Core

## Overview

Một chỗ duy nhất giữ "sự thật" về cách nói chuyện với **CRM/OSSA nội bộ của team**
(`ossa.optis.me`) qua **CRM_PAT** (personal API key). Mọi skill CRM **tái dùng** skill này thay
vì tự dựng lại auth/endpoint. Cái gì chạy được bằng script → đã đóng thành hàm/subcommand trong
`crm_client.py` để **AI khỏi tốn token suy luận lại**.

**Nguyên tắc cốt lõi:**
1. **Kiến thức ở config, cơ chế ở script.** base_url + `denied_paths` + `resources` (scan) →
   `config.yml` (**GITIGNORED** — chứa host nội bộ; khuôn commit là `config.example.yml`). Logic
   gọi API → `crm_client.py`. Không có `profile.yml` (auth header không cần field cá nhân).
2. **Không bao giờ in token.** Script đọc token từ env `$CRM_PAT`, trống thì fallback
   `pass show` (capture, không in). **Verify chỉ bằng `doctor`/`whoami`** — KHÔNG tự gõ
   `cat`/`echo`/`env`/`pass show` trần (bẫy `${VAR:-...}` bung ra token → lọt transcript).
3. **API key có route bị CHẶN.** Nhóm self-admin (`auth`, `users/me/api-keys`, `mcp/pat`) trả 403
   với personal key. Script **guard trước khi gọi** (`config.denied_paths`) — nhóm đó dùng phiên
   đăng nhập thường, đừng cố lách.
4. **Ghi là thao tác thật — mặc định dry-run.** Mọi lệnh GHI (`comment-add`/`task-create`/
   `task-update`, và `raw` method≠GET) in payload trước; chỉ ghi thật khi thêm `--commit`. Trước
   khi `--commit` một thao tác ngoài-nhìn → **hỏi user xác nhận** theo rule an toàn.
5. **Tự lớn dần (self-improve).** Gặp endpoint/field chưa có tài liệu → dò bằng `raw`, làm xong
   **ghi bổ sung vào skill** và **báo user** (xem *Self-improve*).

## Yêu cầu môi trường (kiểm tra TRƯỚC khi chạy)

- **Token**: env `$CRM_PAT` có sẵn (terminal đã auto-load), hoặc `pass show personal/CRM_PAT`
  chạy được (fallback). Không có cả hai → script báo lỗi hướng dẫn set env.
- **config.yml**: tồn tại (có `base_url`). Chưa có → tạo từ `config.example.yml` (xem *Lần đầu*).
  File này đã .gitignore — an toàn để chứa host nội bộ.
- Chạy Python bằng `uv` (PEP 723, tự cài dep):
  ```bash
  uv run <path>/crm-core/scripts/crm_client.py <command> ...
  ```
- Kiểm tra nhanh toàn chuỗi: **`doctor`** → in config/base_url/nguồn-token/whoami (KHÔNG in token).

## Lần đầu dùng (setup config)

Nếu `config.yml` chưa có (máy mới clone repo):
1. Copy `config.example.yml` → `config.yml` (đã .gitignore).
2. Điền `base_url` thật (`https://ossa.optis.me/api`).
3. Chạy `doctor` verify. Tuỳ chọn: `scan --write` để cache workspaces/task-categories/roles vào
   `config.yml > resources` (tra id↔tên nhanh).
4. **Đăng ký source code (nếu user có).** Hỏi/ dò xem user đã clone source CRM về máy chưa
   (thường ở `CODE/SOURCE-CODE/crm/{backend,frontend}`). Có → ghi vào `config.yml > source`
   (list `{role, path, branch}`; **backend** là repo chứa `@Controller/@Get/...` — quan trọng nhất).
   Nhờ vậy khi cần endpoint chưa biết thì **đọc source (chắc chắn) thay vì đoán** (xem *Self-improve*).
   Chưa có source → để `source: []`, self-improve buộc phải dò bằng `raw` (đoán, dễ sai + tốn token).
   Verify: `source status`.

## CLI reference (`crm_client.py`)

Chạy: `uv run scripts/crm_client.py <command> [options]`

### Đọc (read-only — chạy thoải mái)

| Lệnh | Việc | Options |
|---|---|---|
| `doctor` | Verify AN TOÀN: config/base_url/nguồn-token/whoami (KHÔNG in token) | — |
| `whoami` | User hiện tại (`GET /users/me`) | — |
| `scan [resource]` | Scan `workspaces`/`task-categories`/`roles` (trống = hết) | `--write` (ghi config.resources) |
| `source [status\|sync\|find <kw>]` | Source CRM để tra endpoint khỏi đoán: `status` (verify path + behind remote), `sync` (pull --ff-only), `find <kw>` (in bản đồ route) | — |
| `list <resource>` | List `users`/`contacts`/`companies`/`customers`/`tasks`/`task-categories`/`roles` | `--query k=v` (lặp) |
| `get <resource> <id>` | Get 1: `user`/`contact`/`customer`/`task`/`role` | — |
| `comments <taskId>` | List comment của 1 task | — |
| `search --data '<json>'` | Search task (`POST /tasks/search`) | — |

### Ghi (side-effect — mặc định DRY-RUN, thêm `--commit` mới ghi thật)

| Lệnh | Việc | Options |
|---|---|---|
| `comment-add <taskId> --text "..."` | Thêm comment vào task | `--commit` |
| `task-create --data '<json>'` | Tạo task (body JSON: title,assignee,reporter,domain,relatedApps[…]) | `--commit` |
| `task-update <taskId> --set k=jsonvalue` | Sửa task (lặp `--set`, vd `status='"Resolved"'`) | `--commit` |

### Vạn năng

| Lệnh | Việc |
|---|---|
| `raw <METHOD> <path> [--data <json>] [--query k=v]…` | Gọi endpoint bất kỳ qua auth+guard đã đóng gói. GET chạy thẳng; method khác mặc định dry-run, thêm `--commit`. |

`raw` là **nền cho "thao tác mọi thứ"** + công cụ **dò rồi self-improve**. (Path bị `denied_paths`
sẽ bị chặn ngay.)

## Self-improve (BẮT BUỘC làm khi gặp cái mới)

Khi user nhờ thao tác CRM mà **chưa có** subcommand/endpoint tương ứng — **tìm trong source code
trước, ĐỪNG đoán mò**:

1. **Đồng bộ source.** Chạy `source status` → nếu source *behind* remote thì `source sync`
   (pull `--ff-only`) để chắc đang xem code mới nhất.
   - Path **LỆCH** (báo `MISSING` — user đã di chuyển source) → **HỎI user đường dẫn mới** rồi sửa
     `config.yml > source`. ĐỪNG tự đoán path.
   - `config.source` **rỗng** (user chưa clone / chưa đăng ký) → nhảy xuống bước 3 (fallback `raw`).
2. **Tra endpoint trong source (deterministic).** `source find <keyword>` in bản đồ route
   (`@Controller/@Get/@Post/...` + file\:line) — chọn đúng path/method từ đây; field/validation thì
   mở controller + `*.model.ts`/`*.dto.ts` tương ứng. Đây là **nguồn đúng duy nhất**, hơn đoán.
3. **Fallback khi KHÔNG có source.** Dò bằng `raw` (thử endpoint, xem body/shape; 422
   `unrecognized_keys` = key/endpoint không tồn tại). Chỉ dùng khi bước 1–2 không khả dụng.
4. **Làm xong việc cho user** bằng `raw` (hoặc subcommand nếu hợp).
5. **Ghi bổ sung vào skill**: endpoint mới → `reference/api-map.md`; resource scan-được mới →
   thêm vào `SCAN_SOURCES` của `crm_client.py`; thao tác lặp nhiều → thêm hẳn subcommand.
6. **Báo user** một dòng: *"Đã bổ sung `<X>` vào crm-core (`<file>`) để lần sau khỏi dò lại."*

## Files

- `config.yml` — **GITIGNORED**: `base_url`, `auth` (header/token_env/pass_entry), `denied_paths`,
  `source` (repo CRM đã clone để tra endpoint), `resources` (scan). Tạo từ `config.example.yml`.
- `config.example.yml` — **commit**: khuôn placeholder (host để `<crm-host>`).
- `scripts/crm_client.py` — helper + CLI. Auth env→pass, guard denied-path, scan, tất cả subcommand
  + `raw`. Import được: `load_ctx`, `crm_get`, `crm_raw`.
- `reference/api-map.md` — auth, bảng endpoint đã biết, body tạo/sửa task, cheatsheet.

## Common Mistakes

- **Tự gõ lệnh shell để "kiểm tra token"** (`echo "${CRM_PAT:-x}"`, `env`, `cat`, `pass show` trần)
  → lộ token. Bẫy kinh điển: `${VAR:-...}`/`${VAR:+..}${VAR:-..}` khi biến CÓ giá trị bung ra
  **chính token**. Verify chỉ bằng `doctor`/`whoami`.
- **Commit `config.yml`** (chứa host nội bộ + scans) → lộ hạ tầng. `.gitignore` phải có `config.yml`;
  chỉ commit `config.example.yml` (placeholder).
- **Cố gọi `auth`/`users/me/api-keys`/`mcp/pat` bằng API key** → 403. Nhóm self-admin dùng phiên
  đăng nhập thường; script đã guard, đừng gỡ.
- **`--commit` một thao tác ghi mà chưa hỏi user** → comment/tạo/sửa task là ngoài-nhìn, phải
  confirm trước. Mặc định dry-run là để chặn việc này.
- **Bịa endpoint/field khi không chắc** → có source thì `source find <kw>` + đọc controller/model
  (chắc chắn); không có source mới `raw` dò. Rồi self-improve ghi lại. Đừng đoán mò để tài liệu sai.
- **Đọc source cũ (chưa pull)** → tra ra endpoint đã đổi/bỏ. Trước khi dò phải `source status`,
  behind thì `source sync`.
- **Source báo `MISSING` mà tự đoán path mới** (user đã di chuyển source) → sai chỗ. Phải HỎI user
  đường dẫn mới rồi sửa `config.yml > source`.
- **Đổ nguyên list JSON thô vào context** → tốn token. Dùng `--query` để lọc; task description là
  HTML — chỉ lấy khi cần.
