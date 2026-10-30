# Phase 1 — Chuẩn bị & setup đo

**[Model: Sonnet — subagent cho phần đọc/dựng; xác nhận ở main]**

**Mục tiêu:** làm cho app **đo được Web Vitals thật** trước khi fix. Không đo được thì baseline/chẩn đoán/verify đều vô nghĩa — đây là lý do phase này đứng trước mọi bước sửa.

> Toàn bộ cơ chế đo chi tiết (code, meta flag, nơi đọc số, caveat iframe) ở `reference/measurement.md`. Phase này là các bước *áp dụng* cơ chế đó vào app.

## Thứ tự làm

### 1. Kiểm tra hiện trạng instrument
- Mở `admin_entry` (document nhúng App Bridge). Xác định app đã:
  - Nhúng **App Bridge script mới** (`app-bridge.js`) ở `<head>` **mọi** document chưa?
  - Có đăng ký `shopify.webVitals.onReport(...)` chưa?
- Đây là **điều kiện để Shopify thu số** về Partner Dashboard. Thiếu → phải thêm.

### 2. (Nếu thiếu) Thêm instrument — SIDE-EFFECT vào code app → CONFIRM trước
- Trình user diff dự kiến: thêm script App Bridge + callback `onReport` đẩy về endpoint nội bộ (hoặc chỉ để Shopify thu), theo `reference/measurement.md`.
- **Chờ user oke** rồi mới sửa. Không tự ý đụng code app.
- App Bridge phải load **đồng bộ** (không `defer`/`async`).

### 3. Bật debug tại chỗ để verify
- Thêm `<meta name="shopify-debug" content="web-vitals" />` (dev/staging).
- Chạy app trong Shopify Admin, mở console: phải thấy log Web Vitals real-time + send-time. Đây là bằng chứng "đo được".

### 4. Xác định nguồn số chính chủ
- Partner Dashboard → app → mục performance = số p75/28 ngày Shopify dùng để chấm. Ghi lại chỗ đọc.
- Nhắc user: số dashboard cần ~28 ngày & tối thiểu 100 calls/metric mới ổn định; trong lúc dev dùng **debug log tại chỗ** để verify nhanh từng thay đổi.

## Output của phase
1. App đã đo được Web Vitals (đã instrument + verify bằng debug log).
2. Đường đọc số: Partner Dashboard (số chấm) + debug console (verify nhanh).
3. Diff instrument (nếu có) đã được user duyệt.

## Common Mistakes
- Nhảy vào fix khi app chưa instrument → không có số để biết đã cải thiện chưa.
- Sửa code app không confirm → vi phạm "side-effect phải xin phép".
- `defer`/`async` App Bridge → hỏng thu số.
- Tin số Lighthouse/PSI trong iframe → sai; số chính chủ ở Partner Dashboard.
