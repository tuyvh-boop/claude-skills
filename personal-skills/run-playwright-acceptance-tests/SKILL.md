---
name: run-playwright-acceptance-tests
description: Tự sinh test case acceptance từ plan (`<MÃ>-plan.md` nếu có), AC/requirement Jira, và chính repo (selector/route thật) — rồi chạy THẬT bằng Playwright (browser thật, không mock) từ kho DÙNG CHUNG `~/Shopify/skill/personal-workspace/e2e-tests/` (1 lần cài cho mọi app, không cài riêng từng repo), và báo cáo pass/fail map theo từng AC. Tối ưu token nghiêm ngặt: mọi tương tác browser chạy qua Playwright test runner (`npx playwright test`, headless, script hoá), KHÔNG dùng agent lái browser từng bước qua screenshot/computer-use. Dùng khi user nói "test thật task này bằng playwright", "chạy acceptance test", "viết test case theo spec rồi test thật", "kiểm tra bằng browser thật". KHÁC `review-code` (đọc tĩnh diff, không chạy gì) và các skill `*.test.ts` unit test hiện có (Jest/Vitest, không chạm browser thật) — skill này CHỈ dùng khi cần xác nhận hành vi thật trên trình duyệt thật.
metadata:
  trigger: "user muốn xác nhận hành vi thật qua browser (không phải unit test), dựa theo plan/AC Jira, sau khi code xong 1 feature hoặc trước khi merge"
  model_hint: "main loop điều phối việc sinh test case (cần đọc nhiều nguồn); việc CHẠY test giao hẳn cho Bash/Playwright CLI, không qua subagent nào khác để tránh tốn token kép"
  keywords: ["playwright", "e2e", "acceptance test", "test thật", "browser test", "kiểm thử"]
---

# Run Playwright Acceptance Tests

## Kho dùng chung — KHÔNG cài Playwright riêng từng repo

Toàn bộ setup Playwright (package, browser binary, config, test case) nằm ở
**MỘT chỗ cố định, dùng chung cho mọi app**: `~/Shopify/skill/personal-workspace/e2e-tests/` (cùng
thư mục `personal-workspace` với `dev-journal/`, `schedules/`, `skills/` — không nằm trong bất kỳ
worktree/repo app nào). Lý do: Playwright test là black-box (gọi qua HTTP/browser từ ngoài),
không cần sống trong chính codebase app đang test — cài 1 lần, browser
binary cache dùng chung, không phải tải lại/cấu hình lại mỗi lần đổi repo.

```
~/Shopify/skill/personal-workspace/e2e-tests/
├── package.json              <- @playwright/test, cài 1 lần duy nhất
├── playwright.config.ts      <- 1 "project" Playwright / 1 app, đọc baseURL từ local-config.json
├── local-config.example.json <- mẫu, CÓ commit (nếu sau này git-track thư mục này)
├── local-config.json         <- domain thật từng app — KHÔNG commit, tự tạo theo mẫu trên
└── tests/
    ├── <ten-app>/             <- khớp đúng tên app trong dev-journal (option/comp/swatch...)
    │   └── <MÃ>-<ten-feature>.spec.ts
    └── <ten-app>-admin/       <- tách riêng nếu app có cả storefront lẫn admin cần baseURL khác nhau
```

**KHÔNG BAO GIỜ** chạy `npm install @playwright/test` bên trong 1 repo app
(`api`/`cms`/`tae`/`tae-v2`/...) nữa — nếu thấy `@playwright/test` trong
`package.json` của 1 app repo, đó là tàn dư cũ, nên dọn (`npm uninstall
@playwright/test`, xoá `playwright.config.ts`/`e2e/` trong repo đó) rồi
chuyển toàn bộ sang `~/Shopify/skill/personal-workspace/e2e-tests/`.

## Nguyên tắc tối cao: tiết kiệm token

Đây là ràng buộc QUAN TRỌNG NHẤT của skill này, không phải gợi ý:

