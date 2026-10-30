---
name: google-sheet
description: Use when updating multiple Google Sheets from different sources (Jira, skills inventory, raw data) — orchestrates tier-0/1/2 sub-skills in parallel with selective error handling.
metadata:
  trigger: "user says 'update sheets', 'sync everything', 'refresh sheets' — wants single command to coordinate multiple sheet updates"
  model_hint: "main loop (Sonnet/Opus) — orchestration needs dependency tracking + error aggregation"
  keywords: ["google sheets", "orchestrate", "sync", "jira", "skills", "update", "parallel"]
---

# Google Sheet Orchestrator

Skill để **điều phối multiple sheet updates** từ many sources — Jira, skills inventory, data — song song mà transparent, không cascade failure, không silent partial success.

## Nguyên tắc

- **Parallel by default**: independent tier chạy cùng lúc (faster)
- **Validate Sheets API first** (tier 0 health check) → fail-fast
- **Selective error handling**: tier 1 fail ≠ tier 2 fail, không cascade
- **Dual reporting**: full log (debugging) + brief summary (user)
- **Single entry point**: `/update-sheets` + flags, không 3 commands riêng

## Bước 1 — Dependency Graph

**Tiers:**

```
Tier 0: google-sheet-api (foundation)
  ↓ (both depend on)
Tier 1: google-sheet-jira-sync    |    Tier 2: google-sheet-skills-report
  ↓ (independent, parallel)       ↓
  Sheet "Sprint"                  Sheet "Skills Inventory"
```

**Validation flow:**

```
START
  ├─ Check Sheets API reachable (test write)
  │   ├─ 200 OK → continue
  │   └─ Timeout/5XX → STOP, all fail
  ├─ Launch Jira Sync (tier 1) + Skills Report (tier 2) in parallel
  │   ├─ Jira Sync (60s timeout)
  │   └─ Skills Report (30s timeout)
  └─ Collect results
      ├─ Both success → report all green
      ├─ Jira success, skills fail → "Jira ✓, Skills ✗"
      ├─ Jira fail, skills success → "Jira ✗, Skills ✓"
      └─ Both fail → report both errors
```

## Bước 2 — User Entry Point

**Single command:**

```bash
/update-sheets                    # Default: run all (jira + report + api)
/update-sheets --skip jira        # Run skills report + api only
/update-sheets --only jira        # Run jira sync only
/update-sheets --only report      # Run skills report only
/update-sheets --dry-run          # Preview only, don't write
/update-sheets --verbose          # Full debug logs
```

**Không promote:**
- `/update-sheets --jira-board "board-123"` (intermediate, expose if user asks)
- `/update-sheets --compose "jira then report"` (advanced, for power users)

## Bước 3 — Orchestration Flow

### Phase 1: Validate Tier 0

```typescript
async function validateSheetAPI(): Promise<void> {
  try {
    const sheets = google.sheets({ version: "v4" });
    // Test write: create temp sheet, delete
    const testSheet = await sheets.spreadsheets.create({ properties: {} });
    await sheets.spreadsheets.batchUpdate({
      spreadsheetId: testSheet.spreadsheetId,
      requests: [{ deleteSheet: { sheetId: 0 } }]
    });
  } catch (err) {
    throw new Error(
      `Sheets API unreachable: ${err.message}\n` +
      `Check: OAuth token, API enabled, network`
    );
  }
}
```

If validate fails → abort all.

### Phase 2: Parallel Execution

```typescript
async function orchestrate(options: { skip?: string, only?: string }) {
  const tasks = [];
  
  if (shouldRun("jira", options)) {
    tasks.push(
      runWithTimeout(googleSheetJiraSync(), 60000)
        .then(result => ({ tier: "jira", ...result }))
        .catch(err => ({ tier: "jira", error: err.message }))
    );
  }
  
  if (shouldRun("report", options)) {
    tasks.push(
      runWithTimeout(googleSheetSkillsReport(), 30000)
        .then(result => ({ tier: "report", ...result }))
        .catch(err => ({ tier: "report", error: err.message }))
    );
  }
  
  // Wait for all to complete (not fail-fast)
  const results = await Promise.allSettled(tasks);
  return results;
}
```

**Key: Promise.allSettled** (not Promise.all) — wait for all, don't cascade fail.

### Phase 3: Report Results

```typescript
async function reportResults(results: SettledPromise[]) {
  const table = [];
  
  for (const r of results) {
    if (r.status === "fulfilled") {
      const {tier, rows, error} = r.value;
      table.push({
        operation: tier,
        status: error ? "✗ ERROR" : "✓ OK",
        detail: error || `${rows} rows updated`
      });
    }
  }
  
  console.table(table);
  
  // Full log for debugging
  console.log("\nFull log:");
  results.forEach((r, i) => {
    if (r.status === "rejected") {
      console.error(`Task ${i} failed: ${r.reason}`);
    }
  });
}
```

**Output example:**

```
─────────────────────────────────────
 Operation      │ Status  │ Detail
─────────────────────────────────────
 Jira sync      │ ✓ OK    │ 12 rows
 Skills report  │ ✗ ERROR │ 403 Permission denied
─────────────────────────────────────

To retry Skills only:
  /update-sheets --only report --verbose
```

## Bước 4 — Error Handling Strategy

| Scenario | Decision |
|----------|----------|
| Sheets API down | STOP all, report clearly |
| Jira API timeout | Jira fails, Skills continues |
| Sheet write fails (quota?) | Capture error, skip that row, continue |
| Network hiccup | Automatic retry (1x per tier) |
| User cancel (Ctrl+C) | Graceful shutdown, log partial results |

**Never:**
- Silently drop failed writes
- Swallow errors without logging
- Assume success if partial writes happened

## Bước 5 — Idempotency

Both Tier 1 & 2 must be idempotent (safe to retry):

```typescript
// Tier 1 (Jira Sync)
// Match by issue ID → upsert, not append
const existingRow = sheet.findRowByKey(issue.key);
if (existingRow) {
  sheet.updateRow(existingRow, {...issue});  // Update
} else {
  sheet.appendRow({...issue});  // Insert new
}

// Tier 2 (Skills Report)
// Delete old sheet, rebuild from scratch
sheet.deleteSheet("Skills");
sheet.createSheet("Skills");
// Populate fresh → no duplicates risk
```

## Lỗi hay gặp

- **Cascade failure**: Jira fail → don't run Skills. → Fix: parallel + allSettled, không fail-fast.
- **Silent partial write**: Jira wrote 50 rows, error at 51, user doesn't know 50 succeeded. → Fix: track & report "50/60 rows done, error at row 51".
- **Vague error**: "API error" không rõ tại sao. → Fix: "Jira API returned 503 Service Unavailable at 14:32; rolled back partial writes".
- **User confusion on flags**: `--skip` vs `--only` counter-intuitive. → Fix: document clearly, suggest `--dry-run` để preview.
- **Timeout hung**: Jira stuck 5 min, user không biết phải chờ hay cancel. → Fix: explicit timeout + progress indicator ("30s elapsed, expecting 60s...").

**Xem thêm:** `references/orchestrator-runbook.md` cho runbook & troubleshooting.
