# /// script
# requires-python = ">=3.9"
# dependencies = ["requests", "pyyaml"]
# ///
"""
jira_client.py — helper + CLI cho Jira Cloud của team, dùng JIRA_PAT (scoped token).

Mọi thứ (site, cloudId, project, field, alias, VÀ email cá nhân) đọc từ config.yml cạnh script.
config.yml GITIGNORED (chứa host/id/email nội bộ); khuôn commit là config.example.yml.
KHÔNG hardcode trong code, KHÔNG còn profile.yml.

XÁC THỰC (không bao giờ in token):
  Token đọc theo thứ tự — (1) env $JIRA_PAT  → (2) fallback `pass show personal/JIRA_PAT`
  (chạy qua subprocess, capture output vào biến, KHÔNG in ra stdout → không vào transcript).
  Scoped token nên gọi qua gateway: https://api.atlassian.com/ex/jira/<cloudId>/...
  Auth: HTTP Basic (email:token) — email lấy từ config.yml.

TEST / VERIFY: chạy `doctor` (an toàn, không in token). ĐỪNG tự gõ echo/env/cat/pass show
  chạm biến token để "kiểm tra" — bẫy `${VAR:-...}` sẽ bung ra chính token.

Chạy:  uv run jira_client.py <command> [options]
Xem:   uv run jira_client.py --help

Lệnh ĐỌC (read-only):
  myself                  Thông tin user hiện tại (verify token).
  projects                List mọi project user truy cập được (scan; tự phân trang).
  get <KEY>               1 issue gọn (ADF description -> text). --fields --json --raw
  comments <KEY>          List comment (id + created + author + body->text). --json
  search "<JQL>"          JQL search (tự phân trang). --fields --limit --json
  transitions <KEY>       List transition khả dụng (id + name).

Lệnh GHI (side-effect — mặc định --dry-run IN payload, thêm --commit mới ghi thật):
  comment <KEY> --text "..."          Thêm comment (text -> ADF). Hoặc --text-file <path>.
  comment-edit <KEY> <ID> --text ...  Sửa nội dung 1 comment đã có (PUT, giữ id).
  description <KEY> --text "..."      Ghi description (heading h1-h3). Không đè bản có sẵn (--force). --text-file <path>.
  transition <KEY> --to "<name|alias>"Chuyển status.
  assign <KEY> --to <email|me|id>     Gán người.
  edit <KEY> --field <f> --value <v>  Sửa 1 field (description tự text->ADF).

Vạn năng (nền cho "thao tác mọi thứ" + self-improve):
  raw <METHOD> <path> [--data <json>] [--query k=v]...
      Gọi endpoint Jira REST bất kỳ qua đúng auth+gateway đã đóng gói.
      GET chạy thẳng; method khác mặc định --dry-run, thêm --commit mới gửi.

Hàm import được (skill khác `from jira_client import ...`):
  load_ctx(), jira_get(), jira_search(), jira_raw(), adf_to_text(), text_to_adf()
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import requests
import yaml

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
CONFIG_PATH = SKILL_DIR / "config.yml"   # GITIGNORED — gồm site/cloudId/field/email; khuôn: config.example.yml

# Field chuẩn của Jira (nhận thẳng tên, không cần map trong config).
STANDARD_FIELDS = {
    "summary", "status", "assignee", "reporter", "priority", "issuetype",
    "labels", "parent", "description", "created", "updated", "duedate",
    "resolution", "components", "fixVersions", "subtasks", "comment",
}


# ----------------------------- Context / auth -----------------------------

class Ctx:
    """Gói mọi thứ cần để gọi API: config, email, token, base URL, session."""
    def __init__(self, cfg, email, token):
        self.cfg = cfg
        self.email = email
        self.cloud_id = cfg.get("cloud_id") or fetch_cloud_id(cfg["site"])
        self.base = f"https://api.atlassian.com/ex/jira/{self.cloud_id}"
        self.session = requests.Session()
        self.session.auth = (email, token)
        self.session.headers.update({"Accept": "application/json"})


def _load_yaml(path):
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def token_source(auth):
    """Tên biến env + pass entry của token. `JIRA_TOKEN_ENV` (vd JIRA_ADMIN_PAT) ghi đè config
    cho 1 lệnh — dùng token admin tạm để sửa cấu hình, xem instructions/jira/jira-admin-config-token.md."""
    override = os.environ.get("JIRA_TOKEN_ENV", "").strip()
    if override:
        return override, f"personal/{override}"
    return auth.get("token_env", "JIRA_PAT"), auth.get("pass_entry")


def resolve_token(cfg):
    """Env trước; trống thì fallback `pass show` (capture, KHÔNG in). Không có -> lỗi."""
    auth = cfg.get("auth", {})
    env_name, entry = token_source(auth)
    tok = os.environ.get(env_name, "").strip()
    if tok:
        return tok
    if entry:
        try:
            out = subprocess.run(
                ["pass", "show", entry],
                capture_output=True, text=True, timeout=20,
            )
            if out.returncode == 0:
                tok = out.stdout.strip()
                if tok:
                    return tok
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
    die(
        f"Chưa lấy được token (env ${env_name} trống, `pass show {entry}` cũng không có).\n"
        f"  • ĐÃ có PAT trong kho: mở terminal mới (auto-load nạp ${env_name}), "
        f"hoặc export {env_name}=\"$(pass show {entry})\", hoặc đảm bảo `pass show {entry}` chạy được.\n"
        f"  • CHƯA có PAT (lần đầu): tạo API token (nên loại scoped) tại "
        f"https://id.atlassian.com/manage-profile/security/api-tokens, backup PAT nơi an toàn "
        f"(vd Passbolt) vì nó thao tác dưới danh nghĩa chính bạn, rồi nạp vào kho token "
        f"(skill setup-use-credential) TRƯỚC khi chạy lại."
    )


def fetch_cloud_id(site):
    r = requests.get(f"https://{site}/_edge/tenant_info", timeout=20)
    r.raise_for_status()
    return r.json()["cloudId"]


def load_ctx():
    """Dựng Ctx từ config.yml (gồm email). Thiếu email/config -> lỗi hướng dẫn."""
    cfg = _load_yaml(CONFIG_PATH)
    if not cfg:
        die(f"Không đọc được config: {CONFIG_PATH} — copy config.example.yml -> config.yml rồi điền.")
    email = (cfg.get("email") or os.environ.get("JIRA_EMAIL") or "").strip()
    if not email or email == "ban@bsscommerce.com":
        die(
            f"Thiếu email cá nhân trong {CONFIG_PATH}. Copy config.example.yml -> config.yml "
            f"và điền `email: <email Atlassian của bạn>`."
        )
    token = resolve_token(cfg)
    return Ctx(cfg, email, token)


# ----------------------------- HTTP core -----------------------------

def api(ctx, method, path, params=None, data=None):
    """Gọi 1 endpoint Jira REST qua gateway. Trả JSON (hoặc None nếu body rỗng)."""
    url = ctx.base + path if path.startswith("/") else f"{ctx.base}/{path}"
    headers = {}
    if data is not None:
        headers["Content-Type"] = "application/json"
    r = ctx.session.request(
        method.upper(), url, params=params,
        data=json.dumps(data) if data is not None else None,
        headers=headers, timeout=40,
    )
    if r.status_code >= 400:
        die(f"HTTP {r.status_code} {method} {path}\n{r.text[:1500]}")
    if not r.content:
        return None
    ctype = r.headers.get("Content-Type", "")
    return r.json() if "json" in ctype else r.text


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


# ----------------------------- ADF <-> text -----------------------------

def adf_to_text(node, depth=0):
    """Atlassian Document Format (JSON lồng) -> plaintext markdown-ish. Giảm token."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    t = node.get("type")
    content = node.get("content", [])

    def kids(sep=""):
        return sep.join(adf_to_text(c, depth) for c in content)

    if t == "doc":
        return "\n".join(adf_to_text(c, depth) for c in content).strip()
    if t == "paragraph":
        return kids()
    if t == "text":
        txt = node.get("text", "")
        for m in node.get("marks", []):
            mt = m.get("type")
            if mt == "code":
                txt = f"`{txt}`"
            elif mt == "strong":
                txt = f"**{txt}**"
            elif mt == "em":
                txt = f"*{txt}*"
            elif mt == "link":
                href = m.get("attrs", {}).get("href", "")
                txt = f"[{txt}]({href})"
        return txt
    if t == "hardBreak":
        return "\n"
    if t == "heading":
        lvl = node.get("attrs", {}).get("level", 1)
        return "\n" + "#" * lvl + " " + kids() + "\n"
    if t == "bulletList":
        return "\n".join("  " * depth + "- " + adf_to_text(li, depth + 1).strip()
                         for li in content)
    if t == "orderedList":
        out = []
        for i, li in enumerate(content, 1):
            out.append("  " * depth + f"{i}. " + adf_to_text(li, depth + 1).strip())
        return "\n".join(out)
    if t == "listItem":
        return kids("\n")
    if t == "codeBlock":
        return "\n```\n" + kids() + "\n```\n"
    if t == "blockquote":
        return "> " + kids()
    if t == "rule":
        return "\n---\n"
    if t == "mention":
        return node.get("attrs", {}).get("text", "@?")
    if t == "emoji":
        return node.get("attrs", {}).get("text", "")
    if t == "inlineCard":
        return node.get("attrs", {}).get("url", "")
    if t == "mediaInline" or t == "media":
        return "[media]"
    if t in ("table",):
        return "\n" + kids("\n")
    if t in ("tableRow",):
        cells = [adf_to_text(c, depth).strip().replace("\n", " ") for c in content]
        return "| " + " | ".join(cells) + " |"
    if t in ("tableHeader", "tableCell"):
        return kids(" ")
    # fallback: nối nội dung con
    return kids()


