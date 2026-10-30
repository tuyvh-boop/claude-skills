# Format file annotation

## Cấu trúc chung

File annotation là 1 file Markdown, mỗi bảng là 1 section `###`. Sắp xếp theo
thứ tự bảng được thêm vào (không cần alphabet), có thể nhóm theo domain nếu
project lớn (dùng `##` làm heading nhóm, `###` cho từng bảng bên trong).

```markdown
### <table_name>
- Mục đích: <1 câu mô tả bảng này dùng để làm gì trong nghiệp vụ>
- Cột đáng chú ý: <col1> — <ý nghĩa/giá trị>, <col2> — <ý nghĩa/giá trị>
- Quan hệ: <bảng khác> qua <cột> (<FK thật | FK ngầm — không có constraint>)
```

## Ví dụ đầy đủ

```markdown
### orders
- Mục đích: Bảng đơn hàng chính đang dùng (bảng `orders_legacy` là bảng cũ,
  KHÔNG dùng cho dữ liệu mới từ 2024 trở đi).
- Cột đáng chú ý:
  - status (tinyint) — 0: nháp (chưa submit), 1: chờ xử lý, 2: đã huỷ,
    3: hoàn tất. Lưu ý: 2 KHÔNG phải "đã thanh toán", dễ nhầm với payment_status.
  - payment_status (tinyint) — 0: chưa thanh toán, 1: đã thanh toán,
    2: hoàn tiền.
  - source (varchar) — giá trị tự do do frontend gửi lên, không phải enum cố
    định, không dùng để lọc chính xác.
- Quan hệ:
  - customers qua customer_id (FK thật, có constraint trong DB)
  - order_items qua orders.id = order_items.order_id (FK thật)
  - warehouses qua orders.wh_code = warehouses.code (FK NGẦM — không có
    constraint, xác nhận với @tuyvh 2026-08-27)

### orders_legacy
- Mục đích: Bảng đơn hàng CŨ, chỉ còn dữ liệu lịch sử trước 2024. Không insert
  mới. Dễ nhầm với `orders` vì tên gần giống — LUÔN kiểm tra đang query đúng
  bảng trước khi viết query liên quan "đơn hàng".
- Cột đáng chú ý:
  - status (int) — enum KHÁC với orders.status: 1: mới, 5: xong (không dùng
    chung mapping với bảng orders).
- Quan hệ:
  - customers qua cust_id (khác tên cột so với orders.customer_id)
```

## Hướng dẫn hỏi user khi gặp cột khó đoán

Khi gặp cột kiểu `status`, `type`, `flag`, `state`, hoặc số nguyên có vẻ là
code, hỏi theo mẫu:

> Bảng `<table>` có cột `<col>` (kiểu `<data_type>`). Mình thấy các giá trị
> đang tồn tại là: `<liệt kê giá trị distinct nếu query được>`. Từng giá trị
> nghĩa là gì trong nghiệp vụ?

Nếu không query được giá trị distinct (chưa có MCP/DB), hỏi thẳng:

> Cột `<table>.<col>` dùng để làm gì và các giá trị có thể có nghĩa là gì?

Ghi rõ ngày xác nhận và người xác nhận nếu là thông tin quan trọng dễ thay đổi
(vd enum có thể mở rộng thêm giá trị sau này), để lần sau biết thông tin này
đã được hỏi từ ai, tránh hỏi lại hoặc nghi ngờ sai.

## Khi phát hiện nhiều bảng tên giống nhau

Luôn ghi rõ trong phần "Mục đích" của MỖI bảng liên quan: bảng nào là bảng
"chính" đang dùng, bảng nào là legacy/backup/staging, và tiêu chí phân biệt
(tên bảng, thời điểm dữ liệu, cờ trạng thái...). Đây là nguồn nhầm lẫn phổ biến
nhất khi Claude tự chọn bảng để query.
