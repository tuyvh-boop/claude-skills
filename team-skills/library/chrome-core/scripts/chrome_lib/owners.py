"""Sổ đăng ký tab theo owner — để nhiều task / session dùng chung một Chrome mà không giành tab của nhau.

Tab nhận diện bằng `targetId` của CDP (cố định suốt đời tab), không bằng URL hay thứ tự: hai task mở cùng một trang thì
URL trùng, thứ tự tab đổi khi tab khác đóng / mở. File nằm ở state_dir (ngoài repo), khoá bằng `fcntl` vì nhiều process
ghi cùng lúc.
"""
from __future__ import annotations

import fcntl
import json
import time
from contextlib import contextmanager
from pathlib import Path


class Registry:
    def __init__(self, state_dir: Path):
        state_dir.mkdir(parents=True, exist_ok=True)
        self.path = state_dir / "owners.json"
        self.lock_path = state_dir / "owners.lock"

    @contextmanager
    def edit(self):
        with open(self.lock_path, "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            data = json.loads(self.path.read_text()) if self.path.exists() else {}
            yield data
            self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def read(self) -> dict:
        with open(self.lock_path, "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_SH)
            return json.loads(self.path.read_text()) if self.path.exists() else {}

    def touch(self, owner: str) -> dict:
        with self.edit() as data:
            entry = data.setdefault(owner, {"created": time.time(), "tabs": {}})
            entry["last_seen"] = time.time()
            return dict(entry)

    def add_tab(self, owner: str, target_id: str, opener: str | None = None, role: str = "tab") -> None:
        with self.edit() as data:
            entry = data.setdefault(owner, {"created": time.time(), "tabs": {}})
            entry["tabs"][target_id] = {"opener": opener, "role": role, "created": time.time()}
            entry["last_seen"] = time.time()

    def drop_tabs(self, owner: str, target_ids: list[str]) -> None:
        with self.edit() as data:
            entry = data.get(owner)
            if entry:
                for t in target_ids:
                    entry["tabs"].pop(t, None)

    def tabs_of(self, owner: str) -> dict:
        return self.read().get(owner, {}).get("tabs", {})

    def owner_of(self, target_id: str) -> str | None:
        for owner, entry in self.read().items():
            if target_id in entry.get("tabs", {}):
                return owner
        return None

    def remove_owner(self, owner: str) -> dict:
        with self.edit() as data:
            return data.pop(owner, {})

    def set_running(self, owner: str, running: bool) -> None:
        with self.edit() as data:
            entry = data.setdefault(owner, {"created": time.time(), "tabs": {}})
            if running:
                entry["running_since"] = time.time()
            else:
                entry.pop("running_since", None)

    def running_peers(self, owner: str, max_age_s: float = 1800) -> list[str]:
        """Owner khác CÙNG task (phần trước `@`) đang trong một `run` — cùng task thường đánh vào cùng một dev server."""
        task = owner.split("@", 1)[0]
        now = time.time()
        return sorted(o for o, e in self.read().items() if o != owner and o.split("@", 1)[0] == task
                      and now - e.get("running_since", 0) < max_age_s)

    def prune_dead_tabs(self, live_target_ids: set[str]) -> None:
        with self.edit() as data:
            for entry in data.values():
                for t in list(entry.get("tabs", {})):
                    if t not in live_target_ids:
                        entry["tabs"].pop(t)