# URL trong text thuần KHÔNG tự thành link trong ADF — phải gắn link mark, nếu không Jira
# render ra chữ không bấm được. Bắt http/https tới khoảng trắng; nhả dấu câu cuối kẹp vào URL.
_URL_RE = re.compile(r'https?://[^\s]+')
_URL_TRAILING = '.,;:!?)]}>"\''


def _line_to_inline_nodes(line):
    """Tách 1 dòng thành các text node ADF, bọc URL bằng link mark để render bấm được."""
    nodes = []
    pos = 0
    for m in _URL_RE.finditer(line):
        start, end = m.start(), m.end()
        url = m.group(0)
        # Nhả dấu câu dính cuối URL ra ngoài link (vd "...292)." -> link "...292", text ")." )
        trail = ""
        while url and url[-1] in _URL_TRAILING:
            trail = url[-1] + trail
            url = url[:-1]
            end -= 1
        if not url:
            continue
        if start > pos:
            nodes.append({"type": "text", "text": line[pos:start]})
        nodes.append({"type": "text", "text": url, "marks": [{"type": "link", "attrs": {"href": url}}]})
        pos = end
    if pos < len(line):
        nodes.append({"type": "text", "text": line[pos:]})
    return nodes or [{"type": "text", "text": line}]


# Markdown tối thiểu cho comment/description. Inline: **đậm**, *nghiêng*, `code`, [nhãn](url),
# URL trần. Block: dòng trống = ngắt đoạn (KHÔNG sinh paragraph rỗng - Jira render thành khoảng
# hở to), `- `/`* ` bullet, `1. ` numbered, thụt >=2 space = list con, `### ` heading, `---` = đường
# kẻ. Dòng liền nhau trong 1 đoạn nối bằng hardBreak.
# Heading clamp qua tham số text_to_adf(heading_min, heading_max): mặc định h3-h4 cho COMMENT (h1/h2
# quá to giữa luồng comment); description gọi với h1-h3 (là tài liệu, cần header lớn phân cấp rõ).
_INLINE_RE = re.compile(
    r'\*\*(?P<strong>.+?)\*\*'
    r'|(?<![*\w])\*(?P<em>[^\s*](?:[^*]*[^\s*])?)\*(?![*\w])'
    r'|`(?P<code>[^`]+)`'
    r'|\[(?P<label>[^\]]+)\]\((?P<href>https?://[^)\s]+)\)'
)
_BULLET_RE = re.compile(r'^(?P<indent>\s*)[-*] +(?P<body>.*)$')
_ORDERED_RE = re.compile(r'^(?P<indent>\s*)\d+[.)] +(?P<body>.*)$')
_HEADING_RE = re.compile(r'^(?P<hashes>#{1,6}) +(?P<body>.*)$')
HEADING_MIN, HEADING_MAX = 3, 4  # h5/h6 của Jira nhỏ hơn chữ thường (14px) -> không dùng


