---
name: dev-journal-save
description: Lưu và tổ chức nhật ký phát triển (dev journal) — plan/quyết định kỹ thuật, retro sau khi sửa lỗi, tóm tắt thay đổi code quan trọng — vào kho dev-journal/ trung tâm, phân loại theo app/project. Chủ động đề xuất dùng skill này ngay sau khi: sửa xong một lỗi khó hoặc tốn nhiều lần thử, chọn giữa từ 2 phương án kỹ thuật trở lên, hoàn thành một plan hoặc tính năng, hoặc phát hiện một "gotcha" không hiển nhiên trong codebase — kể cả khi người dùng không hề nhắc tới từ "dev journal", "retro", hay "lưu lại". Cũng dùng khi người dùng nói những câu như "ghi lại bài học này", "note lỗi này để lần sau tránh", "lưu vào dev journal", "lưu lại quyết định này".
---

# Dev Journal Save

## Vì sao skill này tồn tại

AI coding agent (kể cả Claude) hay lặp lại đúng lỗi cũ vì mỗi phiên làm việc
gần như quên sạch những gì đã học ở phiên trước, và trong một tổ chức có
nhiều app, bài học rút ra ở app này cũng không tự động tới được app khác.
Skill này biến những khoảnh khắc "à, hoá ra là vậy" trong lúc code thành một
ghi chú ngắn, có cấu trúc, nằm đúng chỗ để phiên sau — hoặc một app khác —
đọc lại được, thay vì để nó trôi mất khi cửa sổ ngữ cảnh đóng lại.

## Khi nào nên chủ động đề xuất lưu

Ngay sau khi một trong các việc sau vừa xảy ra trong phiên, hỏi ngắn gọn
người dùng có muốn lưu lại không — đừng tự ý ghi file mà không hỏi trước,
vì không phải project nào người dùng cũng muốn dùng dev-journal:

- Vừa sửa xong một bug mà phải thử từ 2 cách trở lên mới ra được
- Vừa chọn giữa ít nhất 2 phương án kỹ thuật khác nhau
- Vừa hoàn thành một plan hoặc một tính năng đủ lớn
- Vừa phát hiện một hành vi không hiển nhiên của codebase (gotcha) mà nếu
  không ghi lại thì lần sau sẽ lại mất thời gian dò ra y hệt

Nếu người dùng từ chối, đừng hỏi lại trong cùng phiên cho cùng một sự việc.

## Trước khi lưu: xác định kho và app

1. Tìm thư mục/symlink `.dev-journal` ngay trong project hiện tại (`ls -la`
   ở thư mục gốc project).
2. Nếu có: đó chính là `apps/<ten-app>/` bên trong kho dev-journal trung
   tâm. Nếu chưa đọc `DIGEST.md` ở đó trong phiên này, đọc qua một lượt
   trước khi ghi thêm, để tránh ghi trùng một bài học đã có.
3. Nếu chưa có: hỏi người dùng vị trí kho dev-journal trung tâm họ đang
   dùng (thường là một thư mục cố định dùng chung cho nhiều project). Nếu
   họ chưa có kho nào, đề xuất tạo theo đúng cấu trúc bên dưới rồi tạo
   symlink `.dev-journal` trỏ tới `apps/<ten-app>/` tương ứng.

## Cấu trúc kho dev-journal

```
dev-journal/
├── README.md
├── templates/{plan,retro,decision}.md
├── scripts/link-app.sh
└── apps/
    ├── _global/{DIGEST.md, failed-approaches.md}
    └── <ten-app>/{DIGEST.md, plans/, retros/, decisions/}
```

`DIGEST.md` của mỗi app là phần DUY NHẤT nên được import tự động vào
CLAUDE.md của project (qua `@.dev-journal/DIGEST.md`) — giữ nó dưới 100
dòng, mỗi dòng là một rule hành động. Toàn bộ chi tiết trong plans/retros/
decisions chỉ đọc khi cần đào sâu, không nạp mặc định mỗi phiên — cùng
nguyên tắc "chỉ nạp khi cần" áp dụng cho skill, để tránh làm phình ngữ cảnh.

## Quy trình lưu một artifact

