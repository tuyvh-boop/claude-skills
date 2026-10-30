# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
journal_setup.py — phần tất định của skill setup-work-journal: dò máy, dựng khung, bật hook, tự test, kiểm tra.

Lệnh (chạy `uv run journal_setup.py <lệnh> --help` để xem cờ):
  detect   [--path P]                      máy có gì (git, gh, uv, scanner, git identity, hooksPath global) + journal có sẵn chưa
  modules  [--role R]                      danh mục loại lưu trữ (markdown), đánh dấu loại tick sẵn cho vai trò
  benefits --role R                        bảng lợi ích theo vai trò (markdown)
  plan     --path P --role R [--modules a,b] [--owner O] [--connect A|B|none] [--git-identity keep|own|shared]
                                           cây folder + danh sách file sẽ tạo / gộp, KHÔNG ghi gì
  apply    --path P --role R [--modules a,b] [--owner O] [--dry-run]
                                           tạo / gộp khung (idempotent: không đè file người dùng đã sửa)
  hooks    --path P                        git init nếu cần + bật core.hooksPath=.githooks + chmod
  selftest --path P                        clone tạm, commit secret giả → hook phải chặn; commit sạch → phải qua
  remote-check --path P                    visibility của remote GitHub (PRIVATE / PUBLIC / none)
  companion --path P [--owner O]           sinh skill journal-save trong <journal>/.claude/skills/ (đi theo repo)
  link-companion --path P                  symlink skill đó vào ~/.claude/skills/ để dùng ở mọi repo
  doctor   --path P                        bảng kiểm tổng hợp (markdown)
