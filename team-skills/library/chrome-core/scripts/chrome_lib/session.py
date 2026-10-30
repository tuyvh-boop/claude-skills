"""Lõi: nối Chrome riêng, giữ tab theo owner, tìm frame, ghi console + network, chụp, mở tab mới.

Mọi bẫy dưới đây đã gặp thật (Playwright Python 1.63, Chrome 154):
- `page.frames` không liệt kê iframe app khác site trên trang tải trước lúc nối, có khi cả sau reload → tìm frame từ
  phần tử `<iframe>` (`content_frame()`), không từ `page.frames`.
- `ctx.expect_page()` bắt cả tab mới của owner khác (cùng context mặc định) → luôn `page.expect_popup()`.
- Chạy song song, cú bấm mở popup thỉnh thoảng không ăn → không thấy tab nào có opener là tab mình thì bấm lại một lần.
- Cửa sổ thu nhỏ thì chụp treo dù có cờ chống background → đưa về `normal` trước khi chụp.
- `connect_over_cdp` treo nếu có tab cũ không trả lời → luôn có timeout.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from playwright.sync_api import Browser, BrowserContext, Frame, Page, Playwright
from playwright.sync_api import TimeoutError as PwTimeout

from .config import Config, safe_url
from .owners import Registry


class ChromeCoreError(Exception):
    pass


class LoginRequired(ChromeCoreError):
    pass


class NotAllowed(ChromeCoreError):
    pass


class TabGone(ChromeCoreError):
    pass


def target_id(ctx: BrowserContext, page: Page) -> str | None:
    try:
        s = ctx.new_cdp_session(page)
        tid = s.send("Target.getTargetInfo")["targetInfo"]["targetId"]
        s.detach()
        return tid
    except Exception:
        return None


class Session:
    """Một lượt làm việc của một owner trên Chrome riêng."""

    def __init__(self, pw: Playwright, cfg: Config, owner: str):
        if not owner:
            raise ChromeCoreError("Thiếu owner: truyền --owner <mã task>@<session> hoặc đặt env CHROME_CORE_OWNER.")
        self.cfg = cfg
        self.owner = owner
        self.registry = Registry(cfg.state_dir)
        try:
            self.browser: Browser = pw.chromium.connect_over_cdp(cfg.endpoint, timeout=15000)
        except Exception as e:
            raise ChromeCoreError(f"Không nối được Chrome ở {cfg.endpoint} — đã chạy `chrome.py launch` chưa? ({e})")
        self.ctx: BrowserContext = self.browser.contexts[0]
        self.bcdp = self.browser.new_browser_cdp_session()
        self.console: list[dict] = []
        self.network: list[dict] = []
        self.step = ""
        self._watched: set[int] = set()
        self._dialogs: set[int] = set()
        self.registry.touch(owner)
        self._prune()

    # ---------- tab theo owner ----------
    def _live_targets(self) -> dict[str, dict]:
        return {t["targetId"]: t for t in self.bcdp.send("Target.getTargets")["targetInfos"] if t["type"] == "page"}

    def _prune(self) -> None:
        self.registry.prune_dead_tabs(set(self._live_targets()))

    def _page_by_target(self, tid: str, wait_s: float = 5) -> Page | None:
        deadline = time.time() + wait_s
        while time.time() < deadline:
            for pg in list(self.ctx.pages):
                if target_id(self.ctx, pg) == tid:
                    return pg
            time.sleep(0.1)
        return None

    def main_page(self) -> Page:
        """Tab chính của owner; chưa có thì mở một cửa sổ riêng cho owner."""
        tabs = self.registry.tabs_of(self.owner)
        live = self._live_targets()
        for tid, meta in tabs.items():
            if meta.get("role") == "main" and tid in live:
                pg = self._page_by_target(tid)
                if pg:
                    return self.watch(pg)
        tid = self.bcdp.send("Target.createTarget", {"url": "about:blank", "newWindow": True})["targetId"]
        self.registry.add_tab(self.owner, tid, role="main")
        pg = self._page_by_target(tid)
        if not pg:
            raise ChromeCoreError("Mở cửa sổ mới cho owner nhưng Playwright không thấy tab.")
        return self.watch(pg)

    def owned_pages(self) -> list[Page]:
        tabs = self.registry.tabs_of(self.owner)
        return [pg for pg in list(self.ctx.pages) if target_id(self.ctx, pg) in tabs]

    def page_matching(self, url_part: str) -> Page:
        for pg in self.owned_pages():
            if url_part in pg.url:
                return self.watch(pg)
        raise TabGone(f"Owner {self.owner} không có tab nào chứa '{url_part}'.")

    # ---------- rào ----------
    def guard(self, url: str) -> None:
        if not self.cfg.url_allowed(url):
            raise NotAllowed(f"{safe_url(url)} ngoài origin được phép (config.yml → sites.*.allowed_origins).")

    def check_login(self, page: Page) -> None:
        if self.cfg.is_login_page(page.url):
            raise LoginRequired(
                f"Trang đang ở màn đăng nhập ({safe_url(page.url)}). Nhờ user đăng nhập trong cửa sổ Chrome đó rồi chạy lại. "
                "Không tự điền mật khẩu, không đổi công cụ, không xoá profile."
            )

    def goto(self, page: Page, url: str, wait_until: str = "domcontentloaded") -> Page:
        self.guard(url)
        page.goto(url, wait_until=wait_until)
        self.check_login(page)
        return page

    # ---------- console + network ----------
    def watch(self, page: Page) -> Page:
        if id(page) in self._watched:
            return page
        self._watched.add(id(page))

        def on_console(msg):
            loc = msg.location or {}
            self.console.append({"t": round(time.time(), 3), "step": self.step, "type": msg.type, "text": msg.text[:2000],
                                 "from": safe_url(loc.get("url", ""))})

        def on_response(resp):
            if resp.status >= 400:
                self.network.append({"t": round(time.time(), 3), "step": self.step, "status": resp.status, "method": resp.request.method,
                                     "url": safe_url(resp.url), "frame": safe_url(resp.frame.url) if resp.frame else ""})

        def on_failed(req):
            # 404 rồi ERR_ABORTED cho cùng URL = một lỗi, đã ghi ở on_response
            if (req.failure or "").endswith("ERR_ABORTED") and any(
                    r["url"] == safe_url(req.url) and isinstance(r["status"], int) for r in self.network[-5:]):
                return
            self.network.append({"t": round(time.time(), 3), "step": self.step, "status": "failed", "method": req.method,
                                 "url": safe_url(req.url), "error": (req.failure or "")[:200]})

        page.on("console", on_console)
        page.on("response", on_response)
        page.on("requestfailed", on_failed)
        page.on("pageerror", lambda err: self.console.append(
            {"t": round(time.time(), 3), "step": self.step, "type": "pageerror", "text": str(err)[:2000], "from": safe_url(page.url)}))
        return page

    # ---------- frame ----------
    def frame(self, page: Page, url_contains: str, timeout_s: float = 20, reload_once: bool = True) -> Frame:
        """Frame có `src` / URL chứa đoạn cho trước, tìm cả iframe lồng. Đi từ phần tử `<iframe>` (xem docstring module)."""
        deadline = time.time() + timeout_s
        reloaded = False
        while True:
            found = _search_frames(page.main_frame, url_contains)
            if found:
                return found
            if time.time() > deadline:
                if reload_once and not reloaded:
                    page.reload(wait_until="domcontentloaded")
                    reloaded = True
                    deadline = time.time() + timeout_s
                    continue
                raise ChromeCoreError(f"Không thấy iframe chứa '{url_contains}' sau {timeout_s:.0f}s (đã reload).")
            time.sleep(0.5)

    # ---------- tab mới ----------
    def click_new_tab(self, page: Page, locator, timeout_ms: int = 8000) -> Page:
        """Bấm phần tử mở tab mới (window.open / target=_blank) và trả tab mới, đã đăng ký vào owner."""
        my_tid = target_id(self.ctx, page)
        before = set(self._live_targets())
        for attempt in (1, 2):
            try:
                with page.expect_popup(timeout=timeout_ms) as info:
                    locator.click()
                popup = info.value
                break
            except PwTimeout:
                opened = [t for tid, t in self._live_targets().items() if tid not in before and t.get("openerId") == my_tid]
                if opened:
                    popup = self._page_by_target(opened[0]["targetId"])
                    break
                if attempt == 2:
                    raise ChromeCoreError("Bấm 2 lần mà không có tab mới nào mở từ tab này.")
        tid = target_id(self.ctx, popup)
        if tid:
            self.registry.add_tab(self.owner, tid, opener=my_tid)
        popup.wait_for_load_state("domcontentloaded")
        return self.watch(popup)

    # ---------- trang chưa sẵn sàng ----------
    def wait_hydrated(self, scope, selector: str = "input, button, [role=button]", timeout_ms: int = 120000) -> None:
        """Chờ React nhận DOM: trang SSR (vite dev, remix / react-router) hiện HTML vài giây trước khi hydrate — gõ / bấm
        lúc đó chỉ đổi DOM, state không đổi (Enter không thêm dòng, Save bar không hiện) → Fail giả. Đạt khi phần tử
        đầu tiên khớp `selector` mang key `__react*`."""
        scope.wait_for_function(
            """(sel) => { const e = document.querySelector(sel);
                return !!e && Object['keys'](e).some(k => k.startsWith('__react')); }""",
            arg=selector, timeout=timeout_ms)

    def click_until(self, locator, done, tries: int = 6, wait_ms: int = 3000) -> bool:
        """Bấm tới khi `done()` đúng: cú bấm trước khi handler gắn bị nuốt (tile / nút mở modal ngay khi trang vừa hiện).
        `done` là hàm không tham số, trả bool; chờ tối đa `wait_ms` sau mỗi cú bấm."""
        for _ in range(tries):
            locator.click()
            deadline = time.time() + wait_ms / 1000
            while time.time() < deadline:
                if done():
                    return True
                time.sleep(0.3)
        return False

    def accept_dialogs(self, page: Page) -> None:
        """Tự chấp nhận hộp beforeunload / alert / confirm. Hộp "Leave site?" khi điều hướng khỏi form dirty làm driver
        Playwright đứng (python 100% CPU, không thoát). Chỉ bỏ state chưa lưu trong tab của chính owner."""
        if id(page) not in self._dialogs:
            self._dialogs.add(id(page))
            page.on("dialog", _accept_quietly)

    # ---------- chụp ----------
    def ensure_drawn(self, page: Page) -> None:
        """Cửa sổ đang thu nhỏ thì đưa về normal: Chrome không vẽ cửa sổ thu nhỏ nên chụp sẽ treo."""
        tid = target_id(self.ctx, page)
        if not tid:
            return
        try:
            win = self.bcdp.send("Browser.getWindowForTarget", {"targetId": tid})
        except Exception:
            return
        if win["bounds"].get("windowState") == "minimized":
            self.bcdp.send("Browser.setWindowBounds", {"windowId": win["windowId"], "bounds": {"windowState": "normal"}})
            time.sleep(0.3)

    def shot(self, page: Page, path: Path, full_page: bool = False) -> Path:
        self.ensure_drawn(page)
        path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path), full_page=full_page, timeout=20000)
        return path

    # ---------- dọn ----------
    def close_tab(self, page: Page) -> None:
        tid = target_id(self.ctx, page)
        page.close()
        if tid:
            self.registry.drop_tabs(self.owner, [tid])

    def release(self) -> int:
        """Đóng mọi tab của owner và xoá owner khỏi sổ."""
        entry = self.registry.remove_owner(self.owner)
        live = self._live_targets()
        n = 0
        for tid in entry.get("tabs", {}):
            if tid in live:
                try:
                    self.bcdp.send("Target.closeTarget", {"targetId": tid})
                    n += 1
                except Exception:
                    pass
        return n

    def snapshot(self, page: Page, max_chars: int = 6000) -> str:
        """Accessibility snapshot của trang + từng iframe (aria_snapshot không tự đi vào iframe)."""
        parts = []
        for label, fr in _walk_frames(page.main_frame):
            try:
                text = fr.locator("body").aria_snapshot(timeout=5000)
            except Exception as e:
                text = f"(không đọc được: {str(e)[:80]})"
            parts.append(f"### frame {label}\n{text}")
        out = "\n\n".join(parts)
        return out if len(out) <= max_chars else out[:max_chars] + f"\n… (cắt, tổng {len(out)} ký tự; tăng --max-chars nếu cần)"

    def dump_logs(self, out_dir: Path, prefix: str) -> dict:
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = {}
        for name, rows in (("console", self.console), ("network", self.network)):
            p = out_dir / f"{prefix}-{name}.jsonl"
            p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
            paths[name] = str(p)
        return paths

    def disconnect(self) -> None:
        try:
            self.browser.close()  # với connect_over_cdp: chỉ ngắt kết nối + đóng context do script tạo, không tắt Chrome
        except Exception:
            pass


def _accept_quietly(dialog) -> None:
    # beforeunload có thể đã tự đóng khi điều hướng xong trước lúc handler chạy → accept báo "No dialog is showing";
    # để lỗi đó lọt ra event loop là driver đứng
    try:
        dialog.accept()
    except Exception:
        pass


def _child_frames(frame: Frame) -> list[tuple[str, Frame]]:
    out = []
    try:
        handles = frame.locator("iframe").element_handles()
    except Exception:
        return out
    for h in handles:
        try:
            src = h.get_attribute("src") or ""
            cf = h.content_frame()
        except Exception:
            continue
        if cf:
            out.append((src, cf))
    return out


def _search_frames(frame: Frame, needle: str) -> Frame | None:
    for src, cf in _child_frames(frame):
        if needle in src or needle in (cf.url or ""):
            return cf
        deeper = _search_frames(cf, needle)
        if deeper:
            return deeper
    return None


def _walk_frames(frame: Frame, label: str = "top") -> list[tuple[str, Frame]]:
    out = [(f"{label} {safe_url(frame.url)}", frame)]
    for i, (src, cf) in enumerate(_child_frames(frame)):
        out.extend(_walk_frames(cf, f"{label}>{i}"))
    return out