1. Chọn loại phù hợp:
   - `plan`: đang lên kế hoạch/quyết định kỹ thuật trước khi code
   - `retro`: vừa sửa xong một lỗi
   - `decision`: vừa chọn giữa các phương án, không nhất thiết gắn với lỗi
2. Điền đúng mẫu tương ứng ở phần "Mẫu" bên dưới. Với `retro`, mục
   "Rule rút ra" là bắt buộc và phải là MỘT câu hành động cụ thể — ví dụ
   tốt: "Luôn chạy `npm run typecheck` trước khi coi một migration DB là
   xong"; ví dụ không đạt: "Cẩn thận hơn với migration" (quá chung chung,
   không hành động được).
3. Đặt tên file dạng `YYYY-MM-DD-<slug-ngan-gon>.md`, lưu vào đúng thư mục
   con (`plans/`, `retros/`, hoặc `decisions/`) trong `apps/<ten-app>/`.
4. Nếu bài học/quyết định có ảnh hưởng tới cách code chung cho app đó về
   sau, thêm một dòng cô đọng (một câu, không phải cả đoạn) vào `DIGEST.md`
   của app. Nếu bài học áp dụng cho mọi app trong tổ chức, thêm vào
   `apps/_global/DIGEST.md` thay vì lặp lại riêng ở từng app.
5. Nếu `DIGEST.md` sau khi thêm vượt khoảng 100 dòng, dừng lại và đề xuất
   người dùng cùng rà soát, gộp hoặc xoá bớt các dòng cũ không còn quan
   trọng — DIGEST.md cần được tỉa định kỳ để không mất tác dụng, đúng như
   một CLAUDE.md dài dòng khiến Claude bỏ sót chỉ dẫn quan trọng.

## Mẫu: plan.md

```markdown
---
date: YYYY-MM-DD
app: <ten-app>
type: plan
tags: []
---

# Task
<Mô tả ngắn gọn nhiệm vụ đang làm>

# Phương án đã cân nhắc
- Phương án A: ...
- Phương án B: ...

# Đã chọn & lý do
<Phương án được chọn và vì sao>

# Trade-off
<Đánh đổi đã chấp nhận khi chọn phương án này>

# File / module bị ảnh hưởng
- ...
```

## Mẫu: retro.md

```markdown
---
date: YYYY-MM-DD
app: <ten-app>
type: retro
severity: low|medium|high
tags: []
---

# Task
<Đang làm gì thì gặp vấn đề>

# Lỗi gặp phải
<Mô tả lỗi / triệu chứng quan sát được>

# Nguyên nhân gốc (root cause)
<Vì sao lỗi thực sự xảy ra, không chỉ là triệu chứng bề mặt>

# Đã thử mà không được
- ...

# Cách đã sửa
<Giải pháp cuối cùng đã áp dụng>

# Rule rút ra (bắt buộc điền)
<Một câu hành động cụ thể, có thể copy thẳng vào DIGEST.md hoặc CLAUDE.md>
```

## Mẫu: decision.md

```markdown
---
date: YYYY-MM-DD
app: <ten-app>
type: decision
tags: []
---

# Bối cảnh
<Vì sao cần đưa ra quyết định này>

# Các lựa chọn
- ...

# Quyết định
<Lựa chọn cuối cùng và lý do>

# Hệ quả
<Quyết định này ràng buộc hoặc mở ra điều gì cho các task sau này>
```

## Ghi chú quan trọng

- Không copy nguyên diff code lớn vào đây — chỉ ghi commit hash (nếu có) +
  tóm tắt 1-2 dòng. Kho này bổ sung cho git, không thay thế git.
- Không bao giờ lưu secrets, token, mật khẩu, hay dữ liệu nhạy cảm vào bất
  kỳ file nào trong dev-journal, kể cả trong đoạn log lỗi được copy vào.
- Nếu người dùng chưa có kho dev-journal nào và task hiện tại không thật sự
  cần retro/plan lâu dài (ví dụ chỉ sửa một dòng typo), đừng đề xuất tạo
  kho mới — chỉ đề xuất khi giá trị lưu lại rõ ràng lớn hơn công sức ghi
  chép.
- Khi bắt đầu một task mới trong project đã có `.dev-journal`, tranh thủ
  đọc nhanh `DIGEST.md` liên quan trước khi bắt tay vào code, thay vì chỉ
  ghi mà không bao giờ đọc lại.