- **Không bao giờ lái browser từng bước bằng screenshot/computer-use/vision loop.** Viết test case thành code Playwright (`.spec.ts`) rồi chạy bằng `npx playwright test` qua Bash — Playwright tự điều khiển browser, tự assert, tự chụp ảnh khi fail. 1 lần gọi Bash chạy được hàng chục test case, thay vì hàng chục lượt tool-call nhìn ảnh.
- **Chỉ đọc kết quả tóm tắt** (`npx playwright test --reporter=list` hoặc JSON summary: số pass/fail/skip) — KHÔNG đọc toàn bộ trace/video/HTML report trừ khi có test FAIL cần debug. Test pass thì không cần xem ảnh/trace của nó.
- **Khi có fail, chỉ đọc đúng artifact của test đó** (trace/screenshot/error message của riêng test case fail), không đọc lại toàn bộ report hay trace của các test đã pass.
- **Setup kho dùng chung chỉ 1 lần duy nhất trên cả máy** (xem Bước 1) — kiểm tra đã có `~/Shopify/skill/personal-workspace/e2e-tests/` chưa TRƯỚC KHI tạo mới. Đừng cài lại package/browser mỗi lần chạy skill, dù đang ở app/repo nào.
- **Sinh toàn bộ test case cho 1 feature trong 1 lượt viết file**, không viết từng test case một kèm hỏi qua lại.

Nếu phát hiện bản thân đang chuẩn bị dùng `computer`/screenshot để tương tác browser trong skill này — DỪNG LẠI, đó là dấu hiệu đang đi sai hướng của skill này.

## Bước 0 — Xác định phạm vi & nguồn requirement

1. Cần biết: task/feature nào (mã Jira nếu có), app nào bị đụng (dùng đúng tên app như trong dev-journal: `option`/`comp`/`swatch`...), repo con nào trong app đó (api/cms/tae/tae-v2).
2. Thu thập đúng 3 nguồn, KHÔNG được thiếu nguồn nào nếu nó tồn tại:
   - **Plan**: tìm file `<MÃ>-plan.md` trong worktree hiện tại (do skill `create-plan` tạo ra trước đó). Có thì đọc — nó cho biết phạm vi/file đã đụng, tránh test lan ra ngoài scope.
   - **AC/requirement Jira**: dùng skill `jira-core` (`get <MÃ>`) lấy description/AC thật — đây là nguồn chuẩn để map test case, KHÔNG tự bịa case nếu AC không nhắc tới.
   - **Repo thật**: đọc code vừa implement (route, component, selector thật — vd `data-testid`, `aria-label` đã có sẵn) để viết selector ĐÚNG, không đoán. Nếu component chưa có `data-testid`/`aria-label` ổn định, ưu tiên đề xuất thêm (báo user) hơn là dùng selector giòn (class CSS, text có thể đổi).
3. Nếu thiếu 1 trong 3 nguồn (vd không có file plan vì task nhỏ, hoặc Jira không có AC rõ) — nói rõ đang thiếu gì, hỏi user có muốn tự liệt kê case cần test không, KHÔNG tự bịa AC để lấp chỗ trống.

## Bước 1 — Đảm bảo kho dùng chung tồn tại (CHỈ setup khi CHƯA có)

Kiểm tra `~/Shopify/skill/personal-workspace/e2e-tests/package.json` tồn tại chưa — có rồi thì bỏ qua toàn bộ việc cài đặt, đi thẳng vào phần "Thêm project cho app mới" bên dưới (nếu app này chưa có project).

**CHƯA có kho dùng chung** (lần đầu tiên trên cả máy) — tạo 1 lần:
```
mkdir -p ~/Shopify/skill/personal-workspace/e2e-tests/tests
cd ~/Shopify/skill/personal-workspace/e2e-tests
npm init -y   # rồi sửa lại package.json cho gọn, thêm "devDependencies": {"@playwright/test": "^1.48.0"}
npm install
npx playwright install chromium   # KHÔNG dùng --with-deps nếu môi trường không có sudo tương tác (sẽ hang chờ auth) — thử trước, chỉ thêm --with-deps nếu lỗi thiếu system lib
```
Tạo `playwright.config.ts` đọc `baseURL` theo từng **project** (1 project = 1 app hoặc 1 app+ngữ cảnh, vd `option-storefront` / `option-admin`) từ `local-config.json` (xem cấu trúc ở đầu file này).

