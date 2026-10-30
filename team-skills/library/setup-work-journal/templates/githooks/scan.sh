#!/bin/sh
# Hàm quét secret dùng chung cho pre-commit và pre-push. Đổi scanner / đổi cờ thì chỉ sửa file này.
# Scanner: betterleaks (tự dò v1 hay v2 qua --help); chưa cài → quét pattern (yếu hơn, chỉ để không hở hẳn).

detect_scanner() {
  if command -v betterleaks >/dev/null 2>&1; then
    if betterleaks git --help 2>&1 | grep -q -- '--pre-commit'; then SCANNER=betterleaks-v1; else SCANNER=betterleaks-v2; fi
  else
    SCANNER=none
  fi
}

PATTERN='(-----BEGIN [A-Z ]*PRIVATE KEY-----|glpat-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,}|xox[baprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|shp(at|ss|ca|pa)_[a-fA-F0-9]{32}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|(api[_-]?key|secret|token|passwd|password)["'"'"' :=]{1,4}[A-Za-z0-9/+_-]{16,})'

warn_no_scanner() {
  echo "⚠️  Chưa cài betterleaks — đang quét bằng pattern (yếu hơn)." >&2
  echo "   Cài betterleaks: https://github.com/betterleaks/betterleaks#installation" >&2
}

# Quét phần đã git add. Exit ≠ 0 = có nghi secret.
scan_staged() {
  detect_scanner
  case "$SCANNER" in
    betterleaks-v1) betterleaks git . --pre-commit --staged --redact ;;
    betterleaks-v2) betterleaks git --staged --redact ;;
    none)
      warn_no_scanner
      hit=0
      for f in $(git diff --cached --name-only --diff-filter=AM); do
        if git show ":$f" 2>/dev/null | grep -EqI "$PATTERN"; then echo "❌ Nghi có secret trong: $f" >&2; hit=1; fi
      done
      return $hit ;;
  esac
}

# Quét các commit trong khoảng $1 (cú pháp git log, vd "abc123..def456" hoặc "def456 --not --remotes=origin").
scan_range() {
  detect_scanner
  case "$SCANNER" in
    betterleaks-v1) betterleaks git . --redact --log-opts="$1" ;;
    betterleaks-v2) betterleaks git --redact --log-opts="$1" ;;
    none)
      warn_no_scanner
      # shellcheck disable=SC2086
      if git log -p $1 2>/dev/null | grep -EqI "$PATTERN"; then echo "❌ Nghi có secret trong các commit sắp push." >&2; return 1; fi
      return 0 ;;
  esac
}
