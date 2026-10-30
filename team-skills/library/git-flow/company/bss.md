# Convention — công ty BSS / OPTIS (profile `bss`)

Nền: `rules/conventions/_base.md`. File này chỉ ghi **phần khác biệt của công ty**, và
**KHÔNG chép cứng** rule team — đọc thẳng từ repo `ai-hub` (single source of truth) qua con trỏ,
để team sửa rule `git pull` là mình có bản mới.

> Đặt riêng trong `company/` để dễ thêm/sửa/xoá theo công ty. Công ty khác → thêm `company/<tên>.md`
> + 1 dòng trong `rules/profiles.md`. Không đụng phần generic.

## Kiểm `glab` trước khi tạo MR

**[Model: haiku — main loop]**

1. `glab --version` → chưa có thì hướng dẫn cài theo OS (`uname -s`): Windows `winget install --id GLab.GLab`; macOS
   `brew install glab`; Linux `sudo apt install glab`. User tự cài, không tự chạy lệnh cài.
2. `glab auth status` → chưa auth với host GitLab công ty → hướng dẫn tạo token tại
   `https://sbc-gitlab.bsscommerce.com/-/user_settings/personal_access_tokens` (tick `api`, `read_repository`,
   `write_repository`) rồi user tự chạy `glab auth login` (host `sbc-gitlab.bsscommerce.com`). Không nhận token qua chat.
3. Chưa xong 2 bước trên → vẫn commit + push được, chỉ dừng ở bước tạo MR và đưa link tạo MR từ output `git push`.

## Khác biệt so với `_base.md`

### Commit — format team

```
<branch> (<type>) <subject>

<body>
```

- `<branch>` lấy từ `git branch --show-current` (vd `feature/OPOS-13`); `OPOS-13` = mã Jira. **Không đoán.**
- `<type>`, subject, body, độ phức tạp: theo taxonomy trong `_base.md` (giống hệt team).
- Footer khi complex/breaking: `BREAKING CHANGE: <mô tả + migration>` và/hoặc `Closes <mã Jira>`.
- **KHÔNG** thêm `Co-Authored-By` hay trailer nào (đúng rule team).

### Tách commit — chỉ gợi ý khi diff quá lớn

Mặc định vẫn **1 commit** như `_base.md`. Khác biệt duy nhất so với repo cá nhân: repo công ty có thêm dữ kiện **diff quá lớn** → lúc đó mới **gợi ý** user tách để commit dễ review.

- Ngưỡng: **> ~1000 dòng thay đổi**, VÀ diff gồm ≥ 2 mục đích tách bạch được. **Số file không giới hạn** — đụng bao nhiêu file cũng không phải lý do gợi ý tách.
- Chỉ **hỏi để user confirm**, không tự tách. User bảo giữ nguyên → 1 commit, không nhắc lại.
- Diff lớn nhưng cùng một mục đích (vd rename toàn bộ) → **không** gợi ý tách.

### Branch — format team

- `feature/<MÃ-JIRA>` (mặc định), bug → `fix/<MÃ-JIRA>`. Có thể kèm slug: `feature/OPOS-13-bulk-delete`.
- Base: `master` mới nhất (`git fetch` trước).

## Ranh giới với command team (KHÔNG ôm đồm)

Skill git-flow chỉ làm **phần git thuần**. Việc **đặc thù công ty** thì hand-off, KHÔNG tự làm lại:

| Việc | Xử lý |
|---|---|
| commit theo format team | git-flow tự làm (dùng format ở trên) |
| tạo branch từ master | git-flow tự làm |
| tạo MR đơn giản với `master` | git-flow tự làm được... |
| **...nhưng luồng MR đầy đủ** (rà tài liệu cần update + comment Jira TH1 + đổi status/assignee) | **HỎI hand-off `/te-dev-create-pr`** |
| kéo context Jira đầu task | hand-off `/te-dev-start` (hoặc user tự) |
| merge test (release, 3 repo, comment TH3) | hand-off `/te-dev-merge-test` |
| kéo mã Jira để commit khi branch chưa gắn mã | hỏi user, KHÔNG tự chế mã |

**Ở bước tạo MR (`rules/operations/create-mr.md`), profile `bss` PHẢI hỏi:**
> Repo công ty. Bạn muốn (a) mình tạo MR gọn với `master` ở đây, hay (b) chạy luồng đầy đủ `/te-dev-create-pr` (rà tài liệu + comment Jira + đổi status)?

Không tự ý đụng Jira/status trong git-flow.
