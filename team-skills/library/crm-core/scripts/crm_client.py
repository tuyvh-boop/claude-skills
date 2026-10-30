# /// script
# requires-python = ">=3.9"
# dependencies = ["requests", "pyyaml"]
# ///
"""
crm_client.py — helper + CLI cho CRM/OSSA nội bộ, dùng CRM_PAT (personal API key).

Mọi thứ (base_url, auth, scans) đọc từ config.yml cạnh script. config.yml GITIGNORED
(chứa host nội bộ); khuôn commit là config.example.yml. KHÔNG hardcode, KHÔNG có profile.yml.

XÁC THỰC (không bao giờ in token):
  Token: (1) env $CRM_PAT → (2) fallback `pass show personal/CRM_PAT` (subprocess capture,
  KHÔNG in stdout → không vào transcript). Gắn qua header `X-API-Key` (gọi thẳng base_url).

TEST / VERIFY: chạy `doctor` (an toàn, không in token). ĐỪNG tự gõ echo/env/cat/pass show
  chạm biến token — bẫy `${VAR:-...}` sẽ bung ra chính token.

GUARD: personal API key bị CHẶN ở nhóm self-admin (auth / users/me/api-keys / mcp/pat).
  Script chặn trước khi gọi (config.denied_paths) — dùng phiên đăng nhập thường cho nhóm đó.

Chạy:  uv run crm_client.py <command> [options]

Hàm import được (skill khác `from crm_client import ...`): load_ctx, crm_get, crm_raw.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import requests
import yaml

# ========================== TẦNG 1 — LÕI CHUNG ==========================

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
CONFIG_PATH = SKILL_DIR / "config.yml"   # GITIGNORED; khuôn: config.example.yml


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _load_yaml(path):
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_token(cfg):
    """Env trước; trống thì fallback `pass show` (capture, KHÔNG in). Thiếu -> lỗi."""
    auth = cfg.get("auth", {})
    env_name = auth.get("token_env", "CRM_PAT")
    tok = os.environ.get(env_name, "").strip()
    if tok:
        return tok
    entry = auth.get("pass_entry")
    if entry:
        try:
            out = subprocess.run(["pass", "show", entry],
                                 capture_output=True, text=True, timeout=20)
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.strip()
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
    die(f"Chưa lấy được token. Set env ${env_name} trước "
        f"(mở terminal mới đã auto-load, hoặc: export {env_name}=\"$(pass show {entry})\").")


# --- Guard: chặn path mà personal API key không được đi vào ---

def _normalize_segments(path):
    """Tách path thành đoạn, bỏ rỗng + tiền tố /api. Hạ chữ thường (route không phân biệt hoa)."""
    segs = [s for s in path.split("?")[0].lower().split("/") if s]
    return segs[1:] if segs and segs[0] == "api" else segs


def _assert_allowed(cfg, path):
    denied = cfg.get("denied_paths", [])
    segs = _normalize_segments(path)
    for prefix in denied:
        pref = [str(s).lower() for s in prefix]
        if all(i < len(segs) and segs[i] == p for i, p in enumerate(pref)):
            die(f"Path '{path}' thuộc nhóm CẤM personal API key ({'/'.join(pref)}). "
                f"Nhóm self-admin (đăng nhập/refresh/quản lý key) phải dùng phiên đăng nhập thường.")


class Ctx:
    """Gói config + auth + base URL + session để gọi API."""
    def __init__(self, cfg, token):
        self.cfg = cfg
        self.base = cfg.get("base_url", "").rstrip("/")
        if not self.base:
            die("Thiếu base_url trong config.yml.")
        self.session = requests.Session()
        auth = cfg.get("auth", {})
        hname = auth.get("header_name", "x-api-key")
        self.session.headers[hname] = token
        self.session.headers.setdefault("Accept", "application/json")


def api(ctx, method, path, params=None, data=None):
    """Gọi 1 endpoint REST (guard denied-path trước). Trả JSON / text / None."""
    _assert_allowed(ctx.cfg, path)
    url = ctx.base + path if path.startswith("/") else f"{ctx.base}/{path}"
    headers = {}
    if data is not None:
        headers["Content-Type"] = "application/json"
    r = ctx.session.request(method.upper(), url, params=params,
                            data=json.dumps(data) if data is not None else None,
                            headers=headers, timeout=40)
    if r.status_code >= 400:
        die(f"HTTP {r.status_code} {method} {path}\n{r.text[:1500]}")
    if not r.content:
        return None
    return r.json() if "json" in r.headers.get("Content-Type", "") else r.text


def load_ctx():
    cfg = _load_yaml(CONFIG_PATH)
    if not cfg:
        die(f"Không đọc được config: {CONFIG_PATH} — copy config.example.yml -> config.yml rồi điền.")
    token = resolve_token(cfg)
    return Ctx(cfg, token)


def crm_get(ctx, path, params=None):
    return api(ctx, "GET", path, params=params)


def crm_raw(ctx, method, path, data=None, params=None):
    return api(ctx, method, path, params=params, data=data)


def _me(ctx):
    return api(ctx, "GET", "/users/me")


def cmd_whoami(ctx, args):
    print(json.dumps(_me(ctx), ensure_ascii=False, indent=2))


def cmd_doctor(ctx, args):
    """Kiểm tra core AN TOÀN — KHÔNG bao giờ in token (chỉ in NGUỒN token)."""
    auth = ctx.cfg.get("auth", {})
    env_name = auth.get("token_env", "CRM_PAT")
    src = "env" if os.environ.get(env_name, "").strip() else "pass"
    print(f"config  : {CONFIG_PATH} ({'OK' if CONFIG_PATH.exists() else 'MISSING'})")
    print(f"base_url: {ctx.base}")
    print(f"auth    : header {auth.get('header_name')}  token_env={env_name}")
    print(f"token   : OK (nguồn: {src})")   # KHÔNG in value/length
    me = _me(ctx)
    ws = (me.get("workspace") or {}).get("name", "")
    print(f"whoami  : {me.get('name')} <{me.get('email')}>" + (f" @ {ws}" if ws else ""))


# ========================== TẦNG 2 — MODULE ==========================

def _confirm_or_dry(args, payload, what):
    """In payload; chưa --commit thì DỪNG (dry-run). Trả True nếu được ghi thật."""
    print(f'[{"COMMIT" if getattr(args, "commit", False) else "DRY-RUN"}] {what}')
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not getattr(args, "commit", False):
        print("(dry-run — thêm --commit để ghi thật)")
        return False
    return True


# Resource có thể scan + cache vào config.resources (id <-> name/slug để tra nhanh).
SCAN_SOURCES = {
    # (path, id_key, name_key) — key hỗ trợ dấu chấm cho field lồng (vd "workspace._id").
    "workspaces": ("/workspaces/mine", "workspace._id", "workspace.name"),
    "task-categories": ("/task-categories", "_id", "name"),
    "roles": ("/roles", "_id", "name"),
}


def _dig(obj, dotted):
    """Lấy field theo path 'a.b.c' trong dict lồng; thiếu -> None."""
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _as_list(data):
    """API có thể trả list thẳng hoặc {data|items|values: [...]}. Chuẩn hoá -> list."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("data", "items", "values", "results"):
            if isinstance(data.get(k), list):
                return data[k]
    return []


