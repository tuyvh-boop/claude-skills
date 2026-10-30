---
name: explain-by-analogy
description: Fallback dùng SAU KHI đã giải thích kỹ thuật (qua skill explain-code hoặc giải thích thông thường) mà người hỏi vẫn nói "chưa hiểu", "có ví dụ dễ hình dung hơn không", "giải thích như cho người không biết code". KHÔNG phải skill mặc định — không dùng ngay từ câu hỏi đầu tiên.
---

# Explain by Analogy

## ⚠️ Framework Reminder

Analogies illuminate only when they match the actual confusion point: [[framework_systematic_problem_solving]] —
- **Identify the exact gap first**: don't guess where understanding breaks. "Concept" vs "why use it" vs "how different from X" all need different analogies. Wrong analogy ≠ clearer
- **Use familiar experience, not nested complexity**: map code concept to everyday life (restaurant queue, bank line), not another technical domain. Analogy should reduce cognitive load, not add layers
- **Verify the analogy works**: after explaining via analogy, ask user to map one element back to the code. If they can't, the analogy didn't land; try different angle

## Đây KHÔNG phải skill mặc định

Chỉ kích hoạt khi **một trong hai** điều kiện xảy ra:

1. Đã có một lượt giải thích kỹ thuật trước đó (qua skill `explain-code` hoặc giải thích bình thường), và người hỏi phản hồi kiểu "chưa hiểu", "rối quá", "có cách nào dễ hình dung hơn không".
2. Người hỏi **chủ động** xin ví dụ đời thường / analogy / "giải thích như cho người không biết code".

Nếu câu hỏi đầu tiên của người dùng đã là hỏi về code/khái niệm kỹ thuật mà chưa từng được giải thích kỹ thuật lần nào → **không dùng skill này trước**, hãy giải thích kỹ thuật (hoặc gọi `explain-code`) trước. Analogy là lớp thứ hai, không phải lớp đầu tiên.

## Bước 1 — Xác định CHÍNH XÁC chỗ chưa hiểu

Đừng vội chọn analogy khi chưa biết rõ người hỏi bí ở đâu. Cùng một khái niệm có thể có nhiều điểm mắc khác nhau, và analogy trúng điểm mắc mới có tác dụng — analogy chung chung (định nghĩa lại khái niệm bằng ví dụ) thường không giải quyết được gì.

Ví dụ với "queue":
- Không hiểu **queue là gì** (cấu trúc dữ liệu FIFO) → analogy cần minh hoạ thứ tự vào-trước-ra-trước.
- Không hiểu **tại sao cần queue** (tại sao không xử lý trực tiếp luôn) → analogy cần minh hoạ vấn đề khi không có hàng đợi: quá tải, mất việc, tắc nghẽn.
- Không hiểu **queue khác gì stack** → analogy cần minh hoạ sự đối lập FIFO vs LIFO.

Cách xác định:
- Nếu ngữ cảnh hội thoại đã đủ rõ chỗ vướng (ví dụ người hỏi vừa nói "nhưng sao không xử lý luôn cho nhanh, cần gì phải xếp hàng") → suy ra trực tiếp, không cần hỏi lại.
- Nếu không rõ, hỏi lại ngắn gọn 1 câu, ví dụ: "Bạn đang thấy khó ở chỗ *khái niệm* hay ở chỗ *tại sao dùng nó*?"

Không đoán bừa rồi đưa ra analogy generic — thà hỏi lại 1 câu còn hơn giải thích lạc trọng tâm.

## Bước 2 — Chọn analogy từ trải nghiệm phổ biến

Nguyên tắc chọn:
- Ưu tiên tình huống đời sống hàng ngày ai cũng từng trải qua: quán ăn, ngân hàng, bưu điện, giao thông, nấu ăn, mua sắm, trường học...
- **Không** dùng analogy đòi hỏi hiểu một lĩnh vực kỹ thuật khác mới hiểu được lĩnh vực đang giải thích (ví dụ: đừng giải thích "cache" bằng "register CPU" — người không biết code sẽ không hiểu register là gì, tức là lấy khó giải thích khó).
- Analogy càng cụ thể, càng có nhân vật/hành động rõ ràng thì càng dễ hình dung hơn analogy trừu tượng.
- Một analogy tốt nhắm đúng vào điểm mắc đã xác định ở Bước 1, không cố giải thích toàn bộ khái niệm trong một lần.

