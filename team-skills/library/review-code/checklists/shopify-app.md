# Shopify App Checklist (đặc thù Shopify — cộng thêm lên base)

> Chỉ nạp khi repo là Shopify app (`shopify.app.toml`, dep `@shopify/*`).
> Vẫn theo quy tắc `Áp dụng khi:` — chỉ soi mục khớp bề mặt bị chạm.

## Multi-tenant / cô lập shop (QUAN TRỌNG NHẤT)
- **Mọi query đều scope theo shop** (`shop_id`/`shop_domain`). Thiếu = rò dữ liệu chéo shop → **Critical**. — `Áp dụng khi: db-query`
- **Không tin `shop` từ client**; lấy shop từ session/token đã xác thực, không từ param tuỳ ý. — `Áp dụng khi: api-endpoint, auth`
- **Dữ liệu/khoá cache/tên file** có tách theo shop không? — `Áp dụng khi: db-query, external-call`

## Webhook
- **HMAC verification** trên mọi webhook, dùng so sánh **timing-safe**; verify trên **raw body** (không phải body đã parse). — `Áp dụng khi: webhook`
- **Idempotency:** webhook có thể tới trùng/nhiều lần → xử lý không được nhân đôi tác dụng. — `Áp dụng khi: webhook`
- **Phản hồi nhanh 200 rồi xử lý nền** nếu việc nặng (tránh timeout → Shopify retry). — `Áp dụng khi: webhook`

## Compliance / GDPR (bắt buộc để qua review App Store)
- **3 mandatory webhooks** có xử lý đúng không: `customers/data_request`, `customers/redact`, `shop/redact`. — `Áp dụng khi: webhook`
- **`app/uninstalled`:** dọn dữ liệu/huỷ token/ngừng job khi gỡ app. — `Áp dụng khi: webhook`
- **PII khách hàng** lưu/log tối thiểu, có cơ chế xoá khi bị redact. — `Áp dụng khi: db-query, external-call`

## Auth / OAuth / session token
- **OAuth scope** đúng & tối thiểu; state/nonce chống CSRF trong luồng OAuth. — `Áp dụng khi: auth`
- **Online vs offline token** dùng đúng mục đích; token lưu **mã hoá/an toàn**, không log. — `Áp dụng khi: auth`
- **Session token (embedded app)** verify chữ ký JWT & exp trên mỗi request. — `Áp dụng khi: auth, api-endpoint`

## Shopify Admin API
- **Rate limit:** GraphQL theo **cost/leaky-bucket**, REST theo call limit → có backoff/retry khi `429`/`THROTTLED`. — `Áp dụng khi: external-call`
- **Bulk Operations** cho tập dữ liệu lớn thay vì loop query lẻ. — `Áp dụng khi: external-call`
- **API version** được ghim rõ, không xài field/endpoint đã deprecated. — `Áp dụng khi: external-call, config`
- **Xử lý userErrors** trong GraphQL mutation (không chỉ check HTTP 200). — `Áp dụng khi: external-call`
- **Pagination** (cursor) xử lý đủ, không chỉ trang đầu. — `Áp dụng khi: external-call`

## App Proxy
- **Verify chữ ký** request qua App Proxy (`signature` HMAC) trước khi xử lý. — `Áp dụng khi: api-endpoint`

## Billing
- **Billing API** đúng loại (recurring/usage/one-time); kiểm tra trạng thái charge trước khi mở tính năng trả phí; xử lý `test` flag ở môi trường dev. — `Áp dụng khi: external-call, api-endpoint`

## Embedded frontend
- **App Bridge** dùng đúng; **CSP `frame-ancestors`** cho phép nhúng trong Admin đúng shop. — `Áp dụng khi: ui, config`
- **Polaris** & accessibility cơ bản khi dựng UI trong Admin. — `Áp dụng khi: ui`

## Core Web Vitals — LCP / CLS

> Shopify chấm Web Vitals của embedded app trong Admin (và Lighthouse gate khi review App Store), nên đây là **tiêu chuẩn thường trực**, không phải chỉ soi khi task tên là "fix LCP".
> Chỉ cần diff chạm `ui` là soi — thêm 1 banner, 1 ảnh, 1 loading gate, 1 dep mới là đủ phá vitals.
> Cả hai chỉ số **kéo nhau**: fix CLS bằng skeleton/gate thường làm LCP tăng, và ngược lại. Sửa 1 cái thì phải đo lại cái kia.

### LCP
- **LCP element phải có trong HTML của first paint.** Nếu ảnh/heading LCP nằm sau một client-side data gate (`if (isLoading) return <Skeleton/>`), preload scanner không thấy nó → `fetchPriority="high"` gần như vô nghĩa, request chỉ bắt đầu sau hydration + API. Hoặc render nó ngoài gate, hoặc `<link rel="preload" as="image">` trong `links()`. — `Áp dụng khi: ui, logic`
- **Data gate đúng phạm vi:** mỗi section chỉ chờ query nó thật sự cần. Gate cả trang bằng `isLoading` của query chậm nhất (hoặc `A || B`) = LCP bị kéo theo cái chậm nhất. — `Áp dụng khi: ui, logic`
- **Ảnh:** WebP/AVIF; đúng kích thước slot hiển thị (đừng ship ảnh 1600px cho khung 320px); `loading="lazy"` cho below-the-fold; `fetchPriority="high"` + preload **chỉ cho đúng 1** LCP element. — `Áp dụng khi: ui`
- **Preload phải có tác dụng thật:** không preload `data:` URI (bytes đã inline → no-op), không preload thứ không dùng ở first paint, không preload nhiều thứ (tranh băng thông với LCP). — `Áp dụng khi: ui, config`
- **Root chunk sạch:** locale/i18n, icon set, emoji picker, chart/editor lib, ảnh base64 không được nằm trong chunk khởi động. Soi `import.meta.glob(..., { eager: true })`, barrel `export * from`, `export { default as ... }` hàng loạt. — `Áp dụng khi: config, ui`
- **Đừng nhận dev-only config là fix LCP:** `optimizeDeps.*` chỉ tác động dev server (esbuild pre-bundle), production đi Rollup. — `Áp dụng khi: config`

