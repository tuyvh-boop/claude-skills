# Reference — Kiến thức LCP / CLS / INP + catalog kỹ thuật fix

Dùng ở Phase 3 (đối chiếu tên nguyên nhân) và Phase 4 (chọn kỹ thuật). Bối cảnh: Shopify embedded admin app (App Bridge/iframe, thường React/Polaris).

Nguồn: web.dev (Optimize LCP / Optimize CLS — Google/Chrome team) + Shopify official + case study cộng đồng. Xem mục Nguồn cuối file.

---

## LCP — Largest Contentful Paint (đích ≤ 2.5s)

LCP = TTFB + resource load delay + resource load duration + element render delay. Chẩn đoán (Phase 3) xem phần nào chiếm % lớn nhất rồi chọn kỹ thuật tương ứng:

| Bottleneck | % điển hình | Kỹ thuật fix (embedded/React) |
|---|---|---|
| **TTFB** | ~40% (thủ phạm #1 embedded app) | Tối ưu backend: query DB chậm; **bỏ token exchange thừa mỗi request** (chỉ exchange khi chưa có token hợp lệ → tiết kiệm 300–400ms); đẩy việc phụ (email/log) sang background worker. Bật **HTTP/2** để tránh SSL handshake lặp trong iframe (200–300ms) |
| **Resource load delay** | <10% | Ảnh/asset LCP discoverable sớm trong HTML; `fetchpriority="high"` cho ảnh LCP; **không** `loading="lazy"` cho element LCP |
| **Resource load duration** | ~40% | Ảnh WebP/AVIF; cache header mạnh (`Cache-Control: max-age=..., immutable` + content hash trong tên file); tách bundle `main.js` / `vendors.js` để update không phải tải lại toàn bộ |
| **Element render delay** | <10% | `defer` cho JS (trừ App Bridge phải synchronous); giảm CSS render-blocking; chia nhỏ long task; cân nhắc SSR/streaming (React Suspense) để không chờ JS chạy xong mới thấy nội dung |
| **Perceived / skeleton** | — | Trả sẵn DOM có **Polaris skeleton** từ HTML đầu → cải thiện cảm nhận + hỗ trợ FCP/LCP. ⚠️ Bug đã biết App Bridge 4.x: DOM SSR có thể bị giữ ẩn tới khi JS load xong (khác 3.x) — verify trên version đang dùng |

---

## CLS — Cumulative Layout Shift (đích ≤ 0.1)

| Nguồn shift | Kỹ thuật fix |
|---|---|
| **Web font** (FOIT/FOUT) — phổ biến nhất | `font-display: optional`, khai báo fallback font, preload font critical |
| **Ảnh không kích thước** | Luôn set `width`/`height` (hoặc `aspect-ratio`) trên mọi `<img>` — browser reserve chỗ trước |
| **Content inject động** (banner, toast, data async) | Container fixed-size / `min-height` reserve sẵn; đặt phần load muộn dưới viewport; ưu tiên trigger bằng user action (shift trong 500ms sau input **không** bị tính CLS) |
| **Embed / iframe con** | Reserve chỗ bằng `min-height` / `aspect-ratio` |
| **Animation** | Dùng `transform` thay vì đổi `top/left/width/height` |
| **Skeleton → nội dung thật** | Skeleton phải **cùng kích thước** nội dung thay thế, tránh nhảy khi swap |

---

## INP — Interaction to Next Paint (đích ≤ 200ms)

| Nguồn chậm | Kỹ thuật fix |
|---|---|
| Handler nặng chặn main thread | Chia nhỏ tác vụ, `yield`/`scheduler.postTask`, debounce/throttle input |
| Re-render lớn sau tương tác | Memo hoá, thu hẹp vùng re-render, virtualize list dài |
| Long task từ third-party/JS lớn | Defer/lazy phần không cần cho tương tác đầu; code-split |

---

## Guardrail — đánh đổi hay gặp giữa các metric

Khi fix một metric, coi chừng làm tụt metric khác (Phase 7 phải soi):

- Preload/`fetchpriority` nhiều ảnh cho LCP → có thể tranh băng thông, ảnh hưởng resource khác.
- Đổi cách load ảnh/lazy cho LCP → có thể sinh CLS nếu bỏ kích thước reserve.
- Skeleton/SSR cho LCP → nếu skeleton lệch size nội dung thật → tăng CLS.
- Code-split cho INP/LCP → chunk mới có thể thêm request, xem lại render delay.

---

## Nguồn & độ uy tín

- **Official Shopify (cao nhất — bên chấm điểm):** [admin/oauth performance](https://shopify.dev/docs/apps/build/performance/admin-installation-oauth), [Built for Shopify requirements](https://shopify.dev/docs/apps/launch/built-for-shopify/requirements), [Web Vitals API](https://shopify.dev/docs/api/app-home/apis/device-and-platform-integration/web-vitals-api).
- **web.dev (cao — Google/Chrome team):** [Optimize LCP](https://web.dev/articles/optimize-lcp), [Optimize CLS](https://web.dev/articles/optimize-cls).
- **Cộng đồng (trung bình — verify theo version App Bridge):** [Daniel Beck — Improving LCP on your Shopify App](https://danielbeck.io/posts/improving-last-contentful-paint-shopify-app/) (case study TTFB/token exchange/HTTP/2/bundle split); [Shopify community — LCP<2.5s với Polaris](https://community.shopify.com/t/how-to-achieve-lcp-2-5s-in-a-shopify-app-built-with-polaris/348468); [digismoothie/shopify-admin-web-vitals-logger](https://github.com/digismoothie/shopify-admin-web-vitals-logger).

> ⚠️ Đa số bài "Shopify Core Web Vitals 2026" trên search nói về **storefront/theme** (Lighthouse/CrUX), **không áp dụng** cho embedded app trong iframe.
