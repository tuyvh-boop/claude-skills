# Execute-Plan: TDD Workflow & Optimization Checklist

## TDD Workflow — Đúng trình tự

### 1. Design Interface (trước viết test/code)

**Đầu vào**: AC / plan.md / spec / design

**Output**: Chữ ký hàm/component/endpoint cụ thể
```typescript
// Ví dụ: function computeDiscount(productId: string, quantity: number): Promise<number>
// - Input: productId (string), quantity (number)
// - Output: discount percentage (Promise<number>)
// - Side effects: none
// - Error cases: invalid productId, quantity <= 0
```

**Cách làm**:
- Đọc AC/plan → xác định "cái này cần làm gì?"
- Chốt: tên function/component → input → output → side effect → error handling
- Check: có pattern/helper sẵn làm đúng việc này không? → dùng lại, không design mới

**Lỗi hay gặp**:
- Design interface vừa rồi lại thay đổi ở bước 2 → thiết kế chưa đủ sâu. Quay lại đọc kỹ AC.
- Design quá phức tạp / có "maybe case" → quá rộng. Viết lại ngắn gọn: "interface này chỉ làm Y, case khác xử lý ở chỗ khác".

---

### 2. Write Test (TDD)

**Đầu vào**: Interface + AC/plan (edge case)

**Output**: Test file + test cases fail (chưa có implementation)

**Framework**: Dùng đúng project hiện tại (check `package.json` / test folder hiện có)
- API: Jest + supertest
- React: Jest + React Testing Library
- Database: Jest + test DB container (nếu có)

**Cách viết test**:
- **Happy path**: case bình thường theo AC
- **Edge cases**: từ AC/plan (vd: empty input, boundary value, error)
- **Error handling**: nếu AC nêu cách xử lý lỗi

**Ví dụ**:
```typescript
describe('computeDiscount', () => {
  it('should return 10% for quantity >= 5', async () => {
    const result = await computeDiscount('product-1', 5);
    expect(result).toBe(10);
  });
  
  it('should return 0% for quantity < 5', async () => {
    const result = await computeDiscount('product-1', 4);
    expect(result).toBe(0);
  });
  
  it('should throw for invalid productId', async () => {
    expect(computeDiscount('invalid', 5)).rejects.toThrow();
  });
});
```

**Lỗi hay gặp**:
- Test quá general → không test cái cụ thể AC yêu cầu
- Test viết nhưng logic phức tạp → chẻ nhỏ hơn, test 1 case/test function
- Quên edge case từ AC → đọc lại AC, thêm edge case test

---

### 3. Implement (Code)

**Đầu vào**: Interface + Test (fail)

**Output**: Code pass test + match AC/design/plan

**Cách làm**:
- Chỉ code đủ để test pass
- Tái dùng helper/pattern từ codebase (không viết mới song song)
- Một vòng: code → test pass → đối chiếu với nguồn (xem bước 4)

**Lỗi hay gặp**:
- Code quá nhỏ / quá "ideal" → quên error handling
  - → Fix: test phải cover error case trước, code phải implement error handling
- Code quá phức tạp → mỗi hàm làm 2+ việc
  - → Fix: tách nhỏ interface, tách test, mỗi hàm 1 việc

---

### 4. Cross-check với Nguồn (liên quan đơn vị)

**Input**: Code vừa viết

**Check list**:
- [ ] Code match AC? (không thêm/bớt requirement)
- [ ] Code match design? (UI hiển thị đúng, behavior đúng)
- [ ] Code match plan.md? (sử dụng component/helper/logic theo plan)
- [ ] Code match OpenSpec (nếu có)?
- [ ] Code match convention repo? (naming, structure, style)

**Nếu lệch**: Sửa **ngay lập tức**, không để lại TODO.

**Nếu nguồn mâu thuẫn** (AC vs design khác nhau):
- **Dừng lại**, nêu mâu thuẫn cụ thể
- Hỏi user ưu tiên nguồn nào
- Không tự code 1 bên rồi lờ đi

---

## Đánh giá Tối ưu — Khi thêm field/index/config mới

### Index Optimization

**Nguyên tắc**: Thêm index nếu có truy vấn **cụ thể** từ AC/plan sẽ chạy, không phải "field này thường hay index".

**Cách đánh giá**:
1. Liệt kê truy vấn (WHERE / JOIN / ORDER BY) từ code + AC
2. Xác định truy vấn nào sẽ **chạy thường xuyên** hoặc **critical performance**
3. Nếu truy vấn cần index → thêm. Không → bỏ.

**Ví dụ**:
- ✓ AC: "Lọc sản phẩm theo category + price range" → cần index (category, price)
- ✗ "Product table thường có created_at" → không cần index nếu AC không filter/sort theo created_at

---

### Column/Table Addition

**Nguyên tắc**: Thêm field nếu **thực sự cần lưu trữ dữ liệu** mà AC/design yêu cầu, không phải "để sau này mở rộng".

**Cách đánh giá**:
1. AC nói cần lưu **cái gì**? (metadata, state, config)
2. **Cách sử dụng**: write / read / filter / sort
3. **Quy mô**: bao nhiêu record, mối quan hệ với table khác

