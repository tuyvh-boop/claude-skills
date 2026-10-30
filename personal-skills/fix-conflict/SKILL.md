---
name: fix-conflict
description: Kích hoạt khi user muốn merge một nhánh (mặc định master/main, hoặc nhánh do user chỉ định) vào nhánh hiện tại và xử lý conflict phát sinh — "cập nhật master vào nhánh này", "merge conflict", "fix conflict giúp tôi". Không dùng cho conflict trên UI GitLab MR hay rebase — chỉ merge local qua git.
---

# Fix Conflict

Merge một nhánh vào nhánh hiện tại và xử lý conflict: tự giải những đoạn thật sự an toàn, **dừng
hỏi user** với mọi đoạn có khả năng là xung đột logic thật.

## ⚠️ Framework Reminder

Conflict resolution is not "pick one side" — it's understanding both sides: [[framework_systematic_problem_solving]] —
- **Trace the logic, not just syntax**: merge conflict shows diff structure, but you need to understand what BOTH sides were trying to do. Resolving wrongly compiles but breaks feature
- **Measure impact after merge**: after resolving, verify the result actually works (logic flows correctly, tests pass if repo has them). Don't just assume resolved file is correct
- **Escalate unclear conflicts**: if logic intent isn't clear from code alone, ask user before guessing. Wrong resolution compounds later

## Bước 0: Xác định nhánh nguồn

- Không chỉ định → mặc định nhánh chính của remote (`git symbolic-ref refs/remotes/origin/HEAD`
  hoặc suy ra `master`/`main` từ `git branch -r`).
- User nói rõ nhánh khác ("merge release/x vào đây", "lấy conflict với branch Y") → dùng đúng
  nhánh đó, không tự đổi sang master.

## Bước 1: Pre-check — bắt buộc trước khi merge

```bash
git status
```

Có uncommitted changes → **dừng lại, hỏi user** commit hay stash trước (không tự ý stash khi
chưa hỏi — xem quy tắc an toàn chung về `git stash -u`/`git reset`). Working tree sạch mới sang
Bước 2.

## Bước 2: Merge

```bash
git fetch origin
git merge origin/<branch-nguồn>
```

Không dùng `--no-verify`, không `-X ours`/`-X theirs` (2 flag này tự động chọn 1 bên cho MỌI
conflict — vi phạm nguyên tắc "chỉ tự giải chỗ an toàn" của skill này).

- **Merge sạch, không conflict** → xong. Báo kết quả, hỏi user có muốn `git push` không (side
  effect — luôn xin xác nhận, không tự push).
- **Có conflict** → sang Bước 3.

## Bước 3: Phân loại từng đoạn conflict (không phải cả file)

Liệt kê file conflict: `git diff --name-only --diff-filter=U`. Với **mỗi đoạn** conflict
(`<<<<<<<` … `=======` … `>>>>>>>`) trong từng file, phân loại riêng — một file có thể vừa có
đoạn tự giải được vừa có đoạn phải hỏi.

### 3a. Tự giải — KHÔNG cần hỏi

- **File lock** (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `composer.lock`,
  `Gemfile.lock`…): không merge tay theo markers. Resolve phần code khác trước, rồi xoá conflict
  ở file lock và chạy lại lệnh cài đặt tương ứng (`npm install`/`yarn`/`composer install`) để
  regenerate — không tự đoán nội dung.
- **Cả hai bên chỉ thêm dòng mới ở vị trí gần nhau, không đè lên cùng một đoạn logic** (git báo
  conflict do context gần nhau, không phải nội dung mâu thuẫn thật) → giữ cả hai, sắp xếp hợp lý
  (vd 2 import khác nhau, 2 field khác nhau thêm vào cùng object).
- **Khác biệt thuần format/whitespace** do linter/formatter chạy khác thời điểm → giữ theo
  convention hiện tại của file (chạy formatter của project nếu có, không tự bịa style).

### 3b. Xung đột logic thật — LUÔN dừng hỏi user, không tự quyết

Dấu hiệu: cả hai bên sửa **cùng một đoạn logic** theo hai cách khác nhau; một bên xoá còn bên
kia sửa/thêm vào đúng chỗ đó; hai bên đổi behavior hoặc signature khác nhau cho cùng một
hàm/biến. Với mỗi đoạn này:

1. Dùng `git log -p` hoặc `git show` trên từng bên (nhánh hiện tại và nhánh đang merge vào) để
   hiểu ý đồ mỗi thay đổi — không đoán mò từ mỗi đoạn code đơn lẻ.
2. Tóm tắt ngắn gọn cho user: bên A định làm gì, bên B định làm gì, tại sao chúng xung đột.
3. Đưa lựa chọn: giữ bên hiện tại / giữ bên vừa merge vào / gộp cả hai / để user tự viết lại.
   **Chờ user chọn rồi mới sửa** — không tự ý quyết định giữ bên nào.

## Bước 4: Hoàn tất

Sau khi mọi đoạn conflict (cả 3a lẫn 3b) đã được xử lý — không còn conflict marker nào trong
repo (`git diff --check` hoặc grep `<<<<<<<`) — hiển thị tóm tắt: file nào tự giải theo diện
nào (3a), file nào theo quyết định user (3b), rồi hỏi xác nhận trước khi:

```bash
git add -A
git commit   # dùng message merge mặc định của git, trừ khi user muốn message khác
```

**Không tự `git push`** sau khi commit — hỏi riêng nếu user muốn đẩy lên.

## Huỷ merge

Chỉ chạy `git merge --abort` khi user chủ động yêu cầu huỷ — không tự ý huỷ khi gặp conflict
khó, vì abort sẽ mất toàn bộ phần đã resolve.

## Không thuộc phạm vi skill này

- Conflict hiển thị trên UI GitLab MR (chưa pull về máy) — cần pull nhánh MR về rồi mới áp dụng
  skill này.
- `git rebase` — luồng conflict của rebase khác merge (mỗi commit resolve riêng), chưa hỗ trợ.