def _with_mark(nodes, mark):
    for n in nodes:
        existing = n.get("marks", [])
        # ADF: mark `code` loại trừ mọi mark khác. Chồng strong/em lên text đã có `code`
        # (vd `code` nằm trong **...**) -> Jira trả 400 INVALID_INPUT. Bỏ qua node code.
        if any(m.get("type") == "code" for m in existing):
            continue
        n["marks"] = existing + [mark]
    return nodes


def _inline_nodes(text):
    nodes, pos = [], 0
    for m in _INLINE_RE.finditer(text):
        if m.start() > pos:
            nodes += _line_to_inline_nodes(text[pos:m.start()])
        if m.group("strong") is not None:
            nodes += _with_mark(_inline_nodes(m.group("strong")), {"type": "strong"})
        elif m.group("em") is not None:
            nodes += _with_mark(_inline_nodes(m.group("em")), {"type": "em"})
        elif m.group("code") is not None:
            nodes.append({"type": "text", "text": m.group("code"), "marks": [{"type": "code"}]})
        else:
            href = m.group("href")
            nodes.append({"type": "text", "text": m.group("label"), "marks": [{"type": "link", "attrs": {"href": href}}]})
        pos = m.end()
    if pos < len(text):
        nodes += _line_to_inline_nodes(text[pos:])
    return nodes