### Thêm project cho app MỚI (app chưa từng test bằng skill này)

1. Mở `~/Shopify/skill/personal-workspace/e2e-tests/local-config.json` (tạo nếu chưa có, theo mẫu `local-config.example.json`) — thêm key cho app này.
2. Mở `playwright.config.ts` — thêm 1 entry vào mảng `projects`, `testDir: './tests/<ten-app>'`, `baseURL` trỏ đúng key vừa thêm.
3. Tạo thư mục `tests/<ten-app>/`.

### Xác định domain cho `baseURL` — 2 tình huống khác nhau

- **App có dev server local được** (vd `api`/`cms` chạy qua `docker/docker-compose.yaml` của chính worktree): đọc `docker-compose.yaml`/`.env`/`.env.example` của worktree đó để biết port thật — KHÔNG đoán port. `baseURL` trỏ `localhost:<port>`.
- **App PHẢI chạy trên storefront/admin Shopify thật** (vd storefront V2 — tự khai trong `CLAUDE.md` kiểu "verified on a real storefront", không có dev server local): KHÔNG cố dựng testsite mới qua `/te-dev-new-testsite` nếu user chưa yêu cầu — thay vào đó **hỏi thẳng user domain của 1 store thật đã cài sẵn app** (storefront + admin, nếu cần cả hai, hỏi cả hai). Lưu vào `local-config.json` (key = tên project).
- Nếu 1 feature đụng CẢ storefront lẫn admin (vd OPOS-168: `api` sync giá + `tae-v2` hiển thị giá) → 2 project riêng (`<app>-storefront`, `<app>-admin`), chạy độc lập, không gộp chung 1 test vừa gọi domain storefront vừa gọi admin.
- **`local-config.json` không bao giờ đặt tên theo pattern `.env*`** — permission settings của nhiều máy/project chặn cứng mọi write vào `.env*` (kể cả qua Bash, không chỉ qua tool Write). Domain store KHÔNG BAO GIỜ hardcode vào `playwright.config.ts` nếu thư mục `e2e-tests/` có git-track — luôn đọc qua `local-config.json`.

Nếu feature cần đăng nhập Shopify Admin, setup `storageState` MỘT LẦN cho project đó:
```
npx playwright codegen --save-storage=tests/<app>-admin/.auth/storageState.json <admin-login-url>
```
hoặc viết 1 login helper dùng Playwright's project dependencies, chạy 1 lần, các test case sau tái dùng `storageState` — không đăng nhập lại ở mỗi test (vừa tốn thời gian vừa dễ bị rate-limit). **Đăng nhập Shopify Admin (admin.shopify.com) là tài khoản thật** — KHÔNG tự nhập mật khẩu, phải để user tự đăng nhập 1 lần trong browser headed rồi mình lưu `storageState` lại; mật khẩu STOREFRONT (trang khoá site, không phải tài khoản) thì được phép tự nhập vì đó không phải credential cá nhân.

## Bước 2 — Sinh test case

Viết file `.spec.ts` trong `tests/<ten-app>/<MÃ>-<ten-feature>.spec.ts`, mỗi AC/case trong plan ánh xạ thành 1 `test(...)` block, đặt tên test mô tả đúng AC (vd `test('option gating: hides option type not in plan entitlement', ...)`). Dùng `test.describe` gom theo feature/AC group, ghi rõ mã Jira + app/repo nguồn trong comment đầu file.

Ưu tiên selector theo thứ tự: `data-testid` > `role`/`aria-label` (Playwright recommended) > text content ổn định > CSS class (chỉ khi không còn cách nào khác, và phải nói rõ với user đây là selector giòn, dễ vỡ khi đổi style).

