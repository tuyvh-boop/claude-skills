# Site Shopify — admin, app nhúng, storefront

Helper: `ctx.site("shopify")` (`scripts/chrome_lib/sites/shopify.py`). Config site: `login_markers: [accounts.shopify.com]`,
`allowed_origins` = admin của **store dev** + domain storefront của store đó.

## Đã kiểm trên admin thật

| Việc | Cách |
|---|---|
| Mở app | `open_app(page, store, app_handle, path)` → frame app. Đi qua admin; mở thẳng URL iframe thì App Bridge kéo về admin |
| Lấy frame app | `app_frame(page, app_host="")`: `iframe[name=app-iframe]`. Admin giữ nhiều iframe app cùng lúc → truyền `app_host` để chọn đúng |
| Modal của app (Polaris `Modal`) | Nằm **trong frame app** (`frame.get_by_role("dialog").last`) → locator trong `app` |
| Mở max modal App Bridge | `open_max_modal(page, trigger, route)`: bấm lại tới khi frame `route` có, rồi chờ React hydrate |
| Lấy frame max modal | `modal_frame(page, route)`: tìm theo **path URL** frame (`/product-groups/new`, regex được), rồi đi từ phần tử `<iframe>` (src path khớp route) khi frame khác site không có trong `page.frames`. Admin còn giữ một iframe modal ẩn URL `/` |
| Đóng max modal bằng X | `close_max_modal(page)`: X ở shadow DOM admin, chỉ click chuột thật theo toạ độ ăn |
| SaveBar "Unsaved changes" | Vẽ ở document admin, phía trên max modal. `save_bar(page, "Save"\|"Discard")`, đọc trạng thái `save_bar_state(page)`. Chỉ hiện khi form app báo dirty (react-hook-form `isDirty`) |
| Rời editor dirty | `leave_clean(page, route)` (Discard + chờ iframe đi) trước `goto`; `open_max_modal` đã `accept_dialogs` |
| Dev Console của `shopify app dev` | `hide_dev_console(page)` đầu steps: panel phủ ~250px đáy cửa sổ, click ở đó trúng panel |
| Toast | Vẽ ở document admin: đọc `page` (`expect_toast` tìm cả frame app) |
| Mobile / tablet | `--device mobile` / `--device tablet` (đều Android) chạy được với admin. **Mọi UA iOS (kể cả `iPhone 14`, `iPad Pro 11`) bị admin chặn**: không có iframe app, steps chờ 30 s rồi lỗi |
| Shopify Mobile app (thanh nav nổi, `--shopify-safe-area-inset-*`) | Chrome giả lập không có thanh nav của app → biến safe-area = 0. Gán tay lên `:root` (vd 80px) để kiểm CSS dùng biến; kết quả chỉ là bằng chứng giả lập — nghiệm thu ghi `Pass yếu`, cần máy thật |

## Chưa chạy được

| Việc | Đã gặp | Làm gì |
|---|---|---|
| Storefront store có mật khẩu | Mở thẳng domain rơi `/password`; tìm "View your online store" theo role link hoặc trên trang chủ admin không thấy | Con mắt "View your online store" là **button** cạnh mục Online Store ở sidebar, chỉ hiện khi hover mục đó: `storefront_preview` hover rồi bấm → tab preview không cần mật khẩu, điều hướng trong chính tab đó. Không nhập mật khẩu storefront |

## Bẫy

- **Max modal chạy vite dev**: hiện HTML SSR vài giây trước khi React hydrate → gõ / bấm lúc đó không đổi state (Fail giả).
  `open_max_modal` đã chờ; tự lấy frame thì gọi `ctx.wait_hydrated(frame)` trước khi thao tác.
- **Tile / nút mở modal ngay khi trang vừa hiện**: cú bấm đầu bị nuốt → `ctx.click_until(locator, done)`.
- **Max modal mở chậm (> 4 s mới điều hướng xong)**: bấm lại lúc đó trúng lớp phủ modal (`iframe … intercepts pointer events`, chờ 30 s). `open_max_modal` coi modal đã mở ngay khi có `<iframe>` modal mang route trong src, rồi chờ frame tới 60 s.
- **Form editor reset thêm một lần sau khi vẽ** (ảnh preview tải xong): select / click ngay sau khi trang hiện bị mất →
  thao tác rồi kiểm lại trạng thái, lặp nếu mất.
- **Escape trong popover filter (Polaris `Filters`) đóng luôn cả `Modal`** chứa nó. Đóng popover bằng cách bấm vào tiêu đề
  modal; popover chồng nhau che nút → `dispatch_event("click")`.
- **Polaris web components (`s-*`, App Home)**: input / select / checkbox nằm trong shadow DOM mở — locator Playwright (CSS,
  role, label) xuyên được, `document.querySelectorAll('input')` / `input.labels` trong `evaluate` thì không → đọc `host.value`,
  thuộc tính host (`label`, `placeholder`, `accessibilitylabel`, `error` có trên DOM). Host `s-button` / `s-switch` / `s-checkbox`
  báo 0×0 → bấm qua role (`get_by_role("button", name=…)`) hoặc phần tử bên trong. Lỗi field (`error`) vẽ trong shadow →
  `innerText` không thấy. `s-modal` mở = `<dialog open>` trong shadow root. `filter(has=…)` nhận locator TƯƠNG ĐỐI với phần tử
  ngoài — locator nối từ một scope khác (vd `modal.get_by_text`) sẽ tìm lại scope đó bên trong → luôn rỗng; dùng `has_text`
  hoặc locator gốc frame.
- **Dropdown Polaris tự vẽ không phải `<select>`**: `select_option` không dùng được, bấm mở rồi chọn theo text.
- **Bấm tên group / row trong IndexTable** có khi chỉ hiện tooltip → bấm nút action của row (icon bút).
- **Đổi data qua Admin API rồi đọc lại ngay**: `products(query: …)` đi qua search index, trễ vài giây tới vài phút → app
  vẫn thấy title cũ. Chờ API trả giá trị mới rồi mới vào màn, đừng kết luận app không quét lại.
- **api của app → Shopify `ETIMEDOUT`** (mạng máy dev, dày lên khi nhiều luồng chạy song song): danh sách / search rỗng mà
  UI không báo lỗi. Xem log api trước khi ghi Fail, chạy lại. `run` cảnh báo khi vượt `max_parallel_runs`.
- **Theme editor**: chỉ xem rồi đóng tab. Lưu editor có thể xoá block của app khác khỏi template.
- **Storefront đang chạy bản code nào**: trước khi kết luận, kiểm asset đang nạp có chuỗi chỉ bản mới có:
  `ctx.page.evaluate("async (n) => { const u=[...document.scripts].map(s=>s.src).find(s=>s.includes(n)); return u && (await (await fetch(u)).text()).includes('<chuỗi mới>') }", "<tên asset>")`.
- **Data đổi bằng harness / MCP**: mở lại trang app (app cache); storefront cần đẩy metafield trước khi đọc.
- **Đăng nhập**: Shopify không hỗ trợ tự động hoá màn login → luôn để user tự đăng nhập.
