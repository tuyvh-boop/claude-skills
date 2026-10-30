# /// script
# requires-python = ">=3.9"
# dependencies = ["pexpect", "pyyaml"]
# ///
"""
ssh_client.py — helper + CLI cho ssh-server-core: nối tới các server dạng
"restricted interactive menu" (login vào bị ép vào một menu cố định, quyền hạn
chế, hợp để scan log / xem trạng thái).

MỌI giá trị (danh sách server, alias SSH, menu-map đã khám phá) đọc từ config.yml
CẠNH thư mục skill. config.yml GITIGNORED; khuôn commit là config.example.yml.
KHÔNG hardcode server/host trong script.

KẾT NỐI: chỉ trỏ tới alias trong ~/.ssh/config (field `ssh_alias`). Private key nằm
nguyên trong ~/.ssh — script KHÔNG đọc, KHÔNG in, KHÔNG truyền key. Dùng
`ssh -tt -o BatchMode=yes <alias>` (BatchMode → không hỏi password, key sai thì
fail ngay chứ không treo).

AN TOÀN (theo rule của user):
  - Read-only mặc định. `run` chỉ chạy mục được phân loại `read`; mục `side-effect`
    bị CHẶN CỨNG (không có cờ vượt). Muốn thao tác side-effect → user tự làm bằng `raw`.
  - `explore` chỉ tự bấm thử mục `read`; mục `side-effect`/`unknown` chỉ GHI NHẬN,
    không bấm. Gặp sub-prompt (mục hỏi thêm) thì dừng + ghi hint, KHÔNG tự bịa input.
  - Không có secret nào để lộ (key ở ~/.ssh), nhưng vẫn không in gì nhạy cảm.

TEST/VERIFY: `uv run ssh_client.py selftest` (parse+classify trên fixture, không cần
  mạng) và `uv run ssh_client.py doctor` (login rồi thoát ngay, không side-effect).

Chạy:  uv run ssh_client.py <command> [options]

Hàm import được (skill khác `from ssh_client import ...`):
  load_ctx, parse_menu, classify_option, explore_server, run_option.
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

import yaml

try:
    import pexpect
except ImportError:  # pragma: no cover — uv run tự cài, nhánh này chỉ khi chạy sai cách
    pexpect = None

CONFIG = Path(__file__).resolve().parent.parent / "config.yml"
CONFIG_EXAMPLE = Path(__file__).resolve().parent.parent / "config.example.yml"

# Marker để nhận diện đang ở màn hình menu (dòng "0) Thoat" — chịu được dấu/không dấu).
MENU_MARKER = re.compile(r"^\s*0\)\s*(tho[aá]t|exit|quit|back)", re.IGNORECASE | re.MULTILINE)
# Sau khi một mục CHẠY XONG, menu KHÔNG tự hiện lại mà dừng ở prompt "nhấn Enter".
# Thấy prompt này = mục đã xong, KHÔNG cần input (chỉ cần gửi Enter để về menu).
RETURN_PROMPT = re.compile(r"nhan enter de quay lai menu|nh[aâ]́?n enter", re.IGNORECASE)
# Prompt HỎI THÊM thật sự (chọn service/app/container, nhập query...) — dòng có động từ
# hỏi + kết thúc bằng ':'. Đặt SAU RETURN_PROMPT khi expect để không nuốt nhầm "nhấn Enter".
SUBPROMPT = re.compile(r"(?:chon|ch[oọ]n|nhap|nh[aậ]p|select|enter so)[^\n]*:\s*$",
                       re.IGNORECASE | re.MULTILINE)
# Một dòng option: "  5) Xem trang thai dich vu"
OPTION_LINE = re.compile(r"^\s*(\d+)\)\s*(.+?)\s*$", re.MULTILINE)
ANSI = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")

# ---- Phân loại option theo NHÃN (conservative: không rõ = unknown, KHÔNG tự bấm) ----
# Marker "chỉ đọc" trong nhãn -> ép read (vd "Chay bao cao thong ke (chi doc, khong sua duoc)").
READONLY_MARK = ("chi doc", "read-only", "readonly", "chi xem", "chi select")
# Động từ ĐẦU nhãn cho biết side-effect. Match theo TOKEN đầu, không substring toàn nhãn,
# để "khong sua duoc" (chỉ đọc) không bị dính nhầm vào "sua".
SIDE_VERBS = {
    "restart", "reload", "edit", "sua", "xoa", "delete", "remove", "set",
    "write", "ghi", "stop", "start", "kill", "tao", "create", "update",
    "capnhat", "drop", "truncate", "khoidong", "tat", "bat", "deploy",
}
READ_VERBS = {
    "xem", "list", "duyet", "inspect", "stats", "show", "view", "describe",
    "liet", "doc", "read", "status", "check", "kiemtra",
}
EXIT_VERBS = {"thoat", "exit", "quit", "back"}


def _fold(s: str) -> str:
    """Bỏ dấu + lower, để so khớp từ khoá không phụ thuộc dấu tiếng Việt."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def strip_ansi(s: str) -> str:
    return ANSI.sub("", s)


