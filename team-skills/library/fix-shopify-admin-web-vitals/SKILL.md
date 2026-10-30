---
name: fix-shopify-admin-web-vitals
description: Use khi cần fix Core Web Vitals (LCP / CLS / INP) cho một Shopify EMBEDDED ADMIN app (app nhúng trong Shopify Admin qua App Bridge, chạy trong iframe) — "fix lcp cho app X ở admin", "fix cls/inp cho app X", "fix lcp/cls/inp in app cho app X", "app X ở admin bị chậm LCP/CLS/INP". KHÔNG dùng cho storefront/theme (đó là Lighthouse/CrUX, khác cơ chế), KHÔNG dùng để build feature (code-implementation) hay review diff đơn thuần (review-code).
---

# Fix Shopify Admin Web Vitals (LCP / CLS / INP)

## Overview

Fix Core Web Vitals cho **Shopify embedded admin app** — app nhúng trong Shopify Admin qua App Bridge, chạy **trong iframe**. Đây là task **perf-fix**, bản chất khác task feature: cái mờ nhất không phải "làm gì" mà là "vì sao chậm". Nên skill chạy theo **vòng lặp đo lường**:

```
setup đo → baseline → chẩn đoán bottleneck → chọn cách → plan → sửa MỘT thay đổi → đo lại
                                   ↑─────────────── chưa đạt thì lặp ───────────────┘
```

**Nguyên tắc cốt lõi:**
1. **Đo trước, đoán sau.** Không sửa khi chưa có baseline + chưa định vị bottleneck bằng số thật (attribution). "Measure, don't guess".
2. **Mỗi vòng một thay đổi.** Sửa nhiều thứ cùng lúc rồi đo → không quy được nhân–quả. Một thay đổi → đo lại → giữ/bỏ.
3. **Đúng phạm vi metric.** User gọi fix metric nào thì **chỉ** sửa metric đó. Nhưng **luôn bảo vệ** các metric đang đạt tốt — nếu bản fix làm tụt chúng thì **báo user**, không âm thầm (xem "Guardrail").
4. **iframe ≠ web thường.** Lighthouse/PSI **không đo đúng** app trong iframe. Số chính chủ là Web Vitals do Shopify thu → Partner Dashboard. Xem `reference/measurement.md`.
5. **Tách cơ chế khỏi kiến thức.** Cơ chế (phase, config, gate) ở đây + `phases/`. Kiến thức LCP/CLS/INP + catalog fix ở `reference/web-vitals-knowledge.md`. Cơ chế đo ở `reference/measurement.md`.
6. **Không để kỹ năng mai một.** Ở chế độ `guided`, mỗi phase giải thích *vì sao* trước khi làm — user hiểu cơ chế, không chỉ nhận kết quả.

## Khi nào dùng / KHÔNG

- **Use:** app embedded admin (App Bridge/iframe) lệch ngưỡng LCP/CLS/INP, cần fix.
- **NOT:**
  - **Storefront / theme** — đó là Lighthouse + CrUX, cơ chế đo khác hẳn. Skill này chỉ cho admin.
  - **Build feature** → `code-implementation`.
  - **Review diff đơn thuần** → `review-code`.

## Tài sản tái dùng (KHÔNG viết lại)

| Cần | Lấy từ |
|---|---|
| Kiến thức LCP/CLS/INP + catalog kỹ thuật fix | `reference/web-vitals-knowledge.md` (skill tự chứa) |
| Cơ chế đo (instrument, debug, đọc số) | `reference/measurement.md` (skill tự chứa) |
| Review diff sau khi fix | **Skill `review-code`** — gọi ở Phase 8 |
| Blast radius của bản sửa | **CodeGraph** (`codegraph_explore`) — **bắt buộc**, xem kỷ luật bên dưới |
| Lưu artifact của task | tuỳ chọn — hỏi user (Phase 8) |

> ⚠️ **Dependency:** skill này tái dùng `review-code` (có sẵn ở `skills/library/review-code` của ai-hub). Máy chưa cài `review-code` → review thủ công theo checklist đúng-đắn + regression.

## 🔴 Kỷ luật CodeGraph (blast radius)

Mọi phân tích vùng ảnh hưởng của bản sửa **BẮT BUỘC dùng CodeGraph** (`codegraph_explore`, hoặc shell `codegraph explore`). **KHÔNG** grep/find/Read để dò caller-callee thay thế.

