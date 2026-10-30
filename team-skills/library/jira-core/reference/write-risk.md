# Mức rủi ro của thao tác GHI Jira

Dùng để quyết định thao tác nào **tự `--commit` luôn**, thao tác nào **dry-run rồi hỏi user**.
Tiêu chí: sau khi ghi, có **đưa về đúng trạng thái cũ bằng 1 lệnh** được không.

Skill nào áp bảng này phải nói rõ trong SKILL/phase của nó. Skill không nói thì giữ mặc định
của jira-core (hỏi trước mọi `--commit` ngoài-nhìn).

## 🔴 Dry-run + hỏi trước

| Thao tác | Vì sao |
|---|---|
| Xoá issue | Jira Cloud xoá vĩnh viễn, không có thùng rác |
| Ghi đè `description` **đang có nội dung** | Text của BA có bảng/ảnh/mention; `text_to_adf` làm mất định dạng. History không khôi phục nguyên trạng. Subcommand `description` chặn sẵn (cần `--force`). Description **đang trống** → ghi mới, 🟢 |
| Ghi đè field text / URL / paragraph **đang có nội dung** | Giá trị cũ bị thay (link MR, link doc…). Field đang trống → 🟢 |
| Xoá attachment | File mất hẳn |
| Xoá hoặc sửa comment (nhất là của người khác) | Mất nội dung / sửa lời người khác |
| Xoá worklog | Mất log giờ |
| Đổi issue type, chuyển issue sang project khác | Đổi mã issue, có thể rớt field |
| 1 yêu cầu đụng **>10 issue** | Hiểu sai 1 lần là sai hàng loạt |
| Chuyển status sang **Go Live** hoặc **Done** | Mang nghĩa "đã ship", có thể kích automation / thông báo khách. Đổi lại được về kỹ thuật nhưng hậu quả đã xảy ra |

## 🟢 Tự ghi luôn

Priority · Change Size và mọi field dạng chọn từ danh sách · status (trừ sang Go Live / Done) · assignee · sprint · labels · epic/parent · thêm hoặc gỡ link · thêm attachment ·
thêm comment · sửa `summary` · ghi vào field đang trống.

Ghi xong vẫn **báo lại danh sách đã đổi** (`issue · field · cũ → mới`) để user biết.
