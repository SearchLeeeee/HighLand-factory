"""Recover an explicitly enrolled scope from the current registered Initiative or Leaf."""
from __future__ import annotations

from contextlib import closing
import os
from pathlib import Path
import re
import sqlite3

from . import config, layout, util


def registry_path(args):
    if args.registry:
        return args.registry.resolve()
    return layout.build_layout(args.work, config.load_config(args.work)).registry.resolve()


def registered(entries, ident, directory):
    if not isinstance(entries, list):
        raise util.FactoryError(f"invalid registry entries while resolving {ident}")
    matches = [entry for entry in entries if isinstance(entry, dict) and entry.get("id") == ident]
    if len(matches) != 1:
        raise util.FactoryError(f"expected one registered task with ID {ident}")
    entry = matches[0]
    if entry.get("manifest"):
        path = (directory / entry["manifest"]).resolve()
        entry, directory = util.load_yaml_file(path), path.parent
    if not isinstance(entry, dict) or entry.get("id") != ident:
        raise util.FactoryError(f"manifest ID does not match registered ID {ident}")
    return entry, directory


def target(args):
    if not re.fullmatch(r"I[0-9]{3,}(?:-F[0-9]{2,})?", args.scope):
        raise util.FactoryError("use the full registered Initiative or Feature ID, e.g. I005 or I005-F02")
    path = registry_path(args)
    registry = util.load_yaml_file(path)
    if not isinstance(registry, dict):
        raise util.FactoryError(f"expected a registry mapping in {path}")
    owner = args.scope.partition("-")[0]
    initiative, directory = registered(registry.get("initiatives", []), owner, path.parent)
    if args.scope != owner:
        registered(initiative.get("features", []), args.scope, directory)
    return os.path.normcase(str(path)), owner


def index_path(work):
    return work.resolve() / ".factory" / "analysis" / "flow-scopes.sqlite3"


def live_binding(row):
    records, flow, started = row["records"], row["flow"], row["started"]
    path = Path(records) / flow / "flow.sqlite3"
    if not path.is_file():
        return False
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=20)) as db:
            return db.execute("SELECT 1 FROM flow WHERE name=? AND started=? AND sealed IS NULL",
                              (flow, started)).fetchone() is not None
    except sqlite3.Error as exc:
        raise util.FactoryError(f"cannot verify scoped recording {flow}: {exc}") from exc


def attach_index(db, work):
    path = index_path(work)
    path.parent.mkdir(parents=True, exist_ok=True)
    db.execute("ATTACH DATABASE ? AS routes", (str(path),))


def enrollment(db):
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='enrollment'").fetchone():
        return db.execute("SELECT * FROM enrollment").fetchone()
    return None


def declare(db, kind, registry):
    db.execute("CREATE TABLE enrollment(kind TEXT, registry TEXT, scope TEXT)")
    db.execute("INSERT INTO enrollment VALUES(?,?,NULL)", (kind, registry))


def bind(db, args, records, registry, owner):
    """Commit the authorized scope and its project-local locator in one transaction."""
    kind = "initiative" if owner == args.scope else "feature"
    prior = enrollment(db)
    if args.action == "start":
        declare(db, kind, registry)
    elif (not prior or prior["kind"] != kind or prior["registry"] != registry
          or prior["scope"] not in (None, args.scope)):
        raise util.FactoryError("binding must match the scope authorized when this flow started")
    db.execute("CREATE TABLE IF NOT EXISTS routes.binding(registry TEXT, owner TEXT, scope TEXT, "
               "records TEXT, flow TEXT, started TEXT, PRIMARY KEY(registry,scope))")
    started = db.execute("SELECT started FROM flow").fetchone()[0]
    # Sibling Leaf recordings may coexist. A parent and its Leaf share one enrollment.
    rows = db.execute("SELECT * FROM routes.binding WHERE registry=? AND owner=? "
                      "AND (scope IN (?,?) OR owner=?)", (registry, owner, args.scope, owner, args.scope))
    for row in rows:
        if (Path(row["records"]), row["flow"], row["started"]) == (records, args.flow, started):
            continue
        if live_binding(row):
            raise util.FactoryError(f"scope overlaps open recording {row['flow']} for {row['scope']}")
    db.execute("UPDATE enrollment SET scope=?", (args.scope,))
    db.execute("INSERT OR REPLACE INTO routes.binding VALUES(?,?,?,?,?,?)",
               (registry, owner, args.scope, str(records), args.flow, started))


def lookup(args):
    registry, owner = target(args)
    result = {"target": args.scope, "flow": None}
    path = index_path(args.work)
    if not path.is_file():
        return result
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=20)) as db:
        db.row_factory = sqlite3.Row
        # A rejected first registration can leave an empty index file.
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='binding'").fetchone():
            return result
        rows = db.execute("SELECT * FROM binding WHERE registry=? AND owner=? AND scope IN (?,?)",
                          (registry, owner, args.scope, owner))
        matches = [row for row in rows if live_binding(row)]
    if len(matches) > 1:
        raise util.FactoryError("ambiguous open recordings for this target")
    if matches:
        row = matches[0]
        result.update(flow=row["flow"], scope=row["scope"], records=row["records"])
    return result
