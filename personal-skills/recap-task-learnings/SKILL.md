---
name: recap-task-learnings
description: Sau khi xong (hoặc dừng) một task, tổng hợp 1 bản tóm tắt NGẮN cho CON NGƯỜI đọc — kiến thức/kỹ thuật đã học hoặc áp dụng được trong task này, và những gì còn mơ hồ cần tìm hiểu thêm — lưu vào dev-journal (`apps/<app>/learnings/`). KHÁC `dev-journal-save` (viết plan/retro/decision cho AI đọc, cố định format máy xử lý được, trọng tâm "rule hành động") — skill này viết cho NGƯỜI DÙNG tự đọc lại để ôn kiến thức, văn phong giải thích dễ hiểu hơn, không cần rule hành động cụ thể. Dùng khi user nói "tổng kết bài học task này", "tôi học được gì từ task vừa rồi", "ghi lại kiến thức đã học", hoặc tự chủ động đề xuất ngay sau khi 1 task có nhiều điều mới (kỹ thuật lạ, concept chưa quen, lần đầu dùng 1 pattern/tool).
metadata:
  trigger: "ngay sau khi 1 task/feature hoàn thành hoặc dừng giữa chừng, khi task đó có concept/kỹ thuật mới đáng ghi lại cho người dùng tự học"
  model_hint: "main loop — cần ngữ cảnh đầy đủ của cả task vừa làm để tổng hợp đúng, không tách subagent riêng"
  keywords: ["học được gì", "tổng kết bài học", "ghi lại kiến thức", "recap", "learning", "ôn lại", "cần học thêm"]
---

# Recap Task Learnings

## ⚠️ Framework Reminder

Learning capture requires systematic knowledge extraction: [[framework_systematic_problem_solving]] —
- **Identify what was NEW, not just what was DONE**: "implemented retry logic" is done. "learned why exponential backoff matters vs linear backoff" is the learning. Capture the second, not just repeat the first
- **Trace the investigation path**: how did you discover this knowledge? Through debugging? Through code review feedback? Through hitting a bug? Understanding the path helps you remember and apply it next time
- **Separate "learned and understand" from "learned and still fuzzy"**: a learning summary that papers over gaps is useless. Explicitly note "still unclear: why the team chose this pattern over others"

## Vì sao skill này khác `dev-journal-save`

`dev-journal-save` (plan/retro/decision) viết **cho AI đọc ở phiên sau** —
format cố định, bắt buộc có "Rule rút ra" hành động được, văn phong súc
tích. Skill này viết **cho chính người dùng đọc lại** — mục tiêu là ôn kiến
thức, nên văn phong giải thích đầy đủ hơn, không ép khuôn "rule", và có hẳn
một mục riêng cho "cái gì còn chưa hiểu" (thứ mà retro.md không có chỗ cho,
vì retro chỉ ghi cái đã giải quyết xong).

Hai skill **không thay thế nhau** — một task lớn có thể vừa có retro kỹ
thuật (cho AI) vừa có learning recap (cho người), link qua lại bằng mục
"Liên kết" trong `templates/learning.md`.

## Khi nào chủ động đề xuất

Ngay sau khi một task/feature kết thúc (hoặc dừng giữa chừng có chủ đích),
nếu task đó có ít nhất một trong các dấu hiệu sau, hỏi ngắn gọn người dùng
có muốn tổng kết bài học không — **đừng tự ý ghi file mà không hỏi trước**,
giống nguyên tắc của `dev-journal-save`:

- Lần đầu dùng một pattern/kỹ thuật/thư viện mà người dùng trước đó chưa
  quen (quan sát qua việc họ hỏi lại, hoặc chính Claude phải giải thích khái
  niệm nền tảng trong lúc làm).
- Task chạm vào một phần codebase/kiến trúc mà trước giờ người dùng ít động
  tới.
- Có một quyết định kỹ thuật cần cân nhắc nhiều phương án — người dùng theo
  dõi quá trình đó cũng là một dạng học.
- Người dùng tự hỏi "cái này là gì vậy", "sao lại làm thế này" trong lúc
  task diễn ra — dấu hiệu rõ nhất là chính họ đã bộc lộ gap kiến thức.

Nếu user từ chối, đừng hỏi lại trong cùng phiên cho cùng task đó.

## Trước khi viết: xác định app + đọc lại learnings cũ

1. Tìm `.dev-journal` trong project hiện tại (symlink trỏ tới
   `apps/<ten-app>/` trong kho dev-journal trung tâm — xem skill
   `dev-journal-link` nếu chưa thấy symlink).
