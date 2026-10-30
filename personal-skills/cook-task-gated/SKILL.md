---
name: cook-task-gated
description: Điều phối trọn luồng 1 task Jira trong workspace sapo/comp/swatch-worktrees, TỰ PHÂN LOẠI độ phức tạp task (Tiny/Standard/Complex, dựa vào field Jira "Change Size" hoặc hỏi user nếu field trống) rồi rẽ nhánh độ chặt của quy trình tương ứng — task Tiny đi luồng rút gọn (gộp checkpoint, tự tạo MR + comment Jira, dev chỉ cần bấm merge), task Standard đi luồng mặc định đầy đủ (3 checkpoint: sau khi quét Jira, sau khi có plan đã review, sau khi code+test xong; chỉ push git), task Complex thêm bước audit AC trước khi lên plan và tách phase có checkpoint riêng nếu plan chia nhiều phase độc lập. Tự chuẩn bị worktree cho task (tái dùng nếu đã có, tạo mới qua scripts/new-task.sh nếu chưa), cảnh báo nếu docker của worktree khác đang chạy (port dùng chung, không chạy song song được). Dùng khi user nói "giao task X, chạy đúng quy trình", "cook task X có duyệt plan rồi mới code", hoặc mô tả luồng quét Jira→duyệt→plan→duyệt→code→duyệt→push cho 1 worktree. KHÁC cook-feature (không có mốc dừng duyệt plan riêng, không tự quản lý worktree, không phân loại độ phức tạp) — dùng cook-task-gated khi cần nhiều checkpoint rõ ràng và đang làm việc trong các workspace *-worktrees.
metadata:
  trigger: "user giao mã Jira kèm yêu cầu chạy quy trình quét-jira→duyệt→plan→review→duyệt→code→review→test→duyệt→push trong worktree"
  model_hint: "main loop (Sonnet/Opus) — điều phối nhiều skill, cần giữ context liên tục giữa các bước, phân loại route, và các checkpoint"
  keywords: ["cook", "task", "worktree", "plan", "review", "duyệt", "approval", "push", "jira", "intake", "route", "complexity", "tiny", "complex"]
---

# Cook Task (Gated) — sapo/comp/swatch-worktrees

Skill **điều phối**: nối các skill sẵn có (`jira-core`, `create-plan`, `review-plan`, `fix-plan`, `execute-plan`, `review-code`, `review-code-after-fix`, `git-flow`) thành 1 luồng cho **1 task trong workspace *-worktrees**, **tự phân loại độ phức tạp task** (xem Phase Route) rồi chèn đúng checkpoint theo route đó — mặc định (Standard) có **3 checkpoint xác nhận**: (0) ngay sau khi đọc xong Jira — TRƯỚC khi bắt tay vào plan; (1) sau khi có plan đã review; (2) sau khi code+test xong. **Không re-implement** logic các skill đó — chỉ gọi đúng thứ tự.

> ⚠️ Chưa có kết nối Mattermost trong môi trường hiện tại. Bước "gửi thông báo" / "báo cáo cho người dùng" ở đây = tóm tắt rõ ràng ngay trong chat + dùng `AskUserQuestion` để chờ duyệt. Khi nào có Mattermost webhook/bot, thay bước này bằng gửi/nhận qua đó — xem mục "Mở rộng Mattermost sau này" ở cuối.

## ⚠️ Framework Reminder

Task orchestration requires measuring at every gate, not assuming: [[framework_systematic_problem_solving]] —
- **Route classification is data-driven**: "Tiny/Standard/Complex" must be measured from AC depth, not gut feeling. "Change Size" field + AC complexity both matter; different routing = different checkpoint rigor
- **Checkpoints are verification gates**: don't skip them. Each checkpoint (after Jira, after plan review, after code review) catches issues early before wasting time on wrong direction
- **Cross-layer impact**: task touches api/cms/tae repos; fix in one may break others (schema, API contract, feature interaction). Early Jira read + plan review gates catch these before implementation wastes days

## Nguyên tắc

