### Nguyên liệu dựng workflow AI — `build-workflow/`

Workflow = chuỗi nhiều skill / bước chạy theo thứ tự (vd "nhận task → plan → code → review"). Cùng cách làm với `build-skills/`:

- Mỗi workflow đang ấp ủ 1 folder `build-workflow/<tên-workflow>/` (không ngày): `README.md` (pain đang phải gọi tay nhiều skill,
  các bước dự kiến) + `plan.md` (sửa đè qua các vòng).
- Ý tưởng chưa bắt đầu → 1 mục trong `build-workflow/_backlog.md`.
- Ship xong → chuyển folder sang `build-workflow/_archive/`, xoá mục backlog.
