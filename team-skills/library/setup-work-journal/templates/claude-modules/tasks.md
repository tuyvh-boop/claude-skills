### Task — `apps/<app>/[<mã-task>]-<brief>/`

- Mỗi app 1 folder, mỗi task 1 folder. Không trộn nhiều task vào một folder.
- Tên folder task: `[<mã-task>]-<brief>` — mã Jira trong ngoặc vuông, `<brief>` 2–5 từ thường, không dấu, gạch nối.
  Không có mã → chỉ `<brief>`. **Không gắn ngày vào folder** (vd `[ABC-123]-fix-checkout-button`).
- `README.md` của task: mục tiêu · kết quả · link tới file quan trọng. Không chép lại nội dung file khác.
- `retro.md` của task (singleton, viết khi đóng task): bài học, gồm **chỗ AI làm sai / làm tốt** (skill / prompt nào, đã sửa
  thế nào) — đọc lại các retro để biết nên chỉnh skill, prompt, cách giao việc ở đâu.
- Ghi chép lẻ không thuộc folder con nào → gốc task, tên `<yy-mm-dd>-<slug>.md`.
- `_local/` trong task: thứ nhạy cảm / thô (dump, log có data khách) — đã gitignore.
- Trước khi tạo folder task mới: tìm theo mã / brief trong `apps/<app>/`, có rồi thì dùng lại.
