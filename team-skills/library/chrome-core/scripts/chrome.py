# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.63", "pyyaml>=6"]
# ///
"""chrome.py — điều khiển Chrome riêng (profile đã đăng nhập) cho test e2e. Playwright qua CDP; CDP thô chỉ khi Playwright
không bọc. Mọi lệnh có --help. Lệnh đụng tab cần owner: --owner <mã task>@<session> hoặc env CHROME_CORE_OWNER.

Phiên:     doctor · setup · launch · status · release · close
Một bước:  tabs · goto · eval · shot · console · snapshot · devices
Kịch bản:  run <steps.py>        (hàm run(ctx); xem examples/)
Khác:      console-diff · learn · serve-fixtures · selftest
"""
from __future__ import annotations

import argparse
import http.server
import importlib.metadata
import importlib.util
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import expect, sync_playwright  # noqa: E402

from chrome_lib import config as cfgmod  # noqa: E402
from chrome_lib.config import Config, Site, safe_url, scrub  # noqa: E402
from chrome_lib.devices import device_names, emulate  # noqa: E402
from chrome_lib.owners import Registry  # noqa: E402
from chrome_lib.session import ChromeCoreError, Session, target_id  # noqa: E402
from chrome_lib.sites.shopify import Shopify  # noqa: E402

SKILL_DIR = cfgmod.SKILL_DIR
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CANDIDATES = SKILL_DIR / "reference" / "candidates.md"
SETUP_DOC = SKILL_DIR / "reference" / "setup-first-run.md"
SITES = {"shopify": Shopify}
LAUNCH_FLAGS = [
    "--no-first-run", "--no-default-browser-check",
    "--remote-debugging-address=127.0.0.1",
    # Cửa sổ bị che vẫn vẽ (lỗi lặp nhiều nhất khi test bằng Chrome thường). Không cứu được cửa sổ THU NHỎ — Session.shot lo.
    "--disable-backgrounding-occluded-windows", "--disable-renderer-backgrounding", "--disable-background-timer-throttling",
]


def out(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2) if not isinstance(obj, str) else obj)


def owner_of(args) -> str:
    return getattr(args, "owner", None) or os.environ.get("CHROME_CORE_OWNER", "")


def chrome_up(cfg: Config) -> dict | None:
    try:
        with urllib.request.urlopen(f"{cfg.endpoint}/json/version", timeout=2) as r:
            return json.load(r)
    except OSError:
        return None


def start_chrome(cfg: Config, url: str = "about:blank", headless: bool = False, extra: list[str] | None = None) -> int:
    cfg.profile_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(cfg.profile_dir, 0o700)
    cmd = [cfg.chrome(), f"--user-data-dir={cfg.profile_dir}", f"--remote-debugging-port={cfg.port}", *LAUNCH_FLAGS,
           *(["--headless=new", "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36", "--window-size=1440,900"] if headless else []), *(extra or []), url]
    # start_new_session: Chrome không chết theo khi app Claude / shell cha tắt.
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    for _ in range(60):
        if chrome_up(cfg):
            return proc.pid
        time.sleep(0.25)
    raise SystemExit(f"Chrome không mở cổng {cfg.port} sau 15s.")


# ---------------- phiên ----------------
def cmd_doctor(args, cfg: Config) -> int:
    rep = {
        "config": str(cfgmod.CONFIG_PATH) if cfgmod.CONFIG_PATH.exists() else "chưa có (chạy setup, hoặc chỉ test loopback)",
        "playwright": importlib.metadata.version("playwright"),
        "chrome_bin": cfg.chrome(),
        "profile_dir": str(cfg.profile_dir),
        "profile_exists": cfg.profile_dir.exists() and any(cfg.profile_dir.iterdir()),
        "chrome_running": bool(chrome_up(cfg)),
        "sites": {n: s.allowed_origins for n, s in cfg.sites.items()},
    }
    if args.session:
        site = cfg.sites.get(args.site or "")
        if not site:
            raise SystemExit(f"--session cần --site trong {list(cfg.sites)}")
        if not rep["chrome_running"]:
            start_chrome(cfg, headless=cfg.headless)
        with sync_playwright() as pw:
            sess = Session(pw, cfg, owner_of(args) or "doctor")
            page = sess.main_page()
            url = args.url or site.allowed_origins[0]
            sess.guard(url)
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            rep["session_url"] = safe_url(page.url)
            rep["logged_in"] = not cfg.is_login_page(page.url)
            if owner_of(args) == "" or args.release:
                sess.release()
            sess.disconnect()
    out(rep)
    return 0 if not args.session or rep.get("logged_in") else 3