# ============================ config ============================
def load_ctx() -> dict:
    """Đọc config.yml. Chưa có -> hướng dẫn copy từ .example rồi thoát."""
    if not CONFIG.exists():
        sys.exit(
            f"Thiếu {CONFIG.name}. Copy khuôn rồi điền:\n"
            f"  cp {CONFIG_EXAMPLE} {CONFIG}\n"
            f"rồi khai server (ssh_alias trỏ tới alias trong ~/.ssh/config)."
        )
    ctx = yaml.safe_load(CONFIG.read_text()) or {}
    ctx.setdefault("servers", {})
    return ctx


def save_ctx(ctx: dict) -> None:
    """Ghi lại config.yml (dùng khi explore cập nhật menu-map).
    Lưu ý: yaml.dump làm mất comment — config.yml là DỮ LIỆU máy quản, comment để ở
    config.example.yml."""
    CONFIG.write_text(yaml.safe_dump(ctx, allow_unicode=True, sort_keys=False))


def get_server(ctx: dict, name: str) -> dict:
    srv = ctx["servers"].get(name)
    if not srv:
        have = ", ".join(ctx["servers"]) or "(trống)"
        sys.exit(f"Server '{name}' chưa khai trong config.yml. Đang có: {have}")
    if not srv.get("ssh_alias"):
        sys.exit(f"Server '{name}' thiếu ssh_alias (alias trong ~/.ssh/config).")
    return srv


# ============================ pure helpers (testable) ============================
def parse_menu(text: str) -> list:
    """Từ text màn hình menu -> [{option, label}]. Bỏ ANSI, gom các dòng 'N) nhãn'."""
    text = strip_ansi(text)
    out = []
    seen = set()
    for m in OPTION_LINE.finditer(text):
        opt, label = m.group(1), m.group(2).strip()
        if opt in seen:
            continue
        seen.add(opt)
        out.append({"option": opt, "label": label})
    return out


def classify_option(label: str) -> str:
    """read | side-effect | exit | unknown — thiên về an toàn (không rõ = unknown)."""
    f = _fold(label)
    token = f.split()[0] if f.split() else ""
    # Token đầu dạng "duyet/doc" hay "khoi-dong": xét cả dạng ghép ("khoidong") lẫn từ
    # đầu trước dấu phân cách ("duyet") — chỉ ghép thì "duyetdoc" rơi vào unknown.
    candidates = {re.sub(r"[^a-z]", "", token)}
    candidates.update(re.findall(r"[a-z]+", token)[:1])
    if candidates & EXIT_VERBS:
        return "exit"
    # Marker "chỉ đọc" ép read kể cả động từ mơ hồ (vd "chay bao cao thong ke (chi doc)").
    if any(mk in f for mk in READONLY_MARK):
        return "read"
    if candidates & SIDE_VERBS:
        return "side-effect"
    if candidates & READ_VERBS:
        return "read"
    return "unknown"