Comment ngắn trên mỗi test trỏ về đúng mục AC nào trong Jira/plan (vd `// AC3: option bị khoá khi plan không có entitlement`) — để sau này đối chiếu lại dễ, và để lần review-plan/review-code sau biết test này phủ AC nào.

## Bước 2.5 — Adversarial verify test case (TRƯỚC khi tốn thời gian/token chạy browser thật)

Mục đích: test case tự mình viết ra có thể hiểu sai AC, hoặc assert sai thứ (vd assert UI hiện ra mà quên assert đúng giá trị, hoặc test "pass" dù không thực sự kiểm tra được bug) — phát hiện việc này SAU khi đã chạy `npx playwright test` (tốn thời gian mở browser thật) đắt hơn nhiều so với phát hiện ngay trên code test vừa viết.

**Nạp known-issues trước** (app suy từ mã Jira, prefix OPOS/OPOK→option, OPCS/OPSK→swatch, OPTCLT→comp):
```bash
python3 ~/Shopify/skill/personal-workspace/dev-journal/scripts/get-known-issues.py --app <ten-app>
```

**Model routing**: `Agent(model: "haiku")` cho lượt đầu — việc soi 1 file test tĩnh không cần model mạnh. Không chắc → gọi lại 1 lần với `model: "sonnet"`.

Dùng `Agent` tool, gọi **2 agent độc lập song song**, mỗi agent chỉ nhận: known-issues ở trên, AC gốc (từ Jira/plan), và nội dung file `.spec.ts` vừa viết (KHÔNG chạy test, KHÔNG cần quyền vào browser).

```
Prompt mỗi agent: "Lỗi đã từng gặp ở task trước (kiểm tra có tái diễn
trong bộ test này không): <dán output known-issues>. Đây là AC gốc: <dán
AC>. Đây là file test vừa viết: <dán nội dung .spec.ts>. Hãy CỐ TÌNH tìm
lỗi trong CHÍNH bộ test này — không phải trong feature đang test: (a) AC
nào trong danh sách trên KHÔNG có test nào tương ứng, (b) test nào assert
sai thứ so với tên/comment AC của nó (vd tên nói 'option bị khoá' nhưng
assert chỉ check element tồn tại, không check disabled/hidden thật), (c)
test nào có khả năng LUÔN pass bất kể code đúng hay sai (assertion yếu,
selector quá rộng, thiếu await dẫn tới race condition). Mặc định nghi
ngờ, không mặc định tin test đã viết đúng. Nếu thật sự không tìm ra gì,
trả lời KHÔNG CÓ VẤN ĐỀ kèm lý do đã xem đủ kỹ từng test — không chắc thì
nói rõ 'không chắc'. NGÂN SÁCH TOOL-CALL: tối đa ~3 lượt (chỉ đọc 1 file
tĩnh, không cần nhiều). GIỚI HẠN PHẠM VI: chỉ đọc đúng file .spec.ts được
đưa, KHÔNG tự ý mở thêm file khác trong repo, KHÔNG chạy lệnh Playwright
nào, KHÔNG spawn sub-agent — mục tiêu là soi code test nhanh và rẻ, không
phải điều tra sâu cả codebase."
```

- Có finding cụ thể (test thiếu AC, assert sai, test vô dụng) → sửa file `.spec.ts` ngay, rồi mới sang Bước 3. Không chạy Playwright với bộ test biết trước là có lỗ hổng — vừa tốn thời gian chạy vừa cho kết quả "pass" giả tạo không đáng tin.
- Cả 2 "KHÔNG CÓ VẤN ĐỀ" → sang Bước 3 bình thường, không cần nhắc trong báo cáo cuối (tránh báo cáo dài dòng khi không có gì đặc biệt).
- Bỏ qua bước này nếu chỉ có 1-2 test case rất đơn giản (vd test smoke "trang load được") — áp dụng khi bộ test có từ ~3 case trở lên hoặc test logic nghiệp vụ phức tạp (gating theo plan, điều kiện nhiều nhánh).

## Bước 3 — Chạy test thật + Capture Evidence