def cmd_setup(args, cfg: Config) -> int:
    if not args.ack:
        print(SETUP_DOC.read_text())
        print("\n→ Trình nguyên khối trên cho user, chờ user xác nhận đã tạo account test, rồi chạy lại lệnh với --ack.")
        return 2
    site = Site(name=args.site, allowed_origins=args.allow, login_url=args.login_url or "",
                login_markers=args.login_marker or [])
    cfgmod.save_site(site)
    cfg = cfgmod.load()
    if not chrome_up(cfg):
        start_chrome(cfg, url=args.login_url or args.allow[0])
    else:
        with sync_playwright() as pw:
            sess = Session(pw, cfg, "setup")
            page = sess.main_page()
            page.goto(args.login_url or args.allow[0])
            sess.disconnect()
    out({"saved_site": args.site, "allowed_origins": args.allow,
         "next": "User tự đăng nhập trong cửa sổ Chrome vừa mở (AI không nhập mật khẩu). Xong thì chạy "
                 f"`chrome.py doctor --session --site {args.site} --release`."})
    return 0


def cmd_launch(args, cfg: Config) -> int:
    info = chrome_up(cfg)
    if info:
        out({"running": True, "browser": info.get("Browser"), "port": cfg.port, "note": "đã chạy sẵn, không mở thêm"})
        return 0
    pid = start_chrome(cfg, url=args.url or "about:blank", headless=(cfg.headless or args.headless) and not args.headed)
    out({"running": True, "pid": pid, "port": cfg.port, "profile": str(cfg.profile_dir)})
    return 0


def cmd_status(args, cfg: Config) -> int:
    reg = Registry(cfg.state_dir).read()
    now = time.time()
    owners = {o: {"tabs": len(e.get("tabs", {})), "idle_min": round((now - e.get("last_seen", now)) / 60, 1),
                  "stale": (now - e.get("last_seen", now)) / 3600 > cfg.owner_ttl_hours} for o, e in reg.items()}
    out({"chrome_running": bool(chrome_up(cfg)), "port": cfg.port, "owners": owners})
    return 0


def cmd_release(args, cfg: Config) -> int:
    reg = Registry(cfg.state_dir)
    targets = []
    if args.stale:
        now = time.time()
        targets = [o for o, e in reg.read().items() if (now - e.get("last_seen", now)) / 3600 > cfg.owner_ttl_hours]
    elif owner_of(args):
        targets = [owner_of(args)]
    else:
        raise SystemExit("Cần --owner hoặc --stale.")
    closed = {}
    with sync_playwright() as pw:
        for o in targets:
            sess = Session(pw, cfg, o)
            closed[o] = sess.release()
            sess.disconnect()
    out({"released": closed})
    return 0


def cmd_close(args, cfg: Config) -> int:
    reg = Registry(cfg.state_dir).read()
    live = [o for o, e in reg.items() if e.get("tabs")]
    if live and not args.force:
        out({"closed": False, "reason": "còn owner đang giữ tab", "owners": live,
             "hint": "release từng owner, hoặc --force nếu chắc không ai đang chạy"})
        return 1
    if not chrome_up(cfg):
        out({"closed": False, "reason": "Chrome không chạy"})
        return 0
    with sync_playwright() as pw:
        b = pw.chromium.connect_over_cdp(cfg.endpoint, timeout=15000)
        b.new_browser_cdp_session().send("Browser.close")
    for o in list(reg):
        Registry(cfg.state_dir).remove_owner(o)
    out({"closed": True, "profile_kept": str(cfg.profile_dir)})
    return 0


