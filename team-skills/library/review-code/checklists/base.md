# Base Checklist (phổ quát — mọi loại code)

> Mỗi mục có `Áp dụng khi:` là surface tag phải nằm trong danh sách bề mặt bị chạm (Bước 2 của SKILL).
> `always` = luôn áp dụng cho bất kỳ diff nào.

## Đúng mục tiêu & tính đúng đắn
- **Khớp ý định:** thay đổi có làm đúng cái mục tiêu đề ra không? Thừa/thiếu gì so với yêu cầu? — `Áp dụng khi: always`
- **Bug logic:** off-by-one, sai điều kiện, null/undefined, sai kiểu, nhánh không xử lý. — `Áp dụng khi: logic`
- **Edge case:** input rỗng/null/cực trị, danh sách rỗng, giá trị âm, unicode. — `Áp dụng khi: logic`
- **Regression:** có phá hành vi/tính năng đang chạy không? — `Áp dụng khi: logic`

## Xử lý lỗi
- **Lỗi được bắt & xử lý đúng tầng**, không nuốt exception im lặng, không lộ stacktrace ra ngoài. — `Áp dụng khi: logic, external-call, api-endpoint`
- **Thất bại của external call** (timeout, 4xx/5xx) có được xử lý/retry hợp lý không? — `Áp dụng khi: external-call`

## Bảo mật (của phần code bị chạm)
- **Injection:** SQL/command/template injection từ input chưa sanitize. — `Áp dụng khi: db-query, api-endpoint`
- **Input validation & authz:** endpoint có validate input và kiểm tra quyền không? — `Áp dụng khi: api-endpoint, auth`
- **Secret:** không hardcode key/token/password; không log dữ liệu nhạy cảm. — `Áp dụng khi: config, external-call, auth`
- **Dữ liệu nhạy cảm** không lọt vào URL/query string/log. — `Áp dụng khi: api-endpoint, external-call`

## Database
- **N+1 query / thiếu index / query trong vòng lặp.** — `Áp dụng khi: db-query`
- **Transaction & tính nhất quán** cho thao tác nhiều bước. — `Áp dụng khi: db-query`
- **Migration:** reversible, không khoá bảng lâu, an toàn với dữ liệu hiện có, tương thích ngược. — `Áp dụng khi: db-schema`

## Concurrency / async
- **Race condition, shared mutable state, thiếu khoá/idempotency** ở job nền/queue. — `Áp dụng khi: async`

## API contract
- **Tương thích ngược** của response/param; versioning khi breaking. — `Áp dụng khi: api-endpoint`

## Test
- **Logic mới/đổi có test tương ứng không?** (chỉ đòi test cho phần code diff động tới, KHÔNG đòi test cho code không đổi.) — `Áp dụng khi: logic`
- **Test có ý nghĩa** (kiểm hành vi, không chỉ chạy cho có coverage). — `Áp dụng khi: test`

## Chất lượng & bảo trì
- **Đặt tên rõ nghĩa:** biến/hàm/class/file/folder nói đúng vai trò; không viết tắt tối nghĩa (`$tmp`, `data2`), không đặt tên lệch với quy ước dùng ngay xung quanh nó. — `Áp dụng khi: logic, ui, structure`
- **Trùng lặp / "sửa 1 chỗ phải đổi 3–4 nơi" (shotgun surgery):** cùng một mẩu logic/hằng số/chuỗi bị copy ra nhiều nơi, hoặc muốn đổi **một** hành vi mà phải sửa rải rác nhiều file rời nhau → tách điểm chung (hàm/const/helper). Chỉ raise khi trùng **thật** (cùng lý do thay đổi); trùng ngẫu nhiên (giống code nhưng lý do đổi khác nhau) thì đừng ép gộp. — `Áp dụng khi: logic, ui`
- **Coupling smell / ranh giới module:** module thò tay vào ruột module khác (reach-through, biết chi tiết nội bộ của nhau), phụ thuộc vòng, tầng dưới biết tầng trên, tham số bool/flag điều khiển luồng, hàm/class ôm quá nhiều việc (God object). Đổi một chỗ kéo theo vỡ chỗ tưởng như không liên quan = dấu hiệu coupling. — `Áp dụng khi: logic, structure`
- **Vị trí file/folder hợp lý (theo setup của repo):** file/folder mới hoặc bị di chuyển có đặt đúng nơi theo **cấu trúc & quy ước của chính repo này** không (helper để chung với helper, route với route, test cạnh thứ nó test…). Đối chiếu `apps/<app>.md` (Kiến trúc / Quy ước bắt buộc); **không có profile thì suy từ các file anh em cùng loại — ĐỪNG áp một chuẩn thư mục từ bên ngoài vào.** — `Áp dụng khi: structure`
- **Độ phức tạp hợp lý, không code chết** (nhánh không bao giờ chạy, biến/import thừa, hàm không ai gọi do diff này tạo ra). — `Áp dụng khi: logic`
- **Không rớt lại debug log / console / biến tạm.** — `Áp dụng khi: always`
- **Dependency mới** có cần thiết & an toàn không? — `Áp dụng khi: config`
