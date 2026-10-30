# Convention — repo cá nhân (profile `personal`)

Nền: `_base.md`. Repo cá nhân → giữ **gọn nhẹ**, không quy trình nặng.

## Commit

- Dùng thẳng `_base.md`. Thực tế hay dùng nhất: `feat:` và `fix:`.
- Ưu tiên **chỉ subject** (không body) cho thay đổi nhỏ. Chỉ thêm body khi WHY thực sự cần giải thích.
- Không mã task, không footer, không trailer.

### Tách commit — KHÔNG

Repo cá nhân: **user bảo push → luôn gộp thành đúng 1 commit**, bất kể diff to nhỏ hay gồm mấy mục đích. Không hỏi tách, không gợi ý tách. Diff gồm nhiều thứ → viết subject ở mức khái quát hơn cho đủ bao (theo `_base.md`).

Ngoại lệ duy nhất: **user chủ động** nói muốn tách.

## Branch

- `feat/<slug>` hoặc `fix/<slug>` từ nhánh chính (`main`/`master`).
- Slug ngắn gọn từ mô tả việc (vd `feat/export-csv`).

## PR/MR

- Theo `_base.md` (WHAT + WHY) nhưng có thể ngắn — repo cá nhân không cần phần trade-off nếu không có gì đáng nói.
- Target nhánh chính của repo.

## Không áp dụng

- Không Jira, không comment ticket, không đổi status — đó là chuyện của profile công ty.
