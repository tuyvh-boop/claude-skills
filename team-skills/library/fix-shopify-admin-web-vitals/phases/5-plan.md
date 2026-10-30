# Phase 5 — Plan fix + gate duyệt

**[Model: Opus — main]**

**Mục tiêu:** biến kỹ thuật đã chọn thành **plan sửa cụ thể theo từng file**, có cách verify, và **được user duyệt** trước khi động vào code.

## Nội dung plan (1 vòng = 1 thay đổi)
1. **Thay đổi này là gì** — kỹ thuật + bottleneck nó nhắm.
2. **Sửa file nào, sửa gì** — liệt kê theo file (bám blast radius Phase 4).
3. **Verify thế nào** — đo lại metric in-scope bằng debug log / dashboard, ngưỡng kỳ vọng.
4. **Guardrail** — metric protected nào cần soi sau khi sửa.
5. **Rollback** — nếu không cải thiện hoặc gây regression thì bỏ thay đổi này thế nào.

## Gate duyệt
- Trình plan cho user, **chờ duyệt** rồi mới sang Phase 6.
- **Bỏ gate** chỉ khi `plan.require_human_approval=false` **hoặc** user uỷ quyền RÕ RÀNG ("tự làm", "khỏi cần duyệt").
- User than gấp ("nhanh đi", "gấp lắm") **KHÔNG** phải uỷ quyền → vẫn giữ gate, chỉ **nén plan** xuống vài dòng (thay đổi + file + cách verify) rồi xin duyệt 1 câu.
- User yêu cầu chỉnh → sửa plan, trình lại.

## Output của phase → artifact
Plan fix 1 vòng (5 mục trên), trạng thái đã-duyệt.

## Common Mistakes
- Code trước khi plan được duyệt → sai flow.
- Bỏ gate vì user than gấp → sai; nén plan chứ không bỏ duyệt.
- Plan gộp nhiều thay đổi → vỡ nguyên tắc một-thay-đổi/vòng.
- Quên mục verify/guardrail → Phase 7 không có gì để đối chiếu.
