# Jira API map — auth, endpoint đã biết, JQL

> File này là **bộ nhớ endpoint** của skill. Khi self-improve dò ra endpoint/field mới
> chưa có ở đây → **bổ sung vào file này** rồi báo user (xem *Self-improve* trong SKILL.md).

## Auth (đã đóng gói trong `jira_client.py` — không phải tự dựng lại)

- Token là **scoped API token** (tạo bằng "Create API token with scopes" ở
  id.atlassian.com) → **KHÔNG** gọi thẳng `https://<site>/rest/api/3/...` (401/403).
- Phải qua **gateway**: `https://api.atlassian.com/ex/jira/<cloudId>/rest/api/3/...`
- Auth: **HTTP Basic** `email:token`. Email = tài khoản Atlassian tạo token (trong `config.yml`, gitignored).
- `cloudId` lấy public (không cần token): `GET https://<site>/_edge/tenant_info`.

## Endpoint đã dùng (map sang lệnh CLI)

| Việc | Endpoint | Lệnh CLI |
|---|---|---|
| User hiện tại | `GET /rest/api/3/myself` | `myself` |
| List project | `GET /rest/api/3/project/search` (phân trang `startAt`/`isLast`) | `projects` |
| 1 issue | `GET /rest/api/3/issue/{key}?fields=...` | `get` |
| Comment của issue | `GET /rest/api/3/issue/{key}/comment` | `comments` |
| Thêm comment | `POST /rest/api/3/issue/{key}/comment` (body ADF) | `comment` |
| Upload attachment | `POST /rest/api/3/issue/{key}/attachments` (multipart field `file`, header `X-Atlassian-Token: no-check`; scoped token cần `write:attachment:jira`) | `attach` |
| Sửa comment đã có | `PUT /rest/api/3/issue/{key}/comment/{commentId}` (body ADF, full nội dung mới) | `raw` — chưa có subcommand riêng, dùng `text_to_adf()` build full ADF (cũ + thêm) rồi `raw PUT ... --data '<json>' --commit` |
| JQL search | `GET /rest/api/3/search/jql` (phân trang `nextPageToken`) | `search` |
| Transition khả dụng | `GET /rest/api/3/issue/{key}/transitions` | `transitions` |
| Chuyển status | `POST /rest/api/3/issue/{key}/transitions` (`{transition:{id}}`) | `transition` |
| Gán người | `PUT /rest/api/3/issue/{key}/assignee` (`{accountId}`) | `assign` |
| Tìm user theo email | `GET /rest/api/3/user/search?query=<email>` | (dùng trong `assign`) |
| Sửa field | `PUT /rest/api/3/issue/{key}` (`{fields:{...}}`) | `edit` |
| List field (dò custom id) | `GET /rest/api/3/field` | `raw` |
| List loại link | `GET /rest/api/3/issueLinkType` (Blocks, Relates, Duplicate, Cloners…) | `raw` |
| Tạo link giữa 2 issue | `POST /rest/api/3/issueLink` — ⚠️ chiều ngược trực giác: **`inwardIssue` = task đi block**, `outwardIssue` = task bị block. VD "A is blocked by B": `{"type":{"name":"Blocks"},"inwardIssue":{"key":"B"},"outwardIssue":{"key":"A"}}`. Tạo xong đọc lại `fields=issuelinks` của A để chắc | `raw` |
| Xem link của issue | `GET /rest/api/3/issue/{key}?fields=issuelinks` — mỗi link có `inwardIssue` (đọc bằng `type.inward`) hoặc `outwardIssue` (đọc bằng `type.outward`) | `raw` |
| Đổi issue type hàng loạt (trong cùng project) | `POST /rest/api/3/bulk/issues/move` — key mapping `"<PROJECT>,<typeId>"`; field bắt buộc ở type đích mà issue chưa có → `targetMandatoryFields: [{fields:{customfield_x:{retain:false,type:"raw",value:["<optionId>"]}}}]` và **phải `inferFieldDefaults:false`** (để true + có mapping → 400). Trả `taskId` → theo dõi `GET /rest/api/3/bulk/queue/{taskId}`. Không có dry-run. Key/status giữ nguyên, subtask đi theo cha | `raw` |
| Metadata project (style, issueTypes) | `GET /rest/api/3/project/{key}?expand=issueTypes,lead` — `style: next-gen` = team-managed | `raw` |
| Status theo issue type của project | `GET /rest/api/3/project/{key}/statuses` | `raw` |
| Field trên create screen theo issue type | `GET /rest/api/3/issue/createmeta/{key}/issuetypes/{typeId}` (có `required`, `allowedValues`) | `raw` |
| Field trên edit screen | `GET /rest/api/3/issue/{key}/editmeta` | `raw` |
| Lịch sử đổi status (dựng luồng thực tế) | `GET /rest/api/3/issue/{key}/changelog` (lọc `items[].field=='status'`) | `raw` |
| ⛔ Board config / sprint API | `/rest/agile/1.0/board/*` → **401 scope does not match** (token chưa có scope Jira Software) — xem sprint qua field `customfield_10020` của issue, board qua Chrome | — |
| ⛔ Workflow definition | `POST /rest/api/3/workflows` → **401 scope** — dựng luồng bằng `transitions` trên issue ở từng status + changelog | — |

## Scope của JIRA_PAT hiện tại (dò 24-09-2026, bằng probe GET + endpoint `*/validation` không side-effect)

- ✅ Có: đọc/ghi issue, comment, transition, assign; đọc project, field, issue type, `project/{key}/features`, editmeta/createmeta.
- ❌ Thiếu: `read:workflow:jira` / `write:workflow:jira` (status + workflow, kể cả `workflows/update/validation`),
  mọi scope `jira-software` (board, sprint: `read:board-scope.admin`, `write:sprint`), `priority/search`, `applicationrole`.
- Chưa probe: `write:project.feature:jira` (bật/tắt tab Code…).
- Không phải lỗi scope mà là giới hạn: tạo custom field / xoá issue type cần **global Administer Jira** (user không có);
  field layout của project team-managed **không có public API** → làm UI.
- Muốn thêm scope: có thể phải tạo token mới thay vì sửa token cũ — chưa kiểm chứng.

## JQL cheatsheet (dùng với `search "<JQL>"`)

- `assignee = currentUser()` · `reporter = currentUser()`
- `project = OPCS` · `project in (OPCS, OPOS)`
- `status = "In Development"` · `status in ("To Do","In Development")`
- `sprint in openSprints()` · `sprint in closedSprints()`
- `updated >= -7d` · `created >= startOfWeek()`
- `"Change Size[Dropdown]" = Major` (hoặc lọc phía client theo field change_size)
- Sắp xếp: `ORDER BY updated DESC`

## Ghi chú custom field (project OPTIS)

- `customfield_10020` = Sprint
- `customfield_10016` = Story point estimate
- **Change Size là field PROJECT-SCOPED** (project team-managed/next-gen — mỗi project tự đẻ field
  riêng, cùng tên nhưng khác id): `customfield_10294` = OPCS · `customfield_10293` = OPOS (Tiny/
  Medium/Major, required khi tạo Task). OPTCLT chưa có. Tương tự Score Value/Effort (OPOS
  10256/10257, OPCS 10258/10259), Testcase (OPOS 10360, OPCS 10361). Tra `scope.project.id` trong
  `GET /rest/api/3/field` để biết field thuộc project nào — `config.yml > fields.change_size` hiện
  chỉ đúng cho OPCS.
