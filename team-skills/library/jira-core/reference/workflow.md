# Quy trình status & assignee của task trên Jira — chuẩn team

Chuẩn hoá **khi nào đổi status nào** và **assign cho ai**, dùng chung cho cả team (PM/BA, leader,
dev, dev lead, tester). AI đọc file này trước khi `transition`/`assign` để đi đúng luồng. Comment
kèm theo xem [`comment-templates.md`](comment-templates.md).

## Luồng status

```
to do → research → ready for dev → in development → in code review → ready for test
      → testing → in code review (review lần cuối) → go live → done
```

- **`to do`, `research`** là giai đoạn **người chủ động pick & assign tay** (PM/BA/leader).
- Từ **`ready for dev`** trở đi đi theo luồng dev → review → test → go live ở bảng dưới.
- **Sau `testing` quay lại `in code review`:** test xong, dev lead **review lần cuối trước go live**;
  review xong mới chuyển sang **`go live`** (không nhảy thẳng `testing → go live`).
- Mọi status đều bật **"Allow all statuses to transition"** — có thể nhảy về bất kỳ status nào khi
  cần, nhưng luồng chuẩn đi theo các mũi tên trên.

## Bảng chuyển trạng thái

| Status | Khi nào chuyển vào | Người chuyển → Assignee mới | Comment kèm |
|---|---|---|---|
| **to do** | Task vừa được tạo (*Create*) | PM/BA (tay) → người phân tích | — |
| **research** | Đang phân tích requirement, lên design, dự trù resource | PM/BA/leader (tay) → người research | — |
| **ready for dev** | Research xong, đủ điều kiện cho dev code | Leader → **dev** (leader chọn) | — |
| **in development** | Dev bắt đầu code | Dev → dev (giữ) | — |
| **in code review** | Done dev + đã tạo PR/comment merge request gửi review | Dev → **dev lead** (điều phối người review) | **TH1** |
| **ready for test** | Review & fix xong → merge vào testsite | Dev → **tester** | **TH3** "đã merge test" |
| **testing** | Tester chuẩn bị xong testcase & bắt đầu test | Tester → tester | — |
| **in code review** *(lần cuối)* | Test sạch bug → dev lead review lần cuối trước go live | Tester → **dev lead** | — |
| **go live** | Review lần cuối xong → golive | Dev lead → **tester** (retest trên production) | Comment golive (tự do) |
| **done** | Tester retest trên production + làm document xong | Tester → đóng task | — |

## Vòng lặp & ngoại lệ

- **Sửa review (giữ `in code review`):** mỗi round dev sửa xong góp ý → comment **TH2 "đã fix"** +
  assign lại cho người review / dev lead. Status **vẫn `in code review`** đến khi review OK.
- **Test ra bug (giữ `testing`):** tester thấy bug → assign lại **dev** để fix, **status vẫn
  `testing`**. Dev fix xong round đó → comment + assign lại **tester**. Lặp đến khi sạch bug.
- **Review lần cuối trước go live (`testing → in code review`):** test sạch bug → chuyển về
  **`in code review`** + assign **dev lead** để review lần cuối. Review xong, dev lead mới chuyển
  sang **`go live`**. **Không** nhảy thẳng `testing → go live`.
- **Chuẩn bị testcase sớm:** tester có thể soạn testcase ngay từ khi task ở **`ready for dev`**,
  không cần đợi tới `testing`.

## Comment đi kèm khi đổi status

Khi chuyển các mốc quan trọng nên kèm comment để mọi người nắm (mẫu ở
[`comment-templates.md`](comment-templates.md)):

- **→ in code review:** mẫu **TH1** (mô tả + link MR các repo).
- **trong in code review (sửa review):** mẫu **TH2 "đã fix"**.
- **→ ready for test:** mẫu **TH3 "đã merge test"**.
- **→ go live:** comment tự do (vd "đã golive lên production", lưu ý nếu có).

## Field Change Size

Field có mặt trên mọi task Scrum. Người **lên requirement (BA, CS)** chọn khi tạo/phân tích task —
**không phải dev hay tester chọn**. Mỗi role đọc size đó để biết mức độ nỗ lực và quy trình cần làm.
(Field id: xem `config.yml > fields.change_size`.)

> **Quy tắc "trao đổi 3 bên":** BA/CS, QA, Dev (và Dev lead nếu Major) phải trao đổi **cùng lúc
> trong cùng 1 nhóm chat hoặc họp** — không trao đổi riêng lẻ từng người, tránh mỗi người hiểu một
> kiểu. Sau khi 3 bên đã confirm → **bắt buộc update lại requirement và tài liệu liên quan** để phản
> ánh nội dung đã thống nhất.

### Với BA / CS (người lên requirement)

**Mục đích:** xác định nỗ lực verify và độ chi tiết requirement.

| Size | Khi nào dùng | Yêu cầu |
|---|---|---|
| **Tiny** | Task nhỏ, rõ ràng, độc lập, không ảnh hưởng feature khác | Viết description ngắn → chuyển dev lead assign dev code luôn |
| **Medium** | Feature mức trung | Có spec + **trao đổi 3 bên** (BA, QA, Dev) đảm bảo cùng hiểu một ý tưởng |
| **Major** | Feature lớn, ảnh hưởng quan trọng, hay phát sinh change requirement | Spec rõ ràng đầy đủ (cover edgecase quan trọng) + **trao đổi kỹ 3 bên** (BA, QA, Dev, Dev lead) để đảm bảo khả thi cả QA lẫn tech + **update tài liệu đầy đủ** |

### Với QA / Tester

**Mục đích:** xác định nỗ lực và độ chi tiết acceptance checklist (AC) và testcase.

| Size | Quy trình |
|---|---|
| **Tiny** | Đọc requirement → lên AC & testcase luôn, không cần quá chi tiết |
| **Medium** | **Trao đổi 3 bên** (BA, QA, Dev — không gặp riêng từng người) → lên AC đầy đủ → viết testcase |
| **Major** | **Trao đổi kỹ AC với BA, Dev** → AC chi tiết tất cả các trường hợp quan trọng & edgecase, phải được định nghĩa rõ trước khi dev vào code. **Chỉ lên AC (không viết testcase ngay** vì requirement hay thay đổi trong quá trình dev); testcase viết khi task đạt **Ready for Test** |

### Với Dev

**Mục đích:** xác định nỗ lực research giải pháp và mức độ cần confirm trước khi code.

| Size | Quy trình |
|---|---|
| **Tiny** | Code luôn |
| **Medium** | **Trao đổi 3 bên** (BA, QA, Dev — không gặp riêng) để hiểu rõ requirement trước khi code |
| **Major** | Giống Medium + **bắt buộc research giải pháp** → gửi Dev lead review & brainstorm kỹ trước khi code |
