# ADF ↔ plaintext

## ADF là gì
Jira Cloud trả nội dung rich text (description, comment) dưới dạng **Atlassian Document
Format** — JSON lồng nhau rất nặng token. Ví dụ 1 comment "hello" là cả một cây
`{type:doc, content:[{type:paragraph, content:[{type:text, text:"hello"}]}]}`.

Đọc thẳng ADF vào context AI **tốn token khủng khiếp** (xem OPCS-104 description: vài KB
JSON cho vài dòng chữ). Vì vậy `jira_client.py` **luôn convert**:

- **Đọc** (`get`, `comments`, `search`): `adf_to_text()` → markdown-ish gọn.
- **Ghi** (`comment`, `edit description`): `text_to_adf()` → ADF tối thiểu hợp lệ.

→ AI **không bao giờ phải tự parse/dựng ADF**. Cần rich text phức tạp hơn mức
`text_to_adf()` lo (bảng, panel, ảnh…) thì dùng `raw` với ADF tự dựng.

## adf_to_text — node đã hỗ trợ
`doc, paragraph, text` (+ marks: `code/strong/em/link`), `hardBreak, heading, bulletList,
orderedList, listItem, codeBlock, blockquote, rule, mention, emoji, inlineCard,
media/mediaInline, table/tableRow/tableHeader/tableCell`.

Node lạ → fallback nối nội dung con (không mất chữ). Gặp node hiển thị sai → bổ sung
nhánh trong `adf_to_text()` (đây là điểm self-improve của convert).

## text_to_adf — quy ước ghi (markdown tối thiểu)
- **Dòng trống = ngắt đoạn**, KHÔNG sinh paragraph rỗng (paragraph rỗng Jira render thành khoảng
  hở to — lỗi comment OPCS-104 24-09-2026). Dòng liền nhau trong 1 đoạn → nối bằng `hardBreak`.
- `- ` / `* ` → bulletList · `1. ` → orderedList · thụt ≥2 space → list con (lồng được bullet trong
  numbered và ngược lại).
- `### ` … → heading, **ép về h3–h4** (đây là comment, không dùng h1/h2).
- `---` (một mình một dòng) → `rule`.
- Inline: `**đậm**`, `*nghiêng*`, `` `code` ``, `[nhãn](https://…)`, URL trần tự thành link.
- Chưa hỗ trợ: bảng, panel, ảnh, codeBlock → dựng ADF tay rồi ghi qua `raw`.

## Nhúng ảnh inline vào comment/description (đã làm thật OPOS-157, 25-09-2026)

ADF không nhận attachment id; node ảnh cần **media file id** (UUID của Atlassian Media):
1. Upload: `attach <KEY> <file> --commit` → attachment id.
2. Lấy UUID: `GET /rest/api/3/attachment/content/<id>` với **allow_redirects=False** → 303,
   `Location: https://api.media.atlassian.com/file/<UUID>/binary?...` (query có media token — KHÔNG in).
3. Chèn node: `{"type":"mediaSingle","attrs":{"layout":"center"},"content":[{"type":"media",
   "attrs":{"type":"file","id":"<UUID>","collection":"","width":W,"height":H}}]}` rồi POST comment
   hoặc PUT `/issue/<KEY>/comment/<ID>` (text_to_adf chưa hiểu cú pháp ảnh — tự ghép node).
`collection` để chuỗi rỗng là Jira tự resolve (collection trong redirect trả None).