# ---------------- một bước ----------------
def _open(pw, cfg, args):
    sess = Session(pw, cfg, owner_of(args))
    if getattr(args, "device", None):
        return sess, emulate(pw, sess, args.device)  # tab mới trong context thiết bị, đóng khi lệnh xong
    page = sess.page_matching(args.tab) if getattr(args, "tab", None) else sess.main_page()
    return sess, page


def cmd_tabs(args, cfg: Config) -> int:
    with sync_playwright() as pw:
        sess = Session(pw, cfg, owner_of(args))
        meta = sess.registry.tabs_of(sess.owner)
        rows = []
        for pg in sess.owned_pages():
            tid = target_id(sess.ctx, pg)
            rows.append({"target": tid[:8] if tid else None, "url": safe_url(pg.url), "role": meta.get(tid, {}).get("role")})
        sess.disconnect()
    out(rows)
    return 0


def cmd_goto(args, cfg: Config) -> int:
    with sync_playwright() as pw:
        sess, page = _open(pw, cfg, args)
        sess.goto(page, args.url)
        out({"url": safe_url(page.url), "title": page.title()})
        sess.disconnect()
    return 0


def _js_source(args) -> str:
    return Path(args.js_file).read_text() if args.js_file else args.js


def cmd_eval(args, cfg: Config) -> int:
    with sync_playwright() as pw:
        sess, page = _open(pw, cfg, args)
        if args.url:
            sess.goto(page, args.url)
        target = sess.frame(page, args.frame) if args.frame else page
        res = target.evaluate(_js_source(args))
        out(res)
        sess.disconnect()
    return 0


def cmd_shot(args, cfg: Config) -> int:
    with sync_playwright() as pw:
        sess, page = _open(pw, cfg, args)
        if args.url:
            sess.goto(page, args.url)
        p = sess.shot(page, Path(args.out), full_page=args.full)
        out({"shot": str(p), "url": safe_url(page.url)})
        sess.disconnect()
    return 0


def cmd_console(args, cfg: Config) -> int:
    with sync_playwright() as pw:
        sess, page = _open(pw, cfg, args)
        if args.url:
            sess.goto(page, args.url)
        else:
            page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(int(args.seconds * 1000))
        rows = [r for r in sess.console if args.all or r["type"] in ("error", "warning", "pageerror")]
        res = {"console": rows, "network_errors": sess.network}
        if args.out_dir:
            res["files"] = sess.dump_logs(Path(args.out_dir), args.prefix)
        out(res)
        sess.disconnect()
    return 0


def cmd_snapshot(args, cfg: Config) -> int:
    with sync_playwright() as pw:
        sess, page = _open(pw, cfg, args)
        if args.url:
            sess.goto(page, args.url)
        print(sess.snapshot(page, max_chars=args.max_chars))
        sess.disconnect()
    return 0


def cmd_devices(args, cfg: Config) -> int:
    with sync_playwright() as pw:
        names = device_names(pw)
    out({"aliases": {"mobile": "Pixel 10", "tablet": "Nexus 10"}, "devices": [n for n in names if args.filter.lower() in n.lower()]})
    return 0


# ---------------- kịch bản ----------------
CASE_ID = re.compile(r"^[A-Z]{2,5}-\d+(?:[-_]|$)")


