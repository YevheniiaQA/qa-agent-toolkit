# Source this file, then call: qa_load [project]
# Loads, in order (later wins):
#   ~/.qa-agent/.env                          shared non-secret defaults
#   ~/.qa-agent/projects/<p>/profile.env      project settings, INTEGRATIONS list
#   ~/.qa-agent/projects/<p>/secrets.env      that project's tokens, if the file exists
# <p> is the argument, else the nearest .qa-project file above $PWD.
# Values are assigned literally, never evaluated: a password with ` or $(...) is safe.

qa_project() {
  local d="$PWD"
  while [ "$d" != "/" ]; do
    [ -f "$d/.qa-project" ] && { tr -d '[:space:]' < "$d/.qa-project"; return 0; }
    d=$(dirname "$d")
  done
  return 1
}

# _qa_read <file> [strip]  — "strip" drops trailing "  # comment" (profiles only;
# secrets are kept byte-for-byte so a password containing " #" survives).
_qa_read() {
  local line key val
  [ -f "$1" ] || return 0
  while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] || continue
    key="${line%%=*}"; val="${line#*=}"
    if [ "${2:-}" = strip ]; then
      # pattern expansion only: zsh has no BASH_REMATCH, which once emptied every commented value
      case "$val" in [[:space:]]*\#*|\#*) val=" $val" ;; esac
      val="${val%%[[:space:]]\#*}"
      val="${val%"${val##*[![:space:]]}"}"
    fi
    export "$key=$val"
  done < "$1"
}

qa_load() {
  local p="${1:-$(qa_project)}"
  [ -n "$p" ] || { echo "qa_load: no project given and no .qa-project found above $PWD" >&2; return 1; }
  local dir="$HOME/.qa-agent/projects/$p"
  [ -f "$dir/profile.env" ] || { echo "qa_load: no profile at $dir/profile.env" >&2; return 1; }
  _qa_read "$HOME/.qa-agent/.env" strip
  _qa_read "$dir/profile.env" strip
  _qa_read "$dir/secrets.env"
  export QA_PROJECT="$p"
}

# qa_enabled jira  -> exit 0 only if "jira" is in this project's INTEGRATIONS list
qa_enabled() { [[ ",${INTEGRATIONS:-}," == *",$1,"* ]]; }