def has_menu(text: str) -> bool:
    return bool(MENU_MARKER.search(strip_ansi(text)))


# ============================ transport (pexpect) ============================
def _spawn(alias: str, connect_timeout: int = 8, timeout: int = 20):
    if pexpect is None:
        sys.exit("Thiếu pexpect. Chạy qua `uv run ssh_client.py ...` để uv tự cài.")
    return pexpect.spawn(
        "ssh",
        ["-tt", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={connect_timeout}", alias],
        encoding="utf-8",
        timeout=timeout,
        codec_errors="replace",
    )


def _wait_menu(child, timeout: int = 20) -> str:
    """Đọc tới khi thấy màn hình menu (marker '0) Thoat'). Trả text đã thấy."""
    idx = child.expect([MENU_MARKER, pexpect.EOF, pexpect.TIMEOUT], timeout=timeout)
    buf = (child.before or "") + (child.after if isinstance(child.after, str) else "")
    if idx == 0:
        # Đọc nốt phần đuôi menu (prompt nhập) để không cắt giữa chừng.
        try:
            child.expect([r"[:>]\s*$", pexpect.TIMEOUT], timeout=2)
            buf += child.before or ""
        except Exception:
            pass
        return buf
    if idx == 1:
        raise ConnectionError("Phiên đóng trước khi thấy menu (login fail?).\n" + strip_ansi(buf)[-400:])
    raise TimeoutError("Không thấy menu trong thời gian chờ.\n" + strip_ansi(buf)[-400:])


# ============================ commands ============================
def cmd_doctor(ctx: dict, name: str | None):
    names = [name] if name else list(ctx["servers"])
    if not names:
        sys.exit("config.yml chưa có server nào.")
    rc = 0
    for n in names:
        srv = get_server(ctx, n)
        alias = srv["ssh_alias"]
        try:
            child = _spawn(alias)
            _wait_menu(child)
            print(f"✔ {n:12s} ({alias})  login OK, menu hiện ra")
            try:
                child.sendline("0")           # thoát sạch
                child.expect(pexpect.EOF, timeout=5)
            except Exception:
                child.close(force=True)
        except (ConnectionError, TimeoutError) as e:
            rc = 1
            print(f"✘ {n:12s} ({alias})  {str(e).splitlines()[0]}")
        except Exception as e:  # pragma: no cover
            rc = 1
            print(f"✘ {n:12s} ({alias})  lỗi: {e}")
    return rc


def cmd_list(ctx: dict, _name=None):
    if not ctx["servers"]:
        print("(config.yml chưa có server)")
        return 0
    for n, srv in ctx["servers"].items():
        flag = "explored" if srv.get("explored") else "chưa explore"
        print(f"- {n:12s} {srv.get('ssh_alias',''):24s} [{flag}]  {srv.get('label','')}")
    return 0


def cmd_menu(ctx: dict, name: str):
    srv = get_server(ctx, name)
    menu = srv.get("menu") or []
    if not menu:
        print(f"'{name}' chưa có menu-map. Chạy: uv run ssh_client.py explore {name}")
        return 0
    for it in menu:
        extra = "  ⟨cần input⟩" if it.get("needs_input") else ""
        print(f"  {it['option']:>2}) [{it['kind']:11s}] {_ok_mark(it)} {it['label']}{extra}")
        if it.get("input_hint"):
            print(f"        hint: {it['input_hint']}")
    return 0


def _probe_option(alias: str, option: str) -> dict:
    """Thử MỘT mục trên MỘT session riêng (tránh lệch pha giữa các mục). Không bịa input.
    Trả {needs_input, input_hint, sample}."""
    res = {"needs_input": False, "input_hint": "", "sample": ""}
    child = _spawn(alias)
    try:
        _wait_menu(child)
        child.sendline(option)
        # Thứ tự QUAN TRỌNG: RETURN_PROMPT trước SUBPROMPT (để "nhấn Enter" không bị bắt nhầm).
        idx = child.expect(
            [RETURN_PROMPT, SUBPROMPT, MENU_MARKER, pexpect.TIMEOUT, pexpect.EOF], timeout=15
        )
        before = strip_ansi(child.before or "").strip()
        if idx in (0, 2):                # xong (nhấn-Enter) hoặc menu hiện lại -> KHÔNG cần input
            res["sample"] = before[:600]
        elif idx == 1:                   # prompt hỏi thêm thật sự
            res["needs_input"] = True
            after = strip_ansi(child.after or "").strip()
            res["input_hint"] = (after or (before.splitlines()[-1] if before.splitlines() else ""))[:200]
        else:                            # timeout/eof
            res["sample"] = "(không rõ — xem thủ công bằng `raw`)"
    except (ConnectionError, TimeoutError) as e:
        res["sample"] = f"(lỗi: {str(e).splitlines()[0]})"
    finally:
        child.close(force=True)          # đóng hẳn session này, không bịa input, không side-effect
    return res


def explore_server(alias: str, probe_read: bool = True) -> tuple:
    """Đăng nhập, đọc menu, phân loại. Nếu probe_read: tự bấm thử CHỈ mục 'read', mỗi mục
    một session riêng. Trả (menu_list, raw_menu_text). side-effect/unknown: chỉ ghi nhận."""
    child = _spawn(alias)
    raw = _wait_menu(child)
    child.close(force=True)
    items = parse_menu(raw)
    for it in items:
        it["kind"] = classify_option(it["label"])
        it["needs_input"] = False
        it["input_hint"] = ""
        it["sample"] = ""
        it["user_ok"] = None          # None = user CHƯA duyệt -> run chặn tới khi allow/block
    if probe_read:
        for it in items:
            if it["kind"] != "read":
                continue
            it.update(_probe_option(alias, it["option"]))
    return items, raw


def cmd_explore(ctx: dict, name: str, no_probe: bool = False):
    srv = get_server(ctx, name)
    prior = {it["option"]: it.get("user_ok") for it in (srv.get("menu") or [])}
    items, _ = explore_server(srv["ssh_alias"], probe_read=not no_probe)
    # Lưu vào config.yml (bỏ 'sample' cho gọn). GIỮ LẠI user_ok đã duyệt trước đó
    # (re-explore để refresh menu KHÔNG được xoá quyết định cho phép/cấm của user).
    for it in items:
        if it["option"] in prior:
            it["user_ok"] = prior[it["option"]]
    srv["menu"] = [{k: v for k, v in it.items() if k != "sample"} for it in items]
    srv["explored"] = True
    save_ctx(ctx)

    reads = [i for i in items if i["kind"] == "read"]
    sides = [i for i in items if i["kind"] == "side-effect"]
    unk = [i for i in items if i["kind"] == "unknown"]
    print(f"== explore {name} ({srv['ssh_alias']}) — {len(items)} mục ==")
    print(f"  read: {len(reads)}   side-effect: {len(sides)}   unknown: {len(unk)}")
    for it in items:
        extra = " ⟨cần input⟩" if it.get("needs_input") else ""
        print(f"  {it['option']:>2}) [{it['kind']:11s}] {_ok_mark(it)}{extra} {it['label']}")
    if unk:
        print("\n⚠ Mục 'unknown' KHÔNG được tự bấm. Hỏi user từng mục là read hay side-effect.")
    print(
        "\n⛔ CHƯA mục nào được phép chạy tự động (user_ok=null). Đây là gate BẮT BUỘC:\n"
        "   HỎI USER duyệt từng mục — kể cả mục 'read' hợp lệ user vẫn có thể CẤM — rồi ghi:\n"
        f"     uv run ssh_client.py allow {name} <option...>   # user cho phép\n"
        f"     uv run ssh_client.py block {name} <option...>   # user cấm\n"
        "   `run` chỉ chạy mục user_ok=true. Đã lưu menu-map vào config.yml."
    )
    return 0


def _ok_mark(it: dict) -> str:
    v = it.get("user_ok")
    return "✓cho phép" if v is True else ("✗user cấm" if v is False else "?chưa duyệt")


def _set_access(ctx: dict, name: str, options: list, ok: bool):
    srv = get_server(ctx, name)
    by_opt = {it["option"]: it for it in (srv.get("menu") or [])}
    changed = []
    for o in options:
        it = by_opt.get(str(o))
        if not it:
            print(f"  (bỏ qua {o}: không có trong menu-map)")
            continue
        it["user_ok"] = ok
        changed.append(o)
    save_ctx(ctx)
    verb = "CHO PHÉP" if ok else "CẤM"
    print(f"Đã {verb} mục {', '.join(map(str, changed))} trên {name}.")
    return 0


def run_option(alias: str, option: str, inputs: list | None = None, timeout: int = 20) -> str:
    """Chạy MỘT mục (đã biết là read) và trả output. inputs: các dòng trả lời sub-prompt
    (theo đúng thứ tự nó hỏi). Kết thúc ở prompt 'nhấn Enter' hoặc menu hiện lại.
    timeout: giây chờ output cuối — file log lớn (vài MB) cần 120-300s, mặc định 20s sẽ
    trả buffer dở mà không báo (bug gặp khi đọc log_pm2 22-09-2026)."""
    child = _spawn(alias)
    _wait_menu(child)
    child.sendline(option)
    for val in (inputs or []):
        child.expect([SUBPROMPT, RETURN_PROMPT, MENU_MARKER, pexpect.TIMEOUT], timeout=12)
        child.sendline(val)
    idx = child.expect([RETURN_PROMPT, MENU_MARKER, pexpect.TIMEOUT, pexpect.EOF], timeout=timeout)
    out = strip_ansi(child.before or "").strip()
    child.close(force=True)
    if idx == 2:
        print(f"[ssh_client] CẢNH BÁO: hết {timeout}s chưa thấy prompt kết thúc — output có thể bị CẮT. "
              f"Tăng --timeout.", file=sys.stderr)
    return out


def cmd_run(ctx: dict, name: str, option: str, inputs: list, timeout: int = 20):
    srv = get_server(ctx, name)
    menu = {it["option"]: it for it in (srv.get("menu") or [])}
    it = menu.get(option)
    if not it:
        sys.exit(f"Mục '{option}' chưa có trong menu-map của {name}. Chạy explore trước.")
    if it["kind"] != "read":
        sys.exit(
            f"CHẶN (kind): mục {option} '{it['label']}' là '{it['kind']}', không phải 'read'. "
            f"Skill chỉ chạy mục read. Side-effect → user tự làm qua `raw {name}`."
        )
    # Gate của USER: kể cả mục read hợp lệ, user vẫn có thể CẤM. Chỉ chạy khi user_ok is True.
    if it.get("user_ok") is not True:
        state = "user đã CẤM" if it.get("user_ok") is False else "user CHƯA duyệt"
        sys.exit(
            f"CHẶN (user): mục {option} '{it['label']}' — {state}. "
            f"Hỏi user rồi `allow {name} {option}` nếu được phép."
        )
    print(run_option(srv["ssh_alias"], option, inputs, timeout=timeout))
    return 0


# Mục duyệt file liệt kê dạng "  12) [FILE]     shopify.app.toml" / "  3) [THU MUC] tae".
BROWSE_ENTRY = re.compile(r"^\s*(\d+)\)\s*\[(FILE|THU MUC)\]\s+(.+?)\s*$", re.MULTILINE)
# File không bao giờ được mở qua read-file, kể cả khi config khai nhầm.
SECRET_FILE = re.compile(r"(^|/)(\.env[^/]*|[^/]*\.env|[^/]*\.(pem|key)|id_[a-z0-9]+|[^/]*credential[^/]*)$", re.IGNORECASE)


def browse_path(alias: str, option: str, segments: list, timeout: int = 30) -> str:
    """Lái mục duyệt file theo TÊN: mỗi bước parse danh sách rồi chọn số khớp tên segment.
    Số thứ tự trên server đổi khi có file mới → không lưu số cứng. Trả nội dung file (thô)."""
    child = _spawn(alias)
    _wait_menu(child)
    child.sendline(option)
    for seg in segments:
        child.expect([SUBPROMPT, pexpect.TIMEOUT], timeout=15)
        listing = strip_ansi(child.before or "")
        hits = [m.group(1) for m in BROWSE_ENTRY.finditer(listing) if m.group(3) == seg]
        if len(hits) != 1:
            child.close(force=True)
            sys.exit(f"Không thấy (hoặc thấy {len(hits)}) mục tên '{seg}' trong danh sách — đường dẫn sai hoặc menu đổi.")
        child.sendline(hits[0])
    idx = child.expect([RETURN_PROMPT, SUBPROMPT, MENU_MARKER, pexpect.TIMEOUT, pexpect.EOF], timeout=timeout)
    out = strip_ansi(child.before or "")
    child.close(force=True)
    if idx == 3:
        print(f"[ssh_client] CẢNH BÁO: hết {timeout}s — nội dung có thể bị CẮT. Tăng --timeout.", file=sys.stderr)
    return out


def cmd_read_file(ctx: dict, name: str, key: str, timeout: int = 30):
    """Đọc 1 file khai trong `files:` của server, CHỈ in dòng khớp `show` (danh sách trắng)."""
    srv = get_server(ctx, name)
    files = srv.get("files") or {}
    spec = files.get(key)
    if not spec:
        sys.exit(f"'{key}' chưa khai trong files: của {name}. Có: {', '.join(files) or '(trống)'}")
    path, option, show = spec.get("path", ""), str(spec.get("option", "")), spec.get("show")
    if SECRET_FILE.search(path):
        sys.exit(f"CHẶN: '{path}' trông như file secret — read-file không mở loại file này.")
    if not show:
        sys.exit(f"CHẶN: files.{key} thiếu `show` (regex danh sách trắng) — không in cả file.")
    it = {i["option"]: i for i in (srv.get("menu") or [])}.get(option)
    if not it or it["kind"] != "read" or it.get("user_ok") is not True:
        sys.exit(f"CHẶN: mục {option} của {name} không phải read đã được user cho phép.")
    raw = browse_path(srv["ssh_alias"], option, [s for s in path.split("/") if s], timeout=timeout)
    pat = re.compile(show)
    lines = [ln for ln in raw.splitlines() if pat.search(ln)]
    print(f"# {name}:{spec.get('root', '')}/{path} — {len(lines)} dòng khớp `show`")
    print("\n".join(lines) if lines else "(không dòng nào khớp)")
    return 0


def cmd_raw(ctx: dict, name: str):
    """Bàn giao phiên interactive cho USER tự thao tác (kể cả mục side-effect là việc của user)."""
    srv = get_server(ctx, name)
    print(f"→ Mở phiên interactive tới {name} ({srv['ssh_alias']}). Gõ 0 để thoát.\n")
    if pexpect is None:
        sys.exit("Thiếu pexpect.")
    child = _spawn(srv["ssh_alias"], timeout=None)
    child.interact()
    return 0


# ---- fixture cho selftest: menu HƯ CẤU (chỉ để test logic parse/classify).
# KHÔNG dùng menu/host thật ở đây — file này được commit. Menu thật của server chỉ
# sống trong config.yml (đã gitignore), do `explore` tự điền. ----
_FIXTURE = """===== VIEWER MENU — user@example-host =====
(Chi xem/thao tac trong pham vi cho phep — khong co shell tu do)

1) Xem log ung dung
2) Xem trang thai dich vu
3) Liet ke tien trinh dang chay
4) Xem cau hinh (chi doc)
5) Chay bao cao thong ke (chi doc, khong sua duoc)
6) Restart dich vu (gioi han)
7) Reload cau hinh
8) Duyet/doc file trong thu muc web
9) Khoi-dong lai worker
0) Thoat
"""


def cmd_selftest(_ctx=None, _name=None):
    """Test thuần logic (không cần mạng): parse + classify trên menu hư cấu."""
    items = parse_menu(_FIXTURE)
    assert len(items) == 10, f"parse ra {len(items)} mục, mong 10"
    for it in items:
        it["kind"] = classify_option(it["label"])
    kinds = {it["option"]: it["kind"] for it in items}
    # Kỳ vọng: 6/7 side-effect; 5 ("chay..." nhưng có marker "chi doc") phải là read;
    # 3 ("liet ke") read; 0 exit; 8 ("duyet/doc") read; 9 ("khoi-dong") side-effect.
    expect = {"6": "side-effect", "7": "side-effect", "5": "read", "0": "exit",
              "3": "read", "1": "read", "8": "read", "9": "side-effect"}
    ok = True
    for opt, want in expect.items():
        got = kinds.get(opt)
        mark = "✔" if got == want else "✘"
        if got != want:
            ok = False
        print(f"  {mark} option {opt:>2}: {got:11s} (mong {want})")
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    p = argparse.ArgumentParser(description="ssh-server-core CLI")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor").add_argument("server", nargs="?")
    sub.add_parser("list-servers")
    sub.add_parser("menu").add_argument("server")
    ex = sub.add_parser("explore")
    ex.add_argument("server")
    ex.add_argument("--no-probe", action="store_true", help="chỉ phân loại, không bấm thử mục read")
    rn = sub.add_parser("run")
    rn.add_argument("server")
    rn.add_argument("--option", required=True)
    rn.add_argument("--input", action="append", default=[], help="dòng trả lời sub-prompt (lặp lại được)")
    rn.add_argument("--timeout", type=int, default=20, help="giây chờ output cuối (file log lớn: 120-300)")
    al = sub.add_parser("allow", help="user cho phép Claude dùng các mục này")
    al.add_argument("server")
    al.add_argument("options", nargs="+", help="số option, vd: 1 2 5")
    bl = sub.add_parser("block", help="user cấm Claude dùng các mục này (kể cả mục read)")
    bl.add_argument("server")
    bl.add_argument("options", nargs="+")
    rf = sub.add_parser("read-file", help="đọc file khai trong files: của server, chỉ in dòng khớp show")
    rf.add_argument("server")
    rf.add_argument("key")
    rf.add_argument("--timeout", type=int, default=30)
    sub.add_parser("raw").add_argument("server")
    sub.add_parser("selftest")
    a = p.parse_args()

    # selftest không cần config.
    if a.cmd == "selftest":
        return cmd_selftest()
    ctx = load_ctx()
    if a.cmd == "doctor":
        return cmd_doctor(ctx, a.server)
    if a.cmd == "list-servers":
        return cmd_list(ctx)
    if a.cmd == "menu":
        return cmd_menu(ctx, a.server)
    if a.cmd == "explore":
        return cmd_explore(ctx, a.server, no_probe=a.no_probe)
    if a.cmd == "run":
        return cmd_run(ctx, a.server, a.option, a.input, a.timeout)
    if a.cmd == "allow":
        return _set_access(ctx, a.server, a.options, ok=True)
    if a.cmd == "block":
        return _set_access(ctx, a.server, a.options, ok=False)
    if a.cmd == "read-file":
        return cmd_read_file(ctx, a.server, a.key, a.timeout)
    if a.cmd == "raw":
        return cmd_raw(ctx, a.server)
    p.error("lệnh không rõ")


if __name__ == "__main__":
    sys.exit(main())