def cmd_scan(ctx, args):
    """Scan resource tra-cứu (workspaces/task-categories/roles) -> in + ghi config.resources."""
    names = [args.resource] if args.resource else list(SCAN_SOURCES)
    cfg = _load_yaml(CONFIG_PATH)
    resources = cfg.get("resources") or {}
    for name in names:
        if name not in SCAN_SOURCES:
            die(f"Chưa biết scan '{name}'. Có: {', '.join(SCAN_SOURCES)}")
        path, id_key, name_key = SCAN_SOURCES[name]
        items = _as_list(api(ctx, "GET", path))
        mapping = {str(_dig(it, id_key)): _dig(it, name_key)
                   for it in items if _dig(it, id_key) is not None}
        resources[name] = mapping
        print(f"{name}: {len(mapping)}")
        for i, (k, v) in enumerate(mapping.items()):
            print(f"  {k}\t{v}")
    if args.write:
        cfg["resources"] = resources
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
        print(f"(đã ghi resources vào {CONFIG_PATH})")


# ============ TẦNG 2b — SOURCE CODE (tra endpoint khỏi ĐOÁN MÒ) ============
# config.source: list repo CRM đã clone về máy. Trước khi dò endpoint mới, ưu tiên
# ĐỌC SOURCE (deterministic) thay vì đoán bằng `raw`. Path lệch (user di chuyển) -> báo LỆCH.

import re


