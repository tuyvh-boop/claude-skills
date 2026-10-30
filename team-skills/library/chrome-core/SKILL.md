---
name: chrome-core
description: Use when any task needs a real browser — e2e or UI test, checking a page, reading console / network errors, clicking through a flow, screenshots, mobile view — on a web app, a Shopify admin embedded app iframe, a storefront, or localhost; also when another skill reaches a browser step, when the dedicated Chrome profile must be set up the first time or its login expired, or several tasks test in parallel. Triggers "test trên chrome đi", "mở app X chụp màn hình", "đọc console trong iframe app", "bấm nút này có mở tab mới không", "test e2e luồng checkout trên localhost", "xem mobile". NOT for choosing acceptance cases or recording Pass/Fail, measuring web vitals (fix-shopify-admin-web-vitals), reading Jira / Partner Dashboard when a skill or API exists, or reading a claude.ai design (use the built-in browser pane, already logged in).
---

# chrome-core

## Overview

Một Chrome riêng, profile đã đăng nhập sẵn, điều khiển bằng `scripts/chrome.py` (Playwright qua CDP; CDP thô chỉ cho việc
Playwright không bọc). **Mọi thao tác browser đi qua script này** — không tự viết script CDP / Playwright mới, không
browser pane, không Claude in Chrome. **Chạy `uv run scripts/chrome.py <lệnh> --help` trước, không đọc source.**

## Quy trình + Anti-Hallucination

1. **`doctor`**. Chưa có profile / site chưa khai → **Thiết lập lần đầu** (dưới). Chrome chưa chạy → `launch` — **mặc định chạy ngầm (headless, `headless: true` trong config.yml), không mở cửa sổ cho user**; chỉ khi user phải tự đăng nhập mới `launch --headed`. Chạy tách khỏi shell: `(setsid nohup uv run scripts/chrome.py launch >/dev/null 2>&1 &)` rồi mới `run`/`shot` (Chrome mở trong lệnh Bash bị chết khi lệnh kết thúc).
   
   **Anti-hallucination:** Lệnh `doctor` PHẢI chạy thực sự, output phải show status Chrome (running/not running). Không nói "Chrome ready" nếu không chạy lệnh.
2. **Owner**: mọi lệnh đụng tab cần `--owner <mã task>@<session>` (hoặc env `CHROME_CORE_OWNER`). Lệnh đầu tiên của owner
   tự mở cửa sổ riêng cho nó; script chỉ chạm tab của owner đó → nhiều task chạy song song không giành tab.
3. **Chưa biết selector** → `snapshot --url <trang>` (đi vào cả iframe), chọn locator theo role / label / text.
4. **Việc một bước** → `eval` / `shot` / `console` (mặc định chỉ lỗi, `--all` lấy cả log) / `goto`; giả lập thiết bị thêm `--device`.

   **BẮTI BUỘC capture evidence** cho mỗi `shot`/action:
   ```bash
   # Lưu screenshot với tên task + step
   uv run scripts/chrome.py shot --url <trang> --out evidence/<MÃ>-<feature> --prefix <TC>-<step>
   
   # Lệnh này tự tạo evidence folder, lưu ảnh + metadata
   # Output: evidence/<MÃ>-<feature>/<TC>-<step>.png
   ```

   **Luồng nhiều bước** → viết `steps.py` (`def run(ctx)`, mẫu `examples/steps-open-new-tab.py`):
   ```python
   # steps.py
   # [Task: OPOS-136] Test product variant selector flow
   # Evidence: ./evidence/OPOS-136-variant-selector/
   
   def run(ctx):
       ctx.goto("https://store.test/products/test-prod")
       ctx.shot("01-open-product-page")  # → evidence/OPOS-136-variant-selector/01-open-product-page.png
       
       # Click variant selector
       variant_btn = ctx.page.locator("[data-testid='variant-selector']")
       variant_btn.click()
       ctx.shot("02-variant-menu-open")  # → evidence/.../02-variant-menu-open.png
       
       # Select option
       option = ctx.page.locator("text='Red'")
       option.click()
       ctx.shot("03-option-selected")
       
       # Check ATC button state
       atc = ctx.page.locator("button:has-text('Add to cart')")
       is_enabled = atc.is_enabled()
       ctx.check(is_enabled, "ATC button enabled after selection", is_enabled)
       
       return {"variant_selected": True, "atc_enabled": is_enabled}
   ```
   
   Chạy: `uv run scripts/chrome.py run steps.py --url <trang> --out evidence/<MÃ>-<feature> --prefix <TC>`
   → `<TC>-result.json` (return value + checks) + `-console.jsonl` + `-network.jsonl` + ảnh từng bước.
   
   Một steps chạy nhiều case → `--prefix <luồng> --raw-dir <evidence>/_raw` (result / log / ảnh lỗi vào `_raw/`) 
   và `ctx.shot("TC-05-<bước>")` (tên mở đầu bằng mã thì không gắn tiền tố → ảnh đặt tên theo case).
   
   Chỗ để `steps.py`: 
   - task có runbook (nghiệm thu) → cạnh runbook để lượt sau chạy lại
   - việc lẻ → `scratchpad/steps-<MÃ>-<feature>.py`
   
   **Evidence folder luôn tên theo task:** `evidence/<MÃ>-<feature>/` chứ không phải random, để user audit dễ.
