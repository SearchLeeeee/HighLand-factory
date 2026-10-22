"""Doctor checks and machine-gate execution."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import config as config_mod
from . import util
from .layout import Layout, build_layout, missing_layout_paths


@dataclass
class Check:
    level: str  # ok | warn | fail
    code: str
    message: str
    hint: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"level": self.level, "code": self.code, "message": self.message, "hint": self.hint}


@dataclass
class DoctorResult:
    checks: list[Check] = field(default_factory=list)

    def add(self, level: str, code: str, message: str, hint: str = "") -> None:
        self.checks.append(Check(level, code, message, hint))

    @property
    def errors(self) -> list[Check]:
        return [item for item in self.checks if item.level == "fail"]

    @property
    def warnings(self) -> list[Check]:
        return [item for item in self.checks if item.level == "warn"]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": not self.errors,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "checks": [item.as_dict() for item in self.checks],
        }


def _parse_version(value: str) -> tuple[int, int, int]:
    parts = [part for part in value.strip().lstrip("v").split(".") if part.isdigit()]
    numbers = [int(part) for part in parts[:3]]
    while len(numbers) < 3:
        numbers.append(0)
    return tuple(numbers)  # type: ignore[return-value]


def version_satisfies(current: str, spec: str) -> tuple[bool, str]:
    """Minimal range support: ``>=X.Y``, ``<X.Y``, ``X.Y.Z`` and ``*``."""
    current_tuple = _parse_version(current)
    spec = str(spec or "").strip()
    if not spec or spec == "*":
        return True, ""
    clauses = spec.replace(",", " ").split()
    for clause in clauses:
        if clause.startswith(">="):
            if current_tuple < _parse_version(clause[2:]):
                return False, f"{current} < required {clause}"
        elif clause.startswith("<="):
            if current_tuple > _parse_version(clause[2:]):
                return False, f"{current} > allowed {clause}"
        elif clause.startswith("<"):
            if current_tuple >= _parse_version(clause[1:]):
                return False, f"{current} >= excluded {clause}"
        elif clause.startswith(">"):
            if current_tuple <= _parse_version(clause[1:]):
                return False, f"{current} <= required {clause}"
        elif clause.startswith("^"):
            base = _parse_version(clause[1:])
            if base[0] == 0:
                satisfied = (
                    current_tuple[0] == 0
                    and current_tuple[1] == base[1]
                    and current_tuple >= base
                )
            else:
                satisfied = current_tuple[0] == base[0] and current_tuple >= base
            if not satisfied:
                return False, f"{current} outside ^{clause[1:]}"
        elif clause[0].isdigit():
            if current_tuple != _parse_version(clause):
                return False, f"{current} != pinned {clause}"
        else:
            return True, f"unparsed version clause {clause!r}; skipped"
    return True, ""


def python_has_yaml(python: Path) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            [str(python), "-c", "import sys, yaml; print(sys.version.split()[0], yaml.__version__)"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    if completed.returncode != 0:
        return False, (completed.stderr or completed.stdout).strip()
    return True, completed.stdout.strip()


def run_gate(layout: Layout, kind: str) -> tuple[int, str, str]:
    """Run a machine gate. Returns (exit_code, stdout, stderr)."""
    python = layout.python if layout.python.exists() else Path(sys.executable)
    if kind == "wiki":
        script = layout.factory_root / "skills" / "hl-wiki-merge" / "scripts" / "validate_llm_wiki.py"
        args = [str(python), str(script), "--wiki-root", str(layout.wiki)]
    elif kind == "workspace":
        script = layout.factory_root / "skills" / "hl-feature-workspace" / "scripts" / "feature_workspace.py"
        args = [str(python), str(script), "validate", "--registry", str(layout.registry)]
    elif kind == "all":
        codes: list[int] = []
        outputs: list[str] = []
        for sub in ("wiki", "workspace"):
            code, out, err = run_gate(layout, sub)
            codes.append(code)
            outputs.append(f"[{sub}] {out}{err}")
        return (0 if all(code == 0 for code in codes) else 1), "\n".join(outputs), ""
    else:
        return 2, "", f"unknown gate: {kind}"

    if not script.is_file():
        return 1, "", f"gate script not found: {script}"
    try:
        completed = subprocess.run(
            args,
            cwd=str(layout.work),
            capture_output=True,
            text=True,
            timeout=180,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, "", f"failed to run gate: {exc}"
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def run_doctor(work: Path, *, strict: bool = False, skip_gates: bool = False) -> DoctorResult:
    result = DoctorResult()
    work = work.resolve()

    if not work.is_dir():
        result.add("fail", "WORK_MISSING", f"work directory not found: {work}", "create it or pass --work")
        return result

    try:
        config = config_mod.load_config(work)
    except util.FactoryError as exc:
        result.add("fail", "CONFIG_MISSING", str(exc), "run: factory init --work <path>")
        return result

    errors, warnings = config_mod.validate_config(config)
    for message in errors:
        result.add("fail", "CONFIG_INVALID", message, "fix .factory/factory.yaml")
    for message in warnings:
        result.add("warn", "CONFIG_WARNING", message, "fill it in or accept the risk")
    if errors:
        return result

    local = config_mod.load_local(work)
    if not local:
        result.add("warn", "LOCAL_MISSING", ".factory/local.yaml is missing", "run factory init again or factory install")
    layout = build_layout(work, config, local)

    for label, value in (("factory_root", local.get("factory_root")), ("python", local.get("python"))):
        if not value:
            result.add("fail", f"LOCAL_{label.upper()}_MISSING", f"local.yaml is missing {label}", "re-run factory init")
    if layout.factory_root and not layout.factory_root.is_dir():
        result.add("fail", "FACTORY_ROOT_MISSING", f"factory checkout not found: {layout.factory_root}", "update local.yaml factory_root")
    if layout.python and not Path(layout.python).exists():
        result.add("fail", "PYTHON_MISSING", f"configured python not found: {layout.python}", "update local.yaml python")
    else:
        ok, detail = python_has_yaml(layout.python)
        if ok:
            result.add("ok", "PYTHON_YAML", f"python has PyYAML ({detail})")
        else:
            result.add("fail", "PYTHON_YAML", f"python cannot import yaml: {detail}", "install PyYAML for that interpreter")

    current_version = util.factory_version()
    satisfied, reason = version_satisfies(current_version, str((config.get("factory") or {}).get("version") or ""))
    if satisfied:
        result.add("ok", "FACTORY_VERSION", f"factory {current_version} satisfies {config['factory'].get('version')}")
    else:
        result.add("fail", "FACTORY_VERSION", f"factory version mismatch: {reason}", "run factory upgrade or adjust factory.version")

    missing = missing_layout_paths(layout)
    if missing:
        for path in missing:
            result.add("fail", "LAYOUT_MISSING", f"required path missing: {path}", "re-run factory init --force or create it")
    else:
        result.add("ok", "LAYOUT", "work repo layout present")

    if layout.code.exists():
        result.add("ok", "CODE_ROOT", f"code root: {layout.code}")
    else:
        result.add("fail", "CODE_ROOT_MISSING", f"code root missing: {layout.code}", "create code/ or fix repo settings")

    agents_md = work / "AGENTS.md"
    if agents_md.is_file():
        result.add("ok", "AGENTS_MD", "AGENTS.md present")
    else:
        result.add("warn", "AGENTS_MD_MISSING", "AGENTS.md missing", "re-run factory init")

    if util.is_git_repo(work):
        result.add("ok", "GIT", "work repo is a git repository")
    else:
        result.add("warn", "GIT_MISSING", "work directory is not a git repository", "git init and commit after doctor passes")

    state = config_mod.load_state(work)
    expected_hash = util.sha256_file(layout.workflow_profile) if layout.workflow_profile.is_file() else ""
    recorded_hash = str(state.get("profile_hash") or "")
    if not layout.workflow_profile.is_file():
        result.add("fail", "PROFILE_MISSING", f"workflow profile missing: {layout.workflow_profile}", "run factory upgrade --apply")
    elif recorded_hash and expected_hash != recorded_hash:
        result.add(
            "fail",
            "PROFILE_DRIFT",
            "workflow-profile.md differs from the hash recorded at generation time",
            "edit factory.yaml, then run factory upgrade --apply; never hand-edit the profile",
        )
    else:
        result.add("ok", "PROFILE", "workflow profile matches recorded hash")

    baseline = layout.baseline_evidence
    if baseline.is_file():
        text = baseline.read_text(encoding="utf-8", errors="replace")
        if "Status: pending" in text or "状态: pending" in text:
            result.add("warn", "BASELINE_PENDING", "init baseline evidence is still pending", "run the configured commands once and record the results")
        else:
            result.add("ok", "BASELINE", "baseline evidence recorded")
    else:
        result.add("warn", "BASELINE_MISSING", "baseline evidence file missing", "re-run factory init")

    for key in ("test", "verify"):
        if not (config.get("commands") or {}).get(key):
            result.add("warn", f"COMMAND_{key.upper()}_EMPTY", f"commands.{key} is empty", "configure real commands before implementation")

    if not skip_gates:
        if (layout.factory_root / "skills").is_dir():
            for kind in ("wiki", "workspace"):
                code, out, err = run_gate(layout, kind)
                if code == 0:
                    result.add("ok", f"GATE_{kind.upper()}", f"{kind} gate passed")
                else:
                    detail = (err or out or "").strip().splitlines()
                    summary = detail[0] if detail else f"exit {code}"
                    result.add("fail", f"GATE_{kind.upper()}", f"{kind} gate failed: {summary}", f"run: factory gate {kind} --work {work}")
        else:
            result.add("warn", "GATES_SKIPPED", "skills directory not found; gates skipped", "check factory_root")

    if strict and result.warnings:
        return result
    return result


def exit_code(result: DoctorResult, strict: bool = False) -> int:
    if result.errors:
        return 1
    if strict and result.warnings:
        return 2
    return 0
