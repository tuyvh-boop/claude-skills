# Phase 4 — Chọn cách + blast radius

**[Model: Opus — main]**

**Mục tiêu:** từ bottleneck (Phase 3) → chọn **một kỹ thuật** để thử vòng này, và biết bản sửa **đụng tới đâu** trước khi code.

## Thứ tự làm

### 1. Map bottleneck → kỹ thuật (dùng catalog tự chứa)
- Mở `reference/web-vitals-knowledge.md`, tra mục ứng với metric + bottleneck đã chẩn đoán.
- Chọn kỹ thuật theo **trade-off** (chi phí sửa vs mức cải thiện kỳ vọng vs rủi ro regression). Nhiều lựa chọn → nêu ngắn 2–3 phương án + khuyến nghị, **không** kéo skill discover-solutions vào (skill này tự chứa phần chọn).
- **Chọn đúng MỘT thay đổi** cho vòng này (nguyên tắc một-thay-đổi/vòng). Cái còn lại để dành vòng sau.

### 2. Blast radius — 🔴 BẮT BUỘC CodeGraph
- Dùng `codegraph_explore` (hoặc `codegraph explore`) trên `repo_path` để tìm caller/callee/impact của vùng sắp sửa: đổi cái này **vỡ những đâu**, luồng nào share state.
- **KHÔNG** grep/find/Read để dò quan hệ. `.codegraph/` chưa có → dừng, báo user `codegraph init` (đã check ở Phase 0, nhắc lại nếu lỡ).
- Đọc source 1 file/symbol cụ thể vẫn dùng Read bình thường.
- Ghi ra: điểm tích hợp, contract có thể breaking, luồng regression cần giữ.

### 3. Cân guardrail
- Kỹ thuật này có nguy cơ làm tụt metric protected không? (vd đổi cách load ảnh có thể ảnh hưởng CLS). Nêu rủi ro để Phase 7 soi đúng chỗ.

## Output của phase → artifact
1. **Kỹ thuật chọn** cho vòng này (một thay đổi) + lý do/trade-off.
2. **Blast radius** (CodeGraph): file/hàm ảnh hưởng, regression cần giữ.
3. Rủi ro guardrail dự kiến.

## Common Mistakes
- Chọn nhiều thay đổi gộp một vòng → vỡ nguyên tắc một-thay-đổi.
- Grep thay CodeGraph cho blast radius → cấm.
- Bỏ qua trade-off, chọn kỹ thuật "nghe hay" nhưng rủi ro regression cao.