## Bước 3 — Map ngược lại vào code

Đây là bước bắt buộc, không được bỏ qua. Mục tiêu cuối cùng là người hỏi hiểu được *code*, không phải chỉ hiểu analogy rồi dừng lại đó.

Sau khi kể analogy, luôn chốt lại bằng một đoạn map rõ ràng theo dạng:

> Trong ví dụ này, **[phần tử A trong analogy]** tương ứng với **[khái niệm/biến/hàm B trong code]**.

Map từng phần một, không gộp mập mờ. Nếu có nhiều thành phần, dùng danh sách gạch đầu dòng để map từng cặp.

## Ví dụ mẫu

### Case 1: Cache
**Điểm mắc giả định:** không hiểu *tại sao cache giúp nhanh hơn*, không phải cache là gì.

> Giống như khi nấu ăn, thay vì mỗi lần cần nước mắm lại chạy ra siêu thị mua, bạn để sẵn một chai trong bếp. Lần sau cần thì lấy ngay, không phải đi lại.

Map ngược:
- "Chạy ra siêu thị mua" ↔ gọi API / query database (chậm, tốn chi phí).
- "Chai nước mắm để sẵn trong bếp" ↔ dữ liệu được lưu trong cache.
- "Lấy ngay trong bếp" ↔ đọc từ cache (nhanh, không cần gọi lại nguồn gốc).
- Nếu nước mắm hết hạn phải đổ đi mua mới ↔ cache invalidation/expiry.

### Case 2: Async / Callback
**Điểm mắc giả định:** không hiểu *tại sao code không chạy tuần tự chờ xong mới làm tiếp*.

> Giống như khi bạn đặt đồ ăn online. Bạn không đứng im trước cửa chờ shipper — bạn đặt xong thì làm việc khác, khi đồ ăn đến (có chuông cửa) bạn mới ra nhận.

Map ngược:
- "Đặt đồ ăn online" ↔ gọi hàm bất đồng bộ (ví dụ `fetch()`).
- "Làm việc khác trong lúc chờ" ↔ chương trình không bị block, tiếp tục chạy các dòng code khác.
- "Chuông cửa báo đồ ăn đến" ↔ callback / promise resolve được gọi khi kết quả sẵn sàng.
- "Ra nhận đồ ăn khi có chuông" ↔ đoạn code trong callback được thực thi với dữ liệu trả về.

### Case 3: Queue
**Điểm mắc giả định:** không hiểu *tại sao cần hàng đợi thay vì xử lý trực tiếp ngay* (không phải "queue là gì").

> Giống như quán cà phê giờ cao điểm. Nếu ai gọi món cũng được pha ngay lập tức cùng lúc, nhân viên pha chế sẽ quá tải và làm hỏng hết. Thay vào đó, khách xếp hàng lấy số, nhân viên xử lý lần lượt theo đúng thứ tự — quán không sập, không ai bị bỏ sót.

Map ngược:
- "Nhiều khách gọi món cùng lúc" ↔ nhiều request/task đến cùng lúc.
- "Nhân viên pha chế" ↔ hệ thống/worker xử lý task, có giới hạn năng lực.
- "Hàng đợi lấy số" ↔ queue — nơi giữ tạm các task chưa được xử lý.
- "Xử lý lần lượt theo số thứ tự" ↔ worker lấy task ra khỏi queue theo đúng thứ tự (FIFO), tránh quá tải hệ thống.

## Lưu ý khi trình bày

- Ngắn gọn: 1 analogy + 1 đoạn map là đủ cho một điểm mắc. Đừng dùng nhiều analogy chồng lên nhau cho cùng một khái niệm trong một lượt trả lời.
- Sau khi map xong, có thể hỏi lại 1 câu ngắn để xác nhận đã rõ chưa (ví dụ: "Vậy đã rõ chỗ ... chưa, hay vẫn còn khúc mắc ở đâu?"), để có thể lặp lại Bước 1–3 nếu cần với một điểm mắc khác.