def _git(path, *args, timeout=60):
    """Chạy git trong repo `path`. Trả (rc, stdout, stderr). KHÔNG in gì."""
    try:
        out = subprocess.run(["git", "-C", str(path), *args],
                             capture_output=True, text=True, timeout=timeout)
        return out.returncode, out.stdout.strip(), out.stderr.strip()
    except (FileNotFoundError, subprocess.SubprocessError) as e:
        return 1, "", str(e)


def _source_entries(cfg):
    """config.source có thể là list [{role,path,branch}] hoặc map {role: path}. Chuẩn hoá -> list."""
    src = cfg.get("source") or []
    if isinstance(src, dict):
        src = [{"role": k, "path": v} for k, v in src.items()]
    return src


def _check_entry(e):
    """Trạng thái 1 repo source: MISSING (path lệch) / NOT_GIT / OK (+ branch, dirty)."""
    path = Path(os.path.expanduser(str(e.get("path", "")))).resolve()
    st = {"role": e.get("role", "?"), "path": str(path), "branch": e.get("branch")}
    if not path.exists():
        st["state"] = "MISSING"
        return st
    rc, _, _ = _git(path, "rev-parse", "--show-toplevel")
    if rc != 0:
        st["state"] = "NOT_GIT"
        return st
    st["state"] = "OK"
    _, st["current_branch"], _ = _git(path, "branch", "--show-current")
    _, dirty, _ = _git(path, "status", "--porcelain")
    st["dirty"] = bool(dirty)
    return st


def _source_search_root(path):
    """Ưu tiên thư mục src/ để khỏi quét node_modules cho chậm."""
    p = Path(path)
    return p / "src" if (p / "src").exists() else p


def _source_find(entries, keyword):
    """Grep route decorator (@Controller/@Get/...) trong *.controller.ts, lọc theo keyword.
    Cho AI bản đồ endpoint deterministic thay vì đoán — nguồn duy nhất đúng là source."""
    kw = (keyword or "").lower()
    deco = re.compile(r"@(Controller|Get|Post|Put|Patch|Delete)\(")
    found = 0
    for e in entries:
        st = _check_entry(e)
        if st["state"] != "OK":
            continue
        root = _source_search_root(st["path"])
        for f in sorted(root.rglob("*.controller.ts")):
            if any(part in ("node_modules", "dist", ".git") for part in f.parts):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if kw and kw not in text.lower() and kw not in str(f).lower():
                continue
            hits = [(i + 1, ln.strip()) for i, ln in enumerate(text.splitlines())
                    if deco.search(ln) and not ln.lstrip().startswith(("*", "//", "/*"))]
            if not hits:
                continue
            print(f"— {st['role']}/{f.relative_to(Path(st['path']))}")
            for ln_no, ln in hits:
                print(f"   {ln_no}: {ln}")
            found += 1
    if not found:
        print(f"Không thấy controller khớp '{keyword}'. Đổi keyword, hoặc grep tay trong source.")
        print("Nếu source LỆCH/thiếu: chạy `source status`, hỏi user path mới rồi sửa config.source.")


def cmd_source(ctx, args):
    """Quản lý source code CRM để tra endpoint. action: status (mặc định) | sync | find <keyword>."""
    cfg = _load_yaml(CONFIG_PATH)
    entries = _source_entries(cfg)
    action = getattr(args, "action", None) or "status"

    if not entries:
        print("source: (CHƯA đăng ký) — config.source rỗng.")
        print("Nếu user CÓ source CRM đã clone về máy, thêm vào config.yml để tra endpoint khỏi đoán:")
        print("  source:")
        print("    - role: backend   # nơi có @Controller/@Get/@Post — quan trọng nhất")
        print("      path: /duong/dan/tuyet-doi/toi/backend")
        print("      branch: master")
        print("Chưa có source -> self-improve buộc phải dò bằng `raw` (đoán, dễ sai + tốn token).")
        return

    if action == "find":
        return _source_find(entries, getattr(args, "keyword", None))

    any_missing = False
    for e in entries:
        st = _check_entry(e)
        line = f"[{st['role']}] {st['path']} — {st['state']}"
        if st["state"] == "MISSING":
            any_missing = True
            print(line + "  ⚠️ SOURCE LỆCH: không tìm thấy (user có thể đã di chuyển source).")
            continue
        if st["state"] == "NOT_GIT":
            print(line + "  ⚠️ không phải git repo (kiểm tra lại path).")
            continue
        p = st["path"]
        if action == "sync":
            if st["dirty"]:
                print(line + f"  ⚠️ working tree BẨN (branch {st['current_branch']}) — "
                              "BỎ QUA pull, để user tự xử lý.")
                continue
            rc, o, err = _git(p, "pull", "--ff-only")
            tail = (o or err).splitlines()[-1] if (o or err) else ""
            print(line + f"  branch {st['current_branch']} → pull --ff-only: "
                         f"{'OK' if rc == 0 else 'FAIL'}  {tail}")
            if rc != 0:
                print("     (không fast-forward được — pull TAY, KHÔNG force.)")
        else:  # status
            _git(p, "fetch", "--quiet")
            flags = []
            if st["dirty"]:
                flags.append("dirty")
            rc, behind, _ = _git(p, "rev-list", "--count", "HEAD..@{u}")
            if rc == 0 and behind not in ("0", ""):
                flags.append(f"behind {behind}")
            rc, ahead, _ = _git(p, "rev-list", "--count", "@{u}..HEAD")
            if rc == 0 and ahead not in ("0", ""):
                flags.append(f"ahead {ahead}")
            state = ", ".join(flags) if flags else "up-to-date"
            print(line + f"  branch {st['current_branch']}  [{state}]")
    if any_missing:
        print("\n⚠️ Có source LỆCH. HỎI user đường dẫn mới rồi sửa `source` trong config.yml "
              "(ĐỪNG tự đoán path).")