- **3 checkpoint cứng, không bỏ qua**: (0) ngay sau khi quét xong Jira (trước khi tạo plan); (1) sau khi plan đã qua vòng review-plan sạch; (2) sau khi code đã qua review-code-after-fix sạch + test chạy xong. Không tự ý sang phase kế tiếp nếu chưa nhận "yes" rõ ràng từ user — **đặc biệt không tự nhảy vào code-recon/viết plan ngay khi vừa nhận task**, phải báo cáo Jira trước.
- **Route Standard/Complex: không tạo PR, không comment Jira** trong skill này — phạm vi được giao chỉ dừng ở "push git". Nếu user muốn thêm PR, dùng `te-dev-create-pr` sau, ngoài phạm vi skill này. **Route Tiny là ngoại lệ duy nhất** — tự tạo PR + comment Jira TH1 sau khi push, xem "Route Tiny" ở Phase Route và bước 3 của Phase C.
- **Docker chỉ chạy được 1 task tại 1 thời điểm** trên máy local (port cố định dùng chung — xem `CLAUDE.md` gốc của workspace). Skill này **không tự tắt docker của worktree khác** — chỉ cảnh báo và để user quyết định.
- Mỗi worktree = 3 repo (api/cms/tae) theo convention `scripts/new-task.sh`. Không tự tạo cấu trúc khác.

## Bước 0 — Input & chuẩn bị worktree

1. Cần có **mã Jira** (vd `OPOS-140`). Thiếu thì hỏi user trước khi làm gì khác.
2. Kiểm tra `worktrees/<MÃ>/` đã tồn tại chưa (workspace root: thư mục chứa `scripts/`, `worktrees/`, `.git-src/` — thường là `sapo-worktrees/`, `comp-worktrees/`, hoặc `swatch-worktrees/` tuỳ task thuộc app nào):
   - **Đã có** → tái dùng, không chạy lại `new-task.sh`. Kiểm tra `git status --porcelain` ở cả 3 repo con — nếu có thay đổi chưa commit từ trước, báo cho user biết đang có WIP cũ trong worktree này trước khi tiếp tục (không tự xoá/stash).
   - **Chưa có** → chạy `./scripts/new-task.sh <MÃ>` để tạo worktree + branch `feature/<MÃ>` + `docs/<MÃ>-notes.md`.
3. Kiểm tra xung đột docker: liệt kê các `worktrees/*/docker` khác, với mỗi cái chạy `docker compose -f <path>/docker-compose.yaml ps --status running` (hoặc tương đương) để xem có task nào khác đang chạy container không.
   - Có task khác đang chạy → **chỉ cảnh báo**, ghi chú lại để nhắc lại ở bước test (phase B): user cần tắt task kia trước, hoặc dùng testsite remote (`/te-dev-new-testsite`) để test thật song song. Không tự `docker compose down` cho worktree của người khác.
4. Mở `docs/<MÃ>-notes.md`, điền phần Intent ngắn nếu còn trống (link Jira/mô tả).

## Phase Intake — Quét Jira (trước checkpoint 0, TRƯỚC khi đụng plan/code)

**Bắt buộc chạy bước này ngay sau Bước 0, TRƯỚC Phase A.** Mục đích: cho user thấy rõ task này là gì, đang ở trạng thái nào, có gì cần lưu ý (comment, block, quyết định trước đó) — trước khi tốn công lên plan.

1. Dùng **skill `jira-core`** (helper `jira_client.py get <MÃ>`) lấy: summary, status hiện tại (vd "In Development", "Ready for Test"...), priority, assignee, parent (nếu có), description/AC.
2. Lấy **toàn bộ comment** của issue (`jira_client.py comments <MÃ>` hoặc tương đương trong jira-core) — đọc lướt qua, note lại:
   - Comment nào có quyết định/thay đổi scope so với mô tả gốc.
   - Comment nào là chặn/blocker (vd "chờ confirm design", "revert vì lỗi X") — nếu có, **nêu rõ** trong báo cáo, đừng lờ đi.
   - Comment hệ thống (TH1/TH2/TH3 tự động từ `te-dev-*`) → tóm tắt ngắn (đã gửi review lúc nào, đã merge test chưa...), không cần trích nguyên văn.
