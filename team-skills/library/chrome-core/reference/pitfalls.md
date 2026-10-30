# Bẫy lõi (mọi web) — đã gặp ≥ 2 lần hoặc đã kiểm bằng thực nghiệm

Bẫy đã có helper lo thì chỉ giữ 1 dòng "helper X đã lo, đừng làm tay". Bẫy riêng một nền tảng → `sites/<tên>.md`.

| Bẫy | Triệu chứng | Đã lo / cách làm |
|---|---|---|
| Iframe khác site không có trong `page.frames` khi trang tải trước lúc nối, có khi cả sau reload (Playwright Python 1.63; bản vá upstream ở 1.64 npm) | Frame URL rỗng, "không có iframe" | `ctx.frame()` đi từ phần tử `<iframe>` + reload 1 lần. Đừng dùng `page.frames` |
| `aria_snapshot` không tự đi vào iframe | Snapshot chỉ thấy `- iframe` | `snapshot` / `ctx.snapshot()` duyệt từng frame |
| Cửa sổ bị **che** → Chrome ngừng vẽ | Chụp treo, click không ăn, `visibilityState` hidden | `launch` có 3 cờ chống background |
| Cửa sổ bị **thu nhỏ** → vẫn không vẽ dù có cờ | Chụp timeout | `shot` tự đưa về `normal` trước khi chụp |
| `el.click()` trong JS không mở tab mới | Popup bị chặn (không có user activation) | `click_new_tab(locator)` (cú bấm thật) |
| Nhiều client CDP cùng nối → cú bấm mở popup thỉnh thoảng không ăn (~1/12 khi 3 owner song song) | Chờ popup timeout, không tab nào có opener là tab mình | `click_new_tab` bấm lại đúng 1 lần khi chưa có tab nào mở |
| `context.expect_page()` trên context mặc định | Bắt tab mới của owner khác | `page.expect_popup()` (trong `click_new_tab`) |
| Giả lập thiết bị bằng CDP `Emulation.*` | Trang ngoài mobile, iframe khác site vẫn UA desktop | `emulate`: context Playwright theo device + chép `storage_state` (giữ phiên đăng nhập) |
| Trang không có `<meta name="viewport">` ở mobile | `innerWidth` = 980 dù giả lập máy 360–375 px (đúng như điện thoại thật) | Kiểm mobile bằng UA / `screen.width`, không bằng `innerWidth` |
| UA iOS cũ trong bộ thiết bị Playwright | Trang lớn báo "trình duyệt / iOS cũ không hỗ trợ" | Alias `mobile` = Android, UA đổi số bản Chrome theo bản đang chạy |
| Context thiết bị chặn cookie bên thứ 3 | Iframe dựa vào cookie bên thứ 3 khác cửa sổ thường | Biết giới hạn; case cần cookie bên thứ 3 thì chạy desktop |
| Trang https gọi `http://localhost` | Chrome hỏi quyền Local Network Access, app treo chờ | Chưa kiểm trên app thật. Gặp thì `learn local-network-access`; tunnel https cho api là cách chắc |
| 404 kèm `ERR_ABORTED` cùng URL | Một lỗi bị đếm 2 | `network.jsonl` đã gộp |
| Backend / DB đổi ngoài UI | Trang hiện data cũ (app cache) | Mở lại trang trước khi đọc |
| `connect_over_cdp` treo khi có tab cũ không trả lời | Lệnh đứng mãi | Session có timeout 15 s; tab mồ côi: `release --stale` |
| Trang SSR (vite dev, remix / react-router) hiện HTML trước khi React hydrate | Gõ / bấm không đổi state, Enter không thêm dòng → Fail giả | `ctx.wait_hydrated(frame)` đã lo, đừng chờ bằng sleep |
| Cú bấm ngay khi trang vừa hiện bị nuốt (handler chưa gắn) | Modal / tab không mở, lần chạy sau lại được | `ctx.click_until(locator, done)` đã lo |
| Rời trang có form dirty → hộp beforeunload "Leave site?" | Driver Playwright đứng (`No dialog is showing`), python 100% CPU không thoát | `ctx.accept_dialogs()` đầu steps đã lo; luôn chạy `run` kèm `timeout` |
| Locator khớp cả bản ẩn (popover / bản responsive) | `strict mode violation`, hoặc click chờ phần tử ẩn tới timeout | `.locator("visible=true").first` |
| Nhiều luồng `run` cùng task song song | Backend dev quá tải → `ETIMEDOUT`, list / search rỗng, Fail giả | `run` cảnh báo khi vượt `max_parallel_runs` (mặc định 2); lỗi mạng → chạy lại trước khi ghi Fail |