# ========================== TẦNG 3 — LỆNH ĐẶC THÙ CRM ==========================

def _dump(obj, as_json=True):
    print(json.dumps(obj, ensure_ascii=False, indent=2) if not isinstance(obj, str) else obj)


# --- Đọc ---

def cmd_list(ctx, args):
    """List resource phẳng: users | contacts | companies | customers | tasks | task-categories | roles."""
    paths = {
        "users": "/users", "contacts": "/contacts", "companies": "/companies",
        "customers": "/customers", "tasks": "/tasks",
        "task-categories": "/task-categories", "roles": "/roles",
    }
    if args.resource not in paths:
        die(f"Chưa biết list '{args.resource}'. Có: {', '.join(paths)}")
    params = {}
    for kv in args.query or []:
        k, _, v = kv.partition("=")
        params[k] = v
    _dump(api(ctx, "GET", paths[args.resource], params=params))


def cmd_get(ctx, args):
    """Get 1 resource theo id: user|contact|customer|task|role <id>."""
    paths = {
        "user": "/users/{id}", "contact": "/contacts/{id}",
        "customer": "/customers/{id}", "task": "/tasks/{id}", "role": "/roles/{id}",
    }
    if args.resource not in paths:
        die(f"Chưa biết get '{args.resource}'. Có: {', '.join(paths)}")
    _dump(api(ctx, "GET", paths[args.resource].format(id=args.id)))


def cmd_comments(ctx, args):
    """List comment của 1 task (taskId bắt buộc)."""
    _dump(api(ctx, "GET", "/task-comments", params={"taskId": args.task_id}))


def cmd_search(ctx, args):
    """Search task qua POST /tasks/search với body JSON (vd '{\"search\":\"foo\"}')."""
    body = json.loads(args.data) if args.data else {}
    _dump(api(ctx, "POST", "/tasks/search", data=body))


# --- Ghi (mặc định dry-run) ---

def cmd_comment_add(ctx, args):
    """Thêm comment vào task: POST /task-comments {taskId, content}."""
    payload = {"taskId": args.task_id, "content": args.text}
    if not _confirm_or_dry(args, payload, f"comment-add -> task {args.task_id}"):
        return
    res = api(ctx, "POST", "/task-comments", data=payload)
    print(f'OK — comment id {res.get("_id") or res.get("id") if isinstance(res, dict) else res}')


def cmd_task_create(ctx, args):
    """Tạo task: POST /tasks. Body qua --data JSON.
    Bắt buộc: title, assignee(id), reporter(id), domain, relatedApps[>=1].
    Tuỳ chọn: description, status, priority, category, dueDate, estimateHours, tags, app_id."""
    body = json.loads(args.data)
    if not _confirm_or_dry(args, body, "task-create"):
        return
    res = api(ctx, "POST", "/tasks", data=body)
    print(f'OK — task id {res.get("_id") or res.get("id") if isinstance(res, dict) else res}')


