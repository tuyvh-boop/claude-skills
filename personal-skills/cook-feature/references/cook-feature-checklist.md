# Cook-Feature: Checklist & Common Issues

## Bước 1 — Lấy context Jira + tạo branch

**Checkpoint**:
- [ ] Mã Jira lấy được? AC rõ ràng?
- [ ] Branch đã tạo theo rule `feature/<JIRA>` hoặc `fix/<JIRA>`?
- [ ] Tên branch match tên Jira? (vd: `OPOS-136` → `feature/OPOS-136`)

**Lỗi hay gặp**:
- Mã Jira sai / ticket không tồn tại → hỏi user confirm trước làm chi tiết
- AC mơ hồ → ghi note "AC chưa rõ — cần clarify" rồi tiếp tục, nhưng warning user khi commit
- Branch đã tồn tại → dùng luôn, không tạo mới

---

## Bước 2 — Implement feature

**Checkpoint trước code**:
- [ ] Đã xác định **surface** (in-app/storefront/checkout) cần cover?
- [ ] Có WIP sẵn trên branch không? (kiểm tra `git status`)
- [ ] Architecture/pattern nào cần tái dùng từ code hiện tại?

**Lỗi hay gặp**:
- **Bỏ qua surface check**: Feature phải cover cả in-app + storefront nhưng chỉ code 1 phía
  - → Fix: đọc AC + `shopify-app/surfaces.md` TRƯỚC code
- **Code theo tài liệu cũ**: Dùng pattern deprecated/outdated
  - → Fix: từ create-plan phải cụ thể → code phải verify thực tế hiện tại
- **Không follow convention repo**: Code style/structure khác quy ước CLAUDE.md
  - → Fix: đọc `CLAUDE.md` + `cms/.claude/CLAUDE.md` (nếu CMS) trước code

---

## Bước 3 — Tự soát rủi ro (review-pr-risk)

**Checkpoint**:
- [ ] Risk review: 🔴 (lỗi nghiêm trọng) / 🟡 (cảnh báo) / 🟢 (ổn)?
- [ ] Nếu 🔴 → phải fix trước qua bước 4, không exception

**Lỗi hay gặp**:
- Verdict 🔴 nhưng vẫn push
  - → Fix: **bắt buộc rewind** lại bước 2, fix issue, rồi review lại
- Risk review báo "missing edge case" nhưng bỏ qua
  - → Fix: ghi vào test cases bước 5, không bỏ

---

## Bước 4 — Commit

**Checkpoint**:
- [ ] Commit message rõ ràng theo format `<branch> (<type>) <subject>`?
- [ ] Type đúng? (feat / fix / refactor / docs / ...)
- [ ] Không commit cải thiện/cleanup không liên quan task

**Lỗi hay gặp**:
- Commit message quá dài / không rõ intent
  - → Fix: format theo rule `te-dev-commit` cân nhắc
- Squash quá nhiều commit vào 1 → khó review
  - → Fix: nếu task có 2+ phần rõ ràng → split commit (yêu cầu user xác nhận)
- Commit trên branch sai (master/ai-configs)
  - → Fix: `/te-dev-commit` tự check + cảnh báo

---

## Bước 5 — Tạo PR + Comment Jira

**Checkpoint 1 — Cập nhật docs**:
- [ ] Có file CLAUDE.md / tài liệu nào cần update?
- [ ] Có references/*.md cần thêm info mới?
- [ ] User confirm sửa docs trước commit không?

**Checkpoint 2 — PR Info**:
- [ ] Title rõ ràng? (<20 từ, không generic)
- [ ] Description cover: changes + testing + risks?
- [ ] Có screenshot/demo nếu là UI feature?

**Checkpoint 3 — Jira Comment**:
- [ ] Comment theo rule trong `workflow/jira-comment.md`?
- [ ] Có link PR, test evidence, known issues?

**Lỗi hay gặp**:
- Quên cập nhật CLAUDE.md / docs
  - → Fix: bước 5 bắt buộc scan diff → rà soát cần update gì
- PR description generic / quên test cases
  - → Fix: force structure: "Thay đổi:" + "Test:" + "Rủi ro:"
- Comment Jira thiếu link PR / evidence
  - → Fix: template comment phải có cả 3 thứ: link MR + test evidence + resolved status

---

## Khi nào dừng cook?

Nếu gặp tình huống sau → dừng cook, không cưỡng ép tiếp tục:
- **AC chưa rõ** → ghi note, hỏi PM clarify, rồi rewind đến bước 1
- **Code recon phát hiện constraint không giải quyết được** → escalate PM, không commit với "workaround tạm"
- **Risk review 🔴 nhưng fix cần thêm thời gian** → hỏi user: commit bây giờ + WIP hay sửa xong rồi?
- **User thay đổi yêu cầu giữa chừng** → rewind, xác định lại AC, rồi tiếp tục

Không bao giờ "skip step để nhanh" — mỗi checkpoint là để tránh rework sau.

---

## Memory tracking: Lỗi xảy ra trong task này

Khi cook-feature gặp lỗi, capture lại:
```
Task: OPOS-XXX
Lỗi: [điều gì sai]
Nguyên nhân: [tại sao sai]
Sửa: [cách tránh lần sau]
→ Cập nhật vào "## Lỗi hay gặp" trong SKILL.md
```

Ví dụ:
```
Task: OPOS-139
Lỗi: Quên code storefront side, chỉ code in-app
Nguyên nhân: Không check surfaces.md trước bước 2
Sửa: Thêm step "kiểm tra surface TRƯỚC code" vào bước 2 checklist
```
