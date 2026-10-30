# Phase 3 — Chẩn đoán bottleneck

**[Model: Sonnet — subagent]**

**Mục tiêu:** định vị **vì sao chậm** cho metric in-scope, bằng **số attribution**, không đoán. Đây là bước "truy nguyên nhân gốc" của perf-fix — chọn cách (Phase 4) chỉ đúng khi biết nghẽn ở đâu.

> Bản đồ nguyên nhân → kỹ thuật ở `reference/web-vitals-knowledge.md`. Phase này *chỉ ra* nguyên nhân đang xảy ra ở app thật.

## Cách chẩn đoán theo metric in-scope

Bật `shopify-debug` (Phase 1) để lấy **attribution** — Web Vitals chỉ ra element/tác vụ cụ thể gây chậm.

### Nếu in-scope = LCP
Tách LCP làm 4 phần, xem phần nào chiếm % lớn nhất (attribution cho biết `element`, timing):
- **TTFB** (thường ~40%, thủ phạm số 1 của embedded app): server chậm? token exchange thừa mỗi request? query DB nặng? thiếu HTTP/2 trong iframe?
- **Resource load delay:** ảnh/asset LCP có discoverable sớm không? bị `lazy`?
- **Resource load duration:** kích thước asset LCP, cache header.
- **Element render delay:** JS render-blocking, long task chặn main thread.
→ Ghi ra **phần chiếm % lớn nhất** = nơi cần đánh.

### Nếu in-scope = CLS
Attribution cho biết node nào shift + `sources`. Quy về nhóm:
- Web font (FOIT/FOUT), ảnh không kích thước, content inject động (banner/toast/data async), embed/iframe con, animation đổi layout.
→ Ghi ra **nguồn shift lớn nhất**.

### Nếu in-scope = INP
Attribution cho biết interaction chậm + long task:
- Handler nặng, re-render lớn, long task chặn main thread sau tương tác.
→ Ghi ra **interaction + tác vụ** gây chậm.

## Kỷ luật
- **Chỉ chẩn đoán metric in-scope.** Không đụng nguyên nhân của metric protected.
- Dựa trên **số attribution thật**, không suy từ "thường thì". `reference/` chỉ để đối chiếu tên nguyên nhân.

## Output của phase
- Metric in-scope → **bottleneck cụ thể** (phần/nguồn + số minh chứng + element/route liên quan).
- Xếp hạng nếu có nhiều nguồn: đánh cái tác động lớn nhất trước.

## Common Mistakes
- Đoán nguyên nhân theo lý thuyết mà không xem attribution → sửa nhầm chỗ.
- Chẩn đoán lan sang metric ngoài scope.
- Bỏ qua route tệ nhất (Phase 2) → chẩn đoán trên route không đại diện.