def cmd_task_update(ctx, args):
    """Sửa task: PUT /tasks/:id. Field qua --set key=jsonvalue (lặp lại).
    Vd: --set status='"Resolved"' --set priority='"High"'."""
    body = {}
    for kv in args.set or []:
        k, _, v = kv.partition("=")
        try:
            body[k] = json.loads(v)
        except json.JSONDecodeError:
            body[k] = v  # coi như string trần
    if not body:
        die("task-update cần ít nhất 1 --set key=value.")
    if not _confirm_or_dry(args, {"taskId": args.task_id, **body}, f"task-update {args.task_id}"):
        return
    api(ctx, "PUT", f"/tasks/{args.task_id}", data=body)
    print(f"OK — task {args.task_id} updated")


# --- Vạn năng (self-improve) ---

def cmd_raw(ctx, args):
    params = {}
    for kv in args.query or []:
        k, _, v = kv.partition("=")
        params[k] = v
    data = json.loads(args.data) if args.data else None
    if args.method.upper() != "GET" and not _confirm_or_dry(
            args, {"method": args.method, "path": args.path, "params": params, "data": data},
            f"raw {args.method} {args.path}"):
        return
    _dump(api(ctx, args.method, args.path, params=params, data=data))


# ========================== CLI ==========================

def build_parser():
    p = argparse.ArgumentParser(description="CRM/OSSA client (CRM_PAT, X-API-Key)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("whoami", help="User hiện tại (GET /users/me)")
    sub.add_parser("doctor", help="Kiểm tra core an toàn (config/token/whoami) — KHÔNG in token")

    sc = sub.add_parser("scan", help="Scan resource tra-cứu (workspaces/task-categories/roles)")
    sc.add_argument("resource", nargs="?", help="Trống = scan hết")
    sc.add_argument("--write", action="store_true", help="Ghi vào config.resources")

    sr = sub.add_parser("source", help="Source code CRM để tra endpoint: status|sync|find <keyword>")
    sr.add_argument("action", nargs="?", default="status",
                    choices=["status", "sync", "find"], help="Mặc định status")
    sr.add_argument("keyword", nargs="?", help="Từ khoá (chỉ dùng với 'find')")

    ls = sub.add_parser("list", help="List: users|contacts|companies|customers|tasks|task-categories|roles")
    ls.add_argument("resource")
    ls.add_argument("--query", action="append", help="k=v (lặp lại) -> query string")

    g = sub.add_parser("get", help="Get 1: user|contact|customer|task|role <id>")
    g.add_argument("resource")
    g.add_argument("id")

    cm = sub.add_parser("comments", help="List comment của 1 task")
    cm.add_argument("task_id")

    se = sub.add_parser("search", help="Search task (POST /tasks/search) với --data JSON")
    se.add_argument("--data", help="Body JSON, vd '{\"search\":\"foo\"}'")

    ca = sub.add_parser("comment-add", help="Thêm comment vào task (GHI)")
    ca.add_argument("task_id")
    ca.add_argument("--text", required=True)
    ca.add_argument("--commit", action="store_true")

    tc = sub.add_parser("task-create", help="Tạo task (GHI) — body qua --data JSON")
    tc.add_argument("--data", required=True, help="JSON: title,assignee,reporter,domain,relatedApps[...]")
    tc.add_argument("--commit", action="store_true")

    tu = sub.add_parser("task-update", help="Sửa task (GHI) — --set key=jsonvalue lặp lại")
    tu.add_argument("task_id")
    tu.add_argument("--set", action="append", help="key=jsonvalue, vd status='\"Resolved\"'")
    tu.add_argument("--commit", action="store_true")

    rw = sub.add_parser("raw", help="Gọi endpoint bất kỳ (nền self-improve)")
    rw.add_argument("method")
    rw.add_argument("path", help="Vd /users/me")
    rw.add_argument("--data")
    rw.add_argument("--query", action="append")
    rw.add_argument("--commit", action="store_true")

    return p


HANDLERS = {
    "whoami": cmd_whoami, "doctor": cmd_doctor, "scan": cmd_scan, "source": cmd_source,
    "list": cmd_list, "get": cmd_get, "comments": cmd_comments, "search": cmd_search,
    "comment-add": cmd_comment_add, "task-create": cmd_task_create, "task-update": cmd_task_update,
    "raw": cmd_raw,
}


def main():
    args = build_parser().parse_args()
    ctx = load_ctx()
    HANDLERS[args.cmd](ctx, args)


if __name__ == "__main__":
    main()
