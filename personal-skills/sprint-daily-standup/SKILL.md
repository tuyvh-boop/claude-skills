---
name: sprint-daily-standup
description: Chuẩn bị dữ liệu cho buổi daily standup — tổng hợp mỗi thành viên đang làm task Jira nào, cập nhật gần nhất khi nào, và task nào nghi đứng yên/bị block. Kích hoạt khi user nói "chuẩn bị standup", "daily standup", "ai đang làm gì", "check tiến độ sprint", hoặc tương tự trước buổi standup hàng ngày.
---

# Sprint Daily Standup

## Mục đích

Đọc dữ liệu Jira để chuẩn bị nội dung mở đầu buổi standup: ai đang làm task gì, có cập nhật gần đây không, task nào đứng yên bất thường (nghi block). Đây **chỉ là công cụ chuẩn bị dữ liệu** — không thay thế việc từng người tự báo cáo trong standup, và **không suy diễn quá mức** từ dữ liệu Jira vốn thưa thớt.

**Chỉ đọc — không ghi.** Skill này KHÔNG được gọi bất kỳ hành động ghi/sửa nào lên Jira (comment, transition status, thêm worklog...). Nếu user muốn log worklog, dùng skill riêng `te-jira-worklog` (không phải skill này).

## Bước 1 — Xác định phạm vi

Hỏi nhanh (hoặc suy ra từ ngữ cảnh hội thoại) app nào cần standup: Product Options (OPOS/OPOK) và/hoặc Color Swatch (OPCS/OPSK). Nếu user không chỉ rõ, mặc định lấy cả 2 board Scrum (`OPOS`, `OPCS`) — đây là board chạy sprint, còn Kanban (`OPOK`, `OPSK`) thường ít dùng cho daily standup trừ khi user yêu cầu.

Project key tra sẵn, KHÔNG gọi `getVisibleJiraProjects` để dò lại:

| App | Board | Key |
|---|---|---|
| Product Options | Scrum | `OPOS` |
| Product Options | Kanban | `OPOK` |
| Color Swatch | Scrum | `OPCS` |
| Color Swatch | Kanban | `OPSK` |

Site: `optis-app.atlassian.net`, `cloudId`: `0324d786-4e6b-4cdf-bd05-8d876d21f3a7`.

## Bước 2 — Lấy tool Jira

Các tool Atlassian MCP là deferred tool, tên dạng `mcp__781b21b6...__<tenTool>`. Trước khi gọi, load schema bằng:

```
ToolSearch(query: "select:mcp__781b21b6-ec60-48c0-a419-bd587b118a48__searchJiraIssuesUsingJql,mcp__781b21b6-ec60-48c0-a419-bd587b118a48__getJiraIssue")
```

## Bước 3 — Query issue đang active

Dùng `searchJiraIssuesUsingJql` với `cloudId` ở trên, JQL lọc theo (các) project key trong phạm vi, loại trừ trạng thái đầu/cuối, sort theo cập nhật:

```
project in (OPOS, OPCS) AND status NOT IN ("To Do", "Done") ORDER BY updated ASC
```

- `status NOT IN ("To Do", "Done")` giữ lại: Research, In Development, In Code Review, Ready for Test, Testing.
- Sort `ASC` theo `updated` để các task đứng yên lâu nhất nổi lên đầu — tiện rà soát.
- Lấy field cần: `assignee`, `status`, `summary`, `updated`, `key`.

## Bước 4 — Đào sâu khi cần (tuỳ chọn)

Với issue nghi đứng yên (xem tiêu chí ở Bước 5), có thể gọi `getJiraIssue` để xem thêm comment/worklog gần nhất — giúp phân biệt "im lặng vì thực sự không động tới" với "có update dạng comment/worklog nhưng field `updated` không đổi nhiều". Không bắt buộc gọi cho mọi issue — chỉ gọi khi cần làm rõ cờ cảnh báo.

## Bước 5 — Suy ra cờ cảnh báo "đứng yên bất thường"

Quy tắc gợi ý (áp dụng linh hoạt theo ngày trong tuần, không cứng nhắc):

- Task đang ở status **"In Development"**, **"In Code Review"**, hoặc **"Ready for Test"/"Testing"** mà `updated` cách hiện tại > **2 ngày làm việc** (bỏ qua Thứ 7, Chủ nhật) → gắn cờ ⚠️.
- Task ở status **"Research"** thường vốn chậm hơn (đang tìm hiểu), chỉ gắn cờ nếu > 3-4 ngày làm việc không đổi.
- **Không** tự kết luận "task bị block" — chỉ nêu tín hiệu "đứng yên N ngày, nên hỏi trực tiếp trong standup". Tránh suy diễn nguyên nhân khi dữ liệu Jira không đủ (vd thiếu comment, thiếu worklog không có nghĩa là không làm gì — có thể người đó làm nhưng quên cập nhật Jira).

## Bước 6 — Output: bảng theo người

Sắp xếp theo **Người phụ trách** (assignee) trước, để mở đầu standup dễ đọc theo thứ tự từng người báo cáo. Trong mỗi người, nếu có nhiều task thì sắp theo status (đang code trước, review sau...).

Format bảng:

| Người phụ trách | Task | Status | Cập nhật gần nhất | Cờ cảnh báo |
|---|---|---|---|---|
| Tên A | OPOS-123: Thêm filter theo màu | In Development | 2026-08-25 (2 ngày trước) | ⚠️ Đứng yên 2 ngày làm việc — nên hỏi |
| Tên A | OPOS-118: Fix bug swatch preview | In Code Review | 2026-08-27 (hôm nay) | — |
| Tên B | OPCS-40: Research API v2 | Research | 2026-08-26 (1 ngày trước) | — |

Ghi thêm:
- Task nào chưa có assignee → gom vào nhóm riêng "Chưa gán người" ở cuối bảng, nêu rõ để hỏi ai sẽ nhận.
- Nếu một người không có task active nào trong board đang xét → có thể liệt kê riêng "Không có task active" (tránh để trống gây hiểu nhầm là quên).

## Giới hạn — luôn nhắc lại cuối output

Luôn kèm 1 dòng nhắc: *"Đây là dữ liệu tổng hợp từ Jira để chuẩn bị standup, không thay thế báo cáo trực tiếp của từng người. Các cờ ⚠️ chỉ là tín hiệu để hỏi thêm, không phải kết luận task đang bị block."*
