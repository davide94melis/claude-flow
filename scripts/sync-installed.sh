#!/usr/bin/env bash
# sync-installed.sh
# Sincronizza le skill sdlc-* dal repo claude-flow verso ~/.claude/skills/ e ~/.claude/agents/.
# Rimuove le vecchie installazioni br-* per evitare skill zombie.
#
# Default: dry-run. Usa --apply per eseguire.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
APPLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    -h|--help)
      echo "Usage: $0 [--apply]"
      echo "  Source: $REPO_ROOT/{skills,agents}/sdlc-*"
      echo "  Target: $CLAUDE_HOME/{skills,agents}/"
      exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

PREFIX="[DRY-RUN]"
RUN=":"
[[ $APPLY -eq 1 ]] && { PREFIX="[APPLY]"; RUN=""; }

echo "$PREFIX Sync from $REPO_ROOT -> $CLAUDE_HOME"
echo ""

echo "Cleanup old br-* installations:"
for d in "$CLAUDE_HOME"/skills/br-*; do
  [[ -d "$d" ]] || continue
  echo "  rm -rf $d"
  $RUN rm -rf "$d"
done
for f in "$CLAUDE_HOME"/agents/br-*.md; do
  [[ -f "$f" ]] || continue
  echo "  rm -f $f"
  $RUN rm -f "$f"
done
if [[ -f "$CLAUDE_HOME/skills/BR_SKILLS_DOCUMENTATION.md" ]]; then
  echo "  rm -f $CLAUDE_HOME/skills/BR_SKILLS_DOCUMENTATION.md"
  $RUN rm -f "$CLAUDE_HOME/skills/BR_SKILLS_DOCUMENTATION.md"
fi

echo ""
echo "Install new sdlc-* skills:"
for d in "$REPO_ROOT"/skills/sdlc-*; do
  [[ -d "$d" ]] || continue
  name=$(basename "$d")
  echo "  cp -r $d -> $CLAUDE_HOME/skills/$name"
  $RUN cp -r "$d" "$CLAUDE_HOME/skills/"
done

echo ""
echo "Install new sdlc-* agents:"
for f in "$REPO_ROOT"/agents/sdlc-*.md; do
  [[ -f "$f" ]] || continue
  name=$(basename "$f")
  echo "  cp $f -> $CLAUDE_HOME/agents/$name"
  $RUN cp "$f" "$CLAUDE_HOME/agents/"
done

echo ""
echo "Install workflow scripts (orchestration mode 'deep'):"
if [[ -d "$REPO_ROOT/workflows" ]]; then
  $RUN mkdir -p "$CLAUDE_HOME/workflows"
  found_wf=0
  for f in "$REPO_ROOT"/workflows/*.js; do
    [[ -f "$f" ]] || continue
    found_wf=1
    name=$(basename "$f")
    echo "  cp $f -> $CLAUDE_HOME/workflows/$name"
    $RUN cp "$f" "$CLAUDE_HOME/workflows/"
  done
  [[ $found_wf -eq 0 ]] && echo "  (nessuno script .js in workflows/ — verranno aggiunti dalla rollout skill heavy)"
else
  echo "  (workflows/ assente — skip)"
fi

echo ""
echo "Install documentation reference:"
if [[ -f "$REPO_ROOT/SDLC_SKILLS_DOCUMENTATION.md" ]]; then
  echo "  cp $REPO_ROOT/SDLC_SKILLS_DOCUMENTATION.md -> $CLAUDE_HOME/skills/SDLC_SKILLS_DOCUMENTATION.md"
  $RUN cp "$REPO_ROOT/SDLC_SKILLS_DOCUMENTATION.md" "$CLAUDE_HOME/skills/"
fi

echo ""
if [[ $APPLY -eq 0 ]]; then
  echo "Run with --apply to execute."
else
  echo "Done. Verify with: ls $CLAUDE_HOME/skills/ | grep -E '^(br|sdlc)-'"
  echo ""
  echo "REMINDER: update ~/.claude/CLAUDE.md trigger sections manually"
  echo "  (change '# br-X' -> '# sdlc-X' and 'skill: \"br-X\"' -> 'skill: \"sdlc-X\"')"
fi
