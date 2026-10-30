# Phase 6 — Implement một thay đổi

**[Model: Opus — main]**

**Mục tiêu:** code **đúng một** thay đổi của vòng này theo plan đã duyệt. Không hơn.

## Kỷ luật
- **Chỉ đúng một thay đổi** trong plan Phase 5. Thấy chỗ khác đáng sửa → **ghi lại để dành vòng sau**, không nhét thêm vào vòng này (nếu gộp, Phase 7 không biết cải thiện/regression đến từ đâu).
- Bám **convention của app** (đọc `CLAUDE.md`/doc repo của app). Code mới giống code cũ, không thêm dependency/abstraction khi pattern sẵn có giải quyết được.
- Chỉ đụng các file đã nêu trong blast radius/plan. Lệch ra ngoài → dừng, báo user.
- Không đụng test/config ngoài phạm vi thay đổi.

## Sau khi code
- Chạy được ở dev (app load bình thường trong Admin), chưa cần kết luận số — việc đo để Phase 7.
- Giữ thay đổi ở dạng dễ rollback (Phase 7 có thể quyết bỏ).

## Output của phase
Diff của một thay đổi, sẵn sàng để đo lại.

## Common Mistakes
- Nhét nhiều fix vào một vòng → không quy được nhân–quả.
- Phá convention app / thêm abstraction thừa.
- Sửa lan ra ngoài blast radius đã duyệt.
