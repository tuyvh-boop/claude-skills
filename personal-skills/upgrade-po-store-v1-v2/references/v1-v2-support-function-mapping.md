# Mapping tham khảo: `bssFixSupportXxx` (v1) → socket `support.v1.*` (v2)

> Kết quả nghiên cứu code `tae` (v1) + `tae-v2` (v2) + `api` (backend) tại thời điểm OPOS-138.
> **Đây là baseline lịch sử, không phải nguồn chân lý sống** — tae-v2 có thể đã thêm socket mới.
> Luôn đối chiếu lại với `tae-v2/docs/support-function-guide.md` hiện tại trước khi kết luận
> "chưa có socket tương ứng".

## Bảng mapping

| Hàm v1 (`runscript.js`) | Mục đích | Socket v2 gần nhất | Trạng thái |
|---|---|---|---|
| `bssFixSupportForSpecificStore(shopData, BSS_PO)` | Patch tuỳ ý toàn bộ state cho 1 store | Không có 1-1; viết logic trực tiếp trong `optisPoV2Support` + `transformers.themeConfig`/`optionConfig` | Không migrate 1-1 (có chủ đích — v2 không cho patch tuỳ ý toàn object) |
| `bssFixSupportGenerateProductPage(BSS_PO)` | Custom render OptionSet PDP | — | Chưa thấy tương ứng, double-check lại |
| `bssFixSupportCustomPriceIncreament` | Bật custom price logic | `transformers.priceAddon` | Có tương ứng về mục đích, trigger khác (event-driven → declarative) |
| `bssFixSupportGetTimeoutGenerateOptionSet` | Workaround timing | — | Không cần (reconciler v2 tự coalesce theo animation frame) |
| `bssFixSupportGenerateHomePage()` | Custom homepage rendering | — | Chưa thấy tương ứng |
| `bssFixSupportManualInstall().fileUpload` | Xử lý file upload thủ công cart page | — | Chưa thấy tương ứng rõ ràng (có thể nằm ở module `shorten-file-upload` ngoài `support-function/`) |
| `bssFixEditOptionInMiniCart` | Bật edit option trong mini cart | — | Chưa thấy tương ứng |
| `bssFixSupportSetTimeOutInit` | Delay init cart theo store | — | Không cần (kiến trúc init khác hẳn) |
| `bssFixSupportCustomTimeoutForB2BApp` | Custom timeout chờ B2B app | — | Chưa thấy tương ứng — có thể ngoài scope `support-function/` |
| `bssFixSupportCustomOpenFeature()?.discountBox` | Bật discount box non-premium | — | Chưa thấy tương ứng |
| `bssFixSupportUseOldAddOnLogic` | Dùng add-on logic cũ | — | Không cần (hệ thống giá đã refactor hẳn ở v2) |
| `bssFixSupportBeforeTranslateDefaultText` | Sửa defaultText trước dịch | — | Chưa thấy tương ứng |
| `bssFixSupportCustomInitMinicart` | Override init mini cart | — | Chưa thấy tương ứng |
| `bssFixSupportHandlePriceOnMiniCart` | Custom giá hiển thị mini cart | Có thể gần `transformers.priceAddon`/`optionDisplay` | Chưa thấy tương ứng rõ ràng |
| `bssFixSupportHideWaterMark` (chỉ thấy marker ở backend `support.service.ts`) | Ẩn watermark | `ui.hideWatermark` | **Migrate rõ ràng** — nhưng endpoint backend `hide-watermark`/`watermark-status` vẫn hard-code `runtimeVersion = v1`, không có bản v2 |

6 socket sau của v2 **không có tiền thân ở v1** (năng lực hoàn toàn mới, không phải migrate):
`transformers.cartLineProperties`, `ui.addSlotContent`, `ui.replaceControl`, `conditions.add`,
`validators.add`, `transformers.themeConfig` (riêng `transformers.themeConfig` sau này mới phát hiện
*có* vài tiền thân cụ thể — xem bảng dưới).

## Mapping bổ sung — các hàm phát hiện sau (xác nhận bằng cách đọc call site thật, không chỉ theo tên)

