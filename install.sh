#!/usr/bin/env bash
# install.sh — connect this toolkit to Cursor and Claude Code on this machine.
#
# Usage:  ./install.sh [--copy] [--dry-run]                    for every project of this user
#         ./install.sh --project DIR [--uninstall] [--dry-run]  for one project only
#   (default)  symlink every skill into ~/.cursor/skills and ~/.claude/skills, and every
#              stage agent (built per IDE by bin/qa-build-agents) into ~/.cursor/agents
#              and ~/.claude/agents
#              and every Cursor rule (rules/*.mdc) into ~/.cursor/rules
#   --copy     copy skills, agents and rules instead, for an IDE that does not follow symlinks;
#              re-run after every change to the toolkit
#   --dry-run  print what would change, change nothing
#   --project DIR   install into DIR/.claude only (skills, agents, hooks in
#              DIR/.claude/settings.json). Nothing under ~/.claude, ~/.cursor or ~/.qa-agent/bin
#              is touched, so skills, plugins and connectors already installed stay as they are.
#              Claude Code only. Re-run after updating the toolkit; --uninstall removes
#              exactly what this mode installed.
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
PROJECT=""
UNINSTALL=0
while [ $# -gt 0 ]; do
  case "$1" in
    --copy) MODE=copy ;;
    --dry-run) DRY=1 ;;
    --project) [ $# -ge 2 ] || { echo "install.sh: --project needs a directory" >&2; exit 2; }; PROJECT="$2"; shift ;;
    --uninstall) UNINSTALL=1 ;;
    -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
    *) echo "install.sh: unknown option $1" >&2; exit 2 ;;
  esac
  shift
done
[ "$UNINSTALL" = 1 ] && [ -z "$PROJECT" ] && { echo "install.sh: --uninstall works with --project DIR" >&2; exit 2; }

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

# ---- project install: everything stays inside <project>/.claude -------------------------
if [ -n "$PROJECT" ]; then
  [ -d "$PROJECT" ] || { echo "install.sh: no such directory: $PROJECT" >&2; exit 2; }
  P="$(cd "$PROJECT" && pwd)"
  case "$P" in "$HOME") echo "install.sh: --project is for a project folder, not your home directory" >&2; exit 2 ;; esac
  case "$TK" in *" "*) echo "install.sh: the toolkit path contains a space ($TK); clone it to a path without spaces" >&2; exit 2 ;; esac
  S="$P/.claude/skills"; A="$P/.claude/agents"
  echo "toolkit: $TK   project: $P$([ "$UNINSTALL" = 1 ] && echo '   uninstall')$([ "$DRY" = 1 ] && echo ' (dry run)')"

  if [ "$UNINSTALL" = 1 ]; then
    n=0
    for d in "$S"/*/; do
      d=${d%/}; [ -f "$d/$MARK" ] || continue      # only what this mode copied
      run rm -rf "$d"; n=$((n + 1))
    done
    echo "  $S: $n removed"
    n=0
    for f in "$A"/qa-*.md; do
      [ -f "$f" ] && grep -q "built by qa-build-agents" "$f" || continue
      run rm "$f"; n=$((n + 1))
    done
    echo "  $A: $n removed"
    python3 "$TK/hooks/register.py" --project "$P" --remove $([ "$DRY" = 1 ] && echo --dry-run)
    if [ "$DRY" = 0 ]; then rmdir "$S" "$A" "$P/.claude" 2>/dev/null || true; fi
    exit 0
  fi

  # skills: copies, with the two home-relative toolkit paths pointed at this clone
  run mkdir -p "$S" "$A"
  changed=0
  for src in "$TK"/skills/*/; do
    src=${src%/}; n=$(basename "$src"); dst="$S/$n"
    if { [ -e "$dst" ] || [ -L "$dst" ]; } && [ ! -f "$dst/$MARK" ]; then
      echo "  SKIPPED $dst: exists and was not installed by this toolkit" >&2; continue
    fi
    if [ "$DRY" = 1 ]; then echo "  would: copy $src -> $dst"; changed=$((changed + 1)); continue; fi
    rm -rf "$dst"; cp -R "$src" "$dst"; touch "$dst/$MARK"
    changed=$((changed + 1))
  done
  echo "  $S: $changed skills"

  # agents: the Claude Code build
  if [ "$DRY" = 1 ]; then "$TK/bin/qa-build-agents" --check >/dev/null 2>&1 || true; else "$TK/bin/qa-build-agents" >/dev/null; fi
  changed=0
  for src in "$TK/build/claude/agents/"*.md; do
    [ -e "$src" ] || continue
    dst="$A/$(basename "$src")"
    if [ -e "$dst" ] && ! grep -q "built by qa-build-agents" "$dst"; then
      echo "  SKIPPED $dst: exists and was not installed by this toolkit" >&2; continue
    fi
    run cp "$src" "$dst"; changed=$((changed + 1))
  done
  echo "  $A: $changed agents"

  if [ "$DRY" = 0 ]; then
    # ~/.qa-agent/bin and ~/.qa-agent/toolkit in the copies -> this clone (never the user's home)
    find "$S" "$A" -type f \( -name '*.md' -o -name '*.html' \) -print0 | while IFS= read -r -d '' f; do
      case "$f" in "$S"/*) [ -f "$S/$(echo "${f#"$S"/}" | cut -d/ -f1)/$MARK" ] || continue ;; esac
      case "$f" in "$A"/*) grep -q "built by qa-build-agents" "$f" || continue ;; esac
      TK="$TK" perl -pi -e 's#(?:~|\$HOME)/\.qa-agent/bin#$ENV{TK}/bin#g; s#(?:~|\$HOME)/\.qa-agent/toolkit#$ENV{TK}#g' "$f"
    done
  fi

  echo "hooks:"
  python3 "$TK/hooks/register.py" --project "$P" $([ "$DRY" = 1 ] && echo --dry-run)
  [ "$DRY" = 1 ] && exit 0
  echo "ok: installed for $P only. Check with: $TK/bin/qa-check-isolation $P"
  exit 0
fi

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