### Lệnh chạy (bắt buộc capture output + artifacts):

```bash
cd ~/Shopify/skill/personal-workspace/e2e-tests

# Setup thư mục evidence cho task này
EVIDENCE_DIR="/tmp/claude-*/scratchpad/evidence/<MÃ>-<ten-feature>"
mkdir -p "$EVIDENCE_DIR"/{screenshots,traces}

# Chạy test với FULL output + JSON report + trace on fail
npx playwright test \
  --project=<ten-app> \
  tests/<ten-app>/<MÃ>-<ten-feature>.spec.ts \
  --reporter=json \
  --reporter=list \
  2>&1 | tee "$EVIDENCE_DIR/test-output.log"

# Lưu JSON report
if [ -f "test-results/results.json" ]; then
  cp test-results/results.json "$EVIDENCE_DIR/test-results.json"
fi

# Copy trace + screenshot từ từng test fail vào evidence
for dir in test-results/*/; do
  testname=$(basename "$dir")
  if [ -f "$dir/trace.zip" ]; then
    cp "$dir/trace.zip" "$EVIDENCE_DIR/traces/${testname}.zip"
  fi
  if [ -f "$dir/test-failed-1.png" ]; then
    cp "$dir/test-failed-"*.png "$EVIDENCE_DIR/screenshots/" 2>/dev/null
  fi
done

echo "Evidence saved to: $EVIDENCE_DIR"
```

**Luôn chỉ định `--project`** (tránh chạy nhầm sang project/app khác) VÀ chạy đúng file/thư mục vừa sinh trước (phạm vi hẹp, nhanh, rẻ) — chỉ chạy toàn bộ 1 project khi user yêu cầu regression toàn diện cho app đó.

### Parse kết quả từ evidence files:

```python
# Đọc test-results.json
import json
with open(f"{EVIDENCE_DIR}/test-results.json") as f:
    results = json.load(f)

# Map AC → test → pass/fail từ results['suites'][0]['tests']
for test in results['suites'][0]['tests']:
    status = "✅ Pass" if test['status'] == 'passed' else "❌ Fail"
    print(f"Test: {test['title']}")
    print(f"  Status: {status}")
    print(f"  Duration: {test['duration']}ms")
    if test.get('error'):
        print(f"  Error: {test['error']['message']}")
```

### Adversarial verify cho case phức tạp/lúng túng (NGAY sau khi case đó chạy xong, không chờ cả suite xong)

Khác với Bước 2.5 (soi code test TĨNH, trước khi chạy) — đây là soi **kết quả chạy thật** của riêng những case có dấu hiệu "lúng túng", vì pass/fail của Playwright không tự động đáng tin với case phức tạp (có thể pass giả do assertion yếu, hoặc fail giả do flaky chứ không phải bug thật).

**Chỉ áp dụng cho case khớp ít nhất 1 dấu hiệu sau** (không chạy máy móc cho mọi case — tốn token vô ích cho case đơn giản, rõ ràng):
- Playwright phải **retry** mới ra kết quả cuối (retry count > 0 trong `test-results.json`).
- **Duration** của case đó cao bất thường so với mặt bằng chung các case khác trong cùng file (vd gấp 2-3 lần trung vị) — dấu hiệu đang chờ/polling nhiều, logic timing phức tạp.
- Case có **nhiều điều kiện/nhánh** trong chính nó (nhiều `await`/`if`/multiple assertion không liên quan nhau) — nhận diện qua chính nội dung `.spec.ts` khi viết, không cần chạy mới biết.
- Case **fail nhưng lý do không rõ ràng** (error message generic kiểu timeout, không chỉ thẳng assertion nào sai).

**Với mỗi case khớp**, gọi 1 agent `model: "haiku"` trước (không cần 2 — đã có bằng chứng chạy thật cụ thể để agent bám vào, không phải suy đoán tĩnh như Bước 2.5, nên 1 agent đủ). Agent báo "không chắc" → gọi lại đúng case đó 1 lần với `model: "sonnet"` thay vì tin kết luận mơ hồ:

