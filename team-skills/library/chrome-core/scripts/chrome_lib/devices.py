"""Giả lập thiết bị bằng context Playwright riêng, mang theo phiên đăng nhập.

Vì sao không dùng CDP `Emulation.*` trên tab: lệnh chỉ áp cho target nhận lệnh, iframe khác site là target riêng nên vẫn
thấy UA desktop (đã kiểm bằng thực nghiệm). Context Playwright tạo bằng `new_context(**device)` thì Playwright tự áp cho mọi frame.
Context mới không có cookie → chép `storage_state()` từ context mặc định (profile đã đăng nhập) sang.

Giới hạn: context mới chặn cookie bên thứ 3 như cửa sổ ẩn danh; trang dựa vào cookie bên thứ 3 trong iframe có thể khác
với cửa sổ thường. Context sống tới khi script ngắt kết nối.
"""
from __future__ import annotations

import re

from playwright.sync_api import BrowserContext, Page, Playwright

from .session import Session, target_id

# mobile = máy Android: cùng engine Chromium với Chrome đang chạy. UA iOS cũ trong bộ thiết bị của Playwright bị trang
# lớn chặn ("older version of iOS, not supported" — Shopify admin); muốn giả UA iPhone thì gọi thẳng tên máy.
ALIASES = {"mobile": "Pixel 10", "tablet": "Nexus 10"}  # tablet Android 800px (≥ 768): mọi UA iOS / iPad bị admin Shopify chặn


def device_names(pw: Playwright) -> list[str]:
    return sorted(pw.devices)


def emulate(pw: Playwright, sess: Session, device: str) -> Page:
    name = ALIASES.get(device, device)
    if name not in pw.devices:
        raise SystemExit(f"Không có thiết bị '{device}'. Dùng mobile / tablet hoặc tên trong `chrome.py devices`.")
    spec = dict(pw.devices[name])
    # UA của bộ thiết bị ghim một bản Chrome cũ hơn bản đang chạy → đổi số phiên bản cho khớp, tránh bị chê trình duyệt cũ
    spec["user_agent"] = re.sub(r"Chrome/[\d.]+", f"Chrome/{sess.browser.version}", spec["user_agent"])
    state = sess.ctx.storage_state()
    ctx: BrowserContext = sess.browser.new_context(storage_state=state, **spec)
    page = ctx.new_page()
    tid = target_id(ctx, page)
    if tid:
        sess.registry.add_tab(sess.owner, tid, role=f"device:{name}")
    sess.watch(page)
    return page
