# Comment công việc trên Jira — template chuẩn team

Chuẩn **nội dung** comment khi báo tiến độ task. AI/skill đọc file này để viết đúng 1 trong **4
tình huống** (TH0 cập nhật tiến độ / TH1 / TH2 / TH3). Comment **không thay** việc đổi status — vẫn kéo status + assign đúng
theo [`workflow.md`](workflow.md).

## Cơ chế link (QUAN TRỌNG — khác Markdown thường)

Comment post qua `jira_client.py` → `text_to_adf()`, hiểu **markdown tối thiểu** (chi tiết
`adf.md`): URL trần tự thành link, `[nhãn](url)` cũng được; `**đậm**`, `*nghiêng*`, `` `code` ``;
`- ` bullet, `1. ` numbered, thụt 2–3 space = list con; `#### ` heading (ép h3–h4); `---` đường kẻ.

- **Dòng trống chỉ để ngắt đoạn/khối** — một dòng trống là đủ, không chồng nhiều dòng trống.
- Link của team vẫn ưu tiên **URL trần** (người đọc thấy rõ đích).

## Nguyên tắc chung

- **Styling vừa phải, rõ ràng:** gạch đầu dòng dùng bullet, các bước tuần tự dùng numbered list;
  in đậm nhãn/điểm chính, nghiêng cho nhấn nhẹ, `code` cho tên bảng/field/lệnh — không đậm cả câu.
  Heading chỉ h4 (h3 khi cần nổi hơn) — header phải ≥ cỡ chữ thường; h5/h6 của Jira nhỏ hơn chữ thường nên KHÔNG dùng.

- **Ngôn ngữ:** tiếng Việt; giữ nguyên tên field/scope/repo, mã lỗi, tên file bằng tiếng Anh.
- **Chỉ ghi phần thực sự thay đổi.** 3 repo code là `api`, `cms`, `tae` — repo nào không đụng tới
  thì **bỏ dòng đó**. Linh hoạt theo thay đổi thực tế.
- **Link luôn là merge request.** Không bao giờ dán link commit trần (`/-/commit/<sha>`):
  - Cần chỉ tới **commit cụ thể** (TH0 tiến độ, TH2 commit fix) → dùng **link commit trong MR**
    `<repo>/-/merge_requests/<N>/diffs?commit_id=<sha đầy đủ>`, vd
    `https://sbc-gitlab.bsscommerce.com/sa-division/te-team/sa-swatch-app/api/-/merge_requests/412/diffs?commit_id=bc8314a5028110632805e96e363b91a0161eeaca`.
    Người đọc xem đúng commit đó, rồi bấm sang tab khác của MR để xem cả MR (linh hoạt hơn trang commit lẻ).
  - Comment có **khối Golive** → mỗi repo có **link MR** (`<repo>/-/merge_requests/<N>`), vì golive là merge MR chứ không phải deploy từng commit.
  - Chưa có MR (hiếm: push lẻ, chưa mở MR) → mới được dùng link commit trần, và ghi rõ "chưa có MR".
  - Lấy URL bằng `git-links.sh` của skill `git-flow` (in sẵn `mr-commit` khi branch có MR mở), không tự ghép tay.
- Riêng file migration/seed thì link tới **file trong GitLab**.
- **Phân biệt nhánh đích của link:**
  - Done dev & fix review → MR với **`master`**.
  - Merge test → MR với nhánh **`release/<number>`**.
- **Divider:** một dòng chỉ có `---` → `text_to_adf()` dựng node `rule` (đường kẻ ngang thật).
- **Không để lộ secret:** phần `env` chỉ ghi **tên field + hành động** (thêm/sửa/xóa), KHÔNG dán
  giá trị thật (token, connection string...).

---

## TH0 — Cập nhật tiến độ (code xong một phase / một lượt, chưa done dev cả task)

Dùng khi task chia nhiều phase (hoặc làm nhiều lượt) và mới xong một phần — **không phải** TH1
(TH1 = done dev cả task, gửi review). Khung:

```
Đã code xong **phase <N> (<repo>)**: <summary ngắn: làm gì, CHỈ làm cái gì, *không* đụng gì>
(không chia phase → "Đã code xong **<X>**: ...")

- **api**: <url commit TRONG MR: .../merge_requests/<N>/diffs?commit_id=<sha>>   (repo không đụng thì bỏ)
- **cms**: <url commit trong MR>
- **tae**: <url commit trong MR>
- **file migration/seed** (`<tên file>`): <url file trong GitLab>
- **env api/cms/tae**: <thêm/sửa/xóa field gì>
- **file toml** (`shopify.app.toml`): <thay đổi scope/gì>

#### Golive: <ngày> golive phase <N> trước      (CHỈ khi phase/lượt này golive lẻ)
- **MR**: api <url MR> · cms <url MR> · tae <url MR>   (link MR, KHÔNG link commit)
1. <bước trên prod theo thứ tự: chạy migration…>
2. <bước tiếp>
   - <lưu ý con của bước>

---
#### Chi tiết đã làm
- <từng việc đã làm; nhãn đầu dòng in đậm nếu cần>

**Phase <N+1> sẽ làm**: <việc tiếp theo>
```

> Mẫu thật: OPCS-104 comment 14044 (24-09-2026). Mỗi khối cách nhau đúng **một** dòng trống.

---

## TH1 — Done dev, đã tạo PR gửi review code

Mô tả ngắn gọn việc đã làm (thêm nguyên nhân / cách làm nếu cần), rồi liệt kê các phần thay đổi:

```
<Mô tả ngắn gọn việc đã làm — giải thích thêm nguyên nhân/cách làm nếu cần>

- **api** (master): <url MR với master>            (nếu có code ở api)
- **cms** (master): <url MR với master>            (nếu có code ở cms)
- **tae** (master): <url MR với master>            (nếu có code ở tae)
- **file migration/seed** (<tên file>): <url file trong GitLab>
- **env api/cms/tae**: <thêm/sửa/xóa field gì>
- **file toml (shopify.app.toml)**: <thêm access scope gì / thay đổi gì trong file>
- dev doc <tên dev doc>: <url dev doc của feature>   (nếu được yêu cầu viết)
```

> Chỉ giữ những dòng có thay đổi. VD chỉ `api` đổi thì chỉ ghi dòng `api`.

---

## TH2 — Đã fix review xong

Chỉ repo nào **có review** thì mới phải fix → chỉ ghi repo đó.

```
đã fix
- api (master): <url commit fix trong MR: .../merge_requests/<N>/diffs?commit_id=<sha>>
- cms (master): <url commit fix trong MR>
- tae (master): <url commit fix trong MR>
- <giải thích thêm nếu có>
```

> Nhiều commit fix trong cùng MR → mỗi commit 1 link `diffs?commit_id=`. Người đọc vẫn bấm sang tab
> Changes của MR để xem toàn bộ.
>
> Phần "giải thích thêm": có thể **hỏi user tự viết**, hoặc **dựa vào context sửa review code mà
> tóm tắt lại** (vd tại sao làm như vậy, tại sao không fix point này...).

---

## TH3 — Đã merge test

```
đã merge test
- testsite <number>
- branch: release/<number>

**MR:**
- api (release/<number>): <url MR với nhánh release>
- cms (release/<number>): <url MR với nhánh release>
- tae (release/<number>): <url MR với nhánh release>
```

> Link ở khối **MR** là MR với nhánh **release** (khác TH1/TH2 dùng `master`). Repo nào không đụng
> tới thì bỏ dòng. Dùng nhãn in đậm `**MR:**` làm dấu phân cách (không dùng đường kẻ `=====`).
