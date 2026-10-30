---
name: google-sheet-api
description: Use when reading or writing Google Sheets via API — handles sheet ID resolution, OAuth token lifecycle, and rate-limit management without hardcoding or silent data loss.
metadata:
  trigger: "user says 'sync sheet', 'update sheet API', 'read google sheets', 'write to sheet' — wants structured API access, not manual UI"
  model_hint: "main loop (Sonnet/Opus) — API lifecycle needs careful state management"
  keywords: ["google sheets", "API", "sync", "read", "write", "oauth", "rate limit"]
---

# Google Sheets API

Skill để **đọc/ghi Google Sheets qua API** mà không hardcode sheet ID, không để token hết hạn, không chém dữ liệu khi quota cạn.

## Nguyên tắc

- **Sheet ID runtime**: nhận từ parameter / env var / URL parse, không hardcode
- **Token lifecycle**: kiểm tra upfront trước job, catch 401 mid-job, 1 retry tối đa
- **Rate limit fail-fast**: tính quota math trước, báo user realistic timeline, không retry blind

## Bước 1 — Xác định Sheet ID

**Hierarchy (ưu tiên thứ tự):**

1. **Explicit parameter** — user pass sheet ID hoặc URL
   ```typescript
   /google-sheet-api --sheet-id "ABC123xyz"
   // hoặc
   /google-sheet-api --sheet-url "https://docs.google.com/spreadsheets/d/ABC123xyz/edit"
   ```

2. **Environment variable** — `.env` hoặc env var
   ```
   GOOGLE_SHEET_ID=ABC123xyz
   ```

3. **Parse from URL** — skill regex-extract ID từ share link
   ```
   "https://docs.google.com/spreadsheets/d/ABC123xyz/edit" → ABC123xyz
   ```

4. **Google Drive search** — tìm sheet theo tên (chỉ nếu tên unique, không recommend mặc định)

**Nếu không có:** error ngay, không bịa

## Bước 2 — Validate Sheet Exists

Trước khi code:

```typescript
async function validateSheet(sheetId: string): Promise<void> {
  try {
    await sheets.spreadsheets.get({ spreadsheetId: sheetId });
    // Sheet tồn tại + có quyền truy cập
  } catch (err: any) {
    if (err.status === 404) {
      throw new Error(`Sheet '${sheetId}' không tồn tại hoặc đã bị xoá. Check Google Drive.`);
    }
    if (err.status === 403) {
      throw new Error(`Bạn không có quyền truy cập sheet '${sheetId}'. Hỏi chủ sở hữu để share.`);
    }
    throw err;
  }
}
```

## Bước 3 — OAuth Token Management

### Upfront Check (trước batch)

```typescript
const expiresIn = (expiresAt - Date.now()) / 60000; // minutes
if (expiresIn < 5) {
  console.log("Token hết hạn trong 5 phút, refresh ngay...");
  accessToken = await oauth2Client.refreshAccessToken();
}
```

### Mid-Job Catch (nếu token hết giữa chừng)

```typescript
try {
  await sheets.append(data);
} catch (error) {
  if (error.status === 401) {
    // Token hết, refresh 1 lần
    accessToken = await oauth2Client.refreshAccessToken();
    // Retry task này ONLY (không infinite loop)
    return await sheets.append(data);
  }
  throw error;
}
```

**Không làm:**
- Không retry nhiều lần trên 401 (nếu token xấu, vô tận)
- Không mute lỗi 401 (user cần biết)
- Không store token ở file (dễ bị expose)

## Bước 4 — Rate Limit (5000 cells/100s)

### Fail-Fast Validation

```typescript
const cellsNeeded = 10000;
const quotaPerWindow = 5000;
const windowMs = 100 * 1000;
const minTimeMs = Math.ceil(cellsNeeded / quotaPerWindow) * windowMs;

if (minTimeMs > userDeadline) {
  throw new Error(
    `Quota: cần ${Math.ceil(minTimeMs / 1000)}s, bạn có ${Math.ceil(userDeadline / 1000)}s.\n` +
    `Options:\n` +
    `  1. Giãn deadline thêm ${Math.ceil((minTimeMs - userDeadline) / 1000)}s\n` +
    `  2. Giảm data xuống ${Math.floor(quotaPerWindow * userDeadline / windowMs)} cells\n` +
    `  3. Chia thành nhiều script runs`
  );
}
```

### Sequential Batches (không retry chồng)

```typescript
const batchSize = 4500; // < 5000/window
const batches = chunkArray(cells, batchSize);

for (let i = 0; i < batches.length; i++) {
  await sheets.batchUpdate({ data: batches[i] });
  
  if (i < batches.length - 1) {
    await sleep(105 * 1000); // 100s quota window + 5s buffer
  }
}
```

### Detect Quota Hit

Google Sheets API trả 429:

```typescript
{
  "error": {
    "code": 429,
    "status": "RESOURCE_EXHAUSTED",
    "message": "Resource has been exhausted..."
  },
  "headers": { "Retry-After": 45 }
}
```

**Xử lý:**

```typescript
if (err.code === 429) {
  const retryAfter = parseInt(err.headers['Retry-After'] || '100');
  throw new Error(
    `Quota cạn. Reset sau ${retryAfter}s. ` +
    `Timeline: ${Date.now() - start}ms / ${deadline}ms. ` +
    `Không thể kịp deadline.`
  );
}
```

## Lỗi hay gặp

- **Hardcode sheet ID**: Khi sheet di chuyển/xoá, code fail không recover. → Fix: nhận sheet ID từ param/env/URL parse, không hardcode.
- **Không check token trước**: Token hết ở task #27/50, unclear nào synced. → Fix: upfront check `expiresAt < 5 min`, refresh trước job.
- **Retry infinite trên 401**: Refresh token xấu = infinite loop, vứt deadline. → Fix: 1 retry max per task, fail loud.
- **Quota math blind**: Cố write 10k cells trong 2 phút (quota = 5k/100s = 200s min). → Fix: validate math upfront, báo user realistic time.
- **Silent auth fail**: 403 permission mà không báo → user không biết tại sao. → Fix: catch 403 → explain "bạn không có quyền".

**Xem thêm:** `references/google-sheet-api-flows.md` cho detailed flow diagrams.
