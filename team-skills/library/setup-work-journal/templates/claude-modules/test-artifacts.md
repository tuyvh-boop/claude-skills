### Tài liệu test / nghiệm thu trong task

| Loại | Đích trong folder task | Kiểu |
|---|---|---|
| bộ case nghiệm thu (điều kiện, data, case, changelog) | `tests/acceptance-tests.md` | singleton |
| một lượt chạy: report người đọc + kết quả máy đọc | `tests/runs/<yy-mm-dd>-r<N>-<phạm vi>/report.md` + `results.json` | tích luỹ (folder) |
| bằng chứng (ảnh, video, log, dump) | `tests/runs/<...>/evidence/` | **không lên git** |
| cách chạy một case đã đúc (bước, lệnh, bẫy) | `tests/runbooks/<mã-case>.md` | sửa tại chỗ |
| phản hồi test người khác gửi (link nguồn, từng điểm → case) | `tests/feedback/<yy-mm-dd>-<nguồn>-r<N>.md` | tích luỹ |
| file đính kèm của phản hồi (ảnh tải về) | `tests/feedback/<yy-mm-dd>-<nguồn>-r<N>/` | **không lên git** |
| ghi chú data test (store, product dùng để test) | `tests/test-data.md` | singleton |

- `r<N>`: đếm tiếp trong `tests/runs/` của task (lượt đầu `r1`). `<phạm vi>`: `full` · `after-fix` · `p<n>` (một phase) ·
  tên nhóm case, chữ thường gạch nối. Lượt cũ không sửa.
- Mỗi lượt chỉ track `report.md` + `results.json`. `evidence/` và folder đính kèm của `feedback/` đã gitignore: ảnh và log dễ dính
  token, cookie, email khách mà scanner không đọc được. Cần giữ bằng chứng lâu → mô tả bằng chữ trong `report.md`, ảnh gửi qua Jira.
- Data test chỉ dùng store dev, không ghi domain / thông tin shop khách thật.
