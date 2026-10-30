# Phase 7 — Đo lại + guardrail

**[Model: Sonnet — đo/subagent; quyết định ở main]**

**Mục tiêu:** xác nhận thay đổi vòng này **có cải thiện metric in-scope thật không**, và **không làm tụt metric đang tốt**. Đây là chỗ vòng lặp đóng lại — giữ, bỏ, hay lặp tiếp.

## Thứ tự làm

### 1. Đo lại metric IN-SCOPE
- Verify nhanh tại chỗ bằng debug log (Phase 1) trên route tệ nhất. Ghi số trước → sau.
- Lưu ý: số Partner Dashboard cần ~28 ngày/100 calls mới phản ánh; kết luận nhanh dựa trên debug log tại chỗ, và ghi rõ "cần theo dõi dashboard để chốt p75".

### 2. 🛡️ Guardrail — soi metric PROTECTED
- So metric ngoài scope với **mốc baseline (Phase 2)**.
- **Tụt qua ngưỡng** (LCP>2.5s / CLS>0.1 / INP>200ms) **hoặc xấu đi đáng kể** → **BÁO USER NGAY**: nêu metric nào tụt, thay đổi nào gây ra, để user quyết **giữ / bỏ / đánh đổi**. Không tự ý đánh đổi.

### 3. Quyết định vòng lặp
- **Metric in-scope đạt ngưỡng + không regression** → giữ thay đổi, sang **Phase 8**.
- **Chưa đạt nhưng có cải thiện + còn vòng** (`loop.max_iterations`) → giữ thay đổi, **quay Phase 3** (chẩn đoán bottleneck kế tiếp).
- **Không cải thiện / gây regression** → **rollback** thay đổi này (theo mục rollback Phase 5), quay Phase 3 thử hướng khác.
- **Hết `loop.max_iterations` mà chưa đạt** → dừng lại, báo user tình hình + đề xuất (nới target, đổi hướng, hay chấp nhận mức hiện tại).

### 4. (guided) Báo cáo cuối vòng
Bảng: metric in-scope trước→sau, metric protected trước→sau (đạt/tụt), quyết định (giữ/bỏ/lặp). Hỏi user chốt trước khi lặp hoặc sang Phase 8.

## Output của phase
Kết quả một vòng (số + quyết định), và hướng đi kế (lặp / sang review / dừng).

## Common Mistakes
- Chỉ đo metric in-scope, quên guardrail → để metric tốt tụt âm thầm.
- Kết luận "đã nhanh" khi mẫu chưa đủ → dựa số nhiễu.
- Không rollback khi thay đổi vô ích → tích rác, khó truy nhân–quả vòng sau.
- Lặp vô hạn → theo `loop.max_iterations`, hết thì dừng bàn với user.
