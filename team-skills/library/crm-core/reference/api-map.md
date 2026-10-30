# CRM/OSSA API map — auth, endpoint đã biết

> File này là **bộ nhớ endpoint** của skill. Self-improve dò ra endpoint/field mới chưa có ở đây
> → **bổ sung vào file này** rồi báo user (xem *Self-improve* trong SKILL.md).

## Auth (đã đóng gói trong `crm_client.py` — không tự dựng lại)

- **Personal API key** gắn qua header **`X-API-Key: <token>`**, gọi **thẳng** `base_url`
  (`https://ossa.optis.me/api`) — KHÔNG gateway.
- Key mang **đúng quyền của user chủ key**, TRỪ nhóm self-admin bị chặn:
  `auth/*`, `users/me/api-keys/*`, `mcp/pat/*` (config `denied_paths`; script guard trước khi gọi).
- Backend resolve key → userId → load user; **workspace suy từ user**, không cần header workspace.

## Endpoint đã dùng (map sang lệnh CLI)

| Việc | Endpoint | Lệnh CLI |
|---|---|---|
| User hiện tại | `GET /users/me` | `whoami` · `doctor` |
| Scan workspaces | `GET /workspaces/mine` (list `{workspace:{_id,name},...}`) | `scan workspaces` |
| Scan task categories | `GET /task-categories` | `scan task-categories` |
| Scan roles | `GET /roles` | `scan roles` |
| List users | `GET /users` | `list users` |
| List contacts | `GET /contacts` | `list contacts` |
| List companies | `GET /companies` | `list companies` |
| List customers | `GET /customers` | `list customers` |
| List tasks | `GET /tasks` (query: `search`, `assignee`, `status[]`, `priority[]`, `customerDomain`…) | `list tasks --query k=v` |
| Get user | `GET /users/:userId` | `get user <id>` |
| Get contact | `GET /contacts/:id` | `get contact <id>` |
| Get customer | `GET /customers/:idOrDomain` | `get customer <idOrDomain>` |
| Get task | `GET /tasks/:taskId` | `get task <id>` |
| Get role | `GET /roles/:roleId` | `get role <id>` |
| Comment của task | `GET /task-comments?taskId=<id>` (taskId bắt buộc) | `comments <taskId>` |
| Search task | `POST /tasks/search` (body JSON) | `search --data '{...}'` |
| Thêm comment | `POST /task-comments` `{taskId, content, rootCommentId?}` | `comment-add <taskId> --text` |
| Tạo task | `POST /tasks` (xem body dưới) | `task-create --data '{...}'` |
| Sửa task | `PUT /tasks/:taskId` | `task-update <id> --set k=v` |
| List shift (ca làm) | `GET /shifts` (trả list; mỗi item có `date`,`staffId`,`staffName`,`status`,`bucket`,`startTime`,`endTime`,`templateName`) | `raw GET /shifts` |
| Shift theo user | `GET /shifts/user/:userId` | `raw GET /shifts/user/<id>` |
| Coverage / report shift | `GET /shifts/coverage` · `GET /shifts/report` · `GET /shifts/analytics/team` | `raw GET ...` |

> Response list hay bọc `{data:[...]}` (cũng gặp `items/values/results`) — `list`/`scan` tự chuẩn hoá.
> `companies` chỉ có list/create/update/delete (KHÔNG có get-by-id).
>
> ⚠️ **`GET /tasks` KHÔNG nhận `sort`.** Validate whitelist chặt — key lạ → **HTTP 422**
> `VALIDATION_ERROR: Unrecognized key: "sort"` (không im lặng bỏ qua). Chỉ được các key ở bảng trên
> (`search`, `assignee`, `status[]`, `priority[]`, `customerDomain`, `page`, `limit`…). **Không có tham số
> sort/order/dateFrom/dateTo** — muốn sort theo `createdAt`/lọc theo ngày thì **kéo đủ trang rồi
> sort/lọc client-side** (`pagination.totalPages`), đừng đẩy lên query. Đừng đoán param mới; chưa chắc
> thì dò bằng `raw GET /tasks --query <key>=…` (thấy 422 unrecognized_keys là key đó không tồn tại).

