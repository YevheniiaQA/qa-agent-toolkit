#!/usr/bin/env python3
"""register.py — add (or with --remove, take out) the toolkit's hooks in Cursor and Claude Code.

  qa-guard        before shell / web fetch / MCP calls   integration boundary
  qa-test-lint    after a test file is written           focused tests, fixed waits, weakened assertions
  qa-stage-gate   when a stage agent or the session stops a stage cannot be done without its gate file

Merges into whatever is there: other settings and other hooks are kept, an entry that already
runs one of these scripts is replaced rather than duplicated, and the previous file is copied
to <file>.bak-<timestamp> before any change. Usage: register.py [--remove] [--dry-run]
"""
import datetime, json, os, shlex, shutil, sys

HOME = os.path.expanduser("~")
HERE = os.path.dirname(os.path.realpath(__file__))
CLAUDE = os.path.join(HOME, ".claude", "settings.json")
CURSOR = os.path.join(HOME, ".cursor", "hooks.json")
SCRIPTS = ("qa-guard", "qa-test-lint", "qa-stage-gate")


def cmd(script, *args):
    return " ".join([shlex.quote(os.path.join(HERE, script)), *args])


# (event, matcher or None, command, extra fields)
CLAUDE_HOOKS = [
    ("PreToolUse", "Bash|WebFetch|mcp__.*", cmd("qa-guard", "--ide", "claude"),
     {"timeout": 10, "onFailure": "block", "statusMessage": "qa-guard: checking integrations"}),
    ("PostToolUse", "Write|Edit|MultiEdit", cmd("qa-test-lint", "--ide", "claude"), {"timeout": 10}),
    ("SubagentStop", None, cmd("qa-stage-gate", "--ide", "claude", "--event", "subagent-stop"),
     {"timeout": 120, "statusMessage": "qa-stage-gate: checking the stage's gate file"}),
    ("Stop", None, cmd("qa-stage-gate", "--ide", "claude", "--event", "stop"), {"timeout": 120}),
]
CURSOR_HOOKS = [
    ("beforeShellExecution", None, cmd("qa-guard", "--ide", "cursor"), {"timeout": 10, "failClosed": True}),
    ("beforeMCPExecution", None, cmd("qa-guard", "--ide", "cursor"), {"timeout": 10, "failClosed": True}),
    ("postToolUse", "Write", cmd("qa-test-lint", "--ide", "cursor"), {"timeout": 10}),
    ("subagentStop", None, cmd("qa-stage-gate", "--ide", "cursor", "--event", "subagent-stop"),
     {"timeout": 120, "loop_limit": 3}),
    ("stop", None, cmd("qa-stage-gate", "--ide", "cursor", "--event", "stop"), {"timeout": 120, "loop_limit": 3}),
]


def ours(command):
    return any(os.sep + s + " " in (command or "") + " " or (command or "").startswith(s) for s in SCRIPTS)


def load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)    # a malformed file stops the install: fix it by hand, never overwrite it


def save(path, data, dry):
    new = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if new == old:
        print(f"  {path}: unchanged")
        return
    if dry:
        print(f"  would update {path}")
        return
    if old is not None:
        shutil.copy2(path, f"{path}.bak-{datetime.datetime.now():%Y%m%d-%H%M%S}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(new)
    print(f"  updated {path}")


def claude(remove, dry):
    s = load(CLAUDE, {})
    hooks = s.setdefault("hooks", {})
    for event in {e for e, *_ in CLAUDE_HOOKS}:
        kept = []
        for entry in hooks.get(event, []):
            hs = [h for h in entry.get("hooks", []) if not ours(h.get("command"))]
            if hs:
                kept.append(dict(entry, hooks=hs))
        if not remove:
            for e, matcher, command, extra in CLAUDE_HOOKS:
                if e == event:
                    entry = {"matcher": matcher} if matcher else {}
                    entry["hooks"] = [dict({"type": "command", "command": command}, **extra)]
                    kept.append(entry)
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event, None)
    if not hooks:
        del s["hooks"]
    save(CLAUDE, s, dry)


def cursor(remove, dry):
    h = load(CURSOR, {"version": 1, "hooks": {}})
    h.setdefault("version", 1)
    hooks = h.setdefault("hooks", {})
    for event in {e for e, *_ in CURSOR_HOOKS}:
        kept = [e for e in hooks.get(event, []) if not ours(e.get("command"))]
        if not remove:
            for e, matcher, command, extra in CURSOR_HOOKS:
                if e == event:
                    kept.append(dict({"command": command}, **({"matcher": matcher} if matcher else {}), **extra))
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event, None)
    save(CURSOR, h, dry)


if __name__ == "__main__":
    args = set(sys.argv[1:])
    unknown = args - {"--remove", "--dry-run"}
    if unknown:
        sys.exit(f"register.py: unknown option {' '.join(unknown)}")
    claude("--remove" in args, "--dry-run" in args)
    cursor("--remove" in args, "--dry-run" in args)