Output JSON trừ modules / benefits / plan / doctor (markdown).
"""
import argparse
import json
import os
import platform
import re
import secrets
import shutil
import string
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = Path(__file__).resolve()
TPL = SKILL / "templates"

ROLE_LABEL = {"dev": "Dev", "tester": "Tester", "pma": "BA / PMA"}
ROLES = list(ROLE_LABEL)

# Mỗi loại lưu trữ: level = root (folder gốc) · app (trong apps/<app>/) · task (trong folder task).
# tree: (đường dẫn, comment); `TASK/` = folder một task. render_tree tự sắp thứ tự + vẽ nhánh.
# rec: theo vai trò — "core" = khuyên dùng (tick sẵn) · "extra" = có thể thêm (gợi ý, không tick). Không có = loại khác.
# Ignore (evidence, file đính kèm…) nằm hết ở templates/gitignore.tmpl, không theo loại — mọi journal đều có.
CORE, EXTRA = "core", "extra"
MODULES = [
    dict(id="tasks", usage='"ghi vào retro task ABC-123: AI làm sai chỗ …, đã sửa thế nào"', title="Task theo app", required=True, level="root", rec={r: CORE for r in ROLES},
         stores="Mỗi app một folder, mỗi task một folder: README, retro (bài học + chỗ AI làm sai), ghi chép lẻ, _local/",
         tree=[('apps/<app>/', '1 folder / app'),
               ('apps/<app>/[<mã-task>]-<brief>/', '1 folder / task, vd [ABC-123]-fix-x'),
               ('TASK/README.md', 'mục tiêu · kết quả · link'),
               ('TASK/retro.md', 'bài học, chỗ AI làm sai'),
               ('TASK/<yy-mm-dd>-<slug>.md', 'ghi chép lẻ'),
               ('TASK/_local/', 'nhạy cảm, không lên git')]),
    dict(id="dev-artifacts", usage='"lưu research này vào journal của task ABC-123"', title="Tài liệu dev", level="task", rec={"dev": CORE},
         stores="context, research, chẩn đoán lỗi, solutions, decisions, thiết kế DB, plan, review, giải thích code, "
                "sổ lỗi lúc code, script, prototype UI, golive",
         tree=[('TASK/plan-overview.md', 'plan tổng các giai đoạn'),
               ('TASK/plan-implementation.md', 'plan chi tiết + tiến độ'),
               ('TASK/database-structure-design.md', 'thiết kế DB đã chốt'),
               ('TASK/implement-retro.md', 'sổ lỗi lúc code từng phase'),
               ('TASK/golive.md', 'checklist golive'),
               ('TASK/context/', 'bối cảnh, vùng ảnh hưởng'),
               ('TASK/research/', 'điều tra'),
               ('TASK/diagnosis/', 'chẩn đoán lỗi'),
               ('TASK/solutions/', 'so sánh các hướng'),
               ('TASK/decisions/', 'chốt phương án + lý do'),
               ('TASK/explanations/', 'giải thích code, 1 phase 1 file'),
               ('TASK/review-code/', 'review vòng N'),
               ('TASK/scripts/', 'tài liệu script bulk update'),
               ('TASK/ui-prototype/', 'prototype HTML thay bản thiết kế')]),
    dict(id="test-artifacts", usage='"ghi kết quả lượt test r2 của task ABC-123"', title="Tài liệu test / nghiệm thu", level="task", rec={"dev": CORE, "tester": CORE},
         stores="case nghiệm thu, lượt chạy (report + results.json), runbook, phản hồi test, data test "
                "(ảnh bằng chứng không lên git)",
         tree=[('TASK/tests/', 'nghiệm thu'),
               ('TASK/tests/acceptance-tests.md', 'bộ case nghiệm thu'),
               ('TASK/tests/test-data.md', 'store, product dùng để test'),
               ('TASK/tests/runs/<yy-mm-dd>-r<N>-<phạm-vi>/', '1 lượt: report.md + results.json'),
               ('TASK/tests/runs/<yy-mm-dd>-r<N>-<phạm-vi>/evidence/', 'ảnh, log (không lên git)'),
               ('TASK/tests/runbooks/', 'cách chạy case đã đúc'),
               ('TASK/tests/feedback/', 'phản hồi test')]),
    dict(id="requirement-artifacts", usage='"lưu biên bản họp hôm nay vào task ABC-123" · "thêm câu hỏi này vào open-questions của task ABC-123"', title="Tài liệu requirement", level="task", rec={"pma": CORE},
         stores="ghi chú requirement, câu hỏi chờ trả lời, changelog, quyết định, ghi chú họp",
         tree=[('TASK/requirement/', 'ghi chú requirement'),
               ('TASK/requirement/open-questions.md', 'câu hỏi chờ trả lời'),
               ('TASK/requirement/changelog.md', 'lịch sử đổi requirement'),
               ('TASK/decisions/', 'chốt quyết định + lý do'),
               ('TASK/meetings/', 'ghi chú họp')]),
    dict(id="app-profile", usage='"ghi vào hồ sơ app <app>: deploy phải chạy migration trước"', title="Hồ sơ app", level="app", rec={"dev": CORE, "tester": CORE, "pma": EXTRA},
         stores="tri thức bền vững của app: repo, deploy, môi trường test, chỗ hay lỗi",
         tree=[('apps/<app>/app-profile.md', 'tri thức bền vững của app')]),
    dict(id="daily-work", usage='"hôm nay mình làm gì, ghi daily log"', title="Nhật ký theo ngày", level="root", rec={r: CORE for r in ROLES},
         stores="việc đã làm mỗi ngày / mỗi tuần",
         tree=[('daily-work/<yy-mm>/<yy-mm-dd>.md', 'việc đã làm, 1 file / ngày')]),
    dict(id="learning", usage='"ghi khái niệm <X> vào sổ học"', title="Sổ học", level="root", rec={"dev": CORE, "tester": EXTRA, "pma": EXTRA},
         stores="khái niệm chưa nắm, ôn tới khi nắm",
         tree=[('learning/[<domain>]-<slug>/', 'sổ học: 1 khái niệm / folder'),
               ('learning/[<domain>]-<slug>/README.md', 'là gì · gặp ở đâu · tự kiểm')]),
    dict(id="build-skills", usage='"lưu ý tưởng skill <X> vào build-skills"', title="Nguyên liệu dựng skill AI", level="root", rec={r: EXTRA for r in ROLES},
         stores="lý do, nguyên liệu, plan để dựng skill AI mới",
         tree=[('build-skills/<tên-skill>/', 'dựng skill: README.md + plan.md')]),
    dict(id="build-workflow", usage='"lưu ý tưởng workflow <X> vào build-workflow"', title="Nguyên liệu dựng workflow AI", level="root", rec={r: EXTRA for r in ROLES},
         stores="lý do, các bước dự kiến, plan để dựng workflow nhiều bước (chuỗi skill)",
         tree=[('build-workflow/<tên-workflow>/', 'dựng workflow: README.md + plan.md')]),
    dict(id="reports", usage='"lưu báo cáo tháng 10 vào reports" (số liệu kinh doanh → `_local/`)', title="Báo cáo định kỳ", level="root", rec={r: EXTRA for r in ROLES},
         stores="báo cáo sprint / tháng (.md)",
         tree=[('reports/<loại>/<yy-mm-dd>-<loại>.md', 'báo cáo, 1 kỳ = 1 file')]),
]
MOD = {m["id"]: m for m in MODULES}
HOOK_FILES = ["scan.sh", "pre-commit", "pre-push"]


def run(cmd, cwd=None, check=False):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode:
        sys.exit(f"Lệnh lỗi: {' '.join(cmd)}\n{p.stderr.strip()}")
    return p


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def default_modules(role):
    return [m["id"] for m in MODULES if m.get("required") or m["rec"].get(role) == CORE]


def parse_modules(arg, role):
    ids = default_modules(role) if not arg else [x.strip() for x in arg.split(",") if x.strip()]
    bad = [i for i in ids if i not in MOD]
    if bad:
        sys.exit(f"Loại không có: {', '.join(bad)}. Xem: journal_setup.py modules")
    if "tasks" not in ids:
        ids.insert(0, "tasks")
    return [m["id"] for m in MODULES if m["id"] in ids]   # giữ thứ tự catalog


def enabled_in(claude_md):
    return re.findall(r"<!-- module:([a-z-]+) -->", claude_md) if claude_md else []


TASK_DIR = "apps/<app>/[<mã-task>]-<brief>/"
# Thứ tự trong một folder: file trước (theo vòng đời task), folder sau; tên không có ở đây giữ thứ tự khai báo.
FILE_ORDER = ["CLAUDE.md", "README.md", "app-profile.md", "plan-overview.md", "plan-implementation.md",
              "database-structure-design.md", "implement-retro.md", "golive.md", "retro.md", "acceptance-tests.md",
              "test-data.md", "open-questions.md", "changelog.md"]
DIR_ORDER = [".githooks/", "apps/", "requirement/", "meetings/", "context/", "research/", "diagnosis/", "solutions/",
             "decisions/", "explanations/", "review-code/", "scripts/", "ui-prototype/", "tests/", "runs/", "runbooks/",
             "feedback/", "daily-work/", "learning/", "build-skills/", "build-workflow/", "reports/", "_local/"]


def render_tree(ids, repo_name):
    """Cây kiểu `tree`: ├── └── │, file trước folder, folder không comment + 1 con gộp 1 dòng. Trả (cây, legend)."""
    entries = [("CLAUDE.md", "quy ước lưu, Claude đọc file này"), ("README.md", "cây folder + cách dùng"),
               (".githooks/", "chặn secret trước commit / push")]
    entries += [(path.replace("TASK/", TASK_DIR), cmt) for i in ids for path, cmt in MOD[i]["tree"]]
    entries.append(("_local/", "nhạy cảm cấp repo, không lên git"))
    root = {}
    for path, cmt in entries:                      # dựng cây lồng: tên → [comment, con, thứ tự khai báo]
        parts = re.findall(r"[^/]+/?", path)
        node = root
        for k, part in enumerate(parts):
            item = node.setdefault(part, ["", {}, len(node)])
            if k == len(parts) - 1 and cmt:
                item[0] = cmt
            node = item[1]

    def key(name, seq):
        is_dir = name.endswith("/")
        order = DIR_ORDER if is_dir else FILE_ORDER
        return (is_dir, order.index(name) if name in order else len(order), seq)

    lines, legend = [f"{repo_name}/"], []   # legend: (key folder cha, nhãn folder cha, tên, comment)
    def walk(node, prefix, parent, label):
        kids = sorted(node.items(), key=lambda kv: key(kv[0], kv[1][2]))
        for idx, (name, (cmt, sub, _)) in enumerate(kids):
            while not cmt and len(sub) == 1:        # apps/ + <app>/ → apps/<app>/
                (child, (cmt, sub, _)), = sub.items()
                name += child
            last = idx == len(kids) - 1
            lines.append(f"{prefix}{'└── ' if last else '├── '}{name}")
            if cmt:
                legend.append((parent, label, name, cmt))
            if sub:
                walk(sub, prefix + ("    " if last else "│   "), parent + name, name)
    walk(root, "", "", "")
    return "\n".join(lines), legend


def render_tree_md(ids, repo_name):
    """Cây chỉ có tên (hẹp, không vỡ khi khung xem hẹp) + bảng 'để làm gì' chia nhóm theo folder cha."""
    tree, legend = render_tree(ids, repo_name)
    groups = {}                                    # gom theo folder cha, giữ thứ tự xuất hiện đầu tiên
    for key_, label, name, cmt in legend:
        groups.setdefault(key_, (label, []))[1].append((name, cmt))
    rows = ["| Tên | Để làm gì |", "|---|---|"]
    for label, items in groups.values():
        rows.append(f"| **trong `{label}`** | |" if label else "| **Gốc journal** | |")
        rows += [f"| `{n}` | {c} |" for n, c in items]
    return "```\n" + tree + "\n```\n\n" + "\n".join(rows)


def module_block(i):
    body = (TPL / "claude-modules" / f"{i}.md").read_text().strip()
    return f"<!-- module:{i} -->\n{body}\n<!-- /module:{i} -->"


def render_claude(ids, owner, role):
    t = (TPL / "CLAUDE.md.tmpl").read_text()
    return (t.replace("{{OWNER}}", owner).replace("{{ROLE_LABEL}}", ROLE_LABEL[role])
             .replace("{{MODULE_BLOCKS}}", "\n\n".join(module_block(i) for i in ids) + "\n"))


def benefits_table(role, ids=None):
    """Dòng mở bằng `[<module>]` chỉ giữ khi module đó bật (ids=None: giữ hết, để giải thích lúc chưa chọn)."""
    rows = []
    for line in (TPL / "benefits" / f"{role}.md").read_text().strip().split("\n"):
        m = re.match(r"\| \[([a-z-]+)\] ", line)
        if m:
            if ids is not None and m.group(1) not in ids:
                continue
            line = line.replace(f"[{m.group(1)}] ", "", 1)
        rows.append(line)
    return "\n".join(rows)


def usage_lines(ids):
    """Câu dùng hằng ngày theo đúng các loại đã bật + câu đẩy journal lên GitHub."""
    lines = [f"- {MOD[i]['usage']}" for i in ids if MOD[i].get("usage")]
    lines.append('- "commit và push journal" — lưu chỉ ghi file trên máy; lên GitHub khi bạn bảo commit + push '
                 '(vd cuối ngày). Chưa nối GitHub → nói trước "nối journal lên GitHub"')
    return "\n".join(lines)


def render_readme(ids, owner, role, repo_name):
    t = (TPL / "README.md.tmpl").read_text()
    return (t.replace("{{REPO_NAME}}", repo_name).replace("{{OWNER}}", owner)
             .replace("{{ROLE_LABEL}}", ROLE_LABEL[role])
             .replace("{{BENEFITS}}", benefits_table(role, ids))
             .replace("{{USAGE}}", usage_lines(ids))
             .replace("{{TREE}}", render_tree_md(ids, repo_name)))


def gitignore_lines():
    return (TPL / "gitignore.tmpl").read_text().rstrip("\n").split("\n")


# Luật ignore phải có ở mọi journal — doctor kiểm, thiếu thì báo.
MUST_IGNORE = ["_local/", ".env", "*.pem", "*.key", "**/tests/runs/*/evidence/", "**/tests/feedback/*/", "**/tests/**/*.png"]


def owner_default(path):
    n = run(["git", "config", "user.name"], cwd=path if path.exists() else None).stdout.strip()
    return n or "<tên bạn>"


def compute_actions(path, ids, owner, role):
    """Trả về list (file, action, content|None). action: create · merge · skip · differs."""
    repo = path.name
    acts = []
    cm = path / "CLAUDE.md"
    if not cm.exists():
        acts.append(("CLAUDE.md", "create", render_claude(ids, owner, role)))
    else:
        old = cm.read_text()
        have = enabled_in(old)
        add = [i for i in ids if i not in have]
        new = old
        if "<!-- core:start -->" not in new:   # CLAUDE.md người dùng tự viết: nối luật lõi ở cuối, không đụng phần cũ
            tpl = render_claude([], owner, role)
            core = tpl[tpl.index("<!-- core:start -->"):tpl.index("<!-- core:end -->") + len("<!-- core:end -->")]
            new = new.rstrip("\n") + "\n\n" + core + "\n"
        if add:
            blocks = "\n\n".join(module_block(i) for i in add)
            if "<!-- modules:end -->" in new:
                new = new.replace("<!-- modules:end -->", blocks + "\n\n<!-- modules:end -->", 1).replace("\n\n\n<!-- modules:end", "\n\n<!-- modules:end")
            else:
                new = new.rstrip("\n") + f"\n\n## Các loại lưu trữ đang bật\n\n<!-- modules:start -->\n{blocks}\n\n<!-- modules:end -->\n"
        acts.append(("CLAUDE.md", "skip", None) if new == old else ("CLAUDE.md", "merge", new))
        ids = [m["id"] for m in MODULES if m["id"] in set(have) | set(ids)]
    rd = path / "README.md"
    if not rd.exists():
        acts.append(("README.md", "create", render_readme(ids, owner, role, repo)))
    else:
        old = rd.read_text()
        m = re.search(r"<!-- tree:start -->\n.*?\n<!-- tree:end -->", old, re.S)
        if m:
            new = old[:m.start()] + f"<!-- tree:start -->\n{render_tree_md(ids, repo)}\n<!-- tree:end -->" + old[m.end():]
            acts.append(("README.md", "skip" if new == old else "merge", None if new == old else new))
        else:
            acts.append(("README.md", "skip", None))
    for fname, lines in ((".gitignore", gitignore_lines()),
                         (".gitattributes", (TPL / "gitattributes.tmpl").read_text().rstrip("\n").split("\n"))):
        f = path / fname
        if not f.exists():
            acts.append((fname, "create", "\n".join(lines) + "\n"))
        else:
            old = f.read_text()
            have = set(old.split("\n"))
            miss = [l for l in lines if l and not l.startswith("#") and l not in have]
            acts.append((fname, "merge", old.rstrip("\n") + "\n" + "\n".join(miss) + "\n") if miss else (fname, "skip", None))
    for h in HOOK_FILES:
        src = (TPL / "githooks" / h).read_text()
        f = path / ".githooks" / h
        if not f.exists():
            acts.append((f".githooks/{h}", "create", src))
        else:
            acts.append((f".githooks/{h}", "skip" if f.read_text() == src else "differs", None))
    return acts, ids


# ── lệnh ────────────────────────────────────────────────────────────────────

def cmd_detect(a):
    def ver(cmd):
        if not shutil.which(cmd[0]):
            return None
        p = run(cmd)
        m = re.search(r"\d+\.\d+(\.\d+)?", p.stdout + p.stderr)
        return m.group(0) if m else "?"
    scanner = "betterleaks" if shutil.which("betterleaks") else None
    gh_auth = run(["gh", "auth", "status"]).returncode == 0 if shutil.which("gh") else False
    res = dict(os=platform.system(), git=ver(["git", "--version"]), gh=ver(["gh", "--version"]), gh_logged_in=gh_auth,
               uv=ver(["uv", "--version"]), scanner=scanner, scanner_version=ver([scanner, "version"]) if scanner else None,
               git_user_name=run(["git", "config", "--global", "user.name"]).stdout.strip() or None,
               git_user_email_set=bool(run(["git", "config", "--global", "user.email"]).stdout.strip()),
               global_hooks_path=run(["git", "config", "--global", "core.hooksPath"]).stdout.strip() or None)
    if a.path:
        p = Path(a.path).expanduser()
        cm = p / "CLAUDE.md"
        res.update(path=str(p), path_exists=p.exists(), is_git_repo=(p / ".git").exists(),
                   claude_md=cm.exists(), enabled_modules=enabled_in(cm.read_text()) if cm.exists() else [])
    out(res)


def cmd_modules(a):
    """Có --role: 3 nhóm (khuyên dùng · có thể thêm · loại khác). Không --role: bảng gợi ý cho cả 3 vai trò."""
    if not a.role:
        print("| id | Loại | Lưu gì | " + " | ".join(ROLE_LABEL.values()) + " |")
        print("|---|---|---|" + "---|" * len(ROLES))
        mark = {CORE: "✅", EXTRA: "➕"}
        for m in MODULES:
            cells = ["bắt buộc" if m.get("required") else mark.get(m["rec"].get(r), "") for r in ROLES]
            print(f"| `{m['id']}` | {m['title']} | {m['stores']} | " + " | ".join(cells) + " |")
        print("\n✅ khuyên dùng (tick sẵn) · ➕ có thể thêm")
        return
    groups = [("Khuyên dùng cho " + ROLE_LABEL[a.role] + " (tick sẵn)",
               [m for m in MODULES if m.get("required") or m["rec"].get(a.role) == CORE]),
              ("Có thể thêm", [m for m in MODULES if not m.get("required") and m["rec"].get(a.role) == EXTRA]),
              ("Loại khác", [m for m in MODULES if not m.get("required") and a.role not in m["rec"]])]
    for title, ms in groups:
        if not ms:
            continue
        print(f"**{title}**\n\n| id | Loại | Lưu gì |\n|---|---|---|")
        for m in ms:
            req = " (bắt buộc)" if m.get("required") else ""
            print(f"| `{m['id']}` | {m['title']}{req} | {m['stores']} |")
        print()


def cmd_benefits(a):
    print(benefits_table(a.role))


def cmd_plan(a):
    path = Path(a.path).expanduser()
    ids = parse_modules(a.modules, a.role)
    owner = a.owner or owner_default(path)
    acts, all_ids = compute_actions(path, ids, owner, a.role)
    if a.connect == "A" and not (path / COMPANION / "SKILL.md").exists():
        acts.append((f"{COMPANION}/SKILL.md", "create", None))
    label = {"create": "tạo mới", "merge": "gộp thêm (giữ phần cũ)", "skip": "giữ nguyên", "differs": "khác bản chuẩn — cần xem diff"}
    print(f"**Journal:** `{path}` · vai trò {ROLE_LABEL[a.role]} · chủ {owner}\n")
    print("**Cây folder:**\n\n" + render_tree_md(all_ids, path.name) + "\n")
    print("**File:**\n\n| File | Việc |\n|---|---|")
    for f, act, _ in acts:
        print(f"| `{f}` | {label[act]} |")
    print("\n**Các bước sắp chạy:**\n\n| Bước | Việc | Ở đâu | Cần bạn |\n|---|---|---|---|")
    step5, step8 = {
        "A": ("bật hook chặn secret, tự test bằng secret giả; sinh skill journal-save trong journal",
              "link journal-save vào ~/.claude/skills (dùng được ở mọi repo)"),
        "B": ("bật hook chặn secret, tự test bằng secret giả",
              "thêm khối trỏ journal vào ~/.claude/CLAUDE.md"),
        "none": ("bật hook chặn secret, tự test bằng secret giả", None),
    }[a.connect]
    ask5 = {"own": "tự chạy 2 lệnh git config (tên + email ký commit), báo lại",
            "shared": "cho email công ty nếu chưa nói"}.get(a.git_identity, "—")
    if a.git_identity == "shared":
        step5 += "; đặt tên + email ký commit riêng cho journal"
    elif a.git_identity == "own":
        step5 += "; đổi tên + email ký commit của máy"
    for n, what, where, ask in STEPS_PREVIEW:
        what = {"5": step5, "8": step8}.get(n, what)
        ask = ask5 if n == "5" else ask
        if what:
            print(f"| {n} | {what} | {where} | {ask} |")


# Bước sau xem trước — "oke" ở bước xem trước tính cho các dòng "trên máy"; dòng khác hỏi lại lúc tới bước.
STEPS_PREVIEW = [
    ("4", "tạo các file ở bảng trên", "trên máy", "—"),
    ("5", "", "trên máy", "—"),
    ("6", "commit đầu (chụp lại mốc đầu tiên của journal)", "trên máy", "—"),
    ("7", "tạo repo GitHub **private** + push", "**ra ngoài máy**", "hỏi lại trước khi chạy"),
    ("8", "", "cấu hình Claude cá nhân", "cho xem nội dung, hỏi lại"),
]


def cmd_apply(a):
    path = Path(a.path).expanduser()
    ids = parse_modules(a.modules, a.role)
    owner = a.owner or owner_default(path)
    acts, all_ids = compute_actions(path, ids, owner, a.role)
    done = {"create": [], "merge": [], "skip": [], "differs": []}
    for f, act, content in acts:
        done[act].append(f)
        if a.dry_run or content is None:
            continue
        target = path / f
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        if f.startswith(".githooks/"):
            target.chmod(0o755)
    out(dict(path=str(path), dry_run=a.dry_run, modules=all_ids, **done))


def cmd_hooks(a):
    path = Path(a.path).expanduser()
    if not (path / ".git").exists():
        run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    for h in HOOK_FILES:
        f = path / ".githooks" / h
        if not f.exists():
            sys.exit(f"Thiếu {f} — chạy apply trước.")
        f.chmod(0o755)
    run(["git", "config", "core.hooksPath", ".githooks"], cwd=path, check=True)
    glob = run(["git", "config", "--global", "core.hooksPath"]).stdout.strip() or None
    out(dict(path=str(path), hooks_path=run(["git", "config", "core.hooksPath"], cwd=path).stdout.strip(),
             global_hooks_path=glob, note="repo set core.hooksPath riêng nên đè được giá trị global" if glob else None))


def fake_token():
    return "ghp_" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(36))


def cmd_selftest(a):
    path = Path(a.path).expanduser()
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        shutil.copytree(path / ".githooks", t / ".githooks")
        run(["git", "init", "-q", "-b", "main"], cwd=t, check=True)
        run(["git", "config", "core.hooksPath", ".githooks"], cwd=t, check=True)
        ident = ["-c", "user.name=selftest", "-c", "user.email=selftest@example.com"]
        (t / "note.md").write_text(f"token: {fake_token()}\n")       # secret giả sinh lúc chạy, không in ra
        run(["git", "add", "note.md"], cwd=t)
        dirty = run(["git", *ident, "commit", "-qm", "selftest dirty"], cwd=t)
        run(["git", "rm", "-q", "--cached", "note.md"], cwd=t)
        (t / "note.md").write_text("ghi chú bình thường\n")
        run(["git", "add", "note.md"], cwd=t)
        clean = run(["git", *ident, "commit", "-qm", "selftest clean"], cwd=t)
        scanner = run(["sh", "-c", ". .githooks/scan.sh; detect_scanner; echo $SCANNER"], cwd=t).stdout.strip()
    ok = dirty.returncode != 0 and clean.returncode == 0
    out(dict(passed=ok, scanner=scanner, secret_blocked=dirty.returncode != 0, clean_commit_passed=clean.returncode == 0,
             hint=None if ok else "Hook không chặn được secret giả hoặc chặn nhầm commit sạch — xem .githooks/scan.sh"))


def cmd_remote_check(a):
    path = Path(a.path).expanduser()
    url = run(["git", "remote", "get-url", "origin"], cwd=path).stdout.strip()
    if not url:
        return out(dict(remote=None, visibility=None))
    if not shutil.which("gh"):
        return out(dict(remote=url, visibility="unknown", hint="cài gh hoặc mở trang repo để kiểm Private"))
    p = run(["gh", "repo", "view", "--json", "visibility", "-q", ".visibility"], cwd=path)
    out(dict(remote=url, visibility=p.stdout.strip() or "unknown", error=p.stderr.strip()[:200] or None))


COMPANION = Path(".claude") / "skills" / "journal-save"


def cmd_companion(a):
    path = Path(a.path).expanduser()
    owner = a.owner or owner_default(path)
    src = (TPL / "companion-skill" / "SKILL.md.tmpl").read_text().replace("{{OWNER}}", owner)
    f = path / COMPANION / "SKILL.md"
    if f.exists():
        return out(dict(file=str(f), action="skip" if f.read_text() == src else "differs"))
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(src)
    staged = (path / ".git").exists() and run(["git", "add", str(f)], cwd=path).returncode == 0   # track để clone sang máy khác vẫn có
    out(dict(file=str(f), action="create", staged=staged))


def cmd_link_companion(a):
    target = (Path(a.path).expanduser() / COMPANION).resolve()
    if not (target / "SKILL.md").exists():
        sys.exit("Chưa có skill đi kèm — chạy companion trước.")
    link = Path.home() / ".claude" / "skills" / "journal-save"
    if link.is_symlink() or link.exists():
        same = link.resolve() == target
        return out(dict(link=str(link), action="skip" if same else "conflict", points_to=str(link.resolve()),
                        hint=None if same else "đã có skill tên journal-save khác — hỏi user, không đè"))
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:   # Windows không có quyền symlink → junction không cần admin
        p = run(["cmd", "/c", "mklink", "/J", str(link), str(target)])
        if p.returncode:
            sys.exit(f"Không tạo được link: {p.stderr.strip()}")
    out(dict(link=str(link), action="create", points_to=str(target), note="mở session Claude mới để skill có hiệu lực"))


def cmd_doctor(a):
    path = Path(a.path).expanduser()
    rows = []
    def row(ok, what, fix=""):
        rows.append(("✅" if ok else "⚠️", what, "" if ok else fix))
    row((path / ".git").exists(), "Là git repo", f"`uv run {SCRIPT} hooks --path {path}`")
    hp = run(["git", "config", "core.hooksPath"], cwd=path).stdout.strip() if path.exists() else ""
    row(hp == ".githooks", f"core.hooksPath = `{hp or 'chưa đặt'}`", "`git config core.hooksPath .githooks`")
    row(all((path / ".githooks" / h).exists() for h in HOOK_FILES), "Đủ hook (scan.sh, pre-commit, pre-push)", "chạy chế độ Thêm loại / apply để bù")
    sc = "betterleaks" if shutil.which("betterleaks") else None
    row(sc is not None, f"Scanner: {sc or 'chưa cài — đang quét bằng pattern'}", "cài betterleaks (xem SKILL.md, bảng cài theo OS)")
    if (path / ".githooks" / "scan.sh").exists():
        p = run([sys.executable, __file__, "selftest", "--path", str(path)])
        st = json.loads(p.stdout) if p.returncode == 0 else {"passed": False}
        row(st.get("passed"), "Tự test: secret giả bị chặn, commit sạch đi qua", "xem `.githooks/scan.sh`")
    gi = (path / ".gitignore").read_text().split("\n") if (path / ".gitignore").exists() else []
    miss = [g for g in MUST_IGNORE if g not in gi]
    row(not miss, "`.gitignore` đủ luật chặn (_local/, file secret, evidence, file đính kèm feedback, ảnh trong tests/)",
        "thiếu " + ", ".join(f"`{g}`" for g in miss) + " → chạy chế độ Thêm loại / apply để bù")
    url = run(["git", "remote", "get-url", "origin"], cwd=path).stdout.strip() if path.exists() else ""
    if url:
        vis = run(["gh", "repo", "view", "--json", "visibility", "-q", ".visibility"], cwd=path).stdout.strip() if shutil.which("gh") else "unknown"
        row(vis == "PRIVATE", f"Remote visibility: {vis or 'unknown'}", "đổi repo sang Private ngay (Settings → General → Danger Zone)")
    else:
        rows.append(("—", "Chưa có remote", ""))
    if (path / COMPANION / "SKILL.md").exists():
        link = Path.home() / ".claude" / "skills" / "journal-save"
        ok = link.exists() and link.resolve() == (path / COMPANION).resolve()
        row(ok, "Skill journal-save đã link vào ~/.claude/skills", f"`uv run {SCRIPT} link-companion --path {path}`")
    print("| | Kiểm | Cách sửa |\n|---|---|---|")
    for r in rows:
        print(f"| {r[0]} | {r[1]} | {r[2]} |")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("detect"); sp.add_argument("--path")
    sp = sub.add_parser("modules"); sp.add_argument("--role", choices=ROLES)
    sp = sub.add_parser("benefits"); sp.add_argument("--role", choices=ROLES, required=True)
    for name in ("plan", "apply"):
        sp = sub.add_parser(name)
        sp.add_argument("--path", required=True); sp.add_argument("--role", choices=ROLES, required=True)
        sp.add_argument("--modules", help="id phẩy, bỏ trống = tick sẵn theo vai trò"); sp.add_argument("--owner")
        if name == "apply":
            sp.add_argument("--dry-run", action="store_true")
        else:
            sp.add_argument("--connect", choices=["A", "B", "none"], default="A",
                            help="nối với Claude: A = skill journal-save · B = khối trỏ ~/.claude/CLAUDE.md · none")
            sp.add_argument("--git-identity", choices=["keep", "own", "shared"], default="keep",
                            help="tên ký commit: keep = giữ git config hiện tại · own = máy riêng, user đổi global · "
                                 "shared = máy dùng chung, đặt riêng cho journal")
    for name in ("hooks", "selftest", "remote-check", "doctor", "link-companion"):
        sub.add_parser(name).add_argument("--path", required=True)
    sp = sub.add_parser("companion"); sp.add_argument("--path", required=True); sp.add_argument("--owner")
    a = ap.parse_args()
    {"detect": cmd_detect, "modules": cmd_modules, "benefits": cmd_benefits, "plan": cmd_plan, "apply": cmd_apply,
     "hooks": cmd_hooks, "selftest": cmd_selftest, "remote-check": cmd_remote_check, "doctor": cmd_doctor,
     "companion": cmd_companion, "link-companion": cmd_link_companion}[a.cmd](a)


if __name__ == "__main__":
    main()