3. Đối chiếu nhanh với `docs/<MÃ>-notes.md` và tình trạng worktree đã kiểm tra ở Bước 0 (có WIP cũ không) — nếu status Jira đã là "Done"/"Ready for Test" mà worktree vẫn có việc dở, hoặc ngược lại status còn "To Do" mà code đã có nhiều thay đổi, **nêu rõ sự lệch pha này** trong báo cáo (dấu hiệu task có thể đã bị người khác động vào, hoặc report nhầm task).
4. **Checkpoint 0 — bắt buộc dừng, KHÔNG được tự ý chạy `create-plan` tiếp.** Báo cáo trong chat gồm: summary + AC/description, status hiện tại, điểm đáng chú ý từ comment (đặc biệt blocker/thay đổi scope), tình trạng worktree (từ Bước 0). Dùng `AskUserQuestion` hỏi: *"Đây có đúng task bạn muốn làm không, có cần lưu ý gì từ comment trước khi lên plan?"* với lựa chọn Đúng rồi, lên plan / Có điểm cần làm rõ trước / Dừng lại.
   - "Có điểm cần làm rõ trước" → hỏi cụ thể, có thể cần đọc thêm comment/Jira link con trỏ tới trước khi tiếp tục — không tự suy diễn.
   - "Dừng lại" → kết thúc ở đây.

## Phase Route — Phân loại độ phức tạp (ngay sau checkpoint 0, quyết định rẽ nhánh cho toàn bộ phần còn lại)

**Bắt buộc chạy trước khi chạm vào Phase A**, kể cả khi task "nhìn có vẻ" rất nhỏ — không tự quyết route theo cảm tính.

1. Đọc field **Change Size** của issue qua `jira-core` (field project-scoped — tra đúng `customfield_x` theo project trong `reference/api-map.md` của jira-core, vd OPOS=10293/OPCS=10294; dùng `get <MÃ> --fields customfield_x` hoặc `raw GET` nếu chưa có alias trong `config.yml`). Giá trị thường gặp: `Tiny` / `Medium` / `Major`.
2. Field có giá trị → map trực tiếp: `Tiny` → **Route Tiny**, `Medium` → **Route Standard**, `Major` → **Route Complex**. Không hỏi lại user khi đã có field rõ ràng.
3. Field trống/không đọc được → hỏi user ĐÚNG 1 câu bằng `AskUserQuestion` (gộp vào ngay sau checkpoint 0, không tính là 1 checkpoint riêng), 3 lựa chọn kèm mô tả ngắn theo bảng dưới. Không tự đoán route khi thiếu field — đoán sai route ảnh hưởng toàn bộ phần còn lại của luồng.

| Route | Khi nào | Khác biệt so với luồng mặc định (Phase A/B/C dưới) |
|---|---|---|
| **Tiny** | Fix nhỏ, đụng 1 vài file, không đổi logic nghiệp vụ, rủi ro thấp, không cần bàn giải pháp | Gộp checkpoint 0 + duyệt-plan thành 1 lượt; bỏ `create-plan/review-plan/fix-plan` — viết plan rút gọn 3-5 dòng ngay trong chat; sau Phase B xong tự tạo MR + comment Jira TH1 trước khi hỏi checkpoint cuối (mở rộng phạm vi so với mặc định) |
| **Standard** | Đã rõ giải pháp (nâng cấp version, port tính năng, task không cần research/đánh giá) | Giữ NGUYÊN luồng mặc định của Phase A/B/C bên dưới — không đổi gì |
| **Complex** | Cần research/đánh giá, nhiều rủi ro, ảnh hưởng nhiều module/nhiều phase | Thêm bước audit AC ngay đầu Phase A (mục riêng bên dưới); nếu plan thực sự chia nhiều phase độc lập, mỗi phase lặp lại cặp checkpoint Phase A+B riêng thay vì duyệt 1 lần cho toàn bộ task |

> Workspace này chưa có skill `audit-requirement`/`discover-solutions` riêng — bước audit AC ở Route Complex dưới đây là bản rút gọn làm trực tiếp trong skill này, không phải gọi skill ngoài. Nếu sau này xây `audit-requirement`, thay bước đó bằng gọi skill đó thay vì tự làm tay.

### Route Complex — audit AC trước khi vào Phase A

Trước khi chạy `create-plan`, đọc lại description/AC + toàn bộ comment đã lấy ở Phase Intake, tự trả lời 3 câu:
- AC có mâu thuẫn với chính nó không (2 đoạn mô tả hành vi khác nhau cho cùng 1 case)?
- Có case quan trọng mà AC không nhắc tới (edge case, lỗi, quyền hạn, hiệu năng) không?
- AC có đủ cụ thể để sau này tạo acceptance test không, hay còn mơ hồ (vd "xử lý hợp lý", "tối ưu UX")?

