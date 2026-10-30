"""Ví dụ steps.py: app nằm trong iframe khác site; điền form + Save, bấm nút mở tab mới, chụp tab đó, gây lỗi API để
console / network được ghi.

Chạy trên fixtures:
    uv run scripts/chrome.py serve-fixtures --port 8790 &        # chỉ cần cho ví dụ / selftest, app thật thì không
    uv run scripts/chrome.py launch
    uv run scripts/chrome.py run examples/steps-open-new-tab.py --owner DEMO@s1 \
        --url http://localhost:8790/top.html --out /tmp/demo --prefix TC-01

Khuôn: chỉ locator (role / label / text), không toạ độ, không sleep — chờ bằng ctx.expect / locator; mỗi kiểm tra đi qua
ctx.check để vào result.json; ctx.step đánh dấu bước để biết lỗi console / network do thao tác nào.
"""


def run(ctx):
    app = ctx.frame("/app.html")  # theo đoạn src của iframe, không theo thứ tự frame

    ctx.step("save")
    app.get_by_label("Badge text").fill("NEW")
    app.get_by_role("button", name="Save").click()
    status = app.get_by_role("status")
    ctx.expect(status).to_have_text("Saved: NEW")  # chờ tới khi đúng (mặc định 5 s), sai thì ném lỗi
    ctx.check(True, "Save hiện 'Saved: NEW'", status.inner_text())
    ctx.shot("saved")

    ctx.step("open-editor")
    editor = ctx.click_new_tab(app.get_by_role("button", name="Open editor"))
    ctx.check("/editor.html" in editor.url, "nút Open editor mở tab editor", editor.url)
    ctx.shot("editor", page=editor)
    editor.close()  # tab mình mở thì mình đóng; editor thật có thể có Save làm đổi dữ liệu — chỉ xem

    ctx.step("broken-api")
    with ctx.page.expect_response(lambda r: r.url.endswith("/api/missing")) as resp:
        app.get_by_role("button", name="Call broken API").click()
    ctx.check(resp.value.status == 404, "API lỗi trả 404", resp.value.status)
    return {"status_text": status.inner_text()}