5. Nền tảng có site module (`ctx.site("shopify")`) → dùng helper của nó trước khi tự viết (`reference/sites/<tên>.md`).
6. **Song song**: tối đa `max_parallel_runs` (mặc định 2) luồng `run` cho cùng một task — cùng task là cùng dev server, quá
   tải thì backend `ETIMEDOUT` và list / search rỗng giả. `run` in cảnh báo khi vượt. Kết quả rỗng mà log backend có lỗi
   mạng → chạy lại, không ghi Fail.
7. Xong việc của owner (cuối buổi test, không phải sau mỗi `run`) → `release --owner …`. Không `close` Chrome khi còn owner
   khác giữ tab.
8. **Tự cải thiện.** Gặp thao tác lặp → `learn <id>` (ứng viên); script báo lặp → đúc helper theo
   `reference/self-improve.md` (file đích, selftest xanh). Bẫy → ghi thẳng `reference/pitfalls.md` / `sites/<nền tảng>.md`.

## Quick Reference — `ctx` trong steps.py

| Việc | Gọi |
|---|---|
| Tab chính của owner (Playwright `Page`) | `ctx.page` |
| Frame theo đoạn src (cả iframe lồng, tự reload nếu frame chưa gắn) | `ctx.frame("/app.html")` |
| Chờ tới khi đúng (thay sleep) | `ctx.expect(locator).to_have_text("…")` |
| Đánh dấu bước — console / network sau đó mang `step` | `ctx.step("save")` |
| Bấm nút mở tab mới → tab mới (thuộc owner) | `ctx.click_new_tab(locator)` |
| Chụp (tự đưa cửa sổ thu nhỏ về normal); tên mở đầu bằng mã `TC-05-…` thì không gắn tiền tố | `ctx.shot("ten")` |
| Giả lập thiết bị, mang phiên đăng nhập. `mobile` = Pixel 10 (Android), `tablet` = Nexus 10 (Android, 800px); cần UA iPhone / iPad thì ghi tên máy (`devices`) — admin Shopify chặn mọi UA iOS | `ctx.emulate("mobile")`, `run --device mobile`, `shot --device mobile --url …` |
| Kiểm tra → vào result.json (giá trị `return` của `run` vào khoá `result`) | `ctx.check(cond, "mô tả", actual)` |
| Chờ React hydrate (trang SSR / vite dev) trước khi gõ | `ctx.wait_hydrated(frame)` |
| Bấm lại tới khi có kết quả (cú bấm sớm bị nuốt) | `ctx.click_until(locator, lambda: …)` |
| Rời form dirty không treo driver (beforeunload) | `ctx.accept_dialogs()` đầu steps |
| CDP thô | `ctx.cdp()` |
| Shopify: mở app, max modal (mở / frame / X), SaveBar, Dev Console, toast | `ctx.site("shopify").open_max_modal(...)` … (`reference/sites/shopify.md`) |

