# Phase 2 — Baseline + mục tiêu

**[Model: Sonnet — subagent]**

**Mục tiêu:** có **mốc số thật** để (a) biết lệch ngưỡng bao nhiêu, (b) sau này chứng minh cải thiện, (c) **bảo vệ** metric đang tốt. Không có baseline thì mọi "đã nhanh hơn" chỉ là cảm giác.

## Thứ tự làm

### 1. Đo p75 CẢ 3 metric (không chỉ metric in-scope)
- Lấy p75 hiện tại của **LCP, CLS, INP** từ Partner Dashboard (28 ngày). Cần cả metric PROTECTED để làm mốc guardrail.
- Số chưa đủ 100 calls/28 ngày → ghi rõ "chưa đủ mẫu", dùng debug log tại chỗ làm mốc tạm và nói rõ giới hạn.

### 2. Chốt ngưỡng đích cho metric IN-SCOPE
- Lấy từ `config.yml > targets` (mặc định LCP 2.5s / CLS 0.1 / INP 200ms). Ghi khoảng cách hiện tại → đích.

### 3. Ghi mốc PROTECTED
- Ghi giá trị hiện tại của metric ngoài scope + trạng thái (đạt/chưa). Đây là mốc Phase 7 dùng để phát hiện regression.

### 4. Xác định route tệ nhất
- Web Vitals thu theo mọi route. Tìm route/màn hình có metric in-scope tệ nhất (dashboard theo route, hoặc `worst_routes` trong config). **Tập trung fix route đó trước** — cải thiện p75 nhiều nhất.

## Output của phase (baseline snapshot) → artifact
| Metric | p75 hiện tại | Ngưỡng đích | Trạng thái | Vai trò |
|---|---|---|---|---|
| LCP | … | 2.5s | … | in-scope / protected |
| CLS | … | 0.1 | … | in-scope / protected |
| INP | … | 200ms | … | in-scope / protected |

+ Route tệ nhất (tập trung) + ghi chú độ tin cậy mẫu.

## Common Mistakes
- Chỉ đo metric in-scope → mất mốc guardrail, không phát hiện được regression sau này.
- Bỏ qua "đủ mẫu chưa" → kết luận trên số nhiễu.
- Fix dàn trải mọi route → loãng; ưu tiên route tệ nhất.