```
Prompt: "Case Playwright này có dấu hiệu lúng túng: <mô tả dấu hiệu — retry/
duration cao/case fail mơ hồ>. Đây là nội dung test: <dán đúng test() block
đó, không cần cả file>. Đây là kết quả thật: status=<pass/fail>, duration=
<ms>, retry=<n>, error=<nếu có>. Đây là nội dung trace/log liên quan (nếu
có): <dán log dòng liên quan, KHÔNG dán cả trace.zip>. Đánh giá: (a) nếu
PASS — có khả năng đây là pass giả không (assertion yếu tới mức sai cũng
pass), hay là pass thật dù phải retry/chậm vì lý do hợp lý (network/animation)?
(b) nếu FAIL — đây là bug thật trong code đang test, hay là flaky/lỗi ở
chính test (selector/timing), và vì sao bạn kết luận vậy? Mặc định nghi
ngờ kết quả Playwright báo, không mặc định tin. GIỚI HẠN PHẠM VI: chỉ dựa
vào nội dung được đưa, KHÔNG tự chạy lại Playwright, KHÔNG mở file khác,
KHÔNG spawn sub-agent."
```

- Kết luận "pass giả" hoặc "bug thật" → ghi rõ vào `TEST-REPORT.md` kèm giải thích của agent, KHÔNG báo case đó là pass/fail trơn theo Playwright — đây chính xác là lúc "agent test đang lúng túng" cần được giải quyết bằng lý lẽ thay vì tin mù kết quả máy chạy.
- Kết luận "flaky do chính test" (không phải bug code) → đề xuất sửa lại test (chờ đúng điều kiện thay vì timeout cứng, hoặc selector ổn định hơn) trước khi tính case đó là đáng tin, không chạy lại mong nó "pass may rủi".
- Case không khớp dấu hiệu nào ở trên → bỏ qua bước này, tin thẳng kết quả Playwright như bình thường (đa số case nên rơi vào nhánh này — mục tiêu là chỉ tốn công cho đúng chỗ khó, không phải mọi case).

### Nếu có fail:

1. **Không sửa code ngay** — báo cáo fail trước
2. **Lưu trace/screenshot** từ `test-results/<testname>/trace.zip` vào `evidence/traces/`
3. **Lưu error message** vào file text trong `evidence/`
4. **Chỉ khi user confirm** ("sửa selector rồi chạy lại") mới vào code fix + rerun

## Bước 4 — Báo cáo kết quả với EVIDENCE

**Bắt buộc:**
1. **Chạy thật** — output của `npx playwright test` phải có trong response (không bịa kết quả "anh test rồi nó pass")
2. **Evidence folder** — lưu tất cả artifacts vào `evidence/<MÃ>-<feature>/`:
   - `test-output.log` — stdout/stderr đầy đủ từ lệnh Playwright
   - `test-results.json` — JSON summary từ Playwright (pass/fail/skip, duration)
   - `screenshots/` — ảnh từ failed test (Playwright tự chụp khi assert fail)
   - `traces/` — trace.zip từ failed test (nếu bật `trace: 'on-first-retry'` trong config)
   - **`TEST-REPORT.md`** — bảng map AC → test + status + evidence link

3. **Bảng map chi tiết:**
```
| Mã AC | Mô tả | Test name | Status | Evidence | Ghi chú |
|---|---|---|---|---|---|
| AC1 | option gating hides... | `test-ac1-gating-hidden` | ✅ Pass | [screenshot](screenshots/ac1.png) | Chạy lên 2 lần, pass lần 2 |
| AC2 | plan upgrade shows... | `test-ac2-upgrade` | ❌ Fail | [trace](traces/ac2.zip) [error](evidence/ac2-error.txt) | Selector `.btn-upgrade` không tìm được, button text khác |
| AC3 | storage persist | Không test | ⏭️ Skip | — | Cần mock localStorage persist qua session, không khả thi với Playwright cross-session |
```

