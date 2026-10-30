# Reference — Cơ chế đo Web Vitals cho embedded admin app

Nguồn: Shopify official (admin-installation-oauth performance; Web Vitals API; Built for Shopify requirements) + web.dev.

## Nguyên tắc nền (đọc trước)

- Embedded app chạy **trong iframe** của Shopify Admin. **Lighthouse / PageSpeed Insights KHÔNG đo đúng** app trong iframe — Shopify nói thẳng. Đừng dùng chúng để chấm.
- Shopify **tự thu Web Vitals qua runtime riêng** mỗi lần merchant mở app (mọi route), lưu về **Partner Dashboard**. Đây là **số chính chủ** quyết định badge.
- Điều kiện thu số: app phải nhúng **App Bridge script mới nhất** ở `<head>` **mọi** document. Thiếu → không có data → không đạt Built for Shopify.

## Ngưỡng (Built for Shopify — admin performance)

p75, cửa sổ 28 ngày, tối thiểu 100 calls/metric mới được assess.

| Metric | Ngưỡng | Đơn vị |
|---|---|---|
| LCP | ≤ 2.5s | ms |
| CLS | ≤ 0.1 | — (không đơn vị) |
| INP | ≤ 200ms | ms |

## Instrument — nhúng App Bridge + Web Vitals API

```html
<head>
  <meta name="shopify-api-key" content="%SHOPIFY_API_KEY%" />
  <script src="https://cdn.shopify.com/shopifycloud/app-bridge.js"></script>
  <script>
    shopify.webVitals.onReport((metrics) => {
      // metrics: { appId, shopId, userId, appLoadId, metrics: [{ id, name, value, country }] }
      navigator.sendBeacon('https://your-server/web-vitals', JSON.stringify(metrics));
    });
  </script>
  <!-- App Bridge phải load ĐỒNG BỘ — KHÔNG defer/async -->
</head>
```

- `name` ∈ `LCP | FCP | CLS | INP | TTFB | FID`; `value` ms (trừ CLS không đơn vị); kèm `country` để phân tích theo vùng.
- `shopify.webVitals.onReport(null)` để hủy đăng ký.
- `sendBeacon` để đẩy về endpoint nội bộ mà không chặn unload — dùng khi muốn tự phân tích/segment. Chỉ cần Shopify thu (Partner Dashboard) thì chỉ nhúng App Bridge script là đủ.

## Debug tại chỗ — verify nhanh

```html
<meta name="shopify-debug" content="web-vitals" />
```

- Cho 2 loại log ở console: **real-time** từ Web Vitals (kèm **attribution** — chỉ ra element/tác vụ gây chậm, dùng ở Phase 3) và **send-time** (giá trị cuối Shopify ghi nhận).
- Chỉ bật ở dev/staging.

## Đọc số ở đâu

- **Partner Dashboard → app → performance:** p75 / 28 ngày — số Shopify dùng để chấm. Ưu tiên hơn mọi tool ngoài.
- **Console (debug):** verify nhanh từng thay đổi trong lúc dev (không phải chờ 28 ngày).
- Tool ngoài đo mỗi lần navigate → hay lệch với dashboard; đừng lấy làm chuẩn.

## Caveat hay quên

- Số dashboard cần **~28 ngày + ≥100 calls/metric** mới ổn định. Fix xong không thấy dashboard đổi ngay là bình thường — verify tức thời bằng debug log.
- App Bridge `defer`/`async` → hỏng thu số.
- Sửa `admin_entry` để nhúng script là **side-effect vào code app** → confirm user trước.
