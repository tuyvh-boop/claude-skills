# Sheet Schema — Sprint Planning

> File này là **nguồn sự thật duy nhất** về cấu trúc Google Sheet planning sprint của team.
> Đã được xác nhận qua khảo sát thật (autosheet MCP) ngày 2026-09-29.

## 1. Thông tin sheet gốc

- **Tên Google Sheet**: Sprint Planning (team OPTIS)
- **SHEET_ID**: `12bgqFPu2NPgFgbY7yAupljqBfLcS_-04b9Kl1UQdGhw`
- **Link sheet gốc**: https://docs.google.com/spreadsheets/d/12bgqFPu2NPgFgbY7yAupljqBfLcS_-04b9Kl1UQdGhw/edit
- **Chủ sở hữu / người có quyền sửa schema**: tuyvh@bsscommerce.com

## 2. Danh sách tab (sheet con) và mục đích

| Tên tab (chính xác) | Mục đích | Skill nào dùng tab này |
|---|---|---|
| `Sprint planning` (gid=1920271310) | Task từng thành viên trong sprint hiện tại, theo dõi effort/tiến độ | `sprint-jira-task-intake` |

## 3. Chi tiết cột theo từng tab quan trọng

### Tab: `Sprint planning`

- Header ở **hàng 4**.
- Dữ liệu được chia theo **section theo từng người** (không phải 1 bảng phẳng liên tục):
  - Mỗi section bắt đầu bằng 1 hàng chỉ có tên người ở cột A (vd `Tuy` ở hàng 42).
  - Các hàng tiếp theo là task của người đó.
  - Section kết thúc bằng 1 hàng `Others Tasks (Họp, support, v.v)`.
  - Ngay sau đó là section của người kế tiếp (vd `Huyền - Tester`).
  - **Không có hàng trống sẵn để chèn task mới** — phải insert 1 hàng mới ngay trước hàng "Others Tasks" của đúng section người đó.
- Cột:
  - `A` = **Task** — KHÔNG phải plain text. Đây là text kèm **hyperlink trực tiếp** (rich-text link, không phải công thức `HYPERLINK()`) trỏ tới `https://optis-app.atlassian.net/browse/<KEY>`. Title hiển thị dạng `"<KEY>: <tên task Jira>"`, vd `"OPOS-142: Rà soát toàn bộ giao diện và logic của các Option Type"`.
  - `B` = **Owner / Responsiblity** (header thật trên sheet ghi sai chính tả là "Responsiblity", giữ nguyên không sửa header) — tên nickname người phụ trách, đúng bằng tên section chứa nó (vd `Tuy`). **Đây là 1 cái tên thật, KHÔNG phải literal string "OWNER"** — "OWNER" chỉ là nhãn khái niệm dùng để mô tả ý nghĩa cột này trong tài liệu, không phải giá trị cần ghi vào ô.
  - `C` = Ai đang block — tên người/lý do đang block task, để trống nếu không có.
  - `D` = ET (estimate) — text có đơn vị, vd `2d`, `3d`, `1h`. Không phải số thuần.
  - `E` = Actual Effort — text có đơn vị, vd `1.5d`, `3h`. Không phải số thuần.
  - `F` = Start day — ngày, hiển thị `dd/MM/yyyy`, vd `21/09/2026`.
  - `G` = End day — ngày, hiển thị `dd/MM/yyyy`.
  - `H` = Duration — **cột công thức (formula)**, tự tính ra số ngày (vd `1`, `2`). KHÔNG tự gõ số tay vào cột này — nếu insert row không tự kế thừa formula từ hàng trên, để trống và báo user, không bịa số.
  - `I` = Hoàn thành — số, hiển thị dạng phần trăm (vd `0%`, `50%`, `100%`). Dữ liệu gốc không nhất quán: có ô lưu số nguyên `100` với custom format ra `%`, có ô lưu tỷ lệ `0.5` với format phần trăm chuẩn — khi ghi mới, ưu tiên theo format của các ô liền kề trong cùng section thay vì đoán 1 kiểu chung.

