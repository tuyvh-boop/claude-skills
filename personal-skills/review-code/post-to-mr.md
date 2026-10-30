# Đăng feedback review lên GitLab MR (cơ chế dùng chung)

> Dùng bởi cả `review-code` (lượt đầu) và `review-code-after-fix` (vòng N+1).
> **Chỉ một bản cơ chế** — đừng chép sang skill khác, hãy trỏ về file này.
> GitLab self-hosted của team: `sbc-gitlab.bsscommerce.com`, đăng qua `glab api` (đã auth sẵn).

## Cửa gate — LUÔN hỏi trước khi post

Đăng comment lên MR là hành động outward-facing → **không tự làm**. Sau khi đã trình kết quả review cho user, hỏi đúng một câu:

> "Có muốn mình comment các điểm này lên MR (dạng thread phải giải quyết) không?"

Chỉ post khi user đồng ý. User bảo "chỉ vài điểm" → post đúng các điểm đó.

## Xác định MR cho mỗi repo

Cần cặp `PROJECT_PATH` (URL-encoded) + `MR_IID` cho mỗi repo có finding. App nhiều repo (cms/tae/api…) → mỗi repo một MR riêng, **finding của repo nào post vào MR repo đó**.

Suy ra theo thứ tự:
1. User đã đưa link/số MR trong hội thoại → dùng luôn.
2. Suy từ branch: `glab api "projects/:enc/merge_requests?source_branch=<branch>&state=opened"` → lấy `iid`.
3. Không suy ra được → **hỏi user** số MR của repo đó. Đừng đoán.

```bash
export GITLAB_HOST=sbc-gitlab.bsscommerce.com
PROJ="sa-division%2Fte-team%2F<...>%2Fcms"   # path repo, encode '/' thành %2F
IID=11
```

## Format body mỗi thread

Đúng như bản đã trình cho user (không viết lại khác đi):
- Dòng đầu: `<emoji severity> <Severity> — <tiêu đề 1 câu>` (🔴 Critical · 🟠 Important · 🔵 Minor).
- Thân: diff làm gì → vì sao sai (truy vết giá trị) → **sửa gọn**. Trích `file:line` cụ thể.
- Một finding = một thread. Không gộp nhiều finding vào một thread.

Soạn body ra file tạm trong scratchpad rồi truyền qua `-F body=@file` (tránh lỗi escape với nội dung nhiều dòng/markdown).

## Tạo thread neo đúng dòng code (line-anchored, resolvable)

Thread có `position` sẽ hiện ngay tại dòng trong tab Changes (như review inline). Discussion trên MR **mặc định resolvable** → có nút Resolve.

```bash
# 1) Lấy sha refs của MR (một lần cho mỗi MR)
read BASE START HEAD < <(glab api "projects/$PROJ/merge_requests/$IID" \
  | jq -r '.diff_refs | "\(.base_sha) \(.start_sha) \(.head_sha)"')

# 2) Tạo thread neo dòng NEW của file (dòng phải thuộc diff của MR)
glab api --method POST "projects/$PROJ/merge_requests/$IID/discussions" \
  -F "body=@<scratchpad>/note.md" \
  -f "position[position_type]=text" \
  -f "position[base_sha]=$BASE" -f "position[start_sha]=$START" -f "position[head_sha]=$HEAD" \
  -f "position[new_path]=app/components/.../X.tsx" \
  -f "position[new_line]=666"
```

- `new_line` = số dòng ở **bản mới** (bên phải diff). Neo được khi dòng đó là dòng **thêm/context nằm trong diff** của MR. Với dòng bị xoá dùng `old_path`+`old_line`.
- **Fallback khi không neo được** (dòng không thuộc diff → GitLab trả 400): tạo **thread MR thường, không `position`** (vẫn resolvable):
  ```bash
  glab api --method POST "projects/$PROJ/merge_requests/$IID/discussions" -F "body=@<scratchpad>/note.md"
  ```
  Trong report ghi rõ finding nào neo được dòng, finding nào phải để thread MR thường.
- Response trả `{"id":"<discussion_id>", "notes":[{"id":<note_id>, "resolvable":true, ...}]}` → lưu `discussion_id` + `note_id` để báo cáo và để vòng sau reply/resolve.

## Reply vào thread cũ (dùng ở review-after-fix)

Thêm note vào đúng thread trước đó, **không tạo thread mới**:
```bash
glab api --method POST "projects/$PROJ/merge_requests/$IID/discussions/<discussion_id>/notes" \
  -F "body=@<scratchpad>/reply.md"
```

## Resolve thread cũ (dùng ở review-after-fix)

Đánh dấu đã giải quyết cả thread:
```bash
glab api --method PUT "projects/$PROJ/merge_requests/$IID/discussions/<discussion_id>?resolved=true"
```
(Chỉ resolve, không cần reply. Muốn vừa xác nhận vừa resolve thì reply một câu ngắn trước rồi PUT resolved=true.)

## Báo cáo lại (BẮT BUỘC sau khi post)

Luôn tổng kết cho user, gom theo repo:
- Mỗi thread đã tạo: `<emoji> <tiêu đề>` — link `…/merge_requests/<iid>#note_<id>` — neo dòng hay thread thường.
- Ở review-after-fix: đã **resolve** mấy thread (liệt kê), **reply** mấy thread (liệt kê), **tạo mới** mấy thread.
- Link MR tổng của mỗi repo.

## Bẫy thường gặp

- **Quên gate** → tự post khi chưa hỏi. Luôn hỏi trước.
- **Post note thường thay vì discussion** → `glab mr note` tạo comment KHÔNG resolvable. Phải dùng endpoint `discussions`.
- **Nhét nhiều dòng markdown qua `-f body=...`** → hỏng escape. Dùng `-F body=@file`.
- **Neo `new_line` vào dòng không thuộc diff** → 400. Bắt lỗi và fallback sang thread MR thường, đừng bỏ luôn finding.
- **Post finding của repo này vào MR repo khác** (app nhiều repo). Map repo→MR trước.
- **Vòng after-fix tạo thread MỚI cho điểm tồn đọng** thay vì reply thread cũ → mất mạch. ✅→resolve, 🟡/❌/⚠️→reply thread cũ, chỉ vấn đề MỚI mới tạo thread mới.
- **Quên báo cáo lại link** sau khi post.
