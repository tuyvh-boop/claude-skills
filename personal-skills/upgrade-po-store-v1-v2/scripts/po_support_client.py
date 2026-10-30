# /// script
# requires-python = ">=3.9"
# dependencies = ["requests", "pyyaml"]
# ///
"""
po_support_client.py — helper + CLI để đọc/ghi Support Function của OPTIS Product Options
(bảng `fix_bug_for_stores`, endpoint `/support/get-shop-support` và `/support/update-shop-support-content`
của repo `api`).

QUAN TRỌNG VỀ AUTH: hai endpoint trên hiện là `@Public()` và KHÔNG có guard nào khác trong code
(`support.controller.ts`) — không cần token. Điều đó cũng có nghĩa: gọi đúng domain + đúng
`api_base_url` production là ghi THẬT vào storefront của một cửa hàng thật, lên live NGAY (xem
`SupportService.publishSupportContent` — viết DB rồi push metafield Shopify luôn, không có bước
duyệt). Vì vậy:
  - `get-support` (đọc) chạy thẳng, an toàn.
  - `update-support` (ghi) MẶC ĐỊNH DRY-RUN (chỉ in payload sẽ gửi) — chỉ ghi thật khi thêm `--commit`.
  - KHÔNG BAO GIỜ tự thêm `--commit` thay cho user. Luôn in rõ domain + runtimeVersion + độ dài
    content trước khi hỏi user xác nhận.

Việc BẬT/TẮT runtime v1/v2 của shop (`PATCH /admin/shops/storefront-runtime-version`) KHÔNG nằm
trong script này — endpoint đó cần `ADMIN_API_TOKEN` (bearer) mà skill này không quản lý, và việc
đọc trạng thái hiện tại cần ký HMAC forward (secret riêng của CRM). Dùng CRM/OSSA UI cho bước đó.

Cấu hình: `config.yml` cạnh script (GITIGNORED) — copy từ `config.example.yml`, điền `api_base_url`
và `author`.

Chạy: uv run scripts/po_support_client.py <command> [options]
"""
import argparse
import sys
from pathlib import Path

import requests
import yaml

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
CONFIG_PATH = SKILL_DIR / "config.yml"


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def load_config():
    if not CONFIG_PATH.exists():
        die(f"Thiếu {CONFIG_PATH}. Copy từ config.example.yml rồi điền api_base_url + author.")
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    base_url = (cfg.get("api_base_url") or "").strip()
    if not base_url or base_url == "<fill-in>":
        die("config.yml thiếu api_base_url hợp lệ.")
    return cfg, base_url.rstrip("/")


def cmd_get_support(args):
    _, base_url = load_config()
    resp = requests.get(
        f"{base_url}/support/get-shop-support",
        params={"domain": args.domain, "runtimeVersion": args.runtime_version},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        print("Chưa có support content cho shop/runtimeVersion này.")
        return
    content = data["data"]["content"]
    if args.out:
        Path(args.out).write_text(content, encoding="utf-8")
        print(f"Đã ghi {len(content)} ký tự vào {args.out}")
    else:
        print(content)


def cmd_update_support(args):
    cfg, base_url = load_config()
    author = cfg.get("author") or ""
    if not author or author == "<your name>":
        die("config.yml thiếu author hợp lệ (tên người thực hiện thay đổi).")

    content = Path(args.file).read_text(encoding="utf-8")

    payload = {
        "domain": args.domain,
        "content": content,
        "user": author,
        "runtimeVersion": args.runtime_version,
    }

    print("=== PAYLOAD SẼ GỬI (update-shop-support-content) ===")
    print(f"  endpoint        : POST {base_url}/support/update-shop-support-content")
    print(f"  domain          : {payload['domain']}")
    print(f"  runtimeVersion  : {payload['runtimeVersion']}")
    print(f"  user            : {payload['user']}")
    print(f"  content length  : {len(content)} ký tự (từ {args.file})")

    if not args.commit:
        print("\nDRY-RUN — không gửi gì. Thêm --commit để ghi thật (publish ngay lên storefront).")
        return

    print("\n>>> ĐANG GHI THẬT — nội dung này sẽ publish lên metafield Shopify của store ngay lập tức.")
    resp = requests.post(f"{base_url}/support/update-shop-support-content", json=payload, timeout=20)
    resp.raise_for_status()
    result = resp.json()
    print(result.get("message", result))


def main():
    parser = argparse.ArgumentParser(description="OPTIS Product Options support-function client")
    sub = parser.add_subparsers(dest="command", required=True)

    get_p = sub.add_parser("get-support", help="Đọc support content hiện có của 1 shop (read-only)")
    get_p.add_argument("--domain", required=True)
    get_p.add_argument("--runtime-version", default="v1", choices=["v1", "v2"])
    get_p.add_argument("--out", help="Lưu content ra file thay vì in ra stdout")
    get_p.set_defaults(func=cmd_get_support)

    upd_p = sub.add_parser("update-support", help="Ghi support content cho 1 shop (mặc định dry-run)")
    upd_p.add_argument("--domain", required=True)
    upd_p.add_argument("--runtime-version", default="v2", choices=["v1", "v2"])
    upd_p.add_argument("--file", required=True, help="File chứa nội dung JS sẽ publish")
    upd_p.add_argument("--commit", action="store_true", help="Ghi thật (mặc định chỉ dry-run)")
    upd_p.set_defaults(func=cmd_update_support)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