def text_to_adf(text, heading_min=HEADING_MIN, heading_max=HEADING_MAX):
    """Markdown tối thiểu -> ADF (xem _INLINE_RE / block rules ở trên).
    heading_min/max: khoảng bậc heading cho phép (comment h3-h4, description h1-h3)."""
    content, para = [], []
    stack = []  # [(indent, list_node)] - list đang mở, sâu dần

    def flush_para():
        if not para:
            return
        inline = []
        for i, ln in enumerate(para):
            if i:
                inline.append({"type": "hardBreak"})
            inline += _inline_nodes(ln)
        content.append({"type": "paragraph", "content": inline})
        para.clear()

    def flush_list():
        if stack:
            content.append(stack[0][1])
            stack.clear()

    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_para()
            flush_list()
            continue
        if stripped == "---":
            flush_para()
            flush_list()
            content.append({"type": "rule"})
            continue
        h = _HEADING_RE.match(stripped)
        if h:
            flush_para()
            flush_list()
            level = min(max(len(h.group("hashes")), heading_min), heading_max)
            content.append({"type": "heading", "attrs": {"level": level}, "content": _inline_nodes(h.group("body"))})
            continue
        b, o = _BULLET_RE.match(line), _ORDERED_RE.match(line)
        if b or o:
            flush_para()
            m = b or o
            kind = "bulletList" if b else "orderedList"
            indent = len(m.group("indent"))
            item = {"type": "listItem", "content": [{"type": "paragraph", "content": _inline_nodes(m.group("body"))}]}
            while stack and indent < stack[-1][0]:
                stack.pop()
            if stack and indent > stack[-1][0]:
                parent_item = stack[-1][1]["content"][-1]
                child = {"type": kind, "content": [item]}
                parent_item["content"].append(child)
                stack.append((indent, child))
            elif stack and stack[-1][1]["type"] == kind:
                stack[-1][1]["content"].append(item)
            else:
                if stack and len(stack) == 1:
                    flush_list()
                if stack:  # đổi kiểu list ở cấp con: mở list anh em mới trong cùng item cha
                    stack.pop()
                    parent_item = stack[-1][1]["content"][-1]
                    child = {"type": kind, "content": [item]}
                    parent_item["content"].append(child)
                    stack.append((indent, child))
                else:
                    stack.append((indent, {"type": kind, "content": [item]}))
            continue
        # dòng thường ngay sau list: kết thúc list, mở đoạn mới
        flush_list()
        para.append(stripped)

    flush_para()
    flush_list()
    if not content:
        content = [{"type": "paragraph", "content": []}]
    return {"type": "doc", "version": 1, "content": content}


# ----------------------------- Field name helpers -----------------------------

def resolve_field_name(ctx, name):
    """Tên thân thiện -> field id (customfield_x). Field chuẩn/`customfield_*` giữ nguyên."""
    name = name.strip()
    if name in STANDARD_FIELDS or name.startswith("customfield_"):
        return name
    fmap = ctx.cfg.get("fields", {})
    if name in fmap:
        return fmap[name]
    return name  # để nguyên; Jira tự báo lỗi nếu sai


def friendly_of(ctx, field_id):
    """Ngược lại: field id -> tên thân thiện (để in cho gọn)."""
    for k, v in ctx.cfg.get("fields", {}).items():
        if v == field_id:
            return k
    return field_id


def parse_fields_arg(ctx, arg, default):
    if not arg:
        return default
    return [resolve_field_name(ctx, f) for f in arg.split(",")]


# ----------------------------- Read commands -----------------------------

def jira_get(ctx, key, fields=None):
    params = {}
    if fields:
        params["fields"] = ",".join(fields)
    return api(ctx, "GET", f"/rest/api/3/issue/{key}", params=params)


def _fmt_field_value(ctx, fid, val):
    if val is None:
        return ""
    if isinstance(val, dict):
        # object hay gặp: status/priority/issuetype/assignee/parent...
        for k in ("displayName", "name", "value", "key"):
            if k in val:
                if fid == "parent":
                    return f'{val.get("key","")} {val.get("fields",{}).get("summary","")}'.strip()
                return str(val[k])
        # ADF description
        if val.get("type") == "doc":
            return adf_to_text(val)
        return json.dumps(val, ensure_ascii=False)
    if isinstance(val, list):
        return ", ".join(_fmt_field_value(ctx, fid, v) for v in val)
    return str(val)


def cmd_get(ctx, args):
    default = ["summary", "status", "assignee", "priority", "issuetype",
               "labels", "parent", "description"]
    fields = parse_fields_arg(ctx, args.fields, default)
    issue = jira_get(ctx, args.key, fields)
    if args.raw:
        print(json.dumps(issue, ensure_ascii=False, indent=2))
        return
    f = issue.get("fields", {})
    if args.json:
        out = {"key": issue["key"]}
        for fid in fields:
            out[friendly_of(ctx, fid)] = _fmt_field_value(ctx, fid, f.get(fid))
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    # text gọn
    print(f'{issue["key"]}  {f.get("summary","")}')
    line = []
    if "status" in f:
        line.append(f'Status: {_fmt_field_value(ctx,"status",f.get("status"))}')
    if "priority" in f:
        line.append(f'Priority: {_fmt_field_value(ctx,"priority",f.get("priority"))}')
    if "issuetype" in f:
        line.append(f'Type: {_fmt_field_value(ctx,"issuetype",f.get("issuetype"))}')
    if line:
        print("   ".join(line))
    if "assignee" in f:
        print(f'Assignee: {_fmt_field_value(ctx,"assignee",f.get("assignee")) or "(unassigned)"}')
    for fid in fields:
        if fid in ("summary", "status", "priority", "issuetype", "assignee", "description"):
            continue
        val = _fmt_field_value(ctx, fid, f.get(fid))
        if val:
            print(f'{friendly_of(ctx,fid)}: {val}')
    if "description" in fields:
        desc = f.get("description")
        print("Description:")
        print(adf_to_text(desc) if desc else "  (trống)")