Có bất kỳ điểm nghi vấn nào → liệt kê rõ, hỏi user xác nhận/làm rõ TRƯỚC khi tạo plan — không tự suy diễn AC để lấp chỗ trống (giữ đúng nguyên tắc xuyên suốt skill này). Coi đây là checkpoint 0.5, chèn giữa checkpoint 0 và Phase A, chỉ áp dụng cho Route Complex.

### Route Tiny — rút gọn Phase A/B/C

- **Phase A**: thay vì `create-plan/review-plan/fix-plan`, viết trực tiếp trong chat 3-5 dòng gạch đầu dòng: file sẽ đụng, thay đổi gì, rủi ro gì (nếu có) — không tạo file `<MÃ>-plan.md` riêng.
- **Checkpoint**: GỘP checkpoint 0 (Phase Intake) và duyệt plan rút gọn thành **1 lượt `AskUserQuestion` duy nhất**, ngay khi vừa xác định route là Tiny — không tách 2 lượt như Standard/Complex.
- **Phase B**: giữ NGUYÊN `execute-plan`/`review-code`/`review-code-after-fix`/chạy test như luồng mặc định — KHÔNG rút gọn phần code/test, chỉ rút gọn phần plan. Chất lượng code không giảm chỉ vì task nhỏ.
- **Phase C**: sau khi push, **tự chạy tiếp** `te-dev-create-pr` (tạo MR) rồi comment Jira theo đúng mẫu **TH1** trong `jira-core` (`reference/comment-templates.md`) — mở rộng phạm vi so với Standard/Complex (vốn chỉ dừng ở push, xem "Nguyên tắc" phía trên). Checkpoint cuối cùng vẫn giữ, nhưng đổi nội dung hỏi thành: *"Code+test+MR+comment Jira đã xong, bạn chỉ cần vào GitLab bấm merge — có cần mình làm gì thêm không?"*

## Phase A — Plan (trước checkpoint 1, chỉ chạy sau khi checkpoint 0 = Đúng rồi)

> Route **Tiny** không chạy Phase A như mô tả dưới đây — xem "Route Tiny" ở trên. Route **Complex** chạy đủ các bước dưới đây NHƯNG sau khi đã qua audit AC ở trên. Route **Standard** chạy nguyên văn các bước dưới đây.

Chạy trong worktree vừa chuẩn bị (cd vào `worktrees/<MÃ>/<repo liên quan>` khi cần thao tác code-recon, nhưng việc gọi skill thì gọi ở main loop bình thường).

1. **Skill `create-plan`** với mã Jira → ra `<MÃ>-plan.md`.
2. **Skill `review-plan`** trên plan vừa tạo → lấy findings.
3. Finding nghiêm trọng (critical/major) → **Skill `fix-plan`** áp đúng findings đó vào plan.
4. **Chạy lại `review-plan`** để xác nhận đã sạch.
5. Lặp bước 3–4 tối đa **2 vòng**. Còn finding sau 2 vòng (thường là finding dạng "chưa đủ thông tin nguồn", không tự fix được) → liệt kê rõ trong báo cáo ở bước 6, không cố fix ảo.
6. **Checkpoint 1 — bắt buộc dừng.** Tóm tắt trong chat: nội dung chính của plan (phạm vi, surface, file sẽ đụng), kết quả review-plan (pass hay còn gì tồn đọng), rồi dùng `AskUserQuestion` hỏi duyệt dạng: *"Plan đã sẵn sàng, bạn duyệt để bắt đầu code không?"* với lựa chọn Duyệt / Sửa thêm / Dừng lại.
   - "Sửa thêm" → hỏi cụ thể cần sửa gì, quay lại bước phù hợp trong Phase A (không tự đoán ý).
   - "Dừng lại" → kết thúc skill ở đây, không chạm vào code.