2. Đọc lướt `apps/<ten-app>/learnings/` (vài file gần nhất) để tránh lặp lại
   đúng một bài học đã ghi trước đó — nếu task này chỉ CỦNG CỐ một bài học
   cũ (không phải điều mới), nói thẳng điều đó với user thay vì tạo file
   mới trùng lặp.

## Nội dung tóm tắt (soạn trước, cho user xem rồi mới hỏi lưu)

Dùng khung `templates/learning.md` của kho dev-journal, 2 mục chính:

- **"Đã học / áp dụng được"**: liệt kê cụ thể — mỗi mục là 1 khái niệm/kỹ
  thuật + NGỮ CẢNH đã dùng nó ở đâu trong task vừa làm (không viết chung
  chung kiểu "đã học về TypeScript"). Viết sao cho vài tháng sau đọc lại vẫn
  hiểu ngay tại sao nó quan trọng — như giải thích lại cho chính mình trong
  tương lai, không phải tóm tắt kiểu changelog.
- **"Cần tìm hiểu thêm"**: những thứ có chạm tới trong task nhưng chưa hiểu
  sâu — liệt kê cụ thể (tên khái niệm/công cụ/pattern), không ghi mơ hồ.
  Nếu không có gì thuộc mục này, ghi thẳng "không có" — đừng bịa ra cho đủ
  mục.

Nếu task này cũng có retro kỹ thuật đã lưu qua `dev-journal-save`, điền mục
"Liên kết" trỏ sang đúng file đó, không chép lại nội dung kỹ thuật.

## Hỏi trước khi lưu

Hiện bản nháp ngắn gọn trong chat, hỏi user (vd `AskUserQuestion` hoặc hỏi
thường): *"Mình tổng kết bài học thế này, lưu vào dev-journal (`apps/<app>/
learnings/`) không, hay bạn muốn sửa gì trước?"* — chỉ ghi file sau khi có
xác nhận, đúng tinh thần của `dev-journal-save`.

## Sau khi ghi file: thêm 1 node vào Learning Roadmap

Ngay sau khi file `learnings/<ngày>-<task>.md` được ghi (cùng 1 lượt xác
nhận ở trên, không hỏi thêm lần nữa), gọi:

```bash
python3 ~/Shopify/skill/personal-workspace/dev-journal/scripts/add-roadmap-node.py \
  --app <ten-app> --task "<mã Jira nếu có>" \
  --title "<tiêu đề 1 dòng, súc tích>" \
  --insight "<bài học CHÍNH 1-2 câu — rút từ mục 'Đã học/áp dụng được'>" \
  --source "apps/<ten-app>/learnings/<file-vừa-ghi>.md"
```

- `--title`/`--insight` là bản RÚT GỌN của learning.md vừa ghi, không phải
  nội dung mới — nếu file có nhiều mục "Đã học", chọn mục quan trọng/mới lạ
  nhất, không cố nhét hết vào 1 dòng.
- Node này hiển thị trên `dev-journal/roadmap.html` (cron `learning-roadmap-popup`
  tự render + mở lại lúc 16h30 các ngày làm việc) — mục đích là ôn kiến thức
  trực quan theo thời gian, không phải kho lưu trữ chi tiết (đó vẫn là
  learning.md qua `--source`).
- Nếu script báo lỗi (vd thiếu file `roadmap.json`), báo user thay vì tự bịa
  bỏ qua bước này trong im lặng — node roadmap là phần MỚI của flow, lỗi ở
  đây không được coi là lỗi nhẹ có thể nuốt.

## Khi user hỏi lại kiến thức cũ

Nếu user hỏi kiểu "tôi đã học gì về X rồi", "trước đây mình từng gặp cái
này chưa" — tìm trong `apps/<app>/learnings/` (và `apps/_global/learnings/`
cho kiến thức chung không gắn với 1 app) trước khi trả lời, thay vì tự nhớ
lại từ context phiên hiện tại (có thể thiếu, vì learnings tích luỹ qua
nhiều phiên khác nhau).

## Lỗi hay gặp

- **Viết learning recap giống hệt văn phong retro.md** (chỉ có "Rule rút
  ra", thiếu phần giải thích) → mất hết giá trị khác biệt so với
  `dev-journal-save`. Fix: luôn có phần giải thích đủ chi tiết để đọc lại
  hiểu ngay, không chỉ 1 câu khẩu lệnh.
- **Tự ý ghi file không hỏi** → vi phạm nguyên tắc chung của mọi skill ghi
  vào dev-journal trong workspace này.
- **Bịa thêm mục "cần tìm hiểu thêm" cho đủ bố cục** dù task không thực sự
  để lộ gap nào → ghi "không có" thay vì bịa, giữ đúng tinh thần "No silent
  caps" (không giả vờ đầy đủ).
