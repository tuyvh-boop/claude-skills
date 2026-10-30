# Phase 8 — Review + cất nhật ký

**[Model: review-code lo subagent; fix & tổng hợp ở main]**

**Mục tiêu:** đảm bảo các thay đổi đã giữ lại **đúng, sạch, không kéo nợ**, rồi lưu lại quá trình để lần sau tra được.

## 1. Review diff — gọi skill `review-code`
- Gộp toàn bộ diff đã giữ qua các vòng, **gọi skill `review-code`** trên diff đó.
- Fix theo comment review (flow receiving-review), lặp tới khi sạch.
- Perf-fix hay đụng cache/async/query → review kỹ đúng-đắn, không chỉ tốc độ.

> Nhắc dependency: `review-code` có sẵn ở `skills/library/review-code` của ai-hub. Máy chưa cài → review thủ công theo checklist đúng-đắn + regression, và ghi chú lại.

## 2. Tổng hợp kết quả run
Bảng chốt: metric in-scope trước→sau (mốc baseline → cuối), metric protected (giữ nguyên/tụt/đã xử lý), các thay đổi đã giữ (kèm file), thay đổi đã bỏ + lý do.

## Bước cuối — Lưu output (tuỳ chọn)
Output của cả run (baseline, chẩn đoán, kỹ thuật đã chọn, plan, kết quả đo trước→sau) là **artifact của một task cụ thể** → mặc định trình ra chat, rồi **hỏi user có muốn lưu thành `.md` không** (và lưu ở đâu). Máy có skill lưu nhật ký làm việc riêng → dùng skill đó thay vì tự gõ path. User nói khỏi lưu → thôi.

> Lưu ý: đây chỉ lưu **ghi chép quá trình**. Thay đổi code nằm ở repo app, đi qua flow git bình thường — skill này KHÔNG commit hộ.

## Common Mistakes
- Viết reviewer riêng thay vì gọi `review-code`.
- Review qua loa vì "chỉ là perf" → perf-fix vẫn đổi logic (cache/async), phải soi đúng-đắn.
- Tự nêu tên skill lưu-nhật-ký thay vì để intent tự kích hoạt.
- Tự commit code app hộ user.