## 4. Quy tắc điền dữ liệu đặc thù

- **Format ngày tháng**: `dd/MM/yyyy`.
- **Cách đánh dấu status/tiến độ**: dùng cột `Hoàn thành` (%), KHÔNG có cột status dạng text riêng. Map từ Jira status → %: task chưa Done trên Jira thì để `0%` trừ khi user cho biết % cụ thể khác; không tự suy % từ status Jira (vd "In Development" không mặc định là 50%).
- **Ai được sửa cột nào**: chưa xác nhận rule cụ thể — nếu user không dặn gì khác, mặc định chỉ điền các cột được yêu cầu, các cột còn lại để trống thay vì đoán.
- **Cột A phải luôn có hyperlink Jira** — không ghi task dạng plain text thuần, nếu thiếu link agent sẽ tự tạo sai định dạng so với các hàng khác.
- **KHÔNG chèn task mới bằng cách ghi đè lên hàng "Others Tasks"** — luôn insert 1 hàng mới ngay phía trên hàng đó trong đúng section người phụ trách.

## 5. Cách xác thực / kết nối tới sheet

- **Phương thức chính (cron job tự động)**: Google Sheets API v4 qua Service Account, dùng script
  `/home/bss-group-3775/Shopify/sapo-worktrees/scripts/sheets_client.py` (thư viện `gspread` + `google-auth`).
  - Setup 1 lần: tạo GCP project + Service Account, tải JSON key, share sheet cho email service account (quyền Editor).
  - Runtime cần biến môi trường `GOOGLE_SHEETS_SA_KEY` trỏ tới file JSON key.
  - CLI: `find-row --key <KEY>`, `insert --owner <name> --key <KEY> --title "..." --percent <0-100>`,
    `update-percent --row <n> --percent <0-100>`, `list-sections`.
  - Lý do đổi từ autosheet: autosheet (MCP qua gptforwork.com) tính phí ~$25/tháng sau khi hết free trial;
    Sheets API + Service Account free vĩnh viễn cho khối lượng ghi 1 lần/ngày này.
- **Phương thức phụ (thao tác tay, hội thoại)**: Autosheet MCP (`mcp__autosheet__*`) vẫn dùng được cho việc
  đọc/sửa sheet trong lúc chat trực tiếp với user (hiểu ý định tự nhiên tốt hơn code cứng) — NHƯNG cần user tự
  upgrade billing trên gptforwork nếu hết free trial. Không dùng autosheet cho cron/job tự động vì tốn phí đều đặn.
- **Lưu ý quyền truy cập**: sheet đọc/ghi được miễn là email (autosheet) hoặc service account (Sheets API) đã được share quyền Editor.

## 6. Bài học từ lần chạy thật đầu tiên (2026-09-29, task OPOS-142)

- **Luôn khảo sát (read-only) trước khi ghi**: gọi agent với prompt yêu cầu chỉ đọc để xác định đúng tên tab, hàng header, range của section theo tên người, và hàng trống/hàng cần insert — không tự đoán từ schema tĩnh vì sheet có thể đã đổi cấu trúc.
- **Agent từng tự ý ghi sai dữ liệu khi insert row**: khi yêu cầu insert 1 hàng mới và kế thừa format từ hàng trên, agent đã tự động điền literal text `"OWNER"` vào cột B thay vì tên thật (`"Tuy"`) — khả năng do copy nhầm 1 placeholder/template ẩn trong ô nguồn. **Luôn đọc lại raw value của toàn bộ các ô vừa ghi (không chỉ tin báo cáo tóm tắt của agent) trước khi báo user là xong.**
- **Cột A không phải text đơn giản** — phải giữ hyperlink; nếu agent báo "đã ghi text" nhưng không nhắc tới link, phải hỏi lại rõ để xác nhận có giữ hyperlink hay không.
- **Thiếu dữ liệu (ET/Start day/End day/blocker) thì để trống và hỏi user**, không tự đoán ngày hoặc effort để "cho đủ cột".