def cmd_comments(ctx, args):
    data = api(ctx, "GET", f"/rest/api/3/issue/{args.key}/comment")
    comments = data.get("comments", [])
    if args.json:
        out = [{
            "id": c["id"],
            "author": c.get("author", {}).get("displayName", ""),
            "created": c.get("created", ""),
            "body": adf_to_text(c.get("body")),
        } for c in comments]
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    print(f'{args.key} — {len(comments)} comment')
    for c in comments:
        author = c.get("author", {}).get("displayName", "?")
        print(f'\n[{c["id"]}] {author} · {c.get("created","")}')
        print(adf_to_text(c.get("body")))


def jira_search(ctx, jql, fields=None, limit=100):
    """JQL search qua endpoint enhanced /search/jql, tự phân trang tới `limit`."""
    got = []
    token = None
    page_fields = fields or ["key", "summary", "status", "assignee"]
    while len(got) < limit:
        params = {
            "jql": jql,
            "maxResults": min(100, limit - len(got)),
            "fields": ",".join(page_fields),
        }
        if token:
            params["nextPageToken"] = token
        data = api(ctx, "GET", "/rest/api/3/search/jql", params=params)
        got.extend(data.get("issues", []))
        token = data.get("nextPageToken")
        if not token or not data.get("issues"):
            break
    return got[:limit]


def cmd_search(ctx, args):
    default = ["summary", "status", "assignee"]
    fields = parse_fields_arg(ctx, args.fields, default)
    issues = jira_search(ctx, args.jql, fields, args.limit)
    if args.json:
        out = []
        for it in issues:
            row = {"key": it["key"]}
            for fid in fields:
                row[friendly_of(ctx, fid)] = _fmt_field_value(ctx, fid, it["fields"].get(fid))
            out.append(row)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    print(f'{len(issues)} issue')
    for it in issues:
        f = it["fields"]
        parts = [it["key"], f.get("summary", "")]
        st = _fmt_field_value(ctx, "status", f.get("status"))
        if st:
            parts.append(f"[{st}]")
        print("  " + "  ".join(p for p in parts if p))


def cmd_transitions(ctx, args):
    data = api(ctx, "GET", f"/rest/api/3/issue/{args.key}/transitions")
    for tr in data.get("transitions", []):
        to = tr.get("to", {}).get("name", "")
        print(f'{tr["id"]}\t{tr["name"]}\t-> {to}')


def cmd_myself(ctx, args):
    me = api(ctx, "GET", "/rest/api/3/myself")
    print(json.dumps({
        "accountId": me.get("accountId"),
        "displayName": me.get("displayName"),
        "email": me.get("emailAddress"),
        "timeZone": me.get("timeZone"),
    }, ensure_ascii=False, indent=2))


def cmd_doctor(ctx, args):
    """Kiểm tra core AN TOÀN — KHÔNG bao giờ in token.
    Cách DUY NHẤT nên dùng để verify: đừng tự gõ echo/env/cat/pass show chạm token
    (bẫy `${VAR:-...}` bung ra chính token). Chỉ in NGUỒN token, không in giá trị."""
    auth = ctx.cfg.get("auth", {})
    env_name, _ = token_source(auth)
    src = "env" if os.environ.get(env_name, "").strip() else "pass"
    print(f"config  : {CONFIG_PATH} ({'OK' if CONFIG_PATH.exists() else 'MISSING'})")
    print(f"site    : {ctx.cfg.get('site')}  cloudId={ctx.cloud_id}")
    print(f"email   : {ctx.email}")
    print(f"token   : OK (biến: {env_name}, nguồn: {src})")   # KHÔNG in value/length
    me = api(ctx, "GET", "/rest/api/3/myself")
    print(f"whoami  : {me.get('displayName')} <{me.get('emailAddress')}>")


def cmd_projects(ctx, args):
    got = []
    start = 0
    while True:
        data = api(ctx, "GET", "/rest/api/3/project/search",
                   params={"startAt": start, "maxResults": 50})
        got.extend(data.get("values", []))
        if data.get("isLast", True):
            break
        start += len(data.get("values", []))
        if not data.get("values"):
            break
    if args.json:
        print(json.dumps(
            [{"key": p["key"], "name": p["name"], "id": p["id"],
              "type": p.get("projectTypeKey", "")} for p in got],
            ensure_ascii=False, indent=2))
        return
    print(f'{len(got)} project')
    for p in got:
        print(f'{p["key"]}\t{p["name"]}\t({p.get("projectTypeKey","")})')