class Ctx:
    """Đối tượng truyền vào run(ctx) của steps.py."""

    def __init__(self, pw, sess: Session, page, out_dir: Path, prefix: str):
        self.pw, self.sess, self.page, self.out_dir, self.prefix = pw, sess, page, out_dir, prefix
        self.checks: list[dict] = []
        self.expect = expect  # playwright expect: ctx.expect(locator).to_have_text(...)
        self.notes: list[str] = []
        self._sites = {}

    def goto(self, url: str, page=None):
        return self.sess.goto(page or self.page, url)

    def frame(self, url_contains: str, page=None, timeout_s: float = 20):
        return self.sess.frame(page or self.page, url_contains, timeout_s=timeout_s)

    def click_new_tab(self, locator, page=None):
        return self.sess.click_new_tab(page or self.page, locator)

    def wait_hydrated(self, scope=None, selector: str = "input, button, [role=button]", timeout_ms: int = 120000):
        return self.sess.wait_hydrated(scope or self.page, selector, timeout_ms)

    def click_until(self, locator, done, tries: int = 6, wait_ms: int = 3000) -> bool:
        return self.sess.click_until(locator, done, tries, wait_ms)

    def accept_dialogs(self, page=None):
        return self.sess.accept_dialogs(page or self.page)

    def shot(self, name: str, page=None, full_page: bool = False) -> str:
        # Tên đã mở đầu bằng mã (TC-05-…, TR-01-…) thì giữ nguyên: một steps chạy nhiều case vẫn ra ảnh đặt tên theo case.
        fname = f"{name}.png" if CASE_ID.match(name) else f"{self.prefix}-{name}.png"
        return str(self.sess.shot(page or self.page, self.out_dir / fname, full_page=full_page))

    def emulate(self, device: str):
        self.page = emulate(self.pw, self.sess, device)
        return self.page

    def cdp(self, page=None):
        return self.sess.ctx.new_cdp_session(page or self.page) if (page or self.page).context == self.sess.ctx \
            else (page or self.page).context.new_cdp_session(page or self.page)

    def snapshot(self, page=None) -> str:
        return self.sess.snapshot(page or self.page)

    def site(self, name: str):
        if name not in self._sites:
            self._sites[name] = SITES[name](self.sess)
        return self._sites[name]

    def check(self, ok: bool, what: str, actual=None) -> bool:
        self.checks.append({"ok": bool(ok), "what": what, "actual": actual})
        return bool(ok)

    def note(self, text: str) -> None:
        self.notes.append(text)

    def step(self, name: str) -> None:
        """Đánh dấu bước: các dòng console / network sau đó mang `step` = name (biết lỗi do thao tác nào)."""
        self.sess.step = name


class _ScrubbedStream:
    def __init__(self, inner):
        self._inner = inner

    def write(self, text):
        return self._inner.write(scrub(text))

    def __getattr__(self, name):
        return getattr(self._inner, name)


def cmd_run(args, cfg: Config) -> int:
    steps = Path(args.steps).resolve()
    spec = importlib.util.spec_from_file_location("steps", steps)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out_dir = Path(args.out).resolve()
    # --raw-dir: result / console / network / ảnh lỗi để riêng (vd evidence/_raw), ảnh ctx.shot vẫn ở --out
    raw_dir = Path(args.raw_dir).resolve() if args.raw_dir else out_dir
    raw_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix or steps.stem
    status, result, error = "ok", None, None
    with sync_playwright() as pw:
        sess = Session(pw, cfg, owner_of(args))
        peers = sess.registry.running_peers(sess.owner)
        if len(peers) + 1 > cfg.max_parallel_runs:
            print(f"⚠️  {len(peers) + 1} luồng `run` cùng task đang chạy ({', '.join(peers)} + {sess.owner}) > "
                  f"max_parallel_runs={cfg.max_parallel_runs}: api / dev server dễ ETIMEDOUT → kết quả rỗng giả. "
                  "Chạy tuần tự, hoặc gặp lỗi mạng thì chạy lại trước khi ghi Fail.", file=sys.stderr)
        sess.registry.set_running(sess.owner, True)
        page = sess.main_page()
        ctx = Ctx(pw, sess, page, out_dir, prefix)
        if args.device:
            ctx.emulate(args.device)
        real_stdout, sys.stdout = sys.stdout, _ScrubbedStream(sys.stdout)  # print() trong steps không lộ token
        try:
            if args.url:
                ctx.goto(args.url)
            result = mod.run(ctx)
        except ChromeCoreError as e:
            status, error = "blocked", str(e)
        except Exception as e:  # lỗi trong steps: vẫn ghi log để chẩn đoán
            status, error = "error", f"{type(e).__name__}: {str(e)[:1500]}"
        finally:
            sys.stdout = real_stdout
        if status != "ok" and not args.no_failure_shot:
            try:
                sess.shot(ctx.page, raw_dir / f"{prefix}-failure.png")
            except Exception:
                pass
        files = sess.dump_logs(raw_dir, prefix)
        sess.registry.set_running(sess.owner, False)
        if any(not c["ok"] for c in ctx.checks) and status == "ok":
            status = "check_failed"
        res = {"status": status, "error": error, "result": result, "checks": ctx.checks, "notes": ctx.notes,
               "console_errors": sum(r["type"] in ("error", "pageerror") for r in sess.console),
               "network_errors": len(sess.network), "files": files}
        res = json.loads(scrub(json.dumps(res, ensure_ascii=False)))
        (raw_dir / f"{prefix}-result.json").write_text(json.dumps(res, ensure_ascii=False, indent=2))
        if args.close_tabs:
            for pg in sess.owned_pages():
                if pg != page:
                    sess.close_tab(pg)
        sess.disconnect()
    out({k: res[k] for k in ("status", "error", "checks", "console_errors", "network_errors")} |
        {"result_file": str(raw_dir / f"{prefix}-result.json")})
    return {"ok": 0, "check_failed": 1, "blocked": 3}.get(status, 2)