> ⚠️ **`GET /shifts` KHÔNG nhận key `date`** (422 `unrecognized_keys`). Lọc theo ngày thì kéo list
> rồi lọc client-side theo field `date` (`YYYY-MM-DD`). Route đầy đủ xem `source find shift`.

## Body tạo/sửa task (nguồn: `task.model.ts`)

**`POST /tasks`** — bắt buộc: `title` (≤100), `assignee` (User ObjectId), `reporter` (ObjectId),
`domain`, `relatedApps` (array ≥1). Tuỳ chọn: `description`, `app_id`, `status`
(`Todo|In Progress|Resolved|Pending Confirmation|Cancel|CS Review|Add Backlog|Research|Dev Transfer`,
default `Todo`), `priority` (`Low|Medium|High|Urgent`, default `Medium`), `tags[]`, `category`
(chuỗi tên category), `dueDate`, `estimateHours`.

**`PUT /tasks/:taskId`** — mọi field ở trên đều optional; thêm `shopAssignee`, `resolver`, `reminder`.

**`POST /task-comments`** — `{taskId, content}` (+ `rootCommentId` để reply).

## Dev Projects & Dev Tasks (OPOS, OPCS, v.v.)

Bên cạnh CRM tasks (`/api/tasks`), hệ thống có **dev project management** với riêng task structure:

| Việc | Endpoint | Lệnh CLI |
|---|---|---|
| List dev projects | `GET /api/dev-projects?includeArchived=false` | `raw GET /dev-projects` |
| Get dev project | `GET /api/dev-projects/:projectKey` (vd: OPOS) | `raw GET /dev-projects/OPOS` |
| Search dev tasks | `POST /api/dev-tasks/search` body: `{projectId: "<id>"}` (list all); lọc client-side | `raw POST /dev-tasks/search --data '{\"projectId\":\"6ad64fdbb0ae0e360dd7a7f4\"}'` |
| Get dev task | `GET /api/dev-tasks/:taskId` | `raw GET /dev-tasks/<id>` |
| Dev project sprints | `GET /api/dev-projects/:projectKey/sprints` | `raw GET /dev-projects/OPOS/sprints` |
| Dev task comments (list / thêm) | `GET /api/dev-task-comments?taskId=<devTaskId>` · `POST /api/dev-task-comments` body `{taskId, content}` (`content` là **HTML**: `<p>`, `<strong>`, `<code>`, `<ul><li>`, `<hr>`, `<h4>`) | `raw GET /dev-task-comments --query taskId=...` · `raw POST /dev-task-comments --data '{...}' --commit` |
| Sửa comment dev task của chính mình | `PUT /api/dev-task-comments/:commentId` body `{content}` (HTML) — đã kiểm 2026-10-26 | `raw PUT /dev-task-comments/<id> --data '{"content":"..."}' --commit` |
| Reply trong thread comment dev task | **Chưa tìm ra qua API key** (kiểm 2026-10-30). Reply được lưu bằng field `path` = `,<parentCommentId>,` (comment gốc có `path: ","`), nhưng `POST /dev-task-comments` báo `unrecognized_keys` với `parentId`/`parentCommentId`/`replyTo`/`parent`/`path`; `POST /dev-task-comments/:id/replies` và `/reply` trả 404. Muốn reply → nhờ user reply trên UI, hoặc đăng comment top-level. Có source CRM thì tra lại. | — |
| Dev task epics | `GET /api/dev-tasks/epics?projectId=<id>` | `raw GET /dev-tasks/epics --query projectId=...` |

> **Khác biệt:** CRM tasks = `tasks` (SATEOS-xxxx, TEPOS2-xxx); Dev tasks = `dev-tasks` (OPOS-185, OPCS-123, v.v.)
> Cả 2 đều dùng cùng auth header `X-API-Key` nhưng endpoint khác.
> 
> **Dev tasks search:** POST body chỉ nhận `projectId` (không nhận `key`, `number`, v.v.) → trả hết task của project, filter client-side bằng jq/code.
> Project ID OPOS: `6ad64fdbb0ae0e360dd7a7f4`

## Cheatsheet (self-improve bồi thêm)

- Tra id↔tên category/role/workspace: xem `config.yml > resources` (chạy `scan --write` để refresh).
- Endpoint chưa có subcommand → dùng `raw <METHOD> <path>` (GET chạy thẳng; ghi thì dry-run/`--commit`).