## Thiết lập lần đầu (người mới / site mới cần đăng nhập)

`setup --site <tên> --allow <origin…> --login-url <url> --login-marker <đoạn URL>` **không kèm `--ack`** → script in
khối rủi ro + checklist account test (`reference/setup-first-run.md`). **Trình nguyên khối đó cho user, dừng chờ user xác
nhận đã tạo account test riêng**, rồi chạy lại với `--ack` → Chrome mở trang login → **user tự đăng nhập** →
`doctor --session --site <tên> --release`. Localhost / trang công khai không cần bước này.

## Dừng lại, không tự xoay

| Gặp | Làm |
|---|---|
| Script báo `LoginRequired` | Nhờ user đăng nhập lại **trong cửa sổ Chrome đó**. Không gõ mật khẩu, không xoá / tạo profile, không đổi công cụ |
| `NotAllowed` (origin ngoài config) | Hỏi user có thêm origin không (`setup` / sửa `config.yml`). Không tự nới |
| Hộp xin quyền / CAPTCHA | Nhờ user |
| Muốn Save trên công cụ của bên thứ 3 (theme editor…) | Chỉ khi bước đó yêu cầu và có cách trả lại; mặc định xem rồi đóng |

## Anti-Hallucination Checklist — BẮT BUỘC trước khi báo kết quả

**Trước khi nói "test pass", "screenshot đã lấy", "flow OK", phải confirm ALL:**

- [ ] **Lệnh `run` / `shot` / `eval` thật sự chạy** — output từ CLI có hiển thị (không phải assume)
- [ ] **Evidence folder tồn tại** — `evidence/<MÃ>-<feature>/` folder được tạo, chứa file (không phải trống)
- [ ] **Ảnh screenshot được lưu** — file `.png` từng bước nằm trong folder (không phải chỉ nói "tôi chụp rồi")
- [ ] **Result JSON từ `run steps.py`** — nếu dùng steps, file `<TC>-result.json` trong evidence folder, ghi rõ return value + checks
- [ ] **Console/network log lưu** — file `-console.jsonl` / `-network.jsonl` nếu có lỗi cần debug
- [ ] **Mã task ghi rõ** — folder tên là `evidence/<MÃ>-<feature>`, mã này khớp với Jira/task hiện tại
- [ ] **Không im lặng nếu fail** — nếu lệnh fail / screenshot trống / check fail → báo rõ, không nói suông "OK"

**Nếu BẤT KỲ ô nào KHÔNG ✅:**
- KHÔNG báo kết quả vội
- Chạy lệnh Chrome lại ngay (kiểm tra CLI output)
- Confirm evidence folder có file thật
- Nếu vẫn lỗi → báo lỗi chi tiết cho user, không im lặng

**Ví dụ SAIIII:**
```
❌ "Screenshot đã lấy, variant selector click đúng, ATC button enable"
    — nhưng không có evidence folder, không có ảnh, chỉ nói suông
```

**Ví dụ ĐÚNG:**
```
✅ "Screenshot step 1-3 đã lấy vào evidence/OPOS-136-variant-selector/:
    - 01-open-product-page.png: sản phẩm hiển thị đúng
    - 02-variant-menu-open.png: dropdown mở
    - 03-option-selected.png: 'Red' được chọn, ATC button hiển thị enable
    - OPOS-136-variant-selector-result.json: check 'atc_enabled' = true ✅"
```

## Common Mistakes

- **Chặn / giả request bằng `ctx.page.context.route(...)` trong steps** → mọi owner dùng chung một browser context (một
  profile), nên route ở context chặn / giả luôn request của owner khác đang chạy song song: Save của họ bị abort, check đỏ oan,
  Fail giả. Dùng `ctx.page.route` / `ctx.page.unroute` — vẫn bắt request từ iframe app và max modal trong tab của owner.

- **Giao việc browser cho nhiều subagent mà không bắt `release` ở cuối** → mỗi owner là một cửa sổ riêng, agent xong việc
  để lại cửa sổ (kể cả cửa sổ `about:blank` của owner chưa kịp goto), Chrome chồng hàng chục cửa sổ. Brief của subagent ghi
  rõ "xong vùng thì `release --owner <owner>` (cả owner `-mob`)"; người điều phối chạy `status` sau mỗi agent, owner nào còn
  tab mà agent đã xong thì release. Một cửa sổ `about:blank` không thuộc owner nào là cửa sổ của `launch` — giữ lại.