# ---------------- khác ----------------
def _errors(path: str) -> set[str]:
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    norm = lambda s: re.sub(r"\d{3,}|[0-9a-f]{8,}", "#", s)  # bỏ số / hash đổi theo lượt
    return {f"{r.get('from', '')} :: {norm(r['text'])[:300]}" for r in rows if r.get("type") in ("error", "pageerror")}


def cmd_console_diff(args, cfg: Config) -> int:
    base, new = _errors(args.base), _errors(args.new)
    out({"only_in_new": sorted(new - base), "only_in_base": sorted(base - new), "in_both": len(base & new)})
    return 0


def cmd_learn(args, cfg: Config) -> int:
    """Ghi ứng viên tự cải thiện. Gặp lần 2 → báo ĐÚC. Không ghi ngày / mã task (luật của skill)."""
    text = CANDIDATES.read_text()
    pid = args.pattern_id.strip().lower()
    pat = re.compile(rf"^\| `{re.escape(pid)}` \| (.+?) \| (\d+) \|$", re.M)
    m = pat.search(text)
    if m:
        count = int(m.group(2)) + 1
        text = text[:m.start()] + f"| `{pid}` | {m.group(1)} | {count} |" + text[m.end():]
    else:
        if not args.desc:
            raise SystemExit("Ứng viên mới cần --desc.")
        count = 1
        line = f"| `{pid}` | {args.desc} ({args.kind}{', ' + args.site if args.site else ''}) | 1 |"
        text = text.rstrip("\n") + "\n" + line + "\n"
    CANDIDATES.write_text(text)
    msg = {"id": pid, "count": count}
    if count >= 2:
        msg["action"] = ("ĐÃ LẶP — đúc thành helper trong "
                         "chrome_lib (lõi nếu không phụ thuộc nền tảng, sites/<nền tảng>.py nếu có) + case selftest, rồi xoá "
                         "dòng ứng viên. Luật kỹ thuật: reference/self-improve.md.")
    out(msg)
    return 0


class _FixtureHandler(http.server.BaseHTTPRequestHandler):
    port = 0

    def do_GET(self):
        p = FIXTURES / self.path.split("?")[0].lstrip("/")
        if not p.is_file():
            self.send_response(404)
            self.end_headers()
            return
        body = p.read_text().replace("{PORT}", str(self.port)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def serve_fixtures(port: int) -> http.server.ThreadingHTTPServer:
    _FixtureHandler.port = port
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), _FixtureHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def cmd_serve_fixtures(args, cfg: Config) -> int:
    serve_fixtures(args.port)
    print(f"fixtures: http://localhost:{args.port}/top.html (Ctrl+C để dừng)", flush=True)
    while True:
        time.sleep(3600)


