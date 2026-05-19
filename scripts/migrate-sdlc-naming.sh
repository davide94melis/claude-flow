#!/usr/bin/env bash
# migrate-sdlc-naming.sh
# Rinomina i file BR legacy (REVIEW_BR/GAP_REPORT_BR/PIANO_IMPLEMENTAZIONE_BR/
# PROGRESSO_BR/AVANZAMENTO_BR) ai nomi nuovi (CLARIFY/PLAN/TASKS/PROGRESS.md/
# PROGRESS.xlsx) nelle cartelle plans/{in-progress,todo}/ del repo profili.
#
# Default: dry-run. Usa --apply per eseguire i git mv.
# Default root: C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles
# Override con --root <path>.

set -euo pipefail

DEFAULT_ROOT="C:/Users/davmelis/Documents/MyGitHub/deloitte-profiles"
ROOT="$DEFAULT_ROOT"
APPLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --root) ROOT="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--apply] [--root <path>]"
      echo "  Default root: $DEFAULT_ROOT"
      exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ ! -d "$ROOT" ]]; then
  echo "ERROR: root directory not found: $ROOT" >&2
  exit 1
fi

declare -A MAP=(
  ["REVIEW_BR.md"]="CLARIFY.md"
  ["REVIEW_BR.docx"]="CLARIFY.docx"
  ["GAP_REPORT_BR.md"]="PLAN.md"
  ["PIANO_IMPLEMENTAZIONE_BR.md"]="TASKS.md"
  ["PROGRESSO_BR.md"]="PROGRESS.md"
  ["AVANZAMENTO_BR.xlsx"]="PROGRESS.xlsx"
)

PREFIX="[DRY-RUN]"
[[ $APPLY -eq 1 ]] && PREFIX="[APPLY]"

echo "$PREFIX Scanning $ROOT/*/plans/{in-progress,todo}/"
echo ""

total_renames=0
total_brs=0
conflict_found=0

while IFS= read -r br_dir; do
  br_renames=()

  for old in "${!MAP[@]}"; do
    new="${MAP[$old]}"
    old_path="$br_dir/$old"
    new_path="$br_dir/$new"

    if [[ -f "$old_path" && -f "$new_path" ]]; then
      echo "  CONFLICT in $br_dir:" >&2
      echo "    both $old and $new exist. Resolve manually." >&2
      conflict_found=1
      continue
    fi

    if [[ -f "$old_path" ]]; then
      br_renames+=("$old → $new")
    fi
  done

  if [[ ${#br_renames[@]} -gt 0 ]]; then
    total_brs=$((total_brs + 1))
    rel="${br_dir#$ROOT/}"
    echo "  $rel/"
    for r in "${br_renames[@]}"; do
      echo "    $r"
      total_renames=$((total_renames + 1))
      if [[ $APPLY -eq 1 ]]; then
        old="${r% → *}"
        new="${r#* → }"
        (cd "$ROOT" && git mv "${rel}/${old}" "${rel}/${new}")
      fi
    done
  fi
done < <(find "$ROOT" -mindepth 4 -maxdepth 4 -type d \( -path "*/plans/in-progress/*" -o -path "*/plans/todo/*" \))

echo ""

if [[ $conflict_found -eq 1 ]]; then
  echo "ERROR: conflicts found. Resolve manually before running with --apply." >&2
  exit 2
fi

if [[ $total_renames -eq 0 ]]; then
  echo "Nothing to do. All files already use the new naming."
  exit 0
fi

echo "$total_renames rename operation(s) on $total_brs BR(s)."
if [[ $APPLY -eq 0 ]]; then
  echo "Run with --apply to execute. Then commit and push the deloitte-profiles repo."
else
  echo "Done. Now commit and push the deloitte-profiles repo."
  echo ""
  echo "WARNING: references to old file names inside PROGRESSO.md or other markdown files"
  echo "are NOT modified. Inspect manually if needed."
fi