- **Mở design claude.ai (`claude.ai/design/...`) bằng Chrome của skill** → profile không đăng nhập claude.ai, gặp captcha.
  Design luôn đọc ở browser pane có sẵn (tab riêng, `javascript_tool` gọi `GetFile`); skill này chỉ chụp app để so.
- **In `frame.url` / `src` của iframe app khi debug** → URL mang `id_token`, `session`, `hmac` của phiên app, lọt vào
  transcript. `run` tự che các tham số này trong stdout của steps, `checks`, `result.json`; đường ngoài `run` (`javascript_tool`,
  script Playwright tự viết, `python3 -c`) không được che → chỉ in path (`safe_url`), không in query.
- **Tự viết script CDP / Playwright cho từng việc** → mỗi lần 60–130 s, hay lỗi lần đầu (iframe chưa có URL). Dùng `chrome.py`.
- **Bấm theo toạ độ ảnh** → lệch khi modal / banner dịch. Dùng locator.
- **Lấy frame từ `page.frames`** → iframe khác site có thể không có trong list. `ctx.frame()` đi từ phần tử `<iframe>`.
- **`ctx.expect_page` / chọn tab theo URL hoặc tab đang active** → bắt nhầm tab của owner khác. Dùng `click_new_tab` / `--tab`.
- **`wait_for_timeout` / `networkidle` để chờ** → flaky. Chờ bằng locator / `expect`.
- **Kiểm lặp trên cùng trang** → lần 2 đạt nhờ chữ còn sót từ lần 1. Mỗi lần một `run --url …` (tải lại trang).
- **Gỡ steps quá lâu vì tự viết lại helper có sẵn** (chờ hydrate, bấm lại, đóng max modal, ẩn Dev Console) → đọc
  Quick Reference + `reference/sites/<nền tảng>.md` trước khi viết steps.
- **Kết luận lỗi do task khi console có lỗi** → so với lượt trước / master: `console-diff`.
- **In URL đầy đủ** → URL iframe app mang token trong query. Script đã cắt query; tự in thì cũng cắt.

## CRITICAL — Anti-Hallucination Violations

**Nếu gặp bất kỳ mẫu nào dưới đây, đó là FAIL và phải rewind:**

- ❌ "Screenshot đã lấy, checkout flow OK, payment page mở" — nhưng folder evidence không tồn tại, không có file `.png`.
  - Fix: **Chạy lệnh `shot` / `run steps.py` lại ngay**, lưu evidence, confirm folder có ảnh

- ❌ "Lỗi console: TypeError, nhưng không capture log" — nói suông, không có `-console.jsonl` / `-network.jsonl`.
  - Fix: Chạy `run` với `--out` để lưu log, gửi error message + log cho user

- ❌ "Test pass, tất cả check xanh" — nhưng không chạy lệnh, không có `result.json`, không có ảnh.
  - Fix: Proof of run bắt buộc — stdout từ CLI, file json trong evidence folder

- ❌ "Flow fail ở step 5, tôi sửa code rồi test lại" — nhưng không show evidence của fail lần 1, không có trace/screenshot lỗi.
  - Fix: Lưu evidence của lần fail trước, để user audit, rồi mới retest

- ❌ "Screenshot 1, 2, 3 đều pass" — nhưng folder evidence trống hoặc chỉ có 1 ảnh thay vì 3.
  - Fix: `ctx.shot()` mỗi bước, verify ảnh được lưu từng cái

- ❌ "Không thể test vì không setup được Chrome profile" — nhưng không chạy `doctor --session` để check trạng thái.
  - Fix: Chạy diagnostic lệnh trước, show output, hỏi user không bỏ qua

**Nếu user nhìn thấy bất kỳ violation nào:** hộp thoại `[Artifact comment sent to Claude]` → fix ngay (rewind, chạy lại, lưu evidence đúng).
