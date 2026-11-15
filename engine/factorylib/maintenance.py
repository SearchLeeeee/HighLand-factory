"""Cooperative project mutation leases shared by maintenance and workflow writers.

The protocol coordinates factory entry points, including linked worktrees and
split repositories. It is not an operating-system write barrier. Leases survive
process exit so a review pause can keep the project reserved; there is no TTL or
automatic stale-owner deletion.
"""

from __future__ import annotations

import contextlib
import json
import os
import secrets
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

from . import config, util

LOCK_NAME = "factory-maintenance.lock"
TOKEN_ENV = "FACTORY_MAINTENANCE_TOKEN"


class MaintenanceError(util.FactoryError):
    """A conflicting, missing, or unreadable mutation lease."""


def _git_common(path: Path) -> Path | None:
    if not path.is_dir():
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, timeout=15,
        )
    except FileNotFoundError:
        return None
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MaintenanceError(f"cannot identify repository for {path}: {exc}") from exc
    if result.returncode:
        return None
    common = Path(result.stdout.strip())
    return (path / common).resolve() if not common.is_absolute() else common.resolve()


def _project_roots(work: Path) -> list[Path]:
    roots = [work]
    if config.config_path(work).is_file():
        values = config.load_config(work)
        repo = values.get("repo", {})
        if not isinstance(repo, dict):
            raise MaintenanceError("repo configuration must be a mapping")
        code = repo.get("code_external") if repo.get("mode") == "split" else repo.get("code_path", "code")
        for raw in (code, repo.get("wiki_path", "wiki")):
            if raw:
                path = Path(str(raw)).expanduser()
                roots.append((path if path.is_absolute() else work / path).resolve())
    return roots


def _primary(work: Path) -> Path:
    return work.resolve() / ".factory" / LOCK_NAME


def resolve_lock_paths(work: Path, extra_roots: Sequence[Path] = ()) -> list[Path]:
    """Return stable per-work and shared repository lock locations.

    Existing worktrees share their Git common directory. A split code directory
    without Git still receives a directory-local lease, so two work repos using
    that directory cannot both acquire it.
    """
    work = Path(work).expanduser().resolve()
    paths = {_primary(work)}
    for root in [*_project_roots(work), *(Path(p).expanduser().resolve() for p in extra_roots)]:
        common = _git_common(root)
        if common is not None:
            paths.add(common / LOCK_NAME)
        elif not root.is_relative_to(work) and root.is_dir():
            paths.add(root / ".factory" / LOCK_NAME)
    return sorted(paths, key=lambda p: os.path.normcase(str(p)))