4. **Khi test FAIL:**
   - Đọc error message từ Playwright output
   - Lưu trace + screenshot vào `evidence/`
   - Ghi rõ lý do: assertion fail / selector not found / timeout / ...
   - **KHÔNG tự sửa code + rerun ngay** — báo cáo fail trước, hỏi user muốn debug/fix hay skip
   - Nếu fail do vô tình (selector lạ, timing), hỏi user confirm trước khi chạy lại

5. **Liệt kê case chưa test:**
   - Case nào trong AC/plan mà KHÔNG sinh được test → liệt kê rõ trong bảng (cột Status = `⏭️ Skip`)
   - Ghi rõ lý do: "cần dữ liệu test phức tạp", "cần mock service ngoài", "cần session persistent", v.v.
   - Không im lặng bỏ qua (No silent caps)

**Evidence folder location** (công khai trong response, user tìm dễ):
```
<scratchpad>/evidence/<MÃ>-<feature>/
├── test-output.log
├── test-results.json
├── TEST-REPORT.md
├── screenshots/
│   └── ac1-gating.png
│   └── ac2-upgrade.png
└── traces/
    └── ac2.zip
```
Dùng SendUserFile gửi toàn bộ evidence folder + TEST-REPORT.md link cho user xem.

## Bước 5 — Lưu lại để tái sử dụng (tùy chọn, hỏi trước)

Nếu task có dev-journal (`.dev-journal` symlink), đề xuất lưu 1 decision/retro ngắn ghi lại: feature nào đã có e2e coverage ở `e2e-tests/`, setup gì đã làm 1 lần (storageState, project mới...) — để lần sau skill này (hoặc người khác) không dò lại từ đầu. Dùng đúng flow hỏi-trước-khi-lưu của skill `dev-journal-save`, không tự ý ghi.

## Anti-Hallucination Checklist — BẮTIC BUỘC trước khi báo "Test pass/fail"

**Trước khi nói "test pass" hoặc "test fail", phải confirm ALL:**

- [ ] **Lệnh Playwright thật sự chạy** — output có dòng `Running X tests` từ Playwright CLI (không phải bịa)
- [ ] **Lưu log từ Playwright** — file `test-output.log` có stdout đầy đủ từ `npx playwright test`, không trống
- [ ] **Kết quả JSON từ Playwright** — file `test-results.json` từ `--reporter=json` (hoặc parse từ log), ghi rõ pass/fail per test
- [ ] **Evidence screenshot/trace** — nếu fail, folder `evidence/` chứa trace.zip / screenshot từ Playwright (file thật, không tạo giả)
- [ ] **TEST-REPORT.md được lưu** — bảng map AC → test → status với link evidence
- [ ] **Mã task ghi rõ trong folder** — evidence folder đặt tên `<MÃ>-<feature>`, mã này khớp với Jira/task hiện tại

**Nếu BẤT KỲ ô nào KHÔNG ✅:**
- KHÔNG báo "pass" / "fail" vội
- Chạy lệnh Playwright lại ngay bây giờ (không chờ)
- Nếu vẫn gặp lỗi hoặc không chạy được → báo lỗi chi tiết cho user, không im lặng

**Ví dụ SAIIII:**
```
❌ "Test pass, AC1-AC3 đều xanh, mình đã chạy Playwright rồi"
    — không có file test-output.log, không có screenshot, chỉ là nói suông
```

**Ví dụ ĐÚNG:**
```
✅ "Test pass AC1-AC3, fail AC4. Evidence đã lưu vào evidence/OPOS-136-gating/:
    - test-output.log: 4 passed, 1 failed in 23.4s
    - TEST-REPORT.md có bảng chi tiết
    - ac4-fail.png + ac4-trace.zip trong screenshots/"
```

## Lỗi hay gặp

