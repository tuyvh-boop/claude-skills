# Rule — Báo cáo kết quả (BẮT BUỘC ở step cuối mọi operation)

Mọi operation của git-flow (commit+push, tạo branch, tạo MR/PR) **phải kết thúc bằng một block tóm tắt có link bấm được**, để user mở ra check ngay mà không phải tự đi tìm.

Không được thay block này bằng câu chữ chung chung kiểu "đã push xong nhé".

---

## Lấy link — dùng script, KHÔNG tự bịa URL

```bash
sh <skill>/scripts/git-links.sh            # link cho HEAD
sh <skill>/scripts/git-links.sh <sha>...   # link cho các commit chỉ định
```

Script tự đọc `origin`, chuẩn hoá SSH→HTTPS, và in sẵn: repo URL, branch URL, commit URL từng sha, compare/tạo-PR URL.

- Chạy script **sau khi** push/tạo MR xong.
- `host: unknown` hoặc không có `origin` → **không đoán URL**. In sha/branch dạng text và nói rõ "remote không nhận diện được host nên không có link".
- Link MR/PR vừa tạo: lấy **URL do `gh`/`glab` in ra**, không tự ghép.

---

## Format — Commit + Push

```markdown
Đã push lên **`<branch>`** → `origin/<branch>`

**Commit** (N):
- [`abc1234`](<commit-url>) — feat: add export csv
- [`def5678`](<commit-url>) — fix: handle empty rows

[Xem branch](<branch-url>) · [So sánh với `<base>` / tạo PR](<compare-url>)
```

- Liệt kê **mọi commit vừa tạo trong lần chạy này** (không phải toàn bộ lịch sử), mỗi dòng: sha ngắn (link) + subject.
- Ghi rõ branch đích và remote đã push tới.
- Có pull/merge xen giữa (non-fast-forward) → thêm 1 dòng nói đã merge từ `origin/<branch>` trước khi push.
- Nếu user KHÔNG cho push (chỉ commit) → bỏ dòng push, ghi "chưa push" + lệnh push gợi ý.

## Format — Tạo MR/PR

```markdown
Đã tạo <MR|PR>: [<title>](<mr-url>)

- **Source → target:** `<branch>` → `<base>`
- **Commit** (N): [`abc1234`](<url>) — subject · [`def5678`](<url>) — subject
- **Thay đổi:** N file, +X/−Y dòng

[Mở <MR|PR>](<mr-url>) · [Xem branch](<branch-url>)
```

- `<mr-url>` **luôn** là URL thật do CLI trả về.
- Không có `gh`/`glab` → báo "đã push, chưa tạo được <MR|PR> vì thiếu CLI" + đưa link tạo thủ công (compare URL) để user bấm.

## Format — Tạo branch

```markdown
Đã tạo branch **`<name>`** từ `origin/<base>` (đang đứng ở branch này)

Chưa có trên remote — push lần đầu: `git push -u origin <name>`
```

- Đã push branch lên remote → thay dòng cuối bằng: `[Xem branch](<branch-url>) · [Tạo PR](<compare-url>)`.

---

## Nguyên tắc chung

- **Link phải là markdown link** (`[text](url)`) để bấm được, không dán URL trần.
- Chỉ báo cáo **việc đã thực sự xảy ra** — chưa push thì không được viết "đã push".
- Sai sót (push fail, MR tạo lỗi) → nêu thẳng ở đầu block, kèm bước tiếp theo.
