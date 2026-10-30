#!/usr/bin/env sh
# git-context.sh — gom mọi thông tin git READ-ONLY cần cho skill git-flow trong 1 lần chạy.
#
# Cross-platform: chỉ dùng POSIX sh + lệnh `git` (đã có sẵn ở mọi máy dùng git).
#   - Linux / macOS: chạy trực tiếp.
#   - Windows: chạy qua Git Bash (đi kèm Git for Windows) — KHÔNG cần cài thêm gì.
# Script KHÔNG bao giờ commit / push / thay đổi state — chỉ đọc và in ra.
#
# Cách dùng:
#   sh git-context.sh                 # context cho commit + push (mặc định)
#   sh git-context.sh mr [<base>]     # thêm context cho tạo MR/PR (log & diff base..HEAD)
#
# <base> mặc định = nhánh chính detect được (main/master). Đầu ra chia SECTION có nhãn
# rõ ràng để model đọc/parse; diff có thể lớn — bên gọi tự xử lý kích thước.

set -u

MODE="${1:-status}"
BASE_ARG="${2:-}"

# --- Đảm bảo đang trong git repo ---------------------------------------------
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: không phải git repo (chạy trong thư mục có .git)."
  exit 1
fi

# --- Detect nhánh chính (default branch) -------------------------------------
detect_default_branch() {
  ref=$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null)
  if [ -n "$ref" ]; then
    echo "${ref##*/}"
    return
  fi
  if git show-ref --verify --quiet refs/remotes/origin/main; then echo "main"; return; fi
  if git show-ref --verify --quiet refs/remotes/origin/master; then echo "master"; return; fi
  if git show-ref --verify --quiet refs/heads/main; then echo "main"; return; fi
  echo "master"
}

CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
DEFAULT_BRANCH=$(detect_default_branch)
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "(none)")

# ahead/behind so với upstream (nếu có)
if [ "$UPSTREAM" != "(none)" ]; then
  set -- $(git rev-list --left-right --count HEAD..."$UPSTREAM" 2>/dev/null || echo "0 0")
  AHEAD="${1:-0}"; BEHIND="${2:-0}"
else
  AHEAD="?"; BEHIND="?"
fi

REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "(no origin)")
case "$REMOTE_URL" in
  *github.com*) HOST="github" ;;
  *gitlab*)     HOST="gitlab" ;;
  *bitbucket*)  HOST="bitbucket" ;;
  *)            HOST="unknown" ;;
esac

# Platform CLI khả dụng
PLATFORM_CLI="none"
if command -v gh   >/dev/null 2>&1; then PLATFORM_CLI="gh"; fi
if command -v glab >/dev/null 2>&1; then
  if [ "$PLATFORM_CLI" = "gh" ]; then PLATFORM_CLI="gh+glab"; else PLATFORM_CLI="glab"; fi
fi

echo "=== BRANCH ==="
echo "current: ${CURRENT_BRANCH:-(detached HEAD)}"
echo "default: $DEFAULT_BRANCH"
echo "upstream: $UPSTREAM"
echo "ahead/behind vs upstream: $AHEAD/$BEHIND"
echo

echo "=== REMOTE ==="
echo "url: $REMOTE_URL"
echo "host: $HOST"
echo "platform_cli: $PLATFORM_CLI"
echo

echo "=== STATUS (short) ==="
git status --short
echo

echo "=== STAGED FILES ==="
git diff --cached --name-only
echo

echo "=== SECRET SCAN (heuristic — chỉ để CẢNH BÁO, cần người/subagent xác nhận) ==="
# Quét các dòng THÊM MỚI (^+) trong cả staged + unstaged diff cho pattern nhạy cảm.
SECRET_PATTERN='(api[_-]?key|secret|client[_-]?secret|token|passwd|password|BEGIN [A-Z ]*PRIVATE KEY|aws_access_key_id|authorization:[[:space:]]*bearer)'
HITS=$(git diff --cached; git diff) 2>/dev/null
FLAGGED=$(printf '%s\n' "$HITS" | grep -E '^\+' | grep -Ei "$SECRET_PATTERN" | cut -c1-80)
if git diff --cached --name-only | grep -Eiq '(^|/)\.env($|\.)' ; then
  echo "WARN: có file .env trong staged — kiểm tra kỹ trước khi commit."
fi
if [ -n "$FLAGGED" ]; then
  echo "WARN: dòng thêm mới nghi chứa secret (đã cắt còn 80 ký tự):"
  printf '%s\n' "$FLAGGED"
else
  echo "OK: không thấy pattern secret rõ ràng (không đảm bảo tuyệt đối)."
fi
echo

if [ "$MODE" != "mr" ]; then
  echo "=== STAGED DIFF (git diff --cached) ==="
  git diff --cached
  echo
  echo "=== UNSTAGED DIFF (git diff) ==="
  git diff
  echo
fi

echo "=== RECENT LOG ==="
git log --oneline -8 2>/dev/null || echo "(chưa có commit)"
echo

# --- MR/PR mode ---------------------------------------------------------------
if [ "$MODE" = "mr" ]; then
  BASE="${BASE_ARG:-$DEFAULT_BRANCH}"
  # ưu tiên so với origin/<base> nếu có (phản ánh remote), fallback local <base>
  if git show-ref --verify --quiet "refs/remotes/origin/$BASE"; then
    RANGE_BASE="origin/$BASE"
  else
    RANGE_BASE="$BASE"
  fi
  echo "=== MR BASE ==="
  echo "base: $BASE (range base: $RANGE_BASE)"
  echo
  echo "=== COMMITS ($RANGE_BASE..HEAD) ==="
  git log "$RANGE_BASE..HEAD" --oneline 2>/dev/null || echo "(không tính được range)"
  echo
  echo "=== DIFF STAT ($RANGE_BASE...HEAD) ==="
  git diff "$RANGE_BASE...HEAD" --stat 2>/dev/null || echo "(không tính được diff)"
  echo
  echo "=== DIFF LINE COUNT ($RANGE_BASE...HEAD) ==="
  git diff "$RANGE_BASE...HEAD" 2>/dev/null | wc -l
  echo
fi