# ----------------------------- Write commands -----------------------------

def _confirm_or_dry(args, payload, what):
    """In payload; nếu chưa --commit thì DỪNG (dry-run). Trả True nếu được ghi thật."""
    print(f'[{"COMMIT" if args.commit else "DRY-RUN"}] {what}')
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not args.commit:
        print("(dry-run — thêm --commit để ghi thật)")
        return False
    return True


def _comment_text(args):
    """--text hoặc --text-file (file tiện cho comment dài nhiều dòng, khỏi lo quote shell)."""
    if args.text_file:
        return Path(args.text_file).read_text(encoding="utf-8")
    if args.text is None:
        die("Cần --text hoặc --text-file.")
    return args.text


def cmd_comment(ctx, args):
    body = {"body": text_to_adf(_comment_text(args))}
    if not _confirm_or_dry(args, {"issue": args.key, **body}, f"add comment -> {args.key}"):
        return
    res = api(ctx, "POST", f"/rest/api/3/issue/{args.key}/comment", data=body)
    print(f'OK — comment id {res.get("id")}')


def cmd_attach(ctx, args):
    """Upload file đính kèm vào issue (multipart; Jira bắt buộc header X-Atlassian-Token: no-check)."""
    paths = [Path(p) for p in args.files]
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        die(f"Không thấy file: {', '.join(missing)}")
    names = [args.name] if args.name and len(paths) == 1 else [p.name for p in paths]
    preview = {"issue": args.key, "files": [{"name": n, "bytes": p.stat().st_size} for n, p in zip(names, paths)]}
    if not _confirm_or_dry(args, preview, f"attach -> {args.key}"):
        return
    handles = [p.open("rb") for p in paths]
    try:
        r = ctx.session.post(
            f"{ctx.base}/rest/api/3/issue/{args.key}/attachments",
            headers={"X-Atlassian-Token": "no-check"},
            files=[("file", (n, h)) for n, h in zip(names, handles)],
            timeout=120,
        )
    finally:
        for h in handles:
            h.close()
    if r.status_code >= 400:
        die(f"HTTP {r.status_code} POST attachments\n{r.text[:1500]}")
    browse = ctx.cfg.get("browse_url", "").rstrip("/")
    for a in r.json():
        link = f"{browse.rsplit('/browse', 1)[0]}/rest/api/3/attachment/content/{a['id']}" if browse else ""
        print(f"OK — attachment id {a['id']} {a['filename']} {link}")


def cmd_comment_edit(ctx, args):
    """Ghi đè nội dung 1 comment đã có (giữ nguyên id/vị trí, không tạo comment mới)."""
    current = api(ctx, "GET", f"/rest/api/3/issue/{args.key}/comment/{args.id}")
    body = {"body": text_to_adf(_comment_text(args))}
    preview = {"issue": args.key, "comment_id": args.id, "before": adf_to_text(current.get("body")), **body}
    if not _confirm_or_dry(args, preview, f"edit comment {args.id} -> {args.key}"):
        return
    res = api(ctx, "PUT", f"/rest/api/3/issue/{args.key}/comment/{args.id}", data=body)
    print(f'OK — comment id {res.get("id")} updated {res.get("updated", "")}')


def cmd_description(ctx, args):
    """Ghi description cho issue (heading h1-h3 - description là tài liệu, khác comment h3-h4).
    Mặc định KHÔNG ghi đè description đã có nội dung (rule write-risk 🔴) - cần --force."""
    current = api(ctx, "GET", f"/rest/api/3/issue/{args.key}", params={"fields": "description"})
    cur_adf = (current.get("fields") or {}).get("description")
    cur_text = adf_to_text(cur_adf).strip() if cur_adf else ""
    if cur_text and not args.force:
        die(f'{args.key} đã có description ({len(cur_text)} ký tự). Thêm --force để ghi đè, '
            f'hoặc dùng `edit --field description` nếu cố ý thay.')
    adf = text_to_adf(_comment_text(args), heading_min=1, heading_max=3)
    body = {"fields": {"description": adf}}
    overwrite = bool(cur_text)
    preview = {"issue": args.key, **({"before": cur_text} if overwrite else {}), **body}
    if not _confirm_or_dry(args, preview,
                           f'set description -> {args.key}' + (' (OVERWRITE)' if overwrite else '')):
        return
    api(ctx, "PUT", f"/rest/api/3/issue/{args.key}", data=body)
    print(f'OK — {args.key} description updated')