Nếu cả 3 rõ ràng từ AC → thêm field. Nếu chỉ "có thể cần sau" → không thêm (over-engineer).

**Ví dụ**:
- ✓ AC: "Track sản phẩm được yêu thích lần cuối khi nào" → thêm `last_favorited_at` (clear use case)
- ✗ "Sản phẩm có thể có tags trong tương lai" nhưng AC chưa mention → không thêm table `ProductTag` bây giờ

---

### Decision Checklist

Trước khi thêm **bất kỳ** schema change nào:
- [ ] AC/plan/spec có yêu cầu **cụ thể** điều này không?
- [ ] Nếu không, có **suy luận logic** từ use case AC ngụ ý không?
- [ ] Có **truy vấn/access pattern** cụ thể từ code không?
- [ ] Nếu "để sau này" → **không thêm**

Nếu uncertain (không chắc thêm hay không):
- Nêu rõ lý do cân nhắc
- Hỏi user confirm
- Không tự chọn 1 bên

---

## Pressure Scenarios — TDD Under Deadline

### Scenario: Combinatorial Logic + Time Pressure (RED baseline)

**Context**: 84 state combinations (2 modes × 3 units × 7 weeks × 2 range-types). AC specifies all. Deadline: 1 hour. Temptation: "AC already defines behavior → skip test-first, just code all 84 cases."

**Baseline violation**: Agent chose hybrid approach (decision table + 12–15 spot-checks). Rationalization: "Combinatorial = matrix-driven, not emergent. TDD exhaustive tests too slow for deadline."

**Why this fails**:
- Spot-checks LOOK safe (hit corners of each dimension)
- But interaction bugs hide: e.g., "minute unit vô tác dụng nếu option không có giờ" (only caught when testing minute + hour unit cross-product)
- 9 lỗi loại này trong 1 lượt, phải chạy code-review riêng

**Correct hybrid (don't skip TDD)**:
1. **Decision table** (5 min): matrix of all dimensions + explicit edge cases (rollover midnight, enum out-of-range, field becomes meaningless in combo)
2. **Test-first** (15 min): write tests for representative cells + all edge cases (NOT all 84, just ~12–15 with interaction coverage)
3. **Code** (30 min): implement to pass tests, walk through decision table to ensure no dimension is empty
4. **Coverage walk** (5 min): checklist — "single mode tested?", "all time units?", "week boundaries?", "both range types?"

**Key**: TDD is NOT "exhaustive tests for all 84". TDD is "test first to verify interface + verify you haven't forgotten entire dimension". Time pressure = hybrid OK, but NOT "skip test-first".

---

### Scenario: Schema Decisions Under PM Demo Pressure (RED baseline)

**Context**: PM demo in 60 min. AC: "Save selected date when user picks it." Temptation: Add extensibility fields (`validation_rules`, `cached_value`, `synced_at`) to look prepared.

**Baseline**: Agent deferred all speculative fields. Added only: `user_id` (domain logic) + `created_at` (audit trail). Rationalization: "PM cares about demo behavior, not schema philosophy."

**Boundary rule** (based on RED findings):

| Field Type | Add? | Example | Reasoning |
|---|---|---|---|
| **Direct AC requirement** | ✅ Yes | `selected_date` | Core feature |
| **Domain logic (implicit in AC)** | ✅ Yes | `user_id` ("user picks it") | Necessary for feature to work |
| **Audit/traceability** | ✅ Yes | `created_at` ("when saved?") | Low risk, high support value. Acceptable even if not in AC. |
| **Extensibility (no AC mention)** | ❌ No | `validation_rules`, `updated_at` (if no AC update) | Scope creep. Defer until AC expands. |
| **Performance "best practice"** | ❌ No | Index on date, `synced_at` for future | Don't add without AC query/sync AC |
| **Versioning/replication** | ❌ No | `sync_status`, `remote_id` | Over-engineer under deadline |

**How to handle pressure**:
- Write minimal schema (AC scope only)
- Add audit fields (justified as "support traceability")
- Document what you deferred (internally, not to PM)
- Tell PM: "Schema ready. If you need X query or Y sync later, let me know — ready to extend."

---

## Memory Tracking: Lỗi trong task này

Khi execute-plan gặp lỗi:
```
Task: OPOS-XXX
Lỗi: [chi tiết sai]
Nguyên nhân: [tại sao]
Fix: [cách tránh lần sau]
→ Cập nhật ## Lỗi hay gặp trong SKILL.md
```

Ví dụ:
```
Task: OPOS-140
Lỗi: Thêm field mà AC không mention
Nguyên nhân: Tự suy diễn "tốt cho sau này"
Fix: Thêm rule bắt buộc — đánh giá theo nguyên tắc ở mục trên, hỏi user nếu uncertain
```

---

## RED Phase Findings (2026-09-29)

**Scenario 2: Combinatorial Logic** — Agent skipped test-first under time+AC-specified rationale. Fix: TDD mandatory; hybrid OK (decision table + spot-checks), but NOT skip-test-first.

**Scenario 3: Schema Pressure** — Agent resisted over-engineering (deferred validation_rules, synced_at, etc.). Fix: Boundary rule — audit fields ✅, extensibility fields ❌.