def cmd_selftest(args, cfg: Config) -> int:
    """Chạy toàn bộ lõi trên fixtures với một Chrome tạm (profile tạm, cổng tạm) — không đụng Chrome / profile thật."""
    fport, cport = free_port(), free_port()
    serve_fixtures(fport)
    tmp = Path(tempfile.mkdtemp(prefix="chrome-core-selftest-"))
    tcfg = Config(port=cport, state_dir=tmp / "state", profile_dir=tmp / "profile", chrome_bin=cfg.chrome_bin)
    tcfg.sites["fixture"] = Site("fixture", [f"http://localhost:{fport}"], f"http://localhost:{fport}/login.html",
                                 ["/login.html"])
    start_chrome(tcfg, headless=not args.headed)
    top = f"http://localhost:{fport}/top.html"
    results: list[tuple[str, bool, str]] = []

    def case(name, fn):
        try:
            detail = fn()
            results.append((name, True, str(detail or "")[:120]))
        except Exception as e:
            results.append((name, False, f"{type(e).__name__}: {str(e)[:200]}"))

    with sync_playwright() as pw:
        a = Session(pw, tcfg, "TASK-A@s1")
        pa = a.main_page()
        a.goto(pa, top)

        def frame_and_fill():
            app = a.frame(pa, "/app.html")
            app.get_by_label("Badge text").fill("A1")
            app.get_by_role("button", name="Save").click()
            assert app.get_by_role("status").inner_text() == "Saved: A1"
            return "fill + Save trong iframe khác site"
        case("frame trong iframe khác site", frame_and_fill)

        def nested_frame():
            third = a.frame(pa, "/third-party.html")
            assert third.get_by_role("button", name="Book a call").count() == 1
        case("frame lồng 2 tầng", nested_frame)

        def new_tab():
            app = a.frame(pa, "/app.html")
            tab = a.click_new_tab(pa, app.get_by_role("button", name="Open editor"))
            assert "/editor.html" in tab.url and a.registry.owner_of(target_id(a.ctx, tab)) == "TASK-A@s1"
            return "tab mới thuộc đúng owner"
        case("tab mới từ nút trong iframe", new_tab)

        def console_network():
            app = a.frame(pa, "/app.html")
            app.get_by_role("button", name="Call broken API").click()
            pa.wait_for_timeout(800)
            errs = [c for c in a.console if "fixture-app-error" in c["text"]]
            n404 = [n for n in a.network if n["status"] == 404 and n["url"].endswith("/api/missing")]
            assert errs and errs[0]["from"].endswith("/app.html") and n404
            return f"console={len(errs)} 404={len(n404)}"
        case("console + network của iframe", console_network)

        def owners_isolated():
            b = Session(pw, tcfg, "TASK-B@s2")
            pb = b.main_page()
            b.goto(pb, top)
            assert target_id(b.ctx, pb) != target_id(a.ctx, pa)
            assert {target_id(b.ctx, p) for p in b.owned_pages()}.isdisjoint({target_id(a.ctx, p) for p in a.owned_pages()})
            b.release()
            return "2 owner, 2 cửa sổ, không chung tab"
        case("owner tách nhau", owners_isolated)

        def snapshot():
            s = a.snapshot(pa)
            assert 'button "Open editor"' in s and 'button "Book a call"' in s
        case("snapshot đi vào iframe", snapshot)

        def guard():
            try:
                a.goto(pa, "https://example.com/")
            except ChromeCoreError:
                return "chặn origin ngoài config"
            raise AssertionError("không chặn")
        case("rào origin", guard)

        def login():
            try:
                a.goto(pa, f"http://localhost:{fport}/login.html")
            except ChromeCoreError as e:
                return "phát hiện trang login"
            raise AssertionError("không phát hiện login")
        case("phát hiện login", login)

        def device():
            m = emulate(pw, a, "mobile")
            logs = []
            m.on("console", lambda msg: logs.append(msg.text))
            m.goto(top)
            app = a.frame(m, "/app.html")
            assert app.evaluate("/Mobile/.test(navigator.userAgent)") is True
            return "UA mobile trong iframe"
        case("giả lập mobile tới iframe", device)

        def shot():
            p = a.shot(pa, tmp / "s.png")
            assert p.stat().st_size > 1000
        case("chụp", shot)

        def hydrate_click_leave():
            a.accept_dialogs(pa)
            a.goto(pa, f"http://localhost:{fport}/hydrate.html")
            btn = pa.get_by_role("button", name="Open")
            status = pa.get_by_role("status")
            btn.click()   # trước hydrate: bị nuốt
            assert status.inner_text() == ""
            a.wait_hydrated(pa, "input")
            assert a.click_until(btn, lambda: status.inner_text() == "opened", wait_ms=1500)
            a.goto(pa, top)   # beforeunload đã bật: không accept thì driver đứng
            assert pa.url.endswith("/top.html")
            return "chờ hydrate, bấm lại, rời trang dirty"
        case("trang SSR chưa hydrate + rời form dirty", hydrate_click_leave)

        def parallel_runs():
            reg = a.registry
            reg.set_running("TASK-A@x", True)
            reg.set_running("TASK-A@y", True)
            reg.set_running("TASK-B@z", True)
            peers = reg.running_peers("TASK-A@s1")
            reg.set_running("TASK-A@y", False)
            assert peers == ["TASK-A@x", "TASK-A@y"] and reg.running_peers("TASK-A@s1") == ["TASK-A@x"]
            return "đếm luồng run cùng task, bỏ task khác"
        case("đếm luồng run song song", parallel_runs)

        a.release()
        a.disconnect()
        try:
            pw.chromium.connect_over_cdp(tcfg.endpoint).new_browser_cdp_session().send("Browser.close")
        except Exception:
            pass

    ok = all(r[1] for r in results)
    for name, passed, detail in results:
        print(f"{'PASS' if passed else 'FAIL'}  {name}  {detail}")
    print(f"\n{sum(r[1] for r in results)}/{len(results)} pass")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def owner_arg(p, tab=True):
        p.add_argument("--owner", help="<mã task>@<session>; mặc định env CHROME_CORE_OWNER")
        if tab:
            p.add_argument("--tab", help="chọn tab của owner có URL chứa đoạn này (mặc định: tab chính)")
            p.add_argument("--device", help="mobile (Pixel 10, Android) | tablet (Nexus 10, Android 800px) | tên máy trong `devices` "
                                            "— mở tab mới giả lập thiết bị, cần --url")

    p = sub.add_parser("doctor", help="kiểm môi trường; --session --site X: kiểm phiên đăng nhập")
    p.add_argument("--session", action="store_true")
    p.add_argument("--site")
    p.add_argument("--url", help="trang để kiểm phiên (mặc định origin đầu tiên của site)")
    p.add_argument("--release", action="store_true", help="đóng tab kiểm sau khi xong")
    owner_arg(p, tab=False)

    p = sub.add_parser("setup", help="thiết lập lần đầu một site (in rủi ro + checklist account trước, cần --ack)")
    p.add_argument("--site", required=True)
    p.add_argument("--allow", nargs="+", required=True, help="origin được phép, vd https://admin.example.com")
    p.add_argument("--login-url")
    p.add_argument("--login-marker", nargs="*", help="đoạn URL nhận ra trang login, vd accounts.example.com")
    p.add_argument("--ack", action="store_true", help="user đã đọc rủi ro + đã tạo account test")

    p = sub.add_parser("launch", help="mở Chrome riêng (dùng lại profile); đang chạy thì thôi")
    p.add_argument("--url")
    p.add_argument("--headless", action="store_true", help="chạy không cửa sổ (mặc định theo `headless` trong config.yml, hiện là true)")
    p.add_argument("--headed", action="store_true", help="ép mở cửa sổ thật (cần khi user phải tự đăng nhập)")

    sub.add_parser("status", help="Chrome + owner đang giữ tab")
    p = sub.add_parser("release", help="đóng tab của owner, xoá khỏi sổ")
    owner_arg(p, tab=False)
    p.add_argument("--stale", action="store_true", help="dọn owner quá owner_ttl_hours")
    p = sub.add_parser("close", help="tắt Chrome (giữ profile); từ chối nếu còn owner")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("tabs", help="tab của owner")
    owner_arg(p, tab=False)
    p = sub.add_parser("goto", help="mở URL ở tab của owner")
    owner_arg(p)
    p.add_argument("url")
    p = sub.add_parser("eval", help="chạy hàm JS (trong frame nếu --frame) và in kết quả JSON")
    owner_arg(p)
    p.add_argument("--url", help="goto trước khi chạy")
    p.add_argument("--frame", help="đoạn src/URL của iframe")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--js", help="biểu thức hoặc hàm, vd '() => document.title'")
    g.add_argument("--js-file")
    p = sub.add_parser("shot", help="chụp tab")
    owner_arg(p)
    p.add_argument("--url")
    p.add_argument("--out", required=True)
    p.add_argument("--full", action="store_true")
    p = sub.add_parser("console", help="reload (hoặc --url) rồi gom console lỗi + request lỗi của mọi frame")
    owner_arg(p)
    p.add_argument("--url")
    p.add_argument("--seconds", type=float, default=5)
    p.add_argument("--all", action="store_true", help="cả log / info")
    p.add_argument("--out-dir")
    p.add_argument("--prefix", default="console")
    p = sub.add_parser("snapshot", help="accessibility snapshot trang + từng iframe (để chọn locator)")
    owner_arg(p)
    p.add_argument("--url")
    p.add_argument("--max-chars", type=int, default=6000)
    p = sub.add_parser("devices", help="tên thiết bị giả lập được")
    p.add_argument("--filter", default="")

    p = sub.add_parser("run", help="chạy steps.py (def run(ctx)) — console/network/kết quả ghi vào --out",
                       description="steps.py có `def run(ctx)`; giá trị return vào khoá `result` của <prefix>-result.json. "
                                   "API ctx: page · goto · frame · click_new_tab · shot · emulate · cdp · snapshot · site · "
                                   "check · note · step · expect — xem bảng Quick Reference ở SKILL.md và examples/.")
    owner_arg(p, tab=False)
    p.add_argument("steps")
    p.add_argument("--out", required=True)
    p.add_argument("--prefix", help="tiền tố file, vd TC-03 (mặc định tên file steps)")
    p.add_argument("--raw-dir", help="thư mục cho <prefix>-result.json / -console.jsonl / -network.jsonl / -failure.png "
                                     "(mặc định = --out); ảnh ctx.shot vẫn vào --out")
    p.add_argument("--url", help="goto trước khi gọi run(ctx)")
    p.add_argument("--device", help="mobile | tablet | tên thiết bị Playwright")
    p.add_argument("--close-tabs", action="store_true", help="đóng tab phụ (popup) của lượt sau khi chạy")
    p.add_argument("--no-failure-shot", action="store_true")

    p = sub.add_parser("console-diff", help="lỗi console chỉ có ở lượt mới so với lượt gốc (2 file .jsonl)")
    p.add_argument("base")
    p.add_argument("new")
    p = sub.add_parser("learn", help="ghi ứng viên tự cải thiện; lần 2 thì báo đúc")
    p.add_argument("pattern_id", metavar="id", help="tên ngắn kebab-case, vd open-app-ready")
    p.add_argument("--desc", default="", help="mô tả pattern (lần đầu)")
    p.add_argument("--kind", choices=["thao-tac", "bay"], default="thao-tac")
    p.add_argument("--site", help="nền tảng nếu chỉ đúng với nền tảng đó")
    p = sub.add_parser("serve-fixtures", help="phục vụ trang fixture để thử")
    p.add_argument("--port", type=int, default=8790)
    p = sub.add_parser("selftest", help="chạy lõi trên fixtures với Chrome tạm")
    p.add_argument("--headed", action="store_true")

    args = ap.parse_args()
    cfg = cfgmod.load()
    fn = globals()[f"cmd_{args.cmd.replace('-', '_')}"]
    try:
        return fn(args, cfg)
    except ChromeCoreError as e:
        out({"error": type(e).__name__, "message": str(e)})
        return 3


if __name__ == "__main__":
    sys.exit(main())
