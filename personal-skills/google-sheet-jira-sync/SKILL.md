---
name: google-sheet-jira-sync
description: Use when syncing Jira tasks to Google Sheets — handles schema mapping, partial data sync, and staleness policy without silent overwrites or data loss.
metadata:
  trigger: "user says 'sync jira', 'update sheet from jira', 'pull jira tasks to sheet' — wants automated task sync from Jira source to sheet document"
  model_hint: "main loop (Sonnet/Opus) — sync orchestration needs state management + conflict resolution"
  keywords: ["jira", "sync", "sheet", "tasks", "mapping", "staleness", "conflicts"]
---

# Google Sheet Jira Sync

Skill để **đồng bộ Jira tasks vào Google Sheets** an toàn — schema mapping rõ, scope xác định, conflict handling transparent, không silent data loss.

## Nguyên tắc

- **Schema mapping explicit**: user confirm trước sync, không tự assume field names match
- **Match by ID**: Jira issue ID = primary key, duy nhất & bất biến
- **Jira source of truth**: status/assignee/dates từ Jira win, local sheet columns preserve
- **Staleness on-demand**: default user-triggered, optional daily batch
- **Deleted tasks preserved**: mark status = "DELETED" thay vì xoá

## Bước 1 — Scope xác định trước sync

Hỏi user rõ scope (trước khi fetch Jira):

```
- Current sprint only?
- All open tasks (backlog + sprint)?
- Specific board/filter?
- Include done/closed tasks?
```

**Ví dụ prompt:**
```
"I'll sync Jira tasks to your sheet. Which scope?
  1. Current sprint (default)
  2. All open
  3. Custom filter (specify)
  4. All (backlog + sprint + done)
```

Lưu scope choice → để reuse nếu user sync lại.

## Bước 2 — Schema Mapping Config

Tạo mapping config file (YAML/JSON) trước sync:

```yaml
jira_to_sheets_mapping:
  issue_key:
    sheet_column: "Key"
    transform: identity
    required: true
    
  assignee:
    sheet_column: "Owner"
    transform: extract_name  # extract_name | full_with_email | split_columns
    data_loss: ["email"]
    confirmed_by: user_email
    confirmed_at: "2026-09-29"
    
  status:
    sheet_column: "Status"
    transform: identity
    source_of_truth: jira  # Jira wins on conflicts
    
  custom_field_x:
    sheet_column: "Custom X"
    transform: passthrough
    optional: true
```

**Show preview** trước sync:
```
Row 1 (Jira: OPOS-139):
  assignee: "Jane Doe (jane@company.com)" 
  → sheet owner: "Jane Doe"  [email dropped, ok?]

Row 2 (Jira: OPOS-140):
  assignee: null
  → sheet owner: [empty]
```

Hỏi user: OK? Or Plan B (keep email)? Or Plan C (skip sync)?

## Bước 3 — Partial Sync Logic

**Match by:** Jira issue ID (immutable key)

**Scope detection:**
```typescript
// Từ Jira: danh sách tasks theo scope (sprint / board / filter)
const jiraTasks = await jira.getTasksInScope(scope); // 20 tasks

// Từ Sheet: hiện tại có bao nhiêu rows
const sheetTasks = await sheet.readAllRows(); // 15 rows

// Sync logic:
// - Rows không có Key → local sheet rows (preserve)
// - Key có ở Jira + Sheet → UPDATE
// - Key có ở Jira, không ở Sheet → ADD
// - Key có ở Sheet, không ở Jira → SKIP (keep, mark warning)
```

**Deleted tasks** (ở Jira không còn):

```typescript
const deletedInJira = sheetTasks
  .filter(row => !jiraTasks.find(j => j.key === row.Key))
  .forEach(row => {
    sheet.updateCell(row, "Status", "DELETED"); // Mark, don't remove
    sheet.addNote(row, "Deleted from Jira on 2026-09-29");
  });
```

**Duplicates** (2 rows Sheet = 1 Jira task):

```
Before sync: Sheet has rows for OPOS-139 (2 copies)
→ STOP, ask user: "Rows 5 & 7 both OPOS-139. Merge?"
```

## Bước 4 — Conflict Handling

| Scenario | Decision |
|----------|----------|
| Jira changed, Sheet unchanged | Sync normally |
| Sheet changed, Jira unchanged | STOP, ask user |
| Both changed (diff fields) | Merge (preserve local edits) |
| Both changed (same field) | Jira wins, warn user |

**Track last sync timestamp:**

```typescript
// Hidden column or sheet property
const lastSync = sheet.getProperty("last_sync_timestamp");

// Before syncing, detect sheet-side changes
sheetRows.filter(row => row.last_modified > lastSync)
  .forEach(row => {
    console.warn(`Sheet edited after last sync: Row ${row.Key} at ${row.last_modified}`);
  });
```

**If sheet has unsaved edits:**
```
"Sheet has local edits (rows 3, 5, 8) newer than last sync (2026-09-28 9am).
 Sync anyway? (Jira data will overwrite)
 Options:
   - Yes, sync (Jira wins)
   - No, review manually first
   - Merge (keep local edits, merge Jira updates)"
```

## Bước 5 — Staleness Policy

**Default: On-demand**
```bash
/google-sheet-jira-sync --sheet-id "ABC"
# User calls when they want fresh data
```

**Optional: Periodic batch** (if team syncs heavy)
```bash
# Daily at 9am via schedule
/google-sheet-jira-sync --sheet-id "ABC" --schedule daily@9am
```

**NOT recommended**: Real-time webhooks (overkill, operational overhead)

**Trade-off table:**

| Strategy | Quota | Complexity | Age | Risk |
|----------|-------|-----------|-----|------|
| On-demand | 1-10 calls/day | Low | 0-24h | User must remember |
| Daily @ 9am | ~1 + user calls | Low-Medium | 0-24h + user-driven | Overwrites recent edits |
| Webhooks | 50-100 events | High | <1min | Infra failures, accidental overwrites |

## Lỗi hay gặp

- **Schema mapping sơ sài**: Không check field match, assume "assignee" = "owner". → Fix: create mapping config, show preview, ask user confirm trước sync.
- **Scope mơ hồ**: "Sync the sprint" nhưng không rõ scope (backlog? done?). → Fix: bắt buộc hỏi scope trước fetch.
- **Silently overwrite sheet edits**: User edit row ở sheet, Jira sync cùng lúc, data loss. → Fix: track last sync timestamp, detect sheet edits, ask user trước overwrite.
- **Bỏ lại deleted tasks**: Jira xoá task, sheet vẫn giữ row như hỏng. → Fix: mark status = "DELETED", thêm note, không xoá.
- **Duplicates không detect**: 2 rows Sheet cùng issue key, sync tạo chaos. → Fix: bắt buộc scan duplicates trước sync, hỏi user merge/skip.
- **Reuse old scope**: Lần sau sync, lại dùng scope cũ mà không confirm. → Fix: prompt scope mỗi lần, hoặc `--scope-cache` flag để reuse.

**Xem thêm:** `references/jira-sync-mapping-templates.md` cho cấu hình mapping sẵn.