- **Cài `@playwright/test` bên trong 1 app repo** (api/cms/tae/tae-v2...) thay vì dùng kho chung `~/Shopify/skill/personal-workspace/e2e-tests/` — gây cài lặp lại nhiều lần, test case phân tán theo từng repo, khó tái sử dụng. Fix: luôn kiểm tra/dùng kho chung trước, dọn sạch nếu lỡ cài nhầm vào 1 repo.
- **Dùng `computer`/screenshot để click qua từng bước trong browser** thay vì viết Playwright test — vi phạm trực tiếp nguyên tắc tiết kiệm token của skill này. Fix: luôn viết `.spec.ts` rồi chạy qua CLI.
- **Kết luận "không test được" chỉ vì app không có dev server local** (vd storefront V2) — bỏ cuộc quá sớm. Fix: hỏi user domain store thật đã cài app để test trực tiếp lên đó, thay vì mặc định cần dựng testsite mới hoặc bỏ qua.
- **Hardcode domain store thật vào `playwright.config.ts`** — rò rỉ thông tin store test nếu `e2e-tests/` sau này được git-track. Fix: domain store luôn nằm trong `local-config.json` (gitignored nếu track git), đọc qua `fs.readFileSync` trong config.
- **Tự nhập mật khẩu tài khoản Shopify Admin thật** (admin.shopify.com) để lấy `storageState` — vi phạm nguyên tắc an toàn chung, kể cả trên store của chính user. Fix: luôn để user tự đăng nhập 1 lần (browser headed), chỉ lưu lại session sau đó. Mật khẩu STOREFRONT (khoá site, không phải tài khoản cá nhân) thì được tự nhập.
- **Setup lại Playwright/storageState mỗi lần chạy** dù đã có từ lần trước — tốn thời gian + đăng nhập lặp lại dễ bị khoá tài khoản test. Fix: luôn kiểm tra đã có package/config/storageState chưa trước khi tạo mới.
- **Đọc toàn bộ HTML report/trace của mọi test kể cả pass** — tốn token vô ích. Fix: chỉ đọc artifact của test fail.
- **Tự bịa case khi AC không nhắc tới** để "cho đủ coverage" — sai tinh thần acceptance test (test phải bám AC thật). Fix: thiếu AC thì hỏi user, không đoán.
- **Chạy nhầm sang project/app khác** hoặc chạy toàn bộ khi chỉ cần test 1 feature mới — chậm, có thể đụng vào test cũ không liên quan. Fix: luôn chỉ định đúng `--project` + scope file/thư mục.
- **Dùng CSS class làm selector chính** khi component có sẵn `data-testid`/`aria-label` — test dễ vỡ khi đổi style không liên quan tới logic. Fix: ưu tiên đúng thứ tự selector ở Bước 2.

## CRITICAL — Anti-Hallucination Violations

**Nếu gặp bất kỳ mẫu nào dưới đây, đó là FAIL và phải rewind:**

- ❌ "Test pass, AC1-AC3 xanh tất cả" — nhưng không có file `test-output.log`, không có screenshot. Lệnh không chạy thật, đây là bịa.
  - Fix: **Chạy lệnh ngay bây giờ**, lưu full output, capture evidence

- ❌ "Playwright pass tất cả nhưng tôi không chạy lệnh" — nói suông mà không có proof of run.
  - Fix: Tất cả phải đi kèm stdout đầy đủ từ `npx playwright test`, không ngoại lệ

- ❌ "Fail vì selector không đúng, anh sửa rồi test lại" — nhưng không show test output trước/sau, không có trace của fail lần 1.
  - Fix: Luôn lưu trace/screenshot của test lần fail trước, để user audit được

- ❌ "AC4 không test được vì cần dữ liệu phức tạp" — nhưng không liệt kê trong TEST-REPORT.md, im lặng bỏ đi.
  - Fix: Mỗi AC phải có dòng trong bảng, dù skip, với lý do rõ

- ❌ "Test pass nhưng folder evidence không tồn tại / TEST-REPORT.md trống".
  - Fix: Bắt buộc lưu evidence folder + TEST-REPORT.md, không ngoại lệ

**Nếu user nhìn thấy bất kỳ violation nào:** hộp thoại `[Artifact comment sent to Claude]` → fix ngay (rewind, chạy lại, lưu evidence đúng).
