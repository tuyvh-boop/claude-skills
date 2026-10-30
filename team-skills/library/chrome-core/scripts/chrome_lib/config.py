"""Cấu hình máy + rào origin + nhận diện trang login.

Giá trị máy nằm ở `config.yml` cạnh SKILL.md (gitignored). Thiếu file thì chạy với mặc định: chỉ cho phép loopback.
"""
from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

import yaml

SKILL_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = SKILL_DIR / "config.yml"
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "[::1]"}
CHROME_CANDIDATES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]


@dataclass
class Site:
    name: str
    allowed_origins: list[str] = field(default_factory=list)
    login_url: str = ""
    login_markers: list[str] = field(default_factory=list)


@dataclass
class Config:
    port: int = 9222
    state_dir: Path = Path.home() / ".cache" / "chrome-core"
    profile_dir: Path = Path.home() / ".cache" / "chrome-core" / "chrome-profile"
    chrome_bin: str = ""
    owner_ttl_hours: float = 8
    max_parallel_runs: int = 2
    headless: bool = True
    sites: dict[str, Site] = field(default_factory=dict)

    @property
    def endpoint(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def chrome(self) -> str:
        if self.chrome_bin:
            return self.chrome_bin
        for name in CHROME_CANDIDATES:
            if shutil.which(name):
                return name
        raise SystemExit("Không tìm thấy Chrome / Chromium trên máy — khai `chrome_bin` trong config.yml.")

    def site_of(self, url: str) -> Site | None:
        for site in self.sites.values():
            if any(url.startswith(o) for o in site.allowed_origins):
                return site
        return None

    def url_allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        if parts.scheme in ("about", "data", "chrome", "blob"):
            return True
        if parts.hostname in {h.strip("[]") for h in LOOPBACK_HOSTS}:
            return True
        return self.site_of(url) is not None

    def is_login_page(self, url: str) -> bool:
        return any(m in url for site in self.sites.values() for m in site.login_markers)


def _expand(p: str) -> Path:
    return Path(os.path.expanduser(p))


def load(path: Path = CONFIG_PATH) -> Config:
    cfg = Config()
    if not path.exists():
        return cfg
    raw = yaml.safe_load(path.read_text()) or {}
    cfg.port = int(raw.get("port", cfg.port))
    if raw.get("state_dir"):
        cfg.state_dir = _expand(raw["state_dir"])
    cfg.profile_dir = _expand(raw["profile_dir"]) if raw.get("profile_dir") else cfg.state_dir / "chrome-profile"
    cfg.chrome_bin = raw.get("chrome_bin") or ""
    cfg.owner_ttl_hours = float(raw.get("owner_ttl_hours", cfg.owner_ttl_hours))
    cfg.max_parallel_runs = int(raw.get("max_parallel_runs", cfg.max_parallel_runs))
    cfg.headless = bool(raw.get("headless", cfg.headless))
    for name, s in (raw.get("sites") or {}).items():
        s = s or {}
        cfg.sites[name] = Site(
            name=name,
            allowed_origins=list(s.get("allowed_origins") or []),
            login_url=s.get("login_url") or "",
            login_markers=list(s.get("login_markers") or []),
        )
    return cfg


def save_site(site: Site, path: Path = CONFIG_PATH) -> None:
    raw = yaml.safe_load(path.read_text()) if path.exists() else {}
    raw = raw or {}
    raw.setdefault("sites", {})[site.name] = {
        "allowed_origins": site.allowed_origins,
        "login_url": site.login_url,
        "login_markers": site.login_markers,
    }
    path.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False))


SECRET_PARAM = re.compile(r"(?i)\b(id_token|session|hmac|access_token|token)=[^&\s\"'#]+")


def scrub(text: str) -> str:
    """Che giá trị tham số mang token trong chuỗi bất kỳ (URL iframe app do steps tự in / tự `check`, lỗi Playwright)."""
    return SECRET_PARAM.sub(lambda m: f"{m.group(1)}=***", text)


def safe_url(url: str) -> str:
    """URL bỏ query + fragment: iframe app hay mang token (`id_token`, `hmac`, `session`) trong query."""
    parts = urlsplit(url)
    if not parts.scheme:
        return url
    return f"{parts.scheme}://{parts.netloc}{parts.path}"
