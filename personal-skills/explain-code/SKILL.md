---
name: explain-code
description: Kích hoạt khi user muốn hiểu 1 đoạn code / 1 function / 1 file / 1 PR làm gì và chạy như thế nào (vd "giải thích đoạn code này", "function này làm gì", "luồng chạy của PR này ra sao", "code mới join team đọc không hiểu"). CHỈ diễn giải logic để hiểu nhanh — KHÔNG tìm bug, không đánh giá chất lượng code (việc đó thuộc skill "review-code").
metadata:
  trigger: "user chỉ vào code hỏi 'cái này làm gì', 'how does this work', 'giải thích PR này', 'tại sao viết như thế'"
  model_hint: "main loop (Haiku/Sonnet) — giải thích code không cần phức tạp"
  keywords: ["explain", "understand", "code", "how", "why"]
---

# Explain Code

Diễn giải code cho reviewer / dev mới join team hiểu nhanh "code này làm gì, chạy như thế nào" — không phải audit tìm bug.

⚠️ **Framework & Feedback Reminders:**
- Áp dụng [[framework_systematic_problem_solving]] khi giải thích: **không assume lý do tại sao code viết như vậy** — nếu có thay thế tối ưu hơn rõ ràng, báo rõ (không im lặng vì "không đụng lên an toàn").
- Khi phát hiện tối ưu hóa mid-explanation: [[feedback_explain_code_flag_optimization]] — surface concrete better alternatives, don't silently accept.

## Nguyên tắc cốt lõi

**Chỉ giải thích Ý NGHĨA và LÝ DO** — phần đọc code không tự suy ra được. KHÔNG diễn giải lại syntax hiển nhiên (vd không cần nói "dòng này khai báo biến x", "vòng lặp này chạy qua từng phần tử của mảng"). Nếu một dòng code tự nó đã rõ ràng, đừng nhắc lại — tóm gọn nó vào bước lớn hơn.

## Quy trình

### 1. Tóm tắt tổng thể (1-2 câu, luôn đặt đầu tiên)

Trước khi vào chi tiết, nêu ngay: đoạn code/function/file/PR này tồn tại để làm gì, giải quyết vấn đề gì. Đây là câu trả lời cho "nếu chỉ đọc 1 câu thì đọc câu nào" — người đọc phải nắm được bức tranh lớn trước khi thấy từng bước.

### 2. Diễn giải theo luồng thực thi thực tế

Đi theo **thứ tự chạy thực sự**, không phải thứ tự dòng trong file — hai thứ này khác nhau khi có nhánh điều kiện, callback, async/await, event handler, hoặc gọi hàm được định nghĩa ở nơi khác trong file. Với mỗi bước lớn, nêu rõ:

- **Input**: dữ liệu đi vào bước này là gì, từ đâu tới.
- **Biến đổi**: bước này làm gì với dữ liệu (mức ý nghĩa, không mức syntax).
- **Output**: kết quả bước này đi đâu tiếp — trả về, truyền vào bước sau, hay dừng ở đây.

Nếu code có nhiều nhánh (if/else, try/catch, switch, early return), lần theo TỪNG nhánh sẽ dẫn đến đâu — đừng chỉ giải thích nhánh happy path rồi bỏ qua phần còn lại.

### 3. Nêu bật điểm rẽ nhánh, edge case, side-effect

Đây là phần dev mới **dễ bỏ sót nhất** khi tự đọc code, nên phải chủ động chỉ ra, không đợi được hỏi:

- Điều kiện rẽ nhánh quan trọng (đặc biệt nếu logic không hiển nhiên tại sao lại rẽ như vậy).
- Edge case được xử lý (input rỗng/null, giá trị biên, lỗi mạng, timeout, race condition...).
- Side-effect: gọi API bên ngoài, ghi/đọc DB, ghi file, mutate state ngoài scope hàm (global, props, object được truyền vào), throw/emit event, log, gửi message queue.
- Nếu có side-effect nhưng không thấy code xử lý lỗi tương ứng, nói rõ điều đó (chỉ nêu quan sát, không phán xét "đây là bug" — việc đánh giá bug thuộc skill review-code).

### 4. Sơ đồ mermaid — chỉ khi thực sự cần

Chỉ vẽ khi luồng đủ phức tạp: **hơn 4-5 bước** HOẶC trải trên **nhiều file**. Với luồng ngắn/đơn giản, văn bản là đủ, đừng vẽ cho có.

- Luồng có thứ tự thời gian rõ ràng, nhiều bên tương tác (client gọi service gọi DB...) → dùng `sequenceDiagram`.
- Luồng có rẽ nhánh, điều kiện, nhiều đường đi → dùng `flowchart`.

