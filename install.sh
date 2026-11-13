#!/usr/bin/env bash
# install.sh — connect this toolkit to Cursor and Claude Code on this machine.
#
# Usage:  ./install.sh [--copy] [--dry-run]
#   (default)  symlink every skill into ~/.cursor/skills and ~/.claude/skills, and every
#              stage agent (built per IDE by bin/qa-build-agents) into ~/.cursor/agents
#              and ~/.claude/agents
#              and every Cursor rule (rules/*.mdc) into ~/.cursor/rules
#   --copy     copy skills, agents and rules instead, for an IDE that does not follow symlinks;
#              re-run after every change to the toolkit
#   --dry-run  print what would change, change nothing
#
# Also links ~/.qa-agent/bin to the toolkit's bin/ and registers the qa-guard hook in
# ~/.claude/settings.json and ~/.cursor/hooks.json (hooks/register.py; --remove there
# takes it out again). Existing directories are never
# deleted: anything in the way is moved to ~/.qa-agent/backups/install-<timestamp>/.
# Only skills and agents that exist in the toolkit are touched; others in those folders
# (for example ~/.claude/skills/synced) are left alone. Safe to re-run.
set -euo pipefail

TK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE=link
DRY=0
for a in "$@"; do
  case "$a" in
    --copy) MODE=copy ;;
    --dry-run) DRY=1 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "install.sh: unknown option $a" >&2; exit 2 ;;
  esac
done

TARGETS=("$HOME/.cursor/skills" "$HOME/.claude/skills")
BK="$HOME/.qa-agent/backups/install-$(date +%Y%m%d-%H%M%S)"
MARK=".toolkit-managed"   # marks a --copy mirror, so a re-run refreshes it instead of backing it up

run() { if [ "$DRY" = 1 ]; then echo "  would: $*"; else "$@"; fi; }

# set_aside <path> <backup-subdir> — move whatever is at <path> into the backup folder
set_aside() {
  run mkdir -p "$BK/$2"
  run mv "$1" "$BK/$2/"
  echo "  backed up $1 -> $BK/$2/"
}

echo "toolkit: $TK   mode: $MODE$([ "$DRY" = 1 ] && echo ' (dry run)')"

# 1. bin
BIN="$HOME/.qa-agent/bin"
if [ "$(readlink "$BIN" 2>/dev/null || true)" != "$TK/bin" ]; then
  { [ -e "$BIN" ] || [ -L "$BIN" ]; } && set_aside "$BIN" qa-agent
  run mkdir -p "$HOME/.qa-agent"
  run ln -s "$TK/bin" "$BIN"
  echo "  linked $BIN -> $TK/bin"
fi
case ":$PATH:" in *":$BIN:"*) ;; *) echo "  note: add to your shell profile: export PATH=\"\$HOME/.qa-agent/bin:\$PATH\"" ;; esac