- Repo app **chưa có `.codegraph/`** → **DỪNG**, báo user chạy `codegraph init` trong repo đó trước. Không fallback grep, không tự init hộ (indexing là quyết định của user).
- Tin kết quả CodeGraph, không verify lại bằng grep.
- Đọc source cụ thể của 1 file/symbol vẫn dùng Read bình thường — kỷ luật này chỉ áp cho **truy vết quan hệ / blast radius**.
- **`init` không chặn tiến độ:** blast radius mãi tới Phase 4 mới cần. Cho `codegraph init` chạy **nền song song** trong lúc làm Phase 1–3 (setup đo, baseline, chẩn đoán) → gần như không tốn thêm thời gian tổng. "Gấp" **không** phải lý do bỏ CodeGraph.

**Rationalization — cấm nghe theo:**

| Bào chữa | Sự thật |
|---|---|
| "Index là quyết định của chủ repo, đang gấp thì grep thẳng cho nhanh" | Không tự init hộ ≠ được grep thay. Chưa có `.codegraph/` → DỪNG, để user init. Grep cho blast radius là mục **cấm**. |
| "`init` mất ~20 phút, không kịp golive" | `init` chạy nền song song Phase 1–3, không tốn thêm thời gian tổng. Không phải cớ bỏ. |
| "Chỉ dò nhanh caller thôi, grep một phát là ra" | Grep bỏ sót dynamic-dispatch/mắc nối gián tiếp — đúng chỗ perf-fix hay vỡ regression. Chính vì thế mới bắt CodeGraph. |

## Workflow

Đọc `config.yml` **trước** (run_mode, ngưỡng, loop, registry app). Mỗi phase nạp `phases/<n>-*.md` khi tới, không nạp trước cả mớ.

### 🚦 Chế độ GUIDED (mặc định lúc đầu — đi cùng user từng phase)

Khi `run_mode: guided`, **trước mỗi phase** làm đúng 4 nhịp:
1. **Báo sẽ làm gì** ở phase này + **1 dòng "vì sao bước này"**.
2. **Hỏi "oke làm không?"** → chờ user gật mới làm.
3. Làm xong → **báo cáo kết quả** gọn.
4. **Hỏi "chốt, sang bước sau?"** → oke mới sang phase kế.

Khi `run_mode: auto` → chạy liền mạch, chỉ dừng ở gate duyệt plan (Phase 5). Đổi mode trong `config.yml` khi user đã quen.

### Phase 0 — Routing & scope  **[Haiku — subagent]**
→ Nạp `phases/0-routing.md`. Nhận **app X** từ lệnh + **metric in-scope** (lcp/cls/inp — chỉ cái user gọi). Tra `config.yml` registry để ra repo path / stack / app id. App không có trong registry → hỏi user (1 lần), đừng bịa.

### Phase 1 — Chuẩn bị & setup đo  **[Sonnet — subagent + main]**
→ Nạp `phases/1-setup-do.md`. **Cái phải làm TRƯỚC khi fix:** nhúng App Bridge Web Vitals + `shopify-debug`, verify số thật sự chảy về. Đụng code app → **confirm trước**. Không đo được thì mọi bước sau vô nghĩa.

### Phase 2 — Baseline + mục tiêu  **[Sonnet — subagent]**
→ Nạp `phases/2-baseline.md`. Đo p75 **cả 3** metric (mốc để bảo vệ), chốt **ngưỡng đích** cho metric in-scope, xác định **route tệ nhất** để tập trung.  → artifact

### Phase 3 — Chẩn đoán bottleneck  **[Sonnet — subagent]**
→ Nạp `phases/3-diagnose.md`. Dùng attribution (`shopify-debug` + Web Vitals API) định lượng: metric in-scope nghẽn ở đâu (LCP: TTFB/render/resource; CLS: font/ảnh/inject; INP: long task). Đây là "discover root-cause" của perf.

### Phase 4 — Chọn cách + blast radius  **[Opus — main]**
→ Nạp `phases/4-solutions.md`. Map bottleneck → catalog `reference/web-vitals-knowledge.md`, chọn kỹ thuật theo trade-off. **Blast radius bằng CodeGraph** (bắt buộc).  → artifact

