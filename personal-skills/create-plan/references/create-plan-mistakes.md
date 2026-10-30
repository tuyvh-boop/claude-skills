# Create-Plan: Lỗi hay gặp & Cách tránh

## 1. Over-engineering — Thêm scope chưa yêu cầu

**Triệu chứng**: Plan đề xuất field/case/khả năng mà AC không bao giờ mention. User hỏi "cái này để làm gì?" → không rõ.

**Nguyên nhân**: Tư duy "nếu có thêm thì tốt" hoặc sợ thiếu → bổ sung dự phòng.

**Cách tránh**:
- Đọc AC cẩn thận — chỉ implement **đúng** AC, không "bao lâu".
- Nếu thấy thiếu điều gì → ghi vào mục 6 "Open Questions" thay vì bổ sung vào plan.
- Đặt lại câu hỏi: "AC có mention case này không? Nếu không, bỏ."

---

## 2. Không phủ đủ surface

**Triệu chứn**g: Feature phải chạy cả in-app + storefront nhưng plan chỉ cover 1 phía. Sau khi code, phát hiện bị mất feature/data ở phía kia.

**Nguyên nhân**: Không đọc kỹ AC → không biết feature ảnh hưởng đến các surface nào.

**Cách tránh**:
- **BẮT BUỘC check** `shopify-app/surfaces.md` (qua `~/.claude/.te-config-repo` pointer) trước bước 2.
- Liệt kê: "Feature chạy: in-app (✓) + storefront (?) + checkout (?)".
- Nếu không rõ → hỏi trong "Open Questions", không bỏ qua.

---

## 3. Bỏ qua WIP sẵn có trên branch

**Triệu chứng**: Có code rẻi/đã bắt đầu liên quan nhưng plan đề xuất "viết từ đầu". Sau khi code, discover phải revert lại cái đã có.

**Nguyên nhân**: Không check git status / git log trước soạn plan.

**Cách tránh**:
- Bước 1 bắt buộc: `git status`, `git log --oneline -10` để xem có WIP nào không.
- Nếu có → đưa vào plan luôn: "Dựa trên WIP hiện tại: <file> + <commit>".
- Không bao giờ đề xuất viết lại cái sẵn có ngoại trừ khi rõ cần major refactor.

---

## 4. Thiếu input → Soạn plan không đủ cơ sở

**Triệu chứn**g: Plan soạn xong nhưng user/reviewer chỉ ra "chưa rõ design / AC mơ hồ / constraint code không biết".

**Nguyên nhân**: Cố soạn plan mà không có đủ 3 nguồn (Jira/Design/Code).

**Cách tránh**:
- Bước 2 "Thu thập 3 nguồn" → **phải đủ 3 cái mới tiếp tục**. Thiếu cái nào:
  - Thiếu design → ghi "Chưa có design — cần <link Figma>".
  - Thiếu AC rõ ràng → ghi "AC mơ hồ — cần clarify <điểm>".
  - Không rõ constraint code → ghi "Constraint schema/API chưa xác định — cần research".
- **Không bịa**, không soạn plan với giả định mơ hồ.

---

## 5. Constraint code bị lờ

**Triệu chứn**g: Plan không mention giới hạn schema/API/Shopify platform. Sau khi code, discover "không thể làm đúng AC vì constraint X".

**Nguyên nhân**: Code-recon ở bước 2 chỉ "nông" — chưa kiểm tra schema hiện tại, API contract, Shopify limit.

**Cách tránh**:
- Bước 2 code-recon phải **sâu hơn review-plan**:
  - Kiểm tra schema hiện tại: có field/table cần không?
  - Kiểm tra API contract: endpoint nào sẽ bị đổi?
  - Kiểm tra Shopify limit: có giới hạn nào cần biết?
- Phần 4 "Rủi ro & giả định" **BẮT BUỘC** nêu constraint + cách khắc phục.

---

## 6. Tái dùng code sai — Liệt kê component nhưng không đúng match

**Triệu chứn**g: Plan nói "dùng component X" nhưng khi code phát hiện không match pattern (parameter khác, behavior khác, đã deprecated).

**Nguyên nhân**: Nói chung chung "có pattern tương tự" mà không kiểm tra thực tế.

**Cách tránh**:
- Khi liệt kê reuse: **phải có tên + đường dẫn cụ thể + xác nhận parameter/behavior match**.
- Vd: ✗ "dùng component button" → ✓ "dùng `components/ProductButton.tsx` với props `{sku, quantity, onAdd}` — match use case".
- Nếu không chắc → ghi vào "Open Questions" thay vì khẳng định.

---

## Checklist trước khi approve plan

- [ ] AC có được phủ **hết** không? Không over-engineer thêm?
- [ ] Surface (in-app/storefront/checkout) có được cover đủ?
- [ ] Code-recon có đủ 3 nguồn (Jira/Design/Code)?
- [ ] Constraint (schema/API/platform) có được nêu rõ?
- [ ] WIP sẵn có có được mention?
- [ ] Tái dùng code có cụ thể tên + path?
- [ ] Mục "Open Questions" có rõ ràng cần gì từ PM/design?

Nếu fail ≥2 item → **REWIND, sửa input, viết lại plan**.
