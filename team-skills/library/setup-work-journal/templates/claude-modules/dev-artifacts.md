### Tài liệu dev trong task

| Loại | Đích trong folder task | Kiểu |
|---|---|---|
| bối cảnh, vùng ảnh hưởng | `context/<yy-mm-dd>-<slug>.md` | tích luỹ |
| điều tra, findings | `research/<yy-mm-dd>-<slug>.md` | tích luỹ |
| chẩn đoán lỗi: bằng chứng, giả thuyết, nguyên nhân gốc | `diagnosis/<yy-mm-dd>-<slug>.md` | tích luỹ |
| so sánh các hướng giải pháp | `solutions/<yy-mm-dd>-<slug>.md` | tích luỹ |
| chốt phương án + lý do | `decisions/<yy-mm-dd>-<slug>.md` | tích luỹ |
| thiết kế DB đã chốt (bảng, cột, index, migration + lý do) | `database-structure-design.md` | singleton |
| plan tổng các giai đoạn, chưa chi tiết file / hàm | `plan-overview.md` | singleton |
| plan chi tiết để code từng phase + tiến độ (phase nào xong, MR) | `plan-implementation.md` | singleton |
| sổ lỗi / góp ý trong lúc code, theo phase — đọc trước khi code phase sau | `implement-retro.md` | singleton |
| giải thích code đã viết xong một phase | `explanations/<yy-mm-dd>-phase-<phase>-<slug>.md` | 1 phase 1 file |
| review code vòng N (kể cả review sau khi fix) | `review-code/<yy-mm-dd>-<slug>-rN.md` | tích luỹ |
| plan + tài liệu một script bulk update / backfill | `scripts/<yy-mm-dd>-<slug>.md` | 1 script 1 file |
| prototype UI (HTML/JS thuần, không data khách) thay bản thiết kế | `ui-prototype/` | folder |
| checklist golive | `golive.md` | singleton |

Tích luỹ = mỗi lần một file mới có ngày. Singleton = mỗi task 1 file tên cố định, sửa tại chỗ.
`1 phase 1 file` / `1 script 1 file`: làm lại thì sửa chính file đó, không đẻ file theo ngày mới.
