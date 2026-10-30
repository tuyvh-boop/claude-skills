# Thiết lập lần đầu — đọc kỹ trước khi đăng nhập

## Rủi ro

1. Chrome của skill mở **cổng debug** (127.0.0.1:<port>). Mọi tiến trình đang chạy trên máy này nối được vào cổng đó và
   **điều khiển được phiên đăng nhập** trong profile.
2. Ai nối được cổng thì làm được mọi việc account đăng nhập làm được, trên **mọi hệ thống account đó vào được** — không
   chỉ trang đang test.
3. Thư mục profile chứa **cookie phiên**: có nó là có phiên. Không copy đi đâu, không commit, không gửi cho ai.
4. Vì vậy **chỉ đăng nhập bằng account test quyền hẹp**, không bao giờ bằng account chính của bạn.

Script đã có rào mềm (chỉ mở origin khai trong config, dừng ở trang login, cắt token khỏi URL in ra), nhưng **rào thật là
quyền của account**.

## Checklist account test

- [ ] Email riêng, chỉ dùng để test.
- [ ] Chỉ vào được **môi trường dev / staging** cần test. Không vào production, không vào dữ liệu khách.
- [ ] Chỉ có quyền mà luồng cần test dùng tới.
- [ ] Không có quyền quản trị: settings, billing, quản lý user / staff.
- [ ] Không phải owner của hệ thống.

## Sau khi xác nhận

Chạy lại `setup` kèm `--ack`. Chrome mở trang đăng nhập — **bạn tự đăng nhập** (cả 2FA / CAPTCHA); AI không nhập mật
khẩu. Xong thì `doctor --session --site <tên> --release` kiểm phiên. Profile được giữ cho các lần sau; phiên hết hạn thì
đăng nhập lại trong cửa sổ đó, không tạo profile mới.
