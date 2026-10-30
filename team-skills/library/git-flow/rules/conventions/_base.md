# Convention nền chung (_base) — áp cho mọi repo

Đây là nền dùng chung. Profile (`personal.md` / `company/bss.md`) sẽ ghi đè phần khác biệt.

## Commit message

Cấu trúc mặc định (Conventional Commits):

```
<type>: <subject>

<body — tuỳ chọn>

<footer — tuỳ chọn>
```

**Type** (chọn theo bản chất thay đổi):

```
Tính năng mới cho người dùng?              -> feat
Sửa bug (logic sai, crash)?                -> fix
Tái cấu trúc, không đổi hành vi?           -> refactor
Hiệu năng (query, cache)?                  -> perf
Format / đổi tên / khoảng trắng?           -> style
Deps, config, script, tooling?             -> chore
Tài liệu / comment?                        -> docs
Thêm/sửa test?                             -> test
CI/CD?                                     -> ci
Revert commit trước?                       -> revert
```

**Subject:**
- Tiếng Anh, **imperative mood** (`add`, `fix` — không `added`, `fixes`).
- ≤ 72 ký tự, không dấu chấm cuối.
- Không tên file, không chữ mơ hồ ("fix bug", "update code", "minor changes").

**Body (khi cần):** giải thích **WHY** (diff đã cho thấy WHAT), wrap ~72 ký tự.

## Độ phức tạp → format

| Mức | Dấu hiệu | Format |
|---|---|---|
| Simple | 1–4 file, 1 mục đích | Chỉ subject |
| Moderate | 5–10 file, cần ngữ cảnh | Subject + body |
| Complex | 10+ file, kiến trúc, breaking | Subject + body + footer |

## Tách commit

**Mặc định: 1 lần user bảo push = 1 commit.** KHÔNG tự tách, KHÔNG mặc định hỏi tách.

- Subject phải dùng "and"/"also" **không** phải lý do tách — nó chỉ là tín hiệu subject đang liệt kê thay vì tóm gọn. Xử lý bằng cách viết lại subject ở mức khái quát hơn (vd `feat: add git-flow and tech-news-digest skills` → `feat: add two new skills`), không phải cắt commit.
- Chỉ **gợi ý** tách khi profile cho phép **và** chạm ngưỡng của profile đó (xem `personal.md` / `company/bss.md`). Gợi ý là để user quyết:
  > "Diff khá lớn (~X dòng), gồm (1)… (2)… Tách thành 2 commit hay để 1 commit?"
- User không chọn tách → giữ 1 commit, không thuyết phục thêm.

## Đặt tên branch

- Từ nhánh chính mới nhất (`main`/`master`), kebab-case, không khoảng trắng.
- Prefix theo loại: `feat/` (tính năng), `fix/` (bug), `chore/`, `refactor/`, `docs/`...
- Ví dụ: `feat/dark-mode-toggle`, `fix/login-null-crash`.

## Mô tả PR/MR

Trả lời **WHAT + WHY**. Cấu trúc:

```
<Dòng tóm tắt — 1 câu mệnh lệnh, đủ rõ khi đọc riêng>

<Thân>
- Vấn đề đang giải quyết (bối cảnh/bug/yêu cầu)
- Tại sao chọn cách này (nếu có phương án khác)
- Trade-off / hạn chế (nếu có)
- Link tham khảo (issue, doc, benchmark)
```

Dòng tóm tắt dạng mệnh lệnh ("Add dark mode toggle", KHÔNG "Adding…", "This PR…"), cách thân bằng 1 dòng trắng.

## Attribution

Theo mặc định KHÔNG thêm trailer `Co-Authored-By` / "Generated with…" vào commit, trừ khi profile hoặc user yêu cầu.
