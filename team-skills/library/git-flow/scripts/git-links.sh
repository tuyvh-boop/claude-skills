#!/usr/bin/env sh
# git-links.sh — sinh URL web (repo / branch / commit / compare) để báo cáo cuối mỗi
# operation của skill git-flow. READ-ONLY: chỉ đọc git config + log, không đổi state.
#
# Cách dùng:
#   sh git-links.sh                 # link cho HEAD
#   sh git-links.sh <sha> [<sha>…]  # link cho các commit chỉ định
#
# Cross-platform: POSIX sh + git (Linux/macOS/Windows Git Bash).

set -u

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: không phải git repo."
  exit 1
fi

REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REMOTE_URL" ]; then
  echo "=== LINKS ==="
  echo "host: none (không có remote origin) — báo cáo bằng sha/branch dạng text, KHÔNG bịa URL."
  exit 0
fi

# --- Chuẩn hoá remote URL về dạng web https ----------------------------------
# git@host:group/repo.git | ssh://git@host/group/repo.git | https://host/group/repo.git
WEB=$REMOTE_URL
WEB=${WEB#ssh://}
WEB=${WEB#git+}
WEB=${WEB#git@}
case "$WEB" in
  https://*|http://*) : ;;
  *:*/*)  WEB="https://$(printf '%s' "$WEB" | sed 's|:|/|')" ;;   # scp-like → https
  *)      WEB="https://$WEB" ;;
esac
# bỏ user@ trong https://user@host/... và đuôi .git / dấu / cuối
WEB=$(printf '%s' "$WEB" | sed -e 's|://[^/@]*@|://|' -e 's|\.git$||' -e 's|/$||')

case "$REMOTE_URL" in
  *github.com*) HOST="github" ;;
  *gitlab*)     HOST="gitlab" ;;
  *bitbucket*)  HOST="bitbucket" ;;
  *)            HOST="unknown" ;;
esac

BRANCH=$(git branch --show-current 2>/dev/null)
DEFAULT_BRANCH=$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null | sed 's|.*/||')
[ -n "$DEFAULT_BRANCH" ] || {
  if git show-ref --verify --quiet refs/remotes/origin/main; then DEFAULT_BRANCH="main"; else DEFAULT_BRANCH="master"; fi
}

echo "=== LINKS ==="
echo "host: $HOST"

if [ "$HOST" = "unknown" ]; then
  echo "remote: $REMOTE_URL"
  echo "(host không nhận diện được — báo cáo bằng sha/branch dạng text, KHÔNG bịa URL)"
  exit 0
fi

case "$HOST" in
  github)    COMMIT_PATH="commit"; TREE_PATH="tree" ;;
  gitlab)    COMMIT_PATH="-/commit"; TREE_PATH="-/tree" ;;
  bitbucket) COMMIT_PATH="commits"; TREE_PATH="src" ;;
esac

echo "repo: $WEB"
[ -n "$BRANCH" ] && echo "branch: $WEB/$TREE_PATH/$BRANCH"

# --- Commit links -------------------------------------------------------------
if [ "$#" -eq 0 ]; then
  set -- HEAD
fi
for REV in "$@"; do
  SHA=$(git rev-parse "$REV" 2>/dev/null) || { echo "commit $REV: (không resolve được)"; continue; }
  SHORT=$(git rev-parse --short "$SHA")
  SUBJECT=$(git log -1 --format=%s "$SHA" 2>/dev/null)
  echo "commit $SHORT: $WEB/$COMMIT_PATH/$SHA — $SUBJECT"
done

# --- Compare / tạo MR-PR ------------------------------------------------------
if [ -n "$BRANCH" ] && [ "$BRANCH" != "$DEFAULT_BRANCH" ]; then
  case "$HOST" in
    github) echo "compare (tạo PR): $WEB/compare/$DEFAULT_BRANCH...$BRANCH?expand=1" ;;
    gitlab) echo "compare (tạo MR): $WEB/-/merge_requests/new?merge_request%5Bsource_branch%5D=$BRANCH&merge_request%5Btarget_branch%5D=$DEFAULT_BRANCH" ;;
    bitbucket) echo "compare (tạo PR): $WEB/pull-requests/new?source=$BRANCH&dest=$DEFAULT_BRANCH" ;;
  esac
fi