### CLS
- **Mọi `<img>` có `width` + `height` (hoặc `aspect-ratio`)** để reserve chỗ trước khi ảnh về. — `Áp dụng khi: ui`
- **Skeleton phải khớp nội dung thật:** đúng *số section*, *cấu trúc cột* (full/oneHalf/oneThird, nested `<Layout>`) và *chiều cao* — kể cả slot cho banner ảnh full-width. Skeleton lệch = shift đúng lúc swap, tức là đổi 1 CLS lấy 1 CLS khác. — `Áp dụng khi: ui`
- **Không chèn nội dung sau hydration mà không chừa chỗ:** `isMounted &&`, `typeof window !== 'undefined' &&`. Nếu gate chỉ để "SSR-safe" thì kiểm tra component có thật sự chạm `window`/`localStorage` lúc render không — thường là không, và gate chỉ thêm 1 lần reflow. Giữ gate thì phải `min-height` phủ cả 2 trạng thái (soi cả breakpoint: `flex-direction: column` biến 1 hàng thành 1 dòng mới). — `Áp dụng khi: ui`
- **Banner/alert xuất hiện sau khi data về** phải reserve chỗ, hoặc đặt dưới fold. — `Áp dụng khi: ui, logic`
- **i18n không được đổi text sau first paint:** bundle lazy locale + `fallbackLng: 'en'` + `useSuspense: false` ⇒ paint ra tiếng Anh rồi swap sang ngôn ngữ đích ⇒ reflow toàn trang cho mọi merchant không dùng `en`. Ngôn ngữ đang chọn phải có sẵn lúc paint (SSR vào HTML, preload chunk, hoặc await `loadNamespaces` trước khi paint text đã dịch). — `Áp dụng khi: ui, config`
- **Font:** `font-display: swap` + preload font dùng ở first paint; metric fallback lệch nhiều cũng gây shift. — `Áp dụng khi: ui, config`
- **Animation** dùng `transform`/`opacity`, không animate `top/left/height/margin/width`. — `Áp dụng khi: ui`

### Loading state — lớp bug hay đi kèm mọi fix vitals
- **Bỏ/di chuyển một loading gate thì phải soi MỌI flag dẫn xuất từ data đó ở trạng thái `undefined`:** — `Áp dụng khi: logic, ui, auth`
  - *fail-open* (flag → `true` khi chưa có data) ⇒ flash nội dung bị khoá / nav trả phí, rồi bị swap ⇒ vừa lộ tính năng vừa là cú shift lớn nhất trang.
  - *fail-closed* (flag → `false`) ⇒ flash paywall/empty-state cho merchant đã trả tiền.
  - Cách đúng: cho flag **3 trạng thái** (`unknown`) và render skeleton khi `unknown`, đừng để boolean 2 trạng thái tự quyết lúc đang load.
- **Sửa gate ở 1 route thì rà các route cùng pattern** (`useFeatureLock`, `canAccessRoute`, `ProtectedFeature`…) — fix lẻ 1 chỗ để lại y nguyên bug ở các chỗ còn lại. — `Áp dụng khi: logic, ui`

### Bằng chứng trước khi merge
- **Có số đo trước/sau** (Lighthouse mobile throttling, đúng route, ghi vào MR). Không nhận "thấy nhanh hơn". Và phải có **cả LCP và CLS** ở cả 2 mốc — không chỉ chỉ số đang được fix. — `Áp dụng khi: ui, config`
- **Dep mới ⇒ commit lockfile.** CI chạy `yarn install` sẽ xanh trong khi `Dockerfile` dùng `--frozen-lockfile` fail lúc build image. — `Áp dụng khi: config`
- **Ảnh vừa convert (PNG→WebP, resize)** cần QA thị giác thật, không chỉ so byte size. — `Áp dụng khi: ui`

## Theme / storefront
- **Theme App Extension / Liquid**: không dùng ScriptTag đã deprecated; asset scope đúng. — `Áp dụng khi: ui, config`
- **Vitals trên storefront (tae)** khắt khe hơn cms: extension nhúng vào theme khách → JS phải defer/async, không block render, không CSS chèn muộn làm shift PDP; ảnh swatch có kích thước cố định. — `Áp dụng khi: ui, config`
- **Metafields:** dùng definition, tôn trọng giới hạn key/namespace/kích thước. — `Áp dụng khi: db-query, external-call`

## Deploy / config
- **Scopes trong `shopify.app.toml`** khớp scope code thật sự dùng (không thừa quyền). — `Áp dụng khi: config`
- **Webhook subscription** khai báo khớp handler thực tế. — `Áp dụng khi: config, webhook`