Sơ đồ chỉ nên chứa các bước chính và nhánh rẽ quan trọng — không nhét toàn bộ chi tiết implementation vào sơ đồ, giữ nó dễ nhìn.

### 5. Nếu người hỏi vẫn chưa hiểu

Nếu đã giải thích theo cách trên (tóm tắt → luồng chạy → nhánh/edge case/side-effect, có sơ đồ nếu cần) mà người hỏi vẫn không hiểu, gợi ý chuyển sang skill **explain-by-analogy** để giải thích lại bằng ví dụ đời thường, dễ hình dung hơn.

### 6. Nếu trong lúc giải thích lộ ra 1 cách làm tối ưu hơn rõ ràng

Đây KHÔNG phải chủ động đi tìm bug/review — chỉ áp dụng khi đang diễn giải luồng mà **tự nhiên nhận ra** đoạn code đang đi vòng (vd: gọi qua 1 hàm trung gian rồi tính dư/discard phần lớn kết quả, lặp lại logic đã có sẵn ở chỗ khác, tách 2 bước có thể gộp 1) và có 1 hướng thay thế **cụ thể, so sánh được** — không phải cảm tính chung chung "code này chưa đẹp".

Khi đó, đừng mặc định lý do "không đụng vào cho an toàn" là đủ để im lặng bỏ qua — chủ động báo cho người hỏi biết, trình bày theo đúng thứ tự:

1. **Cách hiện tại làm gì** — tóm tắt ngắn, trỏ đúng file/dòng.
2. **Cách tối ưu hơn cụ thể là gì** — nêu rõ thay đổi (gộp bước, tách hàm, bỏ phần tính dư...), có thể kèm đoạn code ngắn minh hoạ.
3. **Vì sao tối ưu hơn** — nêu rõ cái được (ít bước dư, rõ ý hơn, ít chỗ phải trace...) VÀ cái đánh đổi/rủi ro nếu áp dụng (vd phải đụng vào file đang phục vụ luồng khác đang chạy thật, tăng số hàm phải maintain...) — để người hỏi tự cân nhắc, không tự ý kết luận "nên sửa" thay họ.
4. Luôn chốt lại bằng câu hỏi mở, hỏi người dùng có muốn áp dụng hướng tối ưu hơn không — KHÔNG tự sửa code khi chưa được xác nhận (việc sửa code thật sự vẫn thuộc phạm vi review-code/fix, không phải explain-code).

Nếu không có hướng thay thế cụ thể, so sánh được — chỉ là cảm giác chung chung "code hơi rối" — thì không cần mục này, giữ đúng ranh giới ở "Việc KHÔNG làm" bên dưới.

## Việc KHÔNG làm

- Không chủ động rà toàn bộ code để tìm bug/tối ưu (đó vẫn là việc của skill "review-code") — mục 6 ở trên CHỈ áp dụng khi phát hiện tình cờ ngay trong đoạn đang giải thích, có hướng thay thế cụ thể so sánh được, không phải đi quét chủ động.
- Không tự ý sửa code hoặc kết luận "nên sửa" thay người dùng — chỉ trình bày 2 hướng (hiện tại vs tối ưu hơn) rồi hỏi, để người dùng quyết định.
- Không đánh giá chất lượng code chung chung ("code này tốt/xấu") ngoài phạm vi so sánh cụ thể ở mục 6.
- Không diễn giải lại từng dòng code kiểu "dịch syntax sang tiếng Việt".
- Không lạm dụng sơ đồ mermaid cho luồng đơn giản.

## Lỗi hay gặp

- **Diễn giải syntax thay vì ý nghĩa**: "Dòng này declare biến x = 5" thay vì "x là counter để track..." → Fix: bỏ qua syntax rõ ràng, tóm gọn vào ý nghĩa logic.
- **Quên diễn giải nhánh/ edge case**: Chỉ nói happy path, bỏ qua else/error handling. → Fix: mỗi nhánh điều kiện phải lần theo để xem đi đâu.
- **Không nêu input/output rõ ràng**: Người đọc không biết dữ liệu từ đâu, đi đâu. → Fix: bắt buộc nêu input/output mỗi bước lớn.
- **Chủ động tìm bug khi chỉ cần giải thích**: Giải thích xong rồi đề xuất sửa code. → Fix: mục 6 "tối ưu cơ hội" chỉ áp dụng khi phát hiện **tình cờ**, có **cách so sánh cụ thể** — không chủ động đi tìm bug (dùng review-code cho việc đó).
- **Tóm tắt tổng thể quá muộn hoặc quên**: Vào chi tiết mà không nêu được "cái này làm gì". → Fix: tóm tắt 1-2 câu luôn **đầu tiên** trước chi tiết.
