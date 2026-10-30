# Backup key + cổng Passbolt + rủi ro tự giữ GPG key

Cốt lõi: **private key là thứ DUY NHẤT giải mã được store. Không server, không "quên mật
khẩu → khôi phục".** → hai kiểu hỏng khác hẳn nhau, phải chặn cả hai.

## Backup ngay sau khi tạo key (Step 5) — [USER tự chạy]

Cần passphrase nên **user tự chạy**, AI chỉ đưa lệnh + nhắc:

```bash
mkdir -p ~/gpg-backup
gpg --export-secret-keys --armor <email> > ~/gpg-backup/private-key.asc
gpg --gen-revoke <email> > ~/gpg-backup/revoke.asc
```
(Win native tương tự, đổi đường dẫn cho hợp OS.)

Sau đó:
- Đưa **`private-key.asc` + `revoke.asc` + passphrase** lên **Passbolt** (chỗ cất "chìa khoá
  của chìa khoá") hoặc USB mã hoá offline.
- **Xoá `~/gpg-backup`** sau khi cất an toàn.
- **KHÔNG** commit/đẩy key lên nơi công khai, không để chung git secrets-store.

## 🚧 Cổng bắt buộc

Hỏi user: *"Đã đưa key backup (private-key.asc + revoke.asc + passphrase) lên Passbolt chưa?"*
**Chưa xác nhận → DỪNG, không nạp token.** Lý do: nếu chưa backup mà đã có token trong kho,
lỡ mất key là lockout — mất quyền truy cập cả kho.

## Kiểu 1 — MẤT key (lockout, không phải bị hack)

Ổ hỏng / cài lại OS / xoá nhầm mà **không backup** → mọi `.gpg` thành rác vĩnh viễn, dù vẫn
nhớ passphrase.
- **Nặng: vừa.** Là *mất quyền truy cập*, không phải *lộ token*. PAT (Jira/GitHub…) **cấp
  lại được** ở dịch vụ gốc — chỉ mất công.
- **Chặn bằng:** backup private key + revocation cert (ở trên).

## Kiểu 2 — LỘ key (breach thật)

Ai đó lấy được **cả private key file LẪN passphrase** → giải mã toàn bộ store (kể cả
ciphertext đã hốt từ git trước đó — "harvest now, decrypt later").
- **Nặng: cao.** Mất token thật.
- **Giảm nhẹ:** private key trên đĩa cũng mã hoá bằng passphrase → lấy mỗi file key mà không
  có passphrase thì chưa mở được. **Passphrase mạnh = lớp chặn Kiểu 2.**
- ⚠️ Với cache dài (~400 ngày): máy bị chiếm **lúc cache đang sống** (gpg-agent đã mở khoá
  sẵn) thì lớp chặn này **không tác dụng** — kẻ tấn công dùng luôn key đã mở. Đây là đánh đổi
  đã chấp nhận khi chọn "Hướng A + cache dài".

## Bảng gọn

| | Kiểu 1: Mất key | Kiểu 2: Lộ key |
|---|---|---|
| Chuyện gì | không giải mã store nữa | kẻ khác giải mã được store |
| Là gì | lockout (mất quyền) | breach (mất token) |
| Cứu bằng | **backup key** + rotate token | **passphrase mạnh** + revoke |
| Nặng cỡ nào | vừa (token tạo lại được) | cao |

## Chống Kiểu 2 (ngoài passphrase)

- Passphrase mạnh, **không tái sử dụng**.
- **Không bao giờ** đẩy `private-key.asc` lên nơi công khai.
- Nghi lộ → import `revoke.asc` + phát tán bản thu hồi, rồi **rotate toàn bộ token**.
- Lo rủi ro "cache dài" → giảm `default-cache-ttl`/`max-cache-ttl` bất cứ lúc nào (sửa
  `gpg-agent.conf` rồi `gpgconf --kill gpg-agent`), đổi lại nhập passphrase thường xuyên hơn.

## Nhiều máy

Thêm máy = **import CHÍNH private key này**, không tạo key mới:
```bash
gpg --import ~/gpg-backup/private-key.asc   # lấy từ Passbolt
```
→ Backup private key vừa là phao Kiểu 1, vừa là cách sync sang máy khác.

## Chốt tư duy

> **Passphrase** chống *bị hack* (Kiểu 2) — nhưng chỉ khi cache đã hết hoặc chưa nhập lần nào.
> **Backup key** chống *tự khoá mình* (Kiểu 1). Thiếu một là hở một mặt. Lớp đệm cuối: token
> **rotate lại được từ dịch vụ gốc** → kịch bản xấu nhất chỉ là mất công tạo lại.