| Hàm v1 | Call site v1 | Socket v2 | Trạng thái |
|---|---|---|---|
| `bssFixSupportChangeOptionSetPositionForProduct(BSS_PO, optionSetHtml, idProductOnHomePage, changed)` | `tae/src/modules/option-set/handle-option-set.js` (2 call site, "generate OptionSet for product" — cả main product lẫn home page) — nếu trả `true`, v1 bỏ qua chèn vị trí mặc định, để hook tự `insertAdjacentHTML` | `transformers.themeConfig` → field `product.elementBeforeOptions` / `featureProduct.elementBeforeOptions` (đã có sẵn, đúng use-case này) | **Migrate rõ ràng, có field chuyên dụng** — không cần viết JS tuỳ ý, chỉ cần 1 selector string |
| `bssFixSupportSetDefaultOptionValue(BSS_PO, option, defaultOptionsValue, setCustomDefautOptionValue, currentProduct, ...)` | `tae/src/modules/option-set/data/get-option-attribute.js` (trong `getCurrentVariant`) — plumbing nội bộ để khớp `<option>` native với variant đang chọn | — (v2 có `runtime/observers/variant/variant.resolver.ts` riêng, không expose) | **Không migrate, không cần** — nếu v2 detect sai variant trên theme cụ thể, đó là bug sản phẩm, không phải thứ sửa qua Support Function |
| `bssFixSupportActionAddToCart(BSS_PO, add_to_cart_btn, sticky_add_to_btn, addATCEvent)` | `tae/src/modules/cart/handle-add-to-cart.js` (ngay sau selector cascade mặc định của ATC button) — chọn lại DOM node nút ATC khi selector cascade mặc định không ra đúng nút | `transformers.themeConfig` → field `product.atcButton` (mảng selector thử lần lượt — xem docblock `tae-v2/src/modules/core/theme-config/types.ts`, field `atcButton`) | **Migrate rõ ràng, có field chuyên dụng** — chỉ cần prepend selector vào mảng có sẵn |
| `bssFixSupportForSpecificStore` khi thân hàm thực chất là AJAX-ATC generic cho form **không có** OptionSet (check `form.querySelector('.bss-po-option-set')?.children.length`) | `tae/src/init/runscript.js` | — | **Không migrate vào Support Function** — socket v2 chỉ áp dụng cho Instance có OptionSet, không có hook cho form bất kỳ. Khuyến nghị tách hẳn ra `theme.liquid` của store, ngoài phạm vi app |
| `bssFixSupportCustomAfterAddToCart(BSS_PO, data, button, oldFontSize)` | `tae/src/modules/cart/handle-add-to-cart.js` (nhánh cuối sau khi ATC thành công) — ở v1 **thay thế hoàn toàn** nhánh mini-cart/redirect mặc định | `api.on('cart:added', ...)` | **Cần quyết định, không phải migrate thẳng** — ở v2 đây là hành vi **cộng thêm**, không thay thế Core; phải hỏi xem mini-cart/checkout coordinator mặc định của v2 đã đủ thay cho phần custom (vd refresh cart header) hay chưa |

## So sánh backend v1 vs v2

| | v1 | v2 |
|---|---|---|
| Bảng | `fix_bug_for_stores` / `..._logs` | Cùng bảng, cột `runtime_version` phân biệt, unique `[shopId, runtimeVersion]` |
| Nội dung | Chuỗi JS CommonJS tự do (`module.exports = {...}`) | Không đổi — convention tên export `optisPoV2Support` (chỉ warning nếu thiếu, KHÔNG enforce) |
| Metafield | `OPTION_APP_DATA.BSS_PO_SUPPORT` | `OPTION_APP_DATA.BSS_PO_V2_SUPPORT` (key khác, độc lập hoàn toàn) |
| Parse | `vm.runInNewContext`, timeout 1s, `parseSupportScriptExports()` | Dùng chung helper |

**Hệ quả quan trọng nhất**: hai bản ghi v1/v2 của CÙNG một store là **độc lập hoàn toàn**.
Bật runtime v2 cho store **không** tự convert hay xoá nội dung v1 — nếu không chủ động port,
mọi `bssFixSupportXxx` của store đó im lặng ngừng chạy trên v2 mà không có cảnh báo nào.

## Chỗ hay bị bỏ sót khi convert 1 store cụ thể

1. **Watermark đã tắt bằng CS tool ở v1** → phải đăng ký lại `ui.hideWatermark` thủ công trong
   Support Function v2 (backend không mang theo).
2. **Hard-code `storeId` ngay trong code app** (`tae/src/init/runscript.js`, không phải trong nội
   dung support function của store) — những so sánh kiểu `BSS_PO.storeId == 2136` áp dụng ở MỌI
   store chạy v1, không chỉ store đang convert. Nếu store đang convert phụ thuộc 1 trong các hack
   này, phải viết lại thành 1 đăng ký `where`/`when` riêng trong Support Function của store đó —
   `tae-v2/.eslintrc.js` còn chặn hẳn việc so sánh `storeId`/`domain` trong code app.
3. **Tên export không đúng convention** `optisPoV2Support` → backend chỉ warning, không chặn,
   nên có thể publish "thành công" nhưng storefront không chạy gì — luôn verify bằng
   `BSS_PO_V2.runtime.support.list()` sau khi publish.
