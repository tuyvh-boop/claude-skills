# Phase 0 — Routing & scope

**[Model: Haiku — subagent]**

**Mục tiêu:** biết **fix metric nào**, cho **app nào**, code ở **đâu** — trước khi làm gì.

## Thứ tự làm

### 1. Đọc `config.yml`
- Lấy `run_mode`, `targets`, `loop`, `plan`, và `apps` registry.
- Chưa có `config.yml` → tạo từ `config.example.yml`, báo user điền registry app rồi mới đi tiếp.

### 2. Xác định metric IN-SCOPE (từ nguyên văn lệnh user)
- User nói "fix **lcp**" → in-scope = `[lcp]`. "fix lcp và cls" → `[lcp, cls]`. Nói chung chung "fix web vitals / fix hết" → cả 3.
- **Chỉ metric in-scope mới được đi sửa.** Các metric còn lại chuyển sang danh sách **PROTECTED** (chỉ bảo vệ, không sửa — xem guardrail Phase 7).
- Ghi rõ ra: `in_scope = [...]`, `protected = [...]`.

### 3. Route app X
- Lấy tên app từ lệnh ("... cho app **X**"). Tra `apps.X` trong registry → `repo_path`, `stack`, `shopify_app_id`, `admin_entry`, `worst_routes`.
- **App không có trong registry** → hỏi user (1 lần): repo path ở đâu, stack gì. Gợi ý user thêm vào `config.yml` để lần sau khỏi hỏi. **Đừng bịa** path/stack.
- Lệnh không nêu app rõ → hỏi đúng 1 câu "app nào".

### 4. Kiểm tra tiền đề CodeGraph
- `repo_path` phải có `.codegraph/`. Kiểm tra tồn tại thư mục `.codegraph/` ở repo root.
- **Chưa có** → báo user: blast radius của skill này bắt buộc CodeGraph; chạy `codegraph init` trong repo đó trước rồi quay lại. **Không** fallback grep, **không** tự init hộ.

## Output của phase

Gọn, chuyển sang Phase 1:
1. `in_scope` / `protected` metric.
2. App: `repo_path`, `stack`, `shopify_app_id`, `admin_entry`, `worst_routes`.
3. Xác nhận `.codegraph/` sẵn sàng.
4. `run_mode` (để biết có chạy guided không).

## Common Mistakes
- Suy diễn metric ngoài nguyên văn lệnh → fix lan. Chỉ lấy metric user nói.
- Bịa repo path/stack khi app chưa có registry → sai repo. Hỏi user.
- Bỏ qua check `.codegraph/` → tới Phase 4 mới kẹt. Check ngay Phase 0.
