# Safety — guardrail bắt buộc cho mọi thao tác ghi/push

Đọc trước khi commit / push / tạo branch / tạo MR. Các guard này **không được bỏ qua** dù user giục.

## 1. Protected branch (không commit/push thẳng)

Nhánh coi là protected: `main`, `master`, `develop`, `release/*`, `hotfix/*`.

- Đang **ở** protected branch mà định commit → ⚠️ cảnh báo và hỏi:
  > "Bạn đang ở `<branch>`. Commit thẳng vào nhánh này không nên. Vẫn tiếp tục? (yes / no / tạo branch mới)"
- Định **push tới** protected branch → hỏi xác nhận rõ ràng trước, nêu rủi ro.
- **NEVER** commit/push tới protected branch khi user chưa xác nhận rõ.

## 2. Push luôn cần confirm

Push là hành động outward (ảnh hưởng remote/PR). **Không bao giờ tự push.** Luôn hiện những gì sắp push (branch, số commit, target) rồi chờ user "yes".

## 3. Non-fast-forward → pull MERGE (không rebase)

Push bị từ chối do behind remote (`! [rejected] non-fast-forward`):

- Đề xuất: `git pull` (merge — **KHÔNG** `--rebase`), giải quyết conflict nếu có, rồi push lại.
- Có conflict → dừng, liệt kê file conflict, hỏi user (hoặc hỗ trợ giải), KHÔNG tự ý chọn bên.
- **NEVER** `git push --force` / `--force-with-lease` để đè, trừ khi user yêu cầu tường minh và hiểu rủi ro.

## 4. Secret scan trước commit

- `git-context.sh` đã in section `SECRET SCAN` (heuristic). Có `WARN` → **dừng**, cho user xem dòng nghi ngờ, hỏi có chắc muốn commit không.
- Có file `.env`/key/credential trong staged → cảnh báo mạnh, gợi ý gỡ khỏi staged (`git restore --staged <file>`) + thêm `.gitignore`.
- Không log/echo giá trị secret ra ngoài.

## 5. Staging có kiểm soát

- Chưa stage gì → tóm tắt thay đổi, hỏi: stage tất cả hay chọn lọc? Cảnh báo file **untracked** lạ trước khi `git add -A`.
- Không tự ý `git add -A` khi có file rác/không liên quan trong working tree.

## 6. Thao tác phá huỷ → luôn hỏi

`reset --hard`, `checkout -- <file>` / `restore` (mất thay đổi), `branch -D`, `clean -fd`, `stash drop`... → mô tả chính xác cái gì sẽ mất, hỏi xác nhận. KHÔNG tự chạy.

## 7. Dirty working tree khi chuyển ngữ cảnh

Tạo branch mới / switch branch mà working tree đang dở → cảnh báo (tránh kéo thay đổi rác sang), hỏi user (commit trước? stash? hay mang theo?).

## 8. Không đoán thông tin quan trọng

Mã task, tên branch đích khi mơ hồ, target của MR → **hỏi**, không bịa.