# 2. skills
for t in "${TARGETS[@]}"; do
  ide=$(basename "$(dirname "$t")"); ide=${ide#.}   # cursor or claude
  run mkdir -p "$t"
  changed=0
  for src in "$TK"/skills/*/; do
    src=${src%/}; n=$(basename "$src"); dst="$t/$n"
    if [ "$MODE" = link ]; then
      [ "$(readlink "$dst" 2>/dev/null || true)" = "$src" ] && continue
      { [ -e "$dst" ] || [ -L "$dst" ]; } && set_aside "$dst" "$ide-skills"
      run ln -s "$src" "$dst"
    else
      if [ -d "$dst" ] && [ ! -L "$dst" ] && [ -f "$dst/$MARK" ]; then
        run rsync -a --delete --exclude "$MARK" "$src/" "$dst/"
      else
        { [ -e "$dst" ] || [ -L "$dst" ]; } && set_aside "$dst" "$ide-skills"
        run cp -R "$src" "$dst"
        run touch "$dst/$MARK"
      fi
    fi
    changed=$((changed + 1))
  done
  # links into the toolkit whose skill has since been removed from it
  for l in "$t"/*; do
    [ -L "$l" ] || continue
    case "$(readlink "$l")" in "$TK/skills/"*) [ -e "$l" ] || { run rm "$l"; echo "  removed stale link $l"; } ;; esac
  done
  echo "  $t: $changed updated"
done

# 3. stage agents: one source in agents/, one build per IDE in build/<ide>/agents/
echo "agents:"
if [ "$DRY" = 1 ]; then "$TK/bin/qa-build-agents" --check || true; else "$TK/bin/qa-build-agents"; fi
for ide in claude cursor; do
  t="$HOME/.$ide/agents"; run mkdir -p "$t"; changed=0
  for src in "$TK/build/$ide/agents/"*.md; do
    [ -e "$src" ] || continue
    dst="$t/$(basename "$src")"
    if [ "$MODE" = link ]; then
      [ "$(readlink "$dst" 2>/dev/null || true)" = "$src" ] && continue
      { [ -e "$dst" ] || [ -L "$dst" ]; } && set_aside "$dst" "$ide-agents"
      run ln -s "$src" "$dst"
    else
      cmp -s "$src" "$dst" 2>/dev/null && continue
      { [ -e "$dst" ] || [ -L "$dst" ]; } && set_aside "$dst" "$ide-agents"
      run cp "$src" "$dst"
    fi
    changed=$((changed + 1))
  done
  for l in "$t"/*.md; do
    [ -L "$l" ] || continue
    case "$(readlink "$l")" in "$TK/build/"*) [ -e "$l" ] || { run rm "$l"; echo "  removed stale link $l"; } ;; esac
  done
  echo "  $t: $changed updated"
done

# 3b. Cursor rules: toolkit/rules/*.mdc -> ~/.cursor/rules (Claude Code reads AGENTS.md instead)
echo "rules:"
t="$HOME/.cursor/rules"; run mkdir -p "$t"; changed=0
for src in "$TK/rules/"*.mdc; do
  [ -e "$src" ] || continue
  dst="$t/$(basename "$src")"
  if [ "$MODE" = link ]; then
    [ "$(readlink "$dst" 2>/dev/null || true)" = "$src" ] && continue
    { [ -e "$dst" ] || [ -L "$dst" ]; } && set_aside "$dst" cursor-rules
    run ln -s "$src" "$dst"
  else
    cmp -s "$src" "$dst" 2>/dev/null && continue
    { [ -e "$dst" ] || [ -L "$dst" ]; } && set_aside "$dst" cursor-rules
    run cp "$src" "$dst"
  fi
  changed=$((changed + 1))
done
echo "  $t: $changed updated"

# 4. hooks: qa-guard, qa-stage-gate and qa-test-lint in both IDEs
echo "hooks:"
python3 "$TK/hooks/register.py" $([ "$DRY" = 1 ] && echo --dry-run)

# 4b. the toolkit's own pre-commit: skill-lint, agent build
if git -C "$TK" rev-parse --git-dir >/dev/null 2>&1 && [ "$(git -C "$TK" config core.hooksPath || true)" != githooks ]; then
  run git -C "$TK" config core.hooksPath githooks
  echo "  pre-commit: githooks/pre-commit enabled"
fi

# 5. verify
[ "$DRY" = 1 ] && exit 0
fail=0
for t in "${TARGETS[@]}"; do
  for src in "$TK"/skills/*/; do
    src=${src%/}; n=$(basename "$src")
    if ! diff -rq --exclude "$MARK" "$src" "$t/$n" >/dev/null 2>&1; then
      echo "  MISMATCH $t/$n"; fail=1
    fi
  done
done
for ide in claude cursor; do
  for src in "$TK/build/$ide/agents/"*.md; do
    cmp -s "$src" "$HOME/.$ide/agents/$(basename "$src")" || { echo "  MISMATCH $HOME/.$ide/agents/$(basename "$src")"; fail=1; }
  done
done
for src in "$TK/rules/"*.mdc; do
  [ -e "$src" ] || continue
  cmp -s "$src" "$HOME/.cursor/rules/$(basename "$src")" || { echo "  MISMATCH $HOME/.cursor/rules/$(basename "$src")"; fail=1; }
done
total=$(find "$TK/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
agents=$(find "$TK/agents" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')
[ "$fail" = 0 ] && echo "ok: $total skills and $agents agents identical in Cursor and Claude Code" || exit 1