def cmd_transition(ctx, args):
    # alias -> tên thật
    target = ctx.cfg.get("status_aliases", {}).get(args.to.lower(), args.to)
    data = api(ctx, "GET", f"/rest/api/3/issue/{args.key}/transitions")
    match = None
    for tr in data.get("transitions", []):
        if tr["name"].lower() == target.lower() or tr.get("to", {}).get("name", "").lower() == target.lower():
            match = tr
            break
    if not match:
        avail = ", ".join(f'{t["name"]}' for t in data.get("transitions", []))
        die(f'Không thấy transition "{target}" cho {args.key}. Khả dụng: {avail}')
    payload = {"transition": {"id": match["id"]}}
    if not _confirm_or_dry(args, {"issue": args.key, "to": match["name"], **payload},
                           f'transition {args.key} -> {match["name"]}'):
        return
    api(ctx, "POST", f"/rest/api/3/issue/{args.key}/transitions", data=payload)
    print(f'OK — {args.key} -> {match["name"]}')


def _resolve_account_id(ctx, who):
    if who == "me":
        return api(ctx, "GET", "/rest/api/3/myself")["accountId"]
    if "@" not in who:
        return who  # coi như đã là accountId
    res = api(ctx, "GET", "/rest/api/3/user/search", params={"query": who})
    if not res:
        die(f'Không tìm thấy user cho "{who}"')
    return res[0]["accountId"]


def cmd_assign(ctx, args):
    acc = _resolve_account_id(ctx, args.to)
    payload = {"accountId": acc}
    if not _confirm_or_dry(args, {"issue": args.key, **payload}, f"assign {args.key} -> {args.to}"):
        return
    api(ctx, "PUT", f"/rest/api/3/issue/{args.key}/assignee", data=payload)
    print(f'OK — {args.key} assigned to {args.to}')


def _field_schema(ctx, fid):
    """Schema của 1 field (type/items) từ /field — để bọc value đúng kiểu Jira cần."""
    for f in api(ctx, "GET", "/rest/api/3/field") or []:
        if f.get("id") == fid:
            return f.get("schema") or {}
    return {}


def _shape_value(ctx, fid, raw):
    """Chuỗi user gõ -> value đúng kiểu. Jira từ chối chuỗi trần cho select/priority."""
    if fid == "description":
        return text_to_adf(raw)
    if fid == "labels":
        return [x.strip() for x in raw.split(",")]
    if fid == "priority":
        return {"name": raw}
    if fid.startswith("customfield_"):
        s = _field_schema(ctx, fid)
        if s.get("type") == "option":
            return {"value": raw}
        if s.get("type") == "array" and s.get("items") == "option":
            return [{"value": x.strip()} for x in raw.split(",")]
        if s.get("type") == "number":
            return float(raw)
    return raw


def cmd_edit(ctx, args):
    fid = resolve_field_name(ctx, args.field)
    if args.value_json is not None:
        value = json.loads(args.value_json)
    elif args.value is not None:
        value = _shape_value(ctx, fid, args.value)
    else:
        sys.exit("ERROR: cần --value hoặc --value-json")
    payload = {"fields": {fid: value}}
    if not _confirm_or_dry(args, {"issue": args.key, **payload}, f"edit {args.key}.{args.field}"):
        return
    api(ctx, "PUT", f"/rest/api/3/issue/{args.key}", data=payload)
    print(f'OK — {args.key}.{args.field} updated')


def jira_raw(ctx, method, path, data=None, params=None):
    return api(ctx, method, path, params=params, data=data)


def cmd_changelog(ctx, args):
    """Lịch sử đổi status của 1 hoặc nhiều issue (read-only): {key: [{at, from, to}]} theo thời gian."""
    out = {}
    for key in args.keys:
        items, start = [], 0
        while True:
            res = api(ctx, "GET", f"/rest/api/3/issue/{key}/changelog",
                      params={"startAt": start, "maxResults": 100})
            for h in res.get("values", []):
                for it in h.get("items", []):
                    if it.get("field") == "status":
                        items.append({"at": h["created"], "from": it.get("fromString"),
                                      "to": it.get("toString")})
            start += len(res.get("values", []))
            if res.get("isLast", True) or not res.get("values"):
                break
        out[key] = sorted(items, key=lambda x: x["at"])
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    for key, items in out.items():
        print(key + ": " + (" → ".join(f"{i['at'][:10]} {i['to']}" for i in items) or "(chưa đổi status)"))


def cmd_raw(ctx, args):
    params = {}
    for kv in args.query or []:
        k, _, v = kv.partition("=")
        params[k] = v
    data = json.loads(args.data) if args.data else None
    if args.method.upper() != "GET":
        if not _confirm_or_dry(args, {"method": args.method, "path": args.path,
                                      "params": params, "data": data},
                               f"raw {args.method} {args.path}"):
            return
    res = api(ctx, args.method, args.path, params=params, data=data)
    print(json.dumps(res, ensure_ascii=False, indent=2) if not isinstance(res, str) else res)


# ----------------------------- CLI -----------------------------

