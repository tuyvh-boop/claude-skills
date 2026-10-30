---
name: upgrade-po-store-v1-v2
description: Use when a specific OPTIS Product Options (OPOS) store needs to move its storefront runtime from v1 (bss-po-*) to v2 (optis-po-*) — toggling `storefrontRuntimeVersion`, verifying the automatic OptionSet/ThemeConfig/StoreConfig metaobject sync, and especially converting that store's v1 Support Function (global `bssFixSupportXxx` hooks) into the v2 `optisPoV2Support(support)` API before publishing. Triggers: "nâng cấp store X lên v2", "chuyển store sang runtime v2", "convert support function sang v2", "migrate v1 support function cho shop Y".
metadata:
  trigger: "user muốn nâng cấp 1 store cụ thể từ runtime v1 sang v2, hoặc convert riêng support function của 1 store"
  model_hint: "main loop — việc map từng hàm v1 sang socket v2 cần phán đoán theo ngữ cảnh code thật, không nên delegate mù cho subagent"
  keywords: ["OPTIS", "Product Options", "OPOS", "support function", "v1", "v2", "runtime", "bssFixSupport", "optisPoV2Support", "storefrontRuntimeVersion", "watermark", "migration"]
---

# Upgrade PO Store: v1 → v2

Chuyển **một store cụ thể** từ runtime v1 sang v2. Phần data (OptionSet/Setting/ThemeConfig) tự
động sync khi bật flag; phần rủi ro — **Support Function và mọi hack per-store** — không tự động
và là trọng tâm của skill này.

> Nền tảng kiến trúc (vì sao v1/v2 tách biệt, socket nào ứng với hàm nào) đã có sẵn ở
> [`references/v1-v2-support-function-mapping.md`](references/v1-v2-support-function-mapping.md).
> Đọc file đó trước khi map code — đừng suy luận lại từ đầu.

## Input bắt buộc

- **Domain** của store cần nâng cấp (vd `abc-store.myshopify.com`).
- Đường dẫn local tới 2 repo: `api` (nhánh `master2`/v2 đã checkout) và `tae-v2` (đã pull mới
  nhất — `git pull` trước khi bắt đầu nếu đã lâu không cập nhật, vì mapping/socket có thể đã thêm).
  Nếu thiếu `tae-v2` trong workspace hiện tại, hỏi user đường dẫn thay vì đoán.

## Setup lần đầu (chỉ 1 lần cho máy này)

```bash
cd skills/upgrade-po-store-v1-v2
cp config.example.yml config.yml   # rồi điền api_base_url + author
```

`api_base_url` là host thật của backend `api` (prod/staging/local) — **hỏi user**, đừng đoán.
Ghi thẳng vào store thật thông qua URL sai môi trường là lỗi khó revert.

## Luồng làm việc

### Bước 1 — Xác định trạng thái hiện tại của store

Đọc trạng thái runtime hiện tại của shop. Script không tự đọc được (`GET
/admin/shops/storefront-runtime-version` cần ký HMAC forward riêng của CRM) — hỏi user xem CRM/OSSA
admin, hoặc nếu có quyền DB read-only thì query cột `shops.storefront_runtime_version` (dùng skill
`sql-schema-annotation` nếu có MySQL MCP sẵn).

- Đã là `v2` rồi → bỏ qua bước 2, đi thẳng bước 3 (vẫn cần soát Support Function — store có thể đã
  bật v2 nhưng chưa ai convert Support Function).
- Đang `v1` hoặc `null` → tiếp bước 2.

### Bước 2 — Bật runtime v2 cho store

Thực hiện qua **CRM/OSSA admin UI** (`PATCH /admin/shops/storefront-runtime-version`, cần
`ADMIN_API_TOKEN` mà skill này không giữ) — đây là thao tác ảnh hưởng trực tiếp tới storefront thật
của khách hàng, **luôn làm qua kênh chính thức của team**, không tự ký request thay.

Sau khi bật, backend tự chạy (không cần làm gì thêm):
1. `RuntimeVersionSyncV2Service` → ghi metafield `BSS_PO_RUNTIME` (router đọc cái này để chọn bundle).
2. `StoreConfigSyncV2Service` → sync settings/plan/market sang metaobject `bss-po-store-config`.
3. `ThemeConfigSyncV2Service` → sync theme config sang `bss-po-theme-configs`.
4. `OptionSetSyncV2Service` → đọc lại toàn bộ OptionSet active, ghi metaobject detail + index.

Verify nhanh trên storefront (DevTools Console của 1 trang sản phẩm thuộc store đó):
```js
BSS_PO_V2.optionSetIndex           // có OptionSet của store, map đúng theo variant
BSS_PO_V2.runtime.getThemeConfig() // selector/wrapper đúng theme thật của store
```

### Bước 3 — Đọc Support Function v1 hiện có

```bash
uv run scripts/po_support_client.py get-support --domain <domain> --runtime-version v1 --out /tmp/v1-support.js
```

Nếu không có content (`Chưa có support content...`) → store này chưa từng có support function,
bỏ qua bước 4, chỉ cần kiểm tra bước 5 (watermark) và bước 6 (hard-code storeId).

### Bước 4 — Map từng hàm sang socket v2 và sinh code

1. Tách từng export `bssFixSupportXxx` trong file `/tmp/v1-support.js`.
2. Với mỗi hàm, tra [`references/v1-v2-support-function-mapping.md`](references/v1-v2-support-function-mapping.md)
   để biết socket v2 gợi ý. Bảng đó là baseline — **luôn đọc lại
   `tae-v2/docs/support-function-guide.md` hiện tại** (section 6 "Tra cứu toàn bộ API") trước khi
   viết code, phòng khi v2 đã thêm socket mới kể từ lúc bảng được viết.
