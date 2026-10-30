# Ứng viên tự cải thiện — gặp 1 lần, chưa đúc

Ghi bằng `chrome.py learn <id> --desc "…" [--kind thao-tac|bay] [--site <nền tảng>]`. Script cộng lần gặp; lần 2 nó báo
đúc → làm theo `self-improve.md`, rồi xoá dòng. Không ghi mã task, tên khách, URL thật.

| Key | Pattern (loại, nền tảng) | Lần |
|---|---|---|
| `app-api-id-token` | Gọi api của app nhúng bằng session token: trong frame app `await shopify.idToken()` rồi `fetch` kèm `Authorization: Bearer`, không lấy token từ `src` iframe (thao-tac, shopify) | 1 |
| `read-computed-style` | Đọc màu / style bằng `getComputedStyle` thay ảnh, ghi `.jsonl` để so (thao-tac) | 1 |
| `read-app-global-data` | Đọc data app đổ ra trang (biến global) để chứng minh "có data nhưng không hiện" (thao-tac) | 1 |
| `color-picker-hex` | Nhập màu qua color picker: ô hex trong picker, Enter, đóng picker (thao-tac) | 1 |
| `polaris-tooltip-fade-shot` | Polaris tooltip fade-in: is_visible true nhưng ảnh chụp ngay còn trống; chờ ~1.5s rồi chụp clip quanh tooltip (ctx.shot redraw cửa sổ có thể làm mất hover). (bay) | 1 |
| `poll-without-time-sleep` | Vòng poll trong steps.py dùng time.sleep thì Playwright sync không bơm sự kiện: cây frame (child_frames) / trạng thái trang đứng yên, iframe con mới gắn không thấy. Poll bằng page.wait_for_timeout(250). (bay) | 1 |
| `sidekick-ribbon-blocks-click` | Thanh 'Work with Sidekick' ([data-polaris-frame-global-ribbon]) nổi ở đáy khung admin, nuốt cú bấm vào hàng phần tử cuối trang app (Playwright báo 'subtree intercepts pointer events'). Ẩn bằng page.add_style_tag('[data-polaris-frame-global-ribbon]{display:none!important}') ở phía test. (bay, shopify) | 1 |
| `web-component-rect-zero` | Host Polaris web components (s-box, s-text…) là display: contents → getBoundingClientRect = 0 và CSS ngoài không đè chữ trong shadow; đo phần tử đầu tiên có kích thước trong shadowRoot. Đo host thì check bố cục đạt giả. (bay) | 1 |
| `theme-editor-app-embed-toggle` | Theme editor (?context=apps): mỗi app embed là div[class*=AppEmbedItem] gồm nút mở + toggle tên 'Enable/Disable <tên embed>' (app prod cùng tên → lọc dòng theo handle app). Save khi preview chưa tải xong có thể không ghi: chờ Save enabled + 1,5 s rồi xác nhận bằng nguồn khác (api đọc file theme). (thao-tac, shopify) | 1 |
| `add-app-block-deeplink-persists` | Deep-link theme editor addAppBlockId: đóng tab không Save vẫn có thể để lại block trên theme (gặp 1 lần). Sau khi bấm nút deep-link này, kiểm file theme; có block thì gỡ (sections → Open sub items menu → Remove block → Save). (bay, shopify) | 1 |