7. **Log quality event** (ngay sau khi có verdict, không chờ xong cả task):
   ```bash
   python3 ~/Shopify/skill/personal-workspace/dev-journal/scripts/log-quality-event.py \
     --task <MÃ> --checkpoint plan \
     --outcome approved_clean   # nếu Duyệt ngay, không cần vòng "Sửa thêm" nào
     # hoặc --outcome approved_after_fix --category "<1-2 từ, vd 'AC-gap'>" \
     #      --pattern "<tổng quát hoá lỗi, áp dụng được cho task khác>" nếu có ít nhất 1 vòng "Sửa thêm"
     # hoặc --outcome rejected --category "<lý do>" --pattern "<tổng quát hoá>" nếu "Dừng lại"
   ```
   Đây là dữ liệu thô cho `quality-report.py` (xem skill `recap-task-learnings`/dev-journal) — không phải bước tuỳ chọn, bỏ qua sẽ làm số liệu sai lệch. `--pattern` khi outcome khác `approved_clean` là **bắt buộc** (script tự chặn nếu thiếu) — đây chính là bước tự sinh "known issue" để lần adversarial-verify sau (bước 7 Phase B) tự kiểm tra có tái diễn không, không chỉ ghi chú riêng cho task này rồi quên.

> Lưu ý: checkpoint này đánh số tiếp theo sau checkpoint 0 (Phase Intake) — **không phải checkpoint đầu tiên của cả luồng**.

## Phase B — Code (chỉ chạy sau khi checkpoint 1 = Duyệt)