3. Đọc **thân hàm v1 thật** (không chỉ tên hàm) để hiểu nó làm gì trên store cụ thể này — tên hàm
   chỉ gợi ý mục đích chung, logic thật có thể khác theo từng store.
4. Với hàm **có socket tương ứng rõ ràng**: viết lại bằng `support.v1.<socket>(...)`, giữ đúng
   `where`/`when`/`dependsOn` tương đương điều kiện gốc (vd điều kiện `BSS_PO.storeId == X` trong
   thân hàm v1 → bỏ hẳn, vì `where` đã tự scope theo domain đang convert).
5. Với hàm **chưa có socket tương ứng** (xem cột "Trạng thái" trong bảng mapping): KHÔNG tự bịa ra
   cách giả lập. Liệt kê rõ trong báo cáo cho user, phân loại:
   - "Không cần migrate" — nếu đọc thân hàm thấy nó chỉ còn ý nghĩa trong kiến trúc v1 (vd workaround
     timing, logic add-on cũ).
   - "Cần quyết định" — nếu hàm thực sự đổi hành vi nhìn thấy được cho khách (hiển thị, giá, điều
     kiện) mà v2 chưa có chỗ áp — báo user, không tự publish phần này, đừng đoán.
6. Gộp tất cả registration hợp lệ thành một file `window.optisPoV2Support = (support) => { ... }`
   đúng cú pháp trong guide (một `const api = support.v1`, mỗi registration có `name` mô tả rõ).

### Bước 5 — Watermark (nếu có)

Nếu v1 từng có export `bssFixSupportHideWaterMark`, hoặc user xác nhận store này đã được CS tắt
watermark thủ công trước đây: thêm vào code v2 đang soạn:
```js
api.ui.hideWatermark({ name: 'hide-watermark' });
```
Backend `hide-watermark`/`watermark-status` hiện hard-code `runtimeVersion = v1` — không có cách
nào đọc lại trạng thái này cho v2 qua API, phải hỏi user xác nhận thủ công.

### Bước 6 — Rà hard-code theo storeId trong code app (không phải trong support function)

Một số hành vi của v1 nằm hẳn trong `tae/src/init/runscript.js` dưới dạng `BSS_PO.storeId == <id>`
— không nằm trong nội dung Support Function của store nên **không đọc được qua API**. Hỏi dev/CRM
xem domain đang convert có `storeId` nào trùng các hack đã biết không
(`grep -n "storeId ==" tae/src/init/runscript.js` để liệt kê toàn bộ ứng viên hiện có); nếu có,
thêm registration tương đương vào Support Function v2 đang soạn (dùng `where`/`when`, không hard-code
`storeId` — `tae-v2/.eslintrc.js` còn chặn thẳng kiểu so sánh này trong code app).

### Bước 7 — Review với user trước khi publish

Trình bày cho user:
- File code v2 hoàn chỉnh.
- Bảng mapping cho đúng domain này: hàm nào → socket nào, hàm nào bị bỏ qua và vì sao.
- Danh sách "cần quyết định" (nếu có) — không publish các phần này cho tới khi user xác nhận.

### Bước 8 — Publish (chỉ khi user đồng ý)

```bash
uv run scripts/po_support_client.py update-support --domain <domain> --runtime-version v2 --file v2-support.js
# in payload, KHÔNG gửi gì (dry-run)

uv run scripts/po_support_client.py update-support --domain <domain> --runtime-version v2 --file v2-support.js --commit
# ghi thật — publish ngay lên metafield Shopify, lên live storefront ngay lập tức
```

**Luôn chạy dry-run trước, cho user xem payload (domain + độ dài content), rồi mới hỏi xác nhận
`--commit`.** Đây là ghi trực tiếp vào storefront của một cửa hàng thật — không tự thêm `--commit`
thay cho user dù đã review code kỹ ở bước 7.

### Bước 9 — Verify sau publish

```js
BSS_PO_V2.runtime.support.list()               // status 'active', đủ số registration đã soạn
BSS_PO_V2.runtime.support.list().registrations // đối chiếu từng name với danh sách đã publish
BSS_PO_V2.runtime.support.resolve({ ... })     // test lại where của 1-2 registration quan trọng
```

Convention tên export sai (không phải `optisPoV2Support`) chỉ bị **warning**, không chặn publish —
nếu `list().status` không phải `active`, kiểm tra lại tên hàm trước khi nghi ngờ logic bên trong.

## Rollback

Chuyển `storefrontRuntimeVersion` của store về `v1` qua CRM (như bước 2, chiều ngược lại).
`RuntimeVersionSyncV2Service` luôn chạy đầu tiên và không phụ thuộc shop có đang v2 hay không, nên
router quay lại v1 gần như ngay lập tức. Nội dung Support Function v2 đã publish **không bị xoá** —
vẫn nằm trong `BSS_PO_V2_SUPPORT`, chỉ đơn giản không còn được load.

## Common mistakes

| Sai | Hậu quả |
|---|---|
| Tưởng bật runtime v2 tự convert luôn support function | Mọi `bssFixSupportXxx` của store im lặng ngừng chạy, không có cảnh báo nào |
| Map theo tên hàm mà không đọc thân hàm | Logic thật của store đó có thể khác với ý nghĩa thường gặp của tên hàm |
| Tự `--commit` ngay sau khi soạn xong code | Ghi thẳng production, không có bước duyệt nào ở backend — phải người xác nhận |
| Bỏ qua bước watermark/hard-code storeId | Hai chỗ này không nằm trong nội dung Support Function nên dễ quên nhất |
| Dùng bảng mapping tĩnh mà không đọc lại `support-function-guide.md` | Bảng là baseline lịch sử, `tae-v2` có thể đã thêm socket mới từ lúc đó |