### Phase 5 — Plan fix + gate duyệt  **[Opus — main]**
→ Nạp `phases/5-plan.md`. Plan theo từng file + cách verify. **Trình user duyệt, chờ oke.** Bỏ gate chỉ khi user uỷ quyền RÕ RÀNG ("tự làm"). "Gấp lắm" **không** phải uỷ quyền.  → artifact

### Phase 6 — Implement một thay đổi  **[Opus — main]**
→ Nạp `phases/6-implement.md`. Code **đúng một** thay đổi của vòng này, theo convention app.

### Phase 7 — Đo lại + guardrail  **[Sonnet — subagent + main]**
→ Nạp `phases/7-remeasure.md`. Đo lại: metric in-scope đạt ngưỡng chưa **+ guardrail** metric đã tốt có tụt không. Tụt → báo user + hỏi. Chưa đạt & còn vòng (`loop.max_iterations`) → **quay Phase 3**.

### Phase 8 — Review + cất nhật ký  **[review-code lo subagent; main]**
→ Nạp `phases/8-review.md`. **Gọi skill `review-code`** trên diff → fix theo review → cất artifact của cả run vào nhật ký làm việc.

## Guardrail (bảo vệ metric đang tốt)

- Phase 2 lưu baseline **cả 3** metric làm mốc, kể cả metric ngoài scope.
- Mỗi vòng Phase 7 so metric ngoài scope với mốc: tụt qua ngưỡng (LCP 2.5s / CLS 0.1 / INP 200ms) **hoặc** xấu đi đáng kể → **báo user ngay**, nêu thay đổi nào gây ra, để user quyết giữ/bỏ.
- Không tự ý "đánh đổi" metric này lấy metric kia khi user chưa đồng ý.

## Quick Reference

| Việc | Cách |
|---|---|
| Config | `config.yml` — đọc ở Phase 0 (run_mode, ngưỡng, loop, registry) |
| Route app | Phase 0 · từ lệnh "app X" + registry |
| Metric scope | Phase 0 · chỉ metric user gọi; các metric khác chỉ **bảo vệ** |
| Setup đo | Phase 1 · `reference/measurement.md` |
| Baseline | Phase 2 · p75 cả 3 metric · route tệ |
| Chẩn đoán | Phase 3 · attribution |
| Chọn cách | Phase 4 · `reference/web-vitals-knowledge.md` |
| Blast radius | **CodeGraph bắt buộc** · chưa index thì dừng |
| Gate plan | Phase 5 · bỏ nếu "tự làm" |
| Vòng lặp | Phase 7 chưa đạt → quay Phase 3 · tối đa `loop.max_iterations` |
| Guardrail | Phase 7 · metric tốt tụt → báo user |
| Review | Phase 8 · gọi `review-code` |

## Common Mistakes

- **Sửa khi chưa đo/chưa chẩn đoán** → đoán mò. Phải có baseline + attribution trước (Phase 2–3).
- **Sửa nhiều thay đổi/vòng** → không quy được nhân–quả. Một thay đổi/vòng (Phase 6).
- **Dùng Lighthouse/PSI chấm app iframe** → số sai. Số chính chủ ở Partner Dashboard (`reference/measurement.md`).
- **Fix lan sang metric ngoài scope** → sai yêu cầu. Chỉ metric user gọi; metric khác chỉ bảo vệ.
- **Âm thầm để metric tốt tụt** → vi phạm guardrail. Tụt phải báo (Phase 7).
- **Grep/Read thay CodeGraph cho blast radius** → cấm. Chưa index thì dừng, bảo user `codegraph init`.
- **Bỏ gate duyệt vì user than gấp** → sai. "Gấp" không phải uỷ quyền; chỉ nén plan rồi vẫn xin duyệt.
- **Chạy phăng 8 phase ở guided** → mất mục tiêu "đi cùng user". Guided = hỏi trước/ báo sau mỗi phase.

## Files

- `config.yml` (gitignored) / `config.example.yml` — human chỉnh: run_mode, ngưỡng, loop, registry app.
- `phases/0-routing.md` … `phases/8-review.md` — chi tiết từng phase, nạp on-demand.
- `reference/measurement.md` — cơ chế đo (instrument, debug, đọc số, caveat iframe).
- `reference/web-vitals-knowledge.md` — kiến thức LCP/CLS/INP + catalog kỹ thuật fix.
