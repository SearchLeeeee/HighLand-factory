#!/usr/bin/env bash
# HighLand-factory upgrade (Linux / macOS)
#
# Run this after pulling a newer factory checkout. It refreshes the local engine,
# re-syncs the generic skills/packs into the agent skill roots, and optionally
# refreshes initialized work repos.
#
# Usage:
#   ./install/upgrade.sh                    # sync current checkout
#   ./install/upgrade.sh --pull             # git pull --ff-only, then sync
#   ./install/upgrade.sh --work ~/my-project
#   ./install/upgrade.sh --work ~/a --work ~/b --apply-work-upgrade
#   ./install/upgrade.sh --no-skills        # engine only (external skill manager)
#   ./install/upgrade.sh --skills-root ~/custom/skills --with-packs

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_SCRIPT="$REPO_ROOT/install/install.sh"
FACTORY_CMD="$REPO_ROOT/bin/factory"

PULL=""
NO_SKILLS=""
SKILLS_ROOT=""
FORCE=""
WITH_PACKS=""
APPLY_WORK_UPGRADE=""
WORK_PATHS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pull) PULL="1"; shift ;;
    --work) WORK_PATHS+=("$2"); shift 2 ;;
    --apply-work-upgrade) APPLY_WORK_UPGRADE="1"; shift ;;
    --no-skills) NO_SKILLS="1"; shift ;;
    --skills-root) SKILLS_ROOT="$2"; shift 2 ;;
    --force) FORCE="1"; shift ;;
    --with-packs) WITH_PACKS="1"; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

step() { echo "[upgrade] $*"; }
warn() { echo "[upgrade] WARN: $*" >&2; }

step "Factory repo: $REPO_ROOT"

if [[ -n "$PULL" ]]; then
  step "git pull --ff-only"
  git -C "$REPO_ROOT" pull --ff-only
fi

if [[ -f "$REPO_ROOT/VERSION" ]]; then
  step "Version: $(tr -d '[:space:]' < "$REPO_ROOT/VERSION")"
fi

# Reuse the installer for venv, shims and skill/pack linking. It is idempotent and
# removes links that point into this checkout but whose source skill was deleted.
INSTALL_ARGS=()
[[ -n "$NO_SKILLS" ]] && INSTALL_ARGS+=("--no-skills")
[[ -n "$SKILLS_ROOT" ]] && INSTALL_ARGS+=("--skills-root" "$SKILLS_ROOT")
[[ -n "$FORCE" ]] && INSTALL_ARGS+=("--force")
[[ -n "$WITH_PACKS" ]] && INSTALL_ARGS+=("--with-packs")

bash "$INSTALL_SCRIPT" "${INSTALL_ARGS[@]}"

if [[ ${#WORK_PATHS[@]} -eq 0 ]]; then
  step "No --work paths given. Agent links and engine are refreshed; work repos were not touched."
  step "Refresh a work repo with: install/upgrade.sh --work <path> [--apply-work-upgrade]"
  exit 0
fi

for work_path in "${WORK_PATHS[@]}"; do
  if [[ ! -d "$work_path" ]]; then
    warn "work repo not found: $work_path"
    continue
  fi
  if [[ ! -f "$work_path/.factory/factory.yaml" ]]; then
    warn "$work_path is not an initialized work repo (missing .factory/factory.yaml); skipped"
    continue
  fi
  step "Refreshing work repo: $work_path"
  # Refresh machine-scoped local.yaml without touching agent links again.
  bash "$INSTALL_SCRIPT" --work "$work_path" --no-skills

  step "Checking generated files: $work_path"
  if "$FACTORY_CMD" upgrade --work "$work_path" --check; then
    check_failed=""
  else
    check_failed="1"
  fi

  if [[ -n "$APPLY_WORK_UPGRADE" ]]; then
    if [[ -n "$check_failed" ]]; then
      step "Applying generated-file refresh: $work_path"
      "$FACTORY_CMD" upgrade --work "$work_path" --apply
    else
      step "Already up to date: $work_path"
    fi
    if ! "$FACTORY_CMD" doctor --work "$work_path"; then
      warn "doctor reported issues for $work_path; fix them before starting work"
    fi
  elif [[ -n "$check_failed" ]]; then
    warn "generated files need refresh in $work_path; rerun with --apply-work-upgrade"
  fi
done

step "Done."
step "Next: restart your agent session so it reloads the refreshed skills."