def build_parser():
    p = argparse.ArgumentParser(description="Jira Cloud client (JIRA_PAT scoped token)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("myself", help="Thông tin user hiện tại")
    sub.add_parser("doctor", help="Kiểm tra core an toàn (config/token/whoami) — KHÔNG in token")

    pr = sub.add_parser("projects", help="List project user truy cập được")
    pr.add_argument("--json", action="store_true")

    g = sub.add_parser("get", help="1 issue gọn")
    g.add_argument("key")
    g.add_argument("--fields", help="Danh sách field, phẩy ngăn (tên thân thiện OK)")
    g.add_argument("--json", action="store_true")
    g.add_argument("--raw", action="store_true", help="In JSON gốc từ API")

    c = sub.add_parser("comments", help="List comment (id + created)")
    c.add_argument("key")
    c.add_argument("--json", action="store_true")

    s = sub.add_parser("search", help="JQL search (tự phân trang)")
    s.add_argument("jql")
    s.add_argument("--fields")
    s.add_argument("--limit", type=int, default=100)
    s.add_argument("--json", action="store_true")

    t = sub.add_parser("transitions", help="List transition khả dụng")
    t.add_argument("key")

    cm = sub.add_parser("comment", help="Thêm comment (GHI)")
    cm.add_argument("key")
    cm.add_argument("--text")
    cm.add_argument("--text-file", help="Đọc nội dung từ file (markdown tối thiểu)")
    cm.add_argument("--commit", action="store_true")

    de = sub.add_parser("description", help="Ghi description cho task (GHI; heading h1-h3; mặc định không đè bản đã có)")
    de.add_argument("key")
    de.add_argument("--text")
    de.add_argument("--text-file", help="Đọc nội dung từ file (markdown tối thiểu, heading h1-h3)")
    de.add_argument("--force", action="store_true", help="Cho phép ghi đè description đã có nội dung")
    de.add_argument("--commit", action="store_true")

    ce = sub.add_parser("comment-edit", help="Sửa nội dung 1 comment đã có (GHI)")
    ce.add_argument("key")
    ce.add_argument("id", help="Comment id (xem bằng `comments <KEY>`)")
    ce.add_argument("--text")
    ce.add_argument("--text-file", help="Đọc nội dung từ file (markdown tối thiểu)")
    ce.add_argument("--commit", action="store_true")

    at = sub.add_parser("attach", help="Upload file đính kèm vào issue (GHI)")
    at.add_argument("key")
    at.add_argument("files", nargs="+", help="Đường dẫn file")
    at.add_argument("--name", help="Đổi tên file hiển thị trên Jira (chỉ khi upload 1 file)")
    at.add_argument("--commit", action="store_true")

    tr = sub.add_parser("transition", help="Chuyển status (GHI)")
    tr.add_argument("key")
    tr.add_argument("--to", required=True, help="Tên status/transition hoặc alias")
    tr.add_argument("--commit", action="store_true")

    asg = sub.add_parser("assign", help="Gán người (GHI)")
    asg.add_argument("key")
    asg.add_argument("--to", required=True, help="email | me | accountId")
    asg.add_argument("--commit", action="store_true")

    ed = sub.add_parser("edit", help="Sửa 1 field (GHI)")
    ed.add_argument("key")
    ed.add_argument("--field", required=True)
    ed.add_argument("--value", help="Chuỗi; tự bọc đúng kiểu (priority, select option, number)")
    ed.add_argument("--value-json", help="Value dạng JSON thô, dùng khi field có kiểu lạ")
    ed.add_argument("--commit", action="store_true")

    cl = sub.add_parser("changelog", help="Lịch sử đổi status (read-only), nhận nhiều key")
    cl.add_argument("keys", nargs="+")
    cl.add_argument("--json", action="store_true")

    rw = sub.add_parser("raw", help="Gọi endpoint bất kỳ (nền self-improve)")
    rw.add_argument("method")
    rw.add_argument("path", help="Vd /rest/api/3/issue/OPCS-1")
    rw.add_argument("--data", help="JSON body (chuỗi)")
    rw.add_argument("--query", action="append", help="k=v (lặp lại được)")
    rw.add_argument("--commit", action="store_true")

    return p


HANDLERS = {
    "myself": cmd_myself, "doctor": cmd_doctor, "projects": cmd_projects, "get": cmd_get,
    "comments": cmd_comments, "search": cmd_search, "transitions": cmd_transitions,
    "comment": cmd_comment, "comment-edit": cmd_comment_edit, "description": cmd_description,
    "attach": cmd_attach,
    "transition": cmd_transition, "assign": cmd_assign,
    "edit": cmd_edit, "changelog": cmd_changelog, "raw": cmd_raw,
}


def main():
    args = build_parser().parse_args()
    ctx = load_ctx()
    HANDLERS[args.cmd](ctx, args)


if __name__ == "__main__":
    main()
