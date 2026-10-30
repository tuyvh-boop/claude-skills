# App Profile: <tên-app>

> Copy file này thành `apps/<tên-app>.md` khi lần đầu review app đó.
> Quy tắc vàng: ghi **pattern/luật chắt lọc**, KHÔNG ghi nhật ký sự cố.
> ❌ "2026-08 tìm thấy bug ở OptionService" → ✅ "mọi query option phải scope shop_id; hay quên ở tầng service".
> Mỗi mục vẫn dùng `Áp dụng khi:` (surface tag) để reviewer chỉ soi khi liên quan.

## Kiến trúc & luồng chính
_(Bối cảnh tối thiểu reviewer cần: stack, các module chính, luồng dữ liệu cốt lõi. Ngắn gọn.)_
-

## Quy ước bắt buộc của app
_(Naming, pattern kiến trúc, cách tổ chức code mà PR phải tuân theo. Ghi cả **quy ước đặt tên** và **nơi đặt file/folder** đặc thù repo — reviewer chấm naming/vị trí file dựa vào đây, không áp chuẩn ngoài.)_
- Đặt tên / tổ chức code: ... — `Áp dụng khi: logic`
- Vị trí file/folder (đặt gì ở đâu): ... — `Áp dụng khi: structure`

## Vùng nóng / dễ vỡ (hotspots)
_(File/module hễ đụng tới là phải soi kỹ.)_
- ... — `Áp dụng khi: <surface>`

## Bẫy tái diễn (pattern-level)
_(Lỗi kiểu gì hay lặp lại ở app này. Mô tả pattern, không phải sự cố đơn lẻ.)_
- ... — `Áp dụng khi: <surface>`

## Trọng tâm cần soi kỹ nhất
_(2–4 thứ quan trọng nhất khi review app này.)_
-

## Không áp dụng / bỏ qua (giảm nhiễu)
_(Những mục base/shopify KHÔNG hợp với app này — nói rõ để reviewer khỏi báo thừa.)_
-