1. **Skill `execute-plan`** theo đúng `<MÃ>-plan.md` vừa duyệt (TDD, đối chiếu AC/plan/convention liên tục như skill này đã định nghĩa).
2. **Skill `review-code`** trên diff vừa code (dispatches reviewer subagent, checklist theo app).
3. Có finding → fix trực tiếp (áp đúng finding, không refactor lan ra ngoài phạm vi).
4. **Skill `review-code-after-fix`** để xác nhận các finding đã fix đúng, không phát sinh thêm vấn đề.
5. Lặp bước 3–4 tối đa **2 vòng**; còn gì tồn đọng sau đó (vd finding mức thấp, cần quyết định sản phẩm) → để nguyên, nêu rõ ở bước báo cáo.
6. **Chạy test**: dùng đúng lệnh test của từng repo con đang bị đụng tới (đọc `package.json`/README repo đó — KHÔNG đoán framework khác nếu project chưa có test). Nếu bước 0.3 đã cảnh báo có docker task khác đang chạy và test cần docker (api/cms cần DB/redis) → nhắc lại rõ ràng trong báo cáo thay vì âm thầm chạy test có thể fail do port/data sai.
7. **Adversarial verify — độc lập với `review-code`/`review-code-after-fix` ở trên.** `review-code` ở bước 2 là 1 reviewer duy nhất theo checklist chất lượng code; bước này khác hẳn mục đích: tìm xem diff có thực sự thoả AC/plan không, bằng cách CỐ phản bác thay vì xác nhận.

   **7a. Nạp known-issues trước khi gọi agent** (đóng vòng lặp — không bắt lại đúng lỗi cũ từ đầu):
   ```bash
   python3 ~/Shopify/skill/personal-workspace/dev-journal/scripts/get-known-issues.py --app <ten-app>
   ```
   Dán output này vào đầu prompt của cả 2 agent bên dưới (mục "Lỗi đã từng gặp"), kể cả khi output là "(chưa có known issue nào)" — để agent biết đã check mục này.

   **7b. Model routing theo vai trò** (vai "cố phản bác" không cần model mạnh như vai viết code): gọi `Agent(model: "haiku")` cho cả 2 lượt đầu. Agent nào tự báo "không chắc"/kết luận mơ hồ (không trích được bằng chứng cụ thể dù đã cố) → gọi lại ĐÚNG agent đó 1 lần với `model: "sonnet"` để phân xử dứt điểm, không âm thầm chấp nhận kết luận mơ hồ của haiku.

   Dùng `Agent` tool, gọi **2 agent độc lập song song** (1 message, nhiều tool call), context sạch (không thấy lịch sử phiên này, chỉ nhận đúng: known-issues (7a), nội dung AC từ Jira, `<MÃ>-plan.md`, và diff vừa code):
   ```
   Prompt mỗi agent PHẢI kèm **đường dẫn tuyệt đối của đúng worktree** (vd
   `/home/.../sapo-worktrees/worktrees/<MÃ>/<repo>`) và yêu cầu agent tự
   `cd` vào đó + in `pwd`/`git rev-parse --show-toplevel` TRƯỚC khi phân
   tích — tránh lặp lỗi đã gặp thật (1 agent từng tự ý phân tích nhầm
   worktree khác, ra kết luận sai hoàn toàn vì không được ép xác nhận vị
   trí trước):
   ```
   Prompt mỗi agent: "Lỗi đã từng gặp ở task trước (kiểm tra xem có tái diễn
   không): <dán output 7a>. Worktree cần soi: <path tuyệt đối>. Trước tiên,
   cd vào đúng path này và in `pwd` + `git rev-parse --show-toplevel` để xác
   nhận — đừng dùng cwd mặc định của bạn. Đây là AC gốc: <dán AC>. Đây là
   plan đã duyệt: <dán plan>. Đây là diff đã code: <dán diff>. Hãy CỐ TÌNH
   tìm ra lý do code này KHÔNG thoả đúng AC hoặc lệch khỏi plan — mặc định
   nghi ngờ, không mặc định tin. Kiểm tra RIÊNG xem có khớp 1 trong các
   known-issues ở trên không — nếu khớp, nêu rõ. MỌI kết luận dạng 'X không
   được đọc/dùng ở đâu' hoặc 'không tồn tại' PHẢI kèm đúng lệnh grep/Read đã
   chạy và output thật của nó — không được kết luận suông chỉ từ trí nhớ hay
   suy đoán. Nếu thật sự không tìm ra vấn đề gì sau khi đã cố gắng, trả lời
   KHÔNG CÓ VẤN ĐỀ kèm lý do vì sao đã xem xét đủ kỹ — nếu không đủ tự tin,
   NÓI RÕ 'không chắc' thay vì cố kết luận. Nếu có vấn đề, nêu cụ thể dòng/
   file nào, AC nào bị hở, kèm bằng chứng (lệnh đã chạy + output).
   NGÂN SÁCH TOOL-CALL: tối đa khoảng 6 lượt gọi tool. Nếu tới giới hạn mà
   chưa đủ bằng chứng để kết luận, DỪNG và báo 'cần thêm ngân sách/thông tin
   để kết luận' thay vì cố kết luận ẩu hoặc âm thầm dùng thêm nhiều lượt.
   GIỚI HẠN PHẠM VI (để kiểm soát token): chỉ đọc file nằm trong diff, cộng
   tối đa vài file liền kề thực sự cần để hiểu 1 dòng gọi/import cụ thể —
   KHÔNG tự ý khảo sát rộng toàn repo, KHÔNG tự spawn thêm sub-agent nào
   khác (không có quyền dùng Agent tool trong lượt này). Nếu thấy cần đào
   sâu hơn phạm vi trên mới kết luận được, DỪNG và nói rõ 'cần xem thêm
   <file/thứ gì> mới kết luận được' thay vì tự ý mở rộng điều tra."
   ```
   - Có **ít nhất 1/2 agent** nêu được vấn đề cụ thể (không phải suy diễn mơ hồ) → coi là finding **nghi vấn**, KHÔNG tự tin ngay là thật.
   - **Bắt buộc**: trước khi fix theo finding, chính mình (main loop) tự chạy lại đúng bằng chứng agent đưa ra (Read/grep file thật, đúng dòng agent trích) để xác nhận — không fix mù theo lời agent. Đã có lần thật 2/3 cảnh báo của 1 lượt chạy là sai (1 do agent lạc worktree, 1 do agent grep thiếu) — nếu không tự verify sẽ phí công sửa thứ không có thật, hoặc tệ hơn là sửa sai hướng.
   - Finding verify ra THẬT → quay lại bước 3 để fix, rồi chạy lại từ bước 4.
   - Finding verify ra SAI (agent hallucinate/nhầm chỗ) → ghi rõ trong báo cáo checkpoint là "agent báo X nhưng đã tự kiểm tra, không đúng vì Y" — đừng lặng lẽ bỏ qua, user cần biết tỷ lệ báo sai để còn đánh giá độ tin cậy của bước này.
   - Cả 2 đều "KHÔNG CÓ VẤN ĐỀ" (hoặc sau verify đều là false positive) → qua checkpoint 2, nhưng vẫn **trình bày cả 2 verdict trong báo cáo checkpoint** (không chỉ nói "đã verify xong") — user cần thấy agent nào đã xác nhận, không phải chỉ tin lời tóm tắt.
   - Đừng chạy bước này cho route Tiny nếu Phase B của Tiny đã rút gọn checkpoint — vẫn giữ nguyên review-code/test như note ở Route Tiny, nhưng 2-agent verify này là optional cho Tiny (có thể bỏ nếu task thực sự nhỏ, risk thấp).
8. **Checkpoint 2 — bắt buộc dừng.** Báo cáo trong chat: tóm tắt thay đổi đã code, kết quả review-code-after-fix, kết quả 2 agent adversarial-verify (bước 7), kết quả test (pass/fail, có gì skip vì docker conflict). Dùng `AskUserQuestion` hỏi duyệt: *"Code + test xong, bạn duyệt để push lên git không?"* với lựa chọn Duyệt / Sửa thêm / Dừng lại.
9. **Log quality event** (cùng cách gọi như checkpoint 1 ở Phase A, đổi `--checkpoint code`):
   ```bash
   python3 ~/Shopify/skill/personal-workspace/dev-journal/scripts/log-quality-event.py \
     --task <MÃ> --checkpoint code --outcome <approved_clean|approved_after_fix|rejected> \
     [--category "<vd 'adversarial-verify-caught', 'review-code-caught', 'test-fail'>"] \
     [--pattern "<tổng quát hoá lỗi nếu outcome khác approved_clean — bắt buộc, script tự chặn nếu thiếu>"]
   ```
   Nếu adversarial-verify (bước 7) là nơi phát hiện ra vấn đề (chứ không phải review-code hay user), dùng category `adversarial-verify-caught` — đây chính là số liệu cho biết lớp verify độc lập này có đang thực sự bắt được gì hay chỉ tốn thêm lượt gọi agent vô ích. `--pattern` viết sao để **áp dụng được cho task/app khác**, không chỉ mô tả đúng bug của task này — nó sẽ được bước 7a của lần sau đọc lại nguyên văn.

## Phase C — Push (chỉ chạy sau khi checkpoint 2 = Duyệt)

> Route **Standard**/**Complex**: chạy đúng 2 bước dưới, dừng lại sau khi push. Route **Tiny**: chạy 2 bước dưới RỒI tiếp tục bước 3 (tự tạo MR + comment Jira) — xem "Route Tiny" ở Phase Route.

1. **Skill `git-flow`** (hoặc `te-dev-commit` nếu team convention tách riêng) để commit theo đúng convention rồi push. Checkpoint xác nhận nội dung commit message bên trong skill đó (hỏi "nội dung commit ổn chưa") là lớp khác, **không thay thế** checkpoint 2 ở trên — vẫn phải hỏi đủ cả hai nếu skill con có hỏi.
2. Route Standard/Complex: không tự tạo PR / không tự comment Jira trừ khi user yêu cầu thêm ngay trong lượt duyệt này. Kết thúc: báo cho user branch đã push, nhắc nếu muốn mở PR thì gọi `te-dev-create-pr` riêng.
3. **Chỉ Route Tiny**: gọi tiếp `te-dev-create-pr` để tạo MR, rồi dùng `jira-core` (`comment <MÃ> --text "..." --commit`) để comment theo mẫu **TH1** (`reference/comment-templates.md`) — link MR vừa tạo, mô tả ngắn gọn thay đổi. Đọc output xác nhận comment đã tạo trước khi báo xong với user.

## Khi nào bỏ qua bước

- Việc chọn độ chặt theo độ phức tạp đã được xử lý ở **Phase Route** (route Tiny/Standard/Complex) — không tự ý rút gọn checkpoint ngoài những gì route đã quy định.
- Đã có plan từ trước (user tự viết hoặc phiên trước đã tạo) → bỏ qua bước 1 Phase A, bắt đầu từ review-plan. Áp dụng cho Standard/Complex; Route Tiny vốn đã không tạo file plan riêng.
- Đã có code từ trước (resume task bị ngắt giữa chừng, hoặc user chỉ định dùng lại code có sẵn thay vì làm lại từ plan) → xác định đang ở đâu (`git status`/`git diff`), bắt đầu lại đúng bước đó trong Phase B/C, không chạy lại từ đầu — áp dụng cho mọi route. **Vẫn phải log quality event** dù bỏ qua Phase A: dùng `--checkpoint audit` (không phải `plan`, để phân biệt rõ đây không đi qua `review-plan` thật) ngay sau khi tự đọc code có sẵn đối chiếu AC xong — `--outcome approved_clean` nếu lần đọc đầu đã đúng hết, `--outcome approved_after_fix --category "<lý do>"` nếu lúc đầu đọc nhầm/bỏ sót rồi tự sửa lại kết luận (vd ban đầu tưởng thiếu 1 AC, soi kỹ code mới thấy đã có). Bỏ qua bước log này vì "không phải checkpoint plan thật" sẽ làm `quality-report.py` thiếu hẳn 1 loại dữ liệu (chất lượng của chính bước audit/đọc hiểu code cũ, tách biệt với chất lượng viết code mới).

## Lỗi hay gặp

- **Nhận task là nhảy thẳng vào lên plan/code-recon**: bỏ qua Phase Intake, user chưa kịp biết task là gì đã thấy plan ra luôn. → Fix: Phase Intake + checkpoint 0 là bắt buộc, chạy ngay sau Bước 0, trước mọi thao tác create-plan/code-recon sâu.
- **Bỏ qua checkpoint vì "có vẻ ổn"**: tự ý chạy tiếp sang Phase A/B/C mà chưa có "yes" rõ ràng. → Fix: luôn dùng `AskUserQuestion`, không suy diễn sự im lặng là đồng ý.
- **Tự tắt docker của worktree khác** để giải quyết xung đột port. → Fix: chỉ cảnh báo, để user tự quyết (có thể đang có người dùng khác test dở).
- **Chạy test "cho có"** khi biết docker đang xung đột, rồi báo pass giả. → Fix: nêu rõ test nào bị skip/không tin cậy do xung đột môi trường trong báo cáo checkpoint 2.
- **Tạo PR/comment Jira "tiện thể"** dù route là Standard/Complex (phạm vi chỉ yêu cầu push). → Fix: chỉ Route Tiny mới tự làm bước 3 của Phase C; Standard/Complex dừng đúng ở bước 2, hỏi riêng nếu muốn làm thêm.
- **Bỏ qua Phase Route, mặc định coi mọi task là Standard** vì "có vẻ không nhỏ cũng không phức tạp". → Fix: luôn đọc field Change Size trước; field trống thì hỏi user bằng `AskUserQuestion`, không tự chọn Standard làm default ngầm.
- **Đoán route từ mô tả task thay vì field Jira** khi field Change Size thực ra có giá trị (quên đọc, hoặc đọc sai field id theo project). → Fix: đối chiếu đúng `customfield_x` theo project trong `reference/api-map.md` của jira-core trước khi kết luận field "trống".
- **Route Tiny nhưng vẫn rút gọn luôn cả Phase B** (bỏ review-code/test cho nhanh). → Fix: Route Tiny chỉ rút gọn Phase A (bỏ file plan riêng) và gộp checkpoint — Phase B (code/review/test) giữ nguyên đầy đủ như Standard.
- **Bỏ qua bước log-quality-event vì "task nhỏ không đáng log"**: làm số liệu `quality-report.py` sai lệch (thiếu mẫu), về lâu dài mất khả năng biết agent có đang cải thiện không. → Fix: log mọi checkpoint, kể cả route Tiny.
- **2 agent adversarial-verify chỉ paraphrase lại review-code thay vì thực sự cố phản bác**: nếu cả 2 agent chỉ lặp lại đúng những gì review-code đã nói, bước này không thêm giá trị gì so với chạy review-code 1 lần. → Fix: prompt phải nhấn mạnh "mặc định nghi ngờ", và nếu cả 2 lần nào cũng chỉ đồng ý xuôi theo review-code, cân nhắc đổi góc nhìn mỗi agent (vd 1 agent soi theo AC, 1 agent soi theo edge case/race condition) thay vì hỏi giống hệt nhau.

## Mở rộng Mattermost sau này

Khi có kết nối Mattermost (webhook gửi + bot/token nhận tin):
- Thay phần "tóm tắt trong chat" ở checkpoint 1/2 bằng gửi message qua webhook, và thay `AskUserQuestion` bằng chờ reply từ Mattermost (cần 1 cơ chế poll/subscribe chạy ngoài phiên Claude Code hiện tại — ví dụ scheduled task hoặc bot server riêng, không phải thứ 1 skill có thể tự làm trong lúc đang chạy).
- Bước 0 (nhận giao task) có thể nối với 1 trigger riêng (Mattermost bot → gọi Claude Code headless với mã Jira làm input) thay vì user gõ trực tiếp — đó là phần hạ tầng ngoài phạm vi skill này.