def _read(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise MaintenanceError(f"unreadable mutation lease at {path}; inspect its owner before recovery") from exc
    if not isinstance(value, dict) or value.get("schema") != 1 or not value.get("token"):
        raise MaintenanceError(f"invalid mutation lease at {path}; inspect its owner before recovery")
    return value


def _token(token: str | None) -> str | None:
    return token if token is not None else os.environ.get(TOKEN_ENV)


def status(work: Path) -> list[dict[str, Any]]:
    """Read reservations without exposing the token required to release them."""
    result = []
    for path in resolve_lock_paths(work):
        record = _read(path)
        if record is not None:
            result.append({"path": str(path), **{k: v for k, v in record.items() if k != "token"}})
    return result


def check_access(work: Path, token: str | None = None) -> None:
    supplied = _token(token)
    records = [(path, _read(path)) for path in resolve_lock_paths(work)]
    held = [(path, value) for path, value in records if value is not None]
    for path, value in held:
        if not supplied or not secrets.compare_digest(str(value["token"]), supplied):
            raise MaintenanceError(
                f"project reserved by {value.get('owner', 'unknown')} "
                f"for {value.get('purpose', 'mutation')} at {path}; "
                "resume or release that owned run before another writer starts"
            )
    if supplied:
        if not held:
            raise MaintenanceError("the supplied mutation token has no active reservation")
        # An authorized token must cover every resource named by its lease.
        for _, value in held:
            for raw in value.get("lock_paths", []):
                peer = _read(Path(raw))
                if peer is None or not secrets.compare_digest(str(peer["token"]), supplied):
                    raise MaintenanceError("mutation reservation is incomplete; pause and inspect the owned run")
        current = {str(path) for path, _ in records}
        covered = {str(raw) for _, value in held for raw in value.get("lock_paths", [])}
        if not current.issubset(covered):
            raise MaintenanceError("project repository layout changed after reservation; reacquire before writing")


def acquire(
    work: Path, owner: str, purpose: str, extra_roots: Sequence[Path] = (),
) -> dict[str, Any]:
    """Reserve all resources atomically or remove only this attempt's partial files."""
    if not owner.strip() or not purpose.strip():
        raise MaintenanceError("mutation owner and purpose must be nonempty")
    work = Path(work).expanduser().resolve()
    paths = resolve_lock_paths(work, extra_roots)
    record = {
        "schema": 1, "token": secrets.token_hex(24), "owner": owner,
        "purpose": purpose, "work": str(work), "pid": os.getpid(),
        "host": socket.gethostname(), "created_at": datetime.now(timezone.utc).isoformat(),
        "lock_paths": [str(path) for path in paths],
    }
    payload = (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    created: list[Path] = []
    try:
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError as exc:
                holder = _read(path)
                detail = holder.get("owner", "unknown") if holder else "another writer"
                raise MaintenanceError(f"project reservation already held by {detail} at {path}") from exc
            created.append(path)
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
    except (OSError, MaintenanceError):
        for path in reversed(created):
            # Only files created by this attempt are removed; never a peer's lease.
            with contextlib.suppress(FileNotFoundError):
                path.unlink()
        raise
    return record


def release(work: Path, token: str) -> None:
    """Release an exact owned reservation, including an interrupted acquisition.

    Missing peer files may come from an interrupted release. An explicit owner
    token can clean those remnants; unreadable or differently owned peers still
    fail closed before anything is removed.
    """
    if not token:
        raise MaintenanceError("release requires the owned mutation token")
    work = Path(work).expanduser().resolve()
    primary = _read(_primary(work))
    if primary is None:
        for path in resolve_lock_paths(work):
            candidate = _read(path)
            if candidate and candidate.get("work") == str(work) and secrets.compare_digest(str(candidate["token"]), token):
                primary = candidate
                break
    if primary is None:
        raise MaintenanceError("no owned project reservation exists to release")
    if not secrets.compare_digest(str(primary["token"]), token):
        raise MaintenanceError("release token does not own this project reservation")
    paths = [Path(raw) for raw in primary.get("lock_paths", [])]
    if not paths or _primary(Path(work)) not in paths:
        raise MaintenanceError("reservation has an invalid resource list")
    owned_paths = []
    for path in paths:
        if not path.is_absolute() or path.name != LOCK_NAME:
            raise MaintenanceError("reservation has an invalid resource path")
        record = _read(path)
        if record is not None and not secrets.compare_digest(str(record["token"]), token):
            raise MaintenanceError("reservation changed owner; nothing was released")
        if record is not None:
            owned_paths.append(path)
    # Delete the primary marker last so interrupted release remains diagnosable.
    # A missing peer can be acquired by another work repo after the check.
    # Never unlink a resource that was absent from this owner's validated set.
    owned_paths.sort(key=lambda p: p == _primary(Path(work)))
    for path in owned_paths:
        with contextlib.suppress(FileNotFoundError):
            path.unlink()


@contextlib.contextmanager
def mutation_guard(
    work: Path, token: str | None = None, purpose: str = "mutation",
    extra_roots: Sequence[Path] = (), allow_refactor: bool = True,
) -> Iterator[dict[str, Any]]:
    """Borrow an authorized lease or reserve/release a short mutation operation."""
    work = Path(work).expanduser().resolve()
    supplied = _token(token)
    if supplied:
        check_access(work, supplied)
        lease = _read(_primary(work))
        if lease is None:
            raise MaintenanceError("owned mutation reservation is missing its project marker")
        if not allow_refactor and str(lease.get("purpose", "")).startswith("refactor"):
            raise MaintenanceError("Feature lifecycle writes are blocked during refactor; pause the maintenance run first")
        yield lease
        return
    lease = acquire(work, owner=f"process-{os.getpid()}", purpose=purpose, extra_roots=extra_roots)
    previous = os.environ.get(TOKEN_ENV)
    os.environ[TOKEN_ENV] = lease["token"]
    try:
        yield lease
    finally:
        if previous is None:
            os.environ.pop(TOKEN_ENV, None)
        else:
            os.environ[TOKEN_ENV] = previous
        release(work, lease["token"])


def find_work(start: Path) -> Path | None:
    """Locate the configured project owning a lifecycle manifest or registry."""
    # Preserve the referring project's ownership when a manifest directory is
    # a symlink/junction. Resolving first can discard that project and silently
    # dispatch a lifecycle write as an unguarded standalone operation.
    lexical = Path(os.path.abspath(Path(start).expanduser()))
    for path in (lexical, lexical.resolve()):
        if not path.is_dir():
            path = path.parent
        for candidate in (path, *path.parents):
            if config.config_path(candidate).is_file():
                return candidate.resolve()
    return None
