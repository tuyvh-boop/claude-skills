# Mode brief — in trước bước đầu tiên, điền số thật, bỏ dòng không áp dụng

## Dựng mới

```
**MODE: Dựng mới** — journal cho <vai trò>, đặt ở <path>
- Mục đích: tạo một repo riêng để bạn (và Claude) cất tài liệu làm việc theo task / ngày → quay lại task không mất bối cảnh,
  có số liệu khi báo cáo, thấy AI làm tốt / sai ở đâu để tối ưu; tránh tài liệu rải rác hoặc lỡ đẩy secret lên git.
- Cách làm: hỏi vài câu (bạn nói khỏi hỏi thì mình dùng mặc định, vẫn cho xem trước) → cho bạn xem trước cây folder + danh sách file → tạo khung + bộ chặn secret (tự test bằng secret giả)
  → nối GitHub cá nhân, private.
- Không làm: không tạo template nội dung, không cài phần mềm, không push / tạo repo khi bạn chưa đồng ý, không bao giờ tạo repo public.
- Output: repo `<tên>` — CLAUDE.md (quy ước để Claude tự lưu đúng chỗ) · README (cây folder, cách dùng) · .githooks (chặn secret).
- Cần bạn: trả lời vài câu, <tự cài … nếu bước 0 báo thiếu>, đồng ý bản xem trước (gồm luôn commit đầu), rồi đồng ý riêng lúc tạo repo GitHub.
```

## Thêm loại

```
**MODE: Thêm loại** — journal `<path>`, thêm <danh sách loại>
- Mục đích: mở thêm chỗ lưu mới mà không đụng phần bạn đã viết.
- Cách làm: đọc CLAUDE.md đang có → cho xem trước phần sẽ thêm → nối khối quy ước mới + cập nhật cây trong README → bù hook
  chặn secret nếu thiếu, tự test.
- Không làm: không xoá / sửa quy ước cũ, không commit.
- Output: diff CLAUDE.md, README.md (+ .gitignore nếu loại mới cần) → bạn xem diff rồi tự commit.
- Cần bạn: chọn loại, duyệt bản xem trước.
```

## Kiểm tra

```
**MODE: Kiểm tra** — journal `<path>`
- Mục đích: chắc bộ chặn secret đang chạy thật trên máy này và repo vẫn private; hay hỏng nhất sau khi clone sang máy mới.
- Cách làm: kiểm hook đã bật chưa, scanner có chưa, thử commit một secret giả trong bản sao tạm (phải bị chặn), kiểm visibility remote.
- Không làm: không commit, không đổi visibility hộ bạn.
- Output: bảng ✅ / ⚠️ kèm cách sửa từng dòng.
- Cần bạn: cài phần mềm nếu thiếu; đổi repo sang Private nếu đang public.
```
