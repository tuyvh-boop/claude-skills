---
name: google-sheet-skills-report
description: Use when filling a skills inventory report in Google Sheets — detects active vs orphaned skills using git history, CLAUDE.md references, and metadata signals.
metadata:
  trigger: "user says 'skills report', 'fill skills sheet', 'inventory report' — wants automated skill status detection for team visibility"
  model_hint: "main loop (Sonnet/Opus) — metadata inference needs judgment across multiple signals"
  keywords: ["skills", "inventory", "report", "status", "active", "deprecated", "maintenance"]
---

# Google Sheet Skills Report

Skill để **tạo skills inventory report** — detect active vs orphaned, infer status từ git + CLAUDE.md, layout transparent & scannable.

## Nguyên tắc

- **Multi-signal verify**: không dựa 1 signal (like file age alone)
- **Transparent status**: show confidence level, logic đằng sau
- **Scan before report**: liệt kê tất cả `.claude/skills/`, cross-check CLAUDE.md
- **Audience-specific**: engineer scan status, PM spot red flags, docs browse tier

## Bước 1 — Scan & Multi-Signal Verify

**Tìm tất cả skills:**

```bash
find ~/.claude/skills -name "SKILL.md" -type f
# hay
ls ~/.claude/skills/*/SKILL.md
```

**Cho mỗi skill, collect signals:**

| Signal | Cách lấy |
|--------|----------|
| **Git commit history** | `git log -1 --format=%ai <skill-dir>` |
| **Commit count (90d)** | `git log --since="90 days ago" --oneline <skill-dir> \| wc -l` |
| **CLAUDE.md reference** | `grep -r "skill-name" ~/.claude/CLAUDE.md` |
| **Symlink status** | `ls -l ~/.claude/skills/skill-name` → symlink? direct? |
| **File modification** | `stat -c %y <SKILL.md>` |
| **Content signals** | grep "DEPRECATED\|TODO\|legacy" trong SKILL.md |
| **Infrastructure role** | khác skills có `import <this-skill>` không? |

## Bước 2 — Status Inference Hierarchy

**Priority (confidence descending):**

1. **Explicit "DEPRECATED" marker** → Legacy (100% confident)
   ```
   "DEPRECATED: Use google-sheet instead"
   ```

2. **Git commit within 30 days + in CLAUDE.md** → Active (high confidence)
   ```
   Last commit: 2026-09-27 (2 days ago)
   In CLAUDE.md: yes
   → Status: Active
   ```

3. **Mature design + referenced somewhere** → Stable (medium-high)
   ```
   Last commit: 2026-08-10 (50 days ago)
   In CLAUDE.md: no
   But: other skills import it
   → Status: Stable (infrastructure)
   ```

4. **Stale + no references** → Inactive (low-medium)
   ```
   Last commit: 2026-05-15 (135 days ago)
   In CLAUDE.md: no
   Other skills: no imports
   → Status: Inactive (candidate for removal)
   ```

5. **File age alone** → Ambiguous (don't use)
   - Stable skill = no edits for months = intentional, not abandoned
   - Can't distinguish from truly orphaned

**Confidence levels:**
- 🟢 High: git recent + endorsed + infrastructure use
- 🟡 Medium: file recent OR referenced OR has content
- 🔴 Low: ancient + no references + stub content

## Bước 3 — Report Structure

**Columns (essential):**

| Skill Name | Tier | Status | Last Update | Description |
|---|---|---|---|---|
| execute-plan | Base | 🟢 Active | 2026-09-27 | Implement code grounded in every source |
| google-sheet-api | Tier 1 | 🟢 Active | 2026-09-29 | Google Sheets API without hardcoding |
| old-helper | Tier 2 | 🔴 Orphaned | 2026-05-15 | [Removed from use] |

**Formatting:**

- **Grouping**: Tier (Base → Tier 1 → Tier 2)
- **Status badges**: 🟢 Active | 🟡 Stable | 🔴 Inactive | ⚠️ Legacy
- **Hyperlink skill names** → source repo/GitHub
- **Frozen header** → scroll left/right dễ
- **Color row**: red status = attention needed

**Optional columns** (add nếu team cần):
- Last Modified (absolute date)
- Commit Count (90d)
- Dependency Count (bao nhiêu skills import)
- Owner/Maintainer

## Bước 4 — Audience-Specific Scannability

| Role | Scan | Format |
|---|---|---|
| **Engineer** | Status (green=safe) → Description | Status color badges, bold names, quick ref |
| **PM** | Red flags (inactive + base tier = urgent) | Sort by status, highlight reds |
| **Docs** | Skill → Description | Tier grouping, hide colors |

## Lỗi hay gặp

- **Rely on file age only**: "6 months old = abandoned." Nhưng stable skills không sửa. → Fix: dùng git + CLAUDE.md + content signals.
- **Vô minh detect orphan**: Skill không ở CLAUDE.md → assume defunct. Nhưng có thể infra-only. → Fix: check xem khác skills import không.
- **Không show confidence**: Report nói "Inactive" nhưng không rõ logic. → Fix: column "Signals" = "ancient git, no CLAUDE.md, no imports".
- **Hide stale signals**: Skill có "TODO" markers hay "experimental" = người dùng cần biết. → Fix: flagged trong Status, note ở Description.
- **Quên detect cross-project**: Skill A dùng ở project B, report A chỉ nhìn project A. → Fix: scan broader (all CLAUDE.md files, không chỉ project hiện tại).

**Xem thêm:** `references/skill-status-detection.md` cho methodology chi tiết.
