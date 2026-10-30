"""Site module Shopify: admin + app nhúng + storefront. Chỉ nạp khi bên gọi test Shopify (`ctx.site("shopify")`).

Đã kiểm trên admin thật: mở app qua admin, lấy frame app từ `iframe[name=app-iframe]`, chạy JS / snapshot /
console / request trong frame, mở modal trong app, max modal App Bridge (mở / lấy frame / đóng bằng X), SaveBar
(Save / Discard / đọc trạng thái), ẩn Dev Console của `shopify app dev`. Kết quả từng helper: `reference/sites/shopify.md`.
"""
from __future__ import annotations

import re
import time

from playwright.sync_api import Frame, Page

ADMIN = "https://admin.shopify.com"


class Shopify:
    def __init__(self, sess):
        self.sess = sess

    def admin_url(self, store: str, path: str = "") -> str:
        return f"{ADMIN}/store/{store}/{path.lstrip('/')}"

    def open_app(self, page: Page, store: str, app_handle: str, path: str = "", app_host: str = "") -> Frame:
        """Mở trang app trong admin và trả frame app. Mở thẳng URL iframe thì App Bridge kéo về admin — luôn đi qua admin.

        `app_host`: đoạn host của app (vd `cms.example.com`) để chọn đúng iframe khi admin giữ nhiều iframe app.
        """
        url = self.admin_url(store, f"apps/{app_handle}/{path.lstrip('/')}".rstrip("/"))
        self.sess.goto(page, url)
        return self.app_frame(page, app_host)

    def app_frame(self, page: Page, app_host: str = "") -> Frame:
        if app_host:
            return self.sess.frame(page, app_host)
        handle = page.locator("iframe[name='app-iframe']").first.element_handle(timeout=30000)
        frame = handle.content_frame()
        if frame is None:
            page.reload(wait_until="domcontentloaded")
            frame = page.locator("iframe[name='app-iframe']").first.element_handle(timeout=30000).content_frame()
        return frame

    def modal_frame(self, page: Page, route: str = "", timeout_s: float = 15) -> Frame:
        """Max modal App Bridge: iframe riêng ở document admin, URL = route của app mở trong modal (vd `/product-groups/new`).

        Tìm theo PATH của URL frame (bỏ query) trong `page.frames` trước — `src` của phần tử iframe max modal không chứa
        route nên `sess.frame(route)` hụt; không truyền route thì rơi về đoạn `modal` trong src.
        """
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            for f in page.frames:
                path = f.url.split("?")[0]
                if route and (path.endswith(route) or re.search(route, path)):
                    return f
            # a cross-site modal iframe can be missing from page.frames: walk the <iframe> elements of the admin document
            # and match the route (literal or regex) on the src path
            if route:
                for el in page.locator("iframe").all():
                    try:
                        src = (el.get_attribute("src", timeout=1000) or "").split("?")[0]
                        if src and re.search(route, src):
                            cf = el.element_handle(timeout=1000).content_frame()
                            if cf and re.search(route, cf.url.split("?")[0]):
                                return cf
                    except Exception:
                        continue
            if not route:
                return self.sess.frame(page, "modal", timeout_s=timeout_s, reload_once=False)
            time.sleep(0.5)
        raise AssertionError(f"Không thấy max modal có route '{route}' sau {timeout_s:.0f}s.")

    def open_max_modal(self, page: Page, trigger, route: str, tries: int = 6) -> Frame:
        """Bấm `trigger` (tile / nút trong frame app) tới khi max modal `route` mở, chờ React hydrate rồi trả frame.

        Cú bấm ngay khi trang vừa hiện bị nuốt (handler chưa gắn) → bấm lại; modal chạy vite dev hiện HTML SSR trước khi
        hydrate → gõ sớm chỉ đổi DOM. Tự `accept_dialogs` để rời form dirty không làm driver đứng.
        """
        self.sess.accept_dialogs(page)
        # Count the modal as opened as soon as its <iframe> element exists with the route in src: the frame itself can
        # take > 4 s to navigate, and a second click then lands on the modal overlay (pointer intercepted, 30 s timeout).
        opening = ("(r) => [...document.querySelectorAll('iframe')].some(f => (f.name || '').includes('/modal/')"
                   " && new RegExp(r).test((f.src || '').split('?')[0]))")
        has = lambda: (any(re.search(route, f.url.split("?")[0]) for f in page.frames)
                       or page.evaluate(opening, route))
        if not self.sess.click_until(trigger, has, tries=tries, wait_ms=4000):
            raise AssertionError(f"Bấm {tries} lần mà max modal '{route}' không mở.")
        frame = self.modal_frame(page, route, timeout_s=60)
        self.sess.wait_hydrated(frame)
        return frame

    def close_max_modal(self, page: Page) -> None:
        """Nút X trên title bar max modal: nằm trong shadow DOM ở document admin (role locator xuyên được, CSS thì không);
        `click()` bị chặn, `dispatch_event` bị bỏ qua → click chuột thật vào nút Close enabled ở góc trên phải."""
        width = (page.viewport_size or {}).get("width") or page.evaluate("innerWidth")
        box = None
        for b in page.get_by_role("button", name=re.compile("close", re.I)).all():
            bb = b.bounding_box()
            if bb and bb["y"] < 80 and bb["x"] > width - 150 and b.is_enabled():
                box = bb
        if not box:
            raise AssertionError("Không thấy nút X (Close) của max modal ở góc trên phải.")
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

    def leave_clean(self, page: Page, route: str = "", timeout_ms: int = 15000) -> bool:
        """Trước khi rời editor dirty: bấm Discard trên SaveBar rồi chờ iframe max modal `route` biến mất."""
        btn = page.get_by_role("button", name="Discard", exact=True)
        if btn.count():
            btn.first.click()
        if not route:
            return True
        try:
            page.wait_for_function(
                "(r) => ![...document.querySelectorAll('iframe')].some(f => new RegExp(r).test((f.src || '').split('?')[0]))",
                arg=route, timeout=timeout_ms)
            return True
        except Exception:
            return False

    def hide_dev_console(self, page: Page):
        """Panel 'Dev Console' của `shopify app dev` phủ ~250px đáy admin và max modal: click ở đó trúng panel. Ẩn đi (chỉ UI,
        lần tải sau hiện lại). Trả khung panel sau khi ẩn, hoặc None khi không có panel."""
        panel = page.locator("[class*='_DevTool_']").first
        hide = panel.locator("s-internal-button[accessibilitylabel=hide] button").first
        if panel.count() and hide.count() and hide.is_visible():
            hide.click(timeout=5000)
            page.wait_for_timeout(500)
        return panel.bounding_box() if panel.count() else None

    def expect_toast(self, page: Page, text: str, timeout_ms: int = 10000) -> str:
        """Chờ toast chứa `text`. Tìm ở document admin trước (App Bridge vẽ toast ở đó), rồi tới frame app."""
        for scope in (page, self.app_frame(page)):
            loc = scope.get_by_text(text, exact=False).first
            try:
                loc.wait_for(state="visible", timeout=timeout_ms)
                return loc.inner_text()
            except Exception:
                continue
        raise AssertionError(f"Không thấy toast chứa '{text}'.")

    def save_bar_state(self, page: Page) -> dict:
        """Nút trên SaveBar ở document admin (shadow DOM, đọc qua role): {"Save": enabled?, "Discard": enabled?}.
        Đọc ở admin, không ở `<ui-save-bar>` trong frame app — App Bridge có thể không áp `disabled` đổi sau khi bar hiện."""
        out = {}
        for name in ("Save", "Discard"):
            btn = page.get_by_role("button", name=name, exact=True)
            out[name] = btn.first.is_enabled() if btn.count() else None
        return out

    def save_bar(self, page: Page, action: str = "Save") -> None:
        """Bấm Save / Discard trên SaveBar (contextual bar 'Unsaved changes'). Bar chỉ hiện khi form app báo dirty."""
        for scope in (page, self.app_frame(page)):
            btn = scope.get_by_role("button", name=action, exact=True)
            if btn.count():
                btn.first.click()
                return
        raise AssertionError(f"Không thấy nút '{action}' trên SaveBar.")

    def storefront_preview(self, page: Page, store: str) -> Page:
        """Mở storefront có phiên preview (store dev có mật khẩu): icon con mắt 'View your online store' cạnh mục
        Online Store ở sidebar admin.

        Mở thẳng `<shop>.myshopify.com` sẽ bị đẩy về /password; AI không nhập mật khẩu storefront. Con mắt là `button`
        (không phải `link`) và chỉ hiện khi hover mục Online Store — hover trước rồi mới bấm. Không mở được tab mới → case
        storefront ghi Blocked.
        """
        self.sess.goto(page, self.admin_url(store))
        nav = page.get_by_role("link", name="Online Store", exact=True).first
        nav.wait_for(state="visible", timeout=30000)
        nav.hover()
        eye = page.get_by_role("button", name="View your online store").or_(
            page.get_by_role("link", name="View your online store")).first
        eye.wait_for(state="visible", timeout=10000)
        return self.sess.click_new_tab(page, eye)
