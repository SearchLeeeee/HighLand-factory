#!/usr/bin/env python3
"""HighLand-factory engine CLI.

Usage examples:
  factory init --work <path> [--answers answers.yaml] [--dry-run]
  factory adopt --work <path> --code <code-repo> [--wiki wiki]
  factory doctor --work <path> [--strict]
  factory upgrade --work <path> [--check | --apply]
  factory status --work <path>
  factory resolve --work <path> --json
  factory gate wiki --work <path>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from factorylib import commands, doctor, maintenance, util  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="factory",
        description="HighLand-factory engine: initialize, adopt, check and upgrade a work repo.",
    )
    parser.add_argument("--version", action="version", version=f"HighLand-factory {util.factory_version()}")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a new work repo from templates")
    init.add_argument("--work", required=True, help="work repo directory (created if missing)")
    init.add_argument("--answers", help="YAML file with project answers (partial factory.yaml)")
    init.add_argument("--mode", choices=("new", "adopt"), default="new")
    init.add_argument("--code", help="existing code repo path (enables mono/split detection)")
    init.add_argument("--wiki", help="wiki folder inside the work repo (default: auto-detect)")
    init.add_argument("--python", help="interpreter with PyYAML recorded in local.yaml")
    init.add_argument("--force", action="store_true", help="overwrite planned files (use with care)")
    init.add_argument("--dry-run", action="store_true", help="print the write plan without touching disk")
    init.add_argument("--json", action="store_true", help="machine-readable output")
    init.set_defaults(func=commands.cmd_init)

    adopt = sub.add_parser("adopt", help="attach the factory to an existing repo (split-mode friendly)")
    adopt.add_argument("--work", required=True, help="existing work repo directory (usually the docs/wiki repo)")
    adopt.add_argument("--code", required=True, help="existing code repo path")
    adopt.add_argument("--wiki", help="existing wiki folder inside the work repo (default: auto-detect)")
    adopt.add_argument("--answers", help="YAML file with project answers")
    adopt.add_argument("--python", help="interpreter with PyYAML recorded in local.yaml")
    adopt.add_argument("--force", action="store_true")
    adopt.add_argument("--dry-run", action="store_true")
    adopt.add_argument("--json", action="store_true")
    adopt.set_defaults(func=commands.cmd_adopt)

    check = sub.add_parser("doctor", help="validate config, layout, digest and machine gates")
    check.add_argument("--work", required=True)
    check.add_argument("--strict", action="store_true", help="treat warnings as failures")
    check.add_argument("--skip-gates", action="store_true", help="skip wiki/feature-workspace gates")
    check.add_argument("--json", action="store_true")
    check.set_defaults(func=commands.cmd_doctor)

    upgrade = sub.add_parser("upgrade", help="refresh generated files from the current factory templates")
    upgrade.add_argument("--work", required=True)
    upgrade.add_argument("--check", action="store_true", help="report drift; exit 1 when refresh is needed")
    upgrade.add_argument("--apply", action="store_true", help="apply the refresh")
    upgrade.add_argument("--dry-run", action="store_true")
    upgrade.add_argument("--json", action="store_true")
    upgrade.set_defaults(func=commands.cmd_upgrade)

    status = sub.add_parser("status", help="print a short project/workflow summary")
    status.add_argument("--work", required=True)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=commands.cmd_status)

    resolve = sub.add_parser("resolve", help="print resolved absolute paths")
    resolve.add_argument("--work", required=True)
    resolve.add_argument("--json", action="store_true")
    resolve.set_defaults(func=commands.cmd_resolve)

    gate = sub.add_parser("gate", help="run a machine gate")
    gate.add_argument("kind", choices=("wiki", "workspace", "all"))
    gate.add_argument("--work", required=True)
    gate.add_argument("--json", action="store_true")
    gate.set_defaults(func=commands.cmd_gate)

    access = sub.add_parser("maintenance-check", help="check access to the project mutation lease")
    access.add_argument("--work", required=True)
    access.add_argument("--token", help="owned token; defaults to FACTORY_MAINTENANCE_TOKEN")
    access.set_defaults(func=_maintenance_check)

    lock = sub.add_parser("maintenance-lock", help="acquire, inspect or release a cooperative mutation lease")
    lock.add_argument("--work", required=True)
    lock.add_argument("--action", required=True, choices=("acquire", "release", "status"))
    lock.add_argument("--owner", help="writer or session identifier (required for acquire)")
    lock.add_argument("--purpose", default="workflow", help="why this writer needs the project")
    lock.add_argument("--token", help="exact owned token (required for release)")
    lock.set_defaults(func=_maintenance_lock)

    return parser


def _maintenance_check(args: argparse.Namespace) -> int:
    maintenance.check_access(Path(args.work), args.token)
    util.print_json({"ok": True, "work": str(Path(args.work).expanduser().resolve())})
    return 0


def _maintenance_lock(args: argparse.Namespace) -> int:
    work = Path(args.work)
    if args.action == "acquire":
        if not args.owner:
            raise util.FactoryError("maintenance-lock acquire requires --owner")
        util.print_json(maintenance.acquire(work, args.owner, args.purpose))
    elif args.action == "release":
        if not args.token:
            raise util.FactoryError("maintenance-lock release requires --token")
        maintenance.release(work, args.token)
        util.print_json({"released": True})
    else:
        util.print_json({"leases": maintenance.status(work)})
    return 0


def _extra_mutation_roots(args: argparse.Namespace) -> list[Path]:
    """Reserve an adoption target before its configuration has been written."""
    work = Path(args.work).expanduser().resolve()
    roots = []
    if getattr(args, "code", None):
        roots.append(Path(args.code).expanduser().resolve())
    if getattr(args, "answers", None):
        values = util.load_yaml_file(Path(args.answers).expanduser().resolve())
        repo = values.get("repo", {}) if isinstance(values, dict) else {}
        if isinstance(repo, dict):
            for name in ("code_external", "code_path", "wiki_path"):
                raw = repo.get(name)
                if isinstance(raw, str) and raw:
                    path = Path(raw).expanduser()
                    roots.append((path if path.is_absolute() else work / path).resolve())
    return roots


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        mutating = args.command in {"init", "adopt", "upgrade"} and not (
            getattr(args, "dry_run", False) or getattr(args, "check", False)
        )
        if mutating:
            work = Path(args.work).expanduser().resolve()
            if (args.command == "adopt" or getattr(args, "mode", None) == "adopt") and not work.is_dir():
                raise util.FactoryError(f"adopt requires an existing work directory: {work}")
            with maintenance.mutation_guard(
                work, purpose=f"workflow:factory-{args.command}",
                extra_roots=_extra_mutation_roots(args), allow_refactor=False,
            ):
                return int(args.func(args))
        return int(args.func(args))
    except util.FactoryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
