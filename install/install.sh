#!/usr/bin/env bash
# HighLand-factory installer (Linux / macOS)
#
#   1. Creates <repo>/.venv with PyYAML (or reuses it).
#   2. Writes <repo>/bin/factory and <repo>/bin/factory.cmd.
#   3. Links generic skills into detected agent skill roots.
#   4. Optionally refreshes <work>/.factory/local.yaml (--work <path>).
#
# Usage:
#   ./install/install.sh [--work <path>] [--force] [--python <interpreter>]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
BIN_DIR="$REPO_ROOT/bin"
WORK=""
FORCE=""
PYTHON_ARG=""
NO_SKILLS=""
SKILLS_ROOT=""
WITH_PACKS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --work) WORK="$2"; shift 2 ;;
    --force) FORCE="1"; shift ;;
    --python) PYTHON_ARG="$2"; shift 2 ;;
    --no-skills) NO_SKILLS="1"; shift ;;
    --skills-root) SKILLS_ROOT="$2"; shift 2 ;;
    --with-packs) WITH_PACKS="1"; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

step() { echo "[install] $*"; }
warn() { echo "[install] WARN: $*" >&2; }

find_python() {
  if [[ -n "$PYTHON_ARG" ]]; then
    [[ -x "$PYTHON_ARG" ]] || { echo "Python not found: $PYTHON_ARG" >&2; exit 2; }
    echo "$PYTHON_ARG"; return
  fi
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        command -v "$candidate"; return
      fi
    fi
  done
  echo "No Python 3.10+ interpreter found" >&2; exit 2
}

ensure_venv() {
  if [[ -x "$VENV_DIR/bin/python" ]]; then
    step "Reusing venv: $VENV_DIR"
    return
  fi
  local base; base="$(find_python)"
  step "Creating venv with $base"
  "$base" -m venv "$VENV_DIR"
}

ensure_pyyaml() {
  if "$VENV_DIR/bin/python" -c 'import yaml' 2>/dev/null; then
    step "PyYAML already available"; return
  fi
  if command -v uv >/dev/null 2>&1; then
    step "Installing PyYAML with uv"
    uv pip install --python "$VENV_DIR/bin/python" --quiet pyyaml
  else
    step "Installing PyYAML with pip"
    "$VENV_DIR/bin/python" -m pip install --quiet --disable-pip-version-check pyyaml
  fi
  "$VENV_DIR/bin/python" -c 'import yaml; print("PyYAML", yaml.__version__)'
}

write_shims() {
  mkdir -p "$BIN_DIR"
  cat > "$BIN_DIR/factory" <<EOF
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python" "$REPO_ROOT/engine/factory.py" "\$@"
EOF
  chmod +x "$BIN_DIR/factory"
  cat > "$BIN_DIR/factory.cmd" <<EOF
@echo off
"$VENV_DIR/bin/python" "$REPO_ROOT/engine/factory.py" %*
EOF
  step "Wrote shims under $BIN_DIR"
}

link_skills() {
  local source="$1" destination="$2" label="$3"
  if [[ ! -d "$source" ]]; then warn "$label: source not found: $source"; return; fi
  mkdir -p "$destination"
  local linked=0
  for skill in "$source"/*/; do
    [[ -d "$skill" ]] || continue
    local name; name="$(basename "$skill")"
    local dest="$destination/$name"
    if [[ -e "$dest" || -L "$dest" ]]; then
      if [[ -n "$FORCE" ]]; then rm -rf "$dest"
      else warn "$label: $dest exists; skipped (use --force)"; continue
      fi
    fi
    ln -s "$skill" "$dest"
    linked=$((linked + 1))
  done
  # Remove links this installer created earlier for skills that no longer exist.
  for existing in "$destination"/*; do
    [[ -L "$existing" ]] || continue
    local target; target="$(readlink "$existing")"
    case "$target" in
      "$source"/*)
        local name; name="$(basename "$existing")"
        if [[ ! -d "$source/$name" ]]; then
          rm -f "$existing"
          step "$label: removed stale link $name"
        fi
        ;;
    esac
  done
  step "$label: linked $linked skill(s) into $destination"
}

refresh_work_local() {
  local work="$1"
  if [[ ! -f "$work/.factory/factory.yaml" ]]; then
    warn "--work $work is not initialized yet; run: factory init --work \"$work\""
    return
  fi
  cat > "$work/.factory/local.yaml" <<EOF
# Machine-scoped factory values. Gitignored; safe to contain absolute paths.
factory_root: "$REPO_ROOT"
python: "$VENV_DIR/bin/python"
node: null
ports: {}
env: {}
platform: "$(uname -s | tr '[:upper:]' '[:lower:]')"
EOF
  step "Refreshed $work/.factory/local.yaml"
}

step "Factory repo: $REPO_ROOT"
ensure_venv
ensure_pyyaml
write_shims

if [[ -n "$NO_SKILLS" ]]; then
  step "Skipping skill linking (--no-skills)"
elif [[ -n "$SKILLS_ROOT" ]]; then
  link_skills "$REPO_ROOT/skills" "$SKILLS_ROOT" "custom"
  if [[ -n "$WITH_PACKS" ]]; then link_skills "$REPO_ROOT/packs" "$SKILLS_ROOT" "custom-packs"; fi
else
  for pair in "$HOME/.dsh/skills:dsh" "$HOME/.claude/skills:claude" "$HOME/.codex/skills:codex"; do
    parent="${pair%%:*}"; label="${pair##*:}"
    if [[ -d "$(dirname "$parent")" ]]; then
      link_skills "$REPO_ROOT/skills" "$parent" "$label"
      if [[ -n "$WITH_PACKS" ]]; then link_skills "$REPO_ROOT/packs" "$parent" "$label-packs"; fi
    fi
  done
fi

if [[ -n "$WORK" ]]; then refresh_work_local "$WORK"; fi

echo
step "Done. Add this directory to PATH to call 'factory' anywhere:"
echo "  $BIN_DIR"
echo
step "Or call it directly: $BIN_DIR/factory --version"
step "Initialize a work repo:"
echo "  $BIN_DIR/factory init --work ~/my-project"
echo "  $BIN_DIR/factory doctor --work ~/my-project"
