#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
from validate_llm_wiki import validate_wiki  # noqa: E402


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root

    def write(self, relative: str, text: str, bom_crlf: bool = False) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if bom_crlf:
            path.write_bytes(b"\xef\xbb\xbf" + text.replace("\n", "\r\n").encode())
        else:
            path.write_text(text, encoding="utf-8")

    def asset(self, relative: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"asset")


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.wiki = Fixture(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def codes(result) -> set[str]:
        return {item.code for item in result.errors}

    def test_pass_handles_bom_crlf_encoding_query_images_and_code(self) -> None:
        tick = chr(96)
        self.wiki.write(
            "README.md",
            "# Home\n[Area](area/README.md?view=all#area)\n"
            "![Chart](assets/chart%20one.png)\n"
            + tick + "[[ignored]] and [ignored](missing.md)" + tick + "\n"
            + tick * 3 + "md\n[[ignored-too]]\n[ignored](missing.md)\n" + tick * 3 + "\n",
            bom_crlf=True,
        )
        self.wiki.write("area/README.md", "# Area\n[Topic](topic.md#ascii-heading)\n")
        self.wiki.write("area/topic.md", "# ASCII heading\n")
        self.wiki.asset("assets/chart one.png")
        result = validate_wiki(self.root)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual((result.files_scanned, result.links_checked), (3, 3))

    def test_wikilink_broken_link_and_legacy_references_fail(self) -> None:
        tick = chr(96)
        self.wiki.write(
            "README.md",
            "# Home\n[[Topic]]\n[Missing](missing.md)\n"
            + tick + r"decisions\decision-log.md" + tick + "\n"
            "See discussions/archive.md and 04-open-questions.md.\n",
        )
        result = validate_wiki(self.root)
        self.assertTrue(
            {"OBSIDIAN_WIKILINK", "BROKEN_LOCAL_LINK", "LEGACY_REFERENCE"}
            <= self.codes(result)
        )

    def test_feature_workspace_exclusion_and_traversal_failure(self) -> None:
        self.wiki.write(
            "README.md",
            "# Home\n[Area](area.md)\n[Workspace](feature-workspace/README.md)\n",
        )
        self.wiki.write("area.md", "# Area\n")
        self.wiki.write("feature-workspace/README.md", "# Excluded\n[Bad](missing.md)\n")
        result = validate_wiki(self.root)
        self.assertEqual((result.files_scanned, result.files_excluded), (2, 1))
        self.assertTrue(
            {"FEATURE_WORKSPACE_LINK", "FEATURE_WORKSPACE_DISCOVERY"} <= self.codes(result)
        )
        self.assertNotIn("BROKEN_LOCAL_LINK", self.codes(result))

    def test_refactor_history_is_not_scanned_or_required_to_be_reachable(self) -> None:
        self.wiki.write("README.md", "# Current home\n")
        self.wiki.write("refactor-workspace/run-001/report.md", "# Historical\n[Old](missing.md)\n")
        result = validate_wiki(self.root)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual((result.files_scanned, result.files_excluded), (1, 1))
        self.assertIn("refactor-workspace", result.process_workspaces)

    def test_refactor_link_and_normalized_traversal_are_blocked(self) -> None:
        self.wiki.write("README.md", "# Home\n[Current](current.md)\n")
        self.wiki.write(
            "current.md", "# Current\n[History](refactor-workspace/run/report.md)\n"
            "[Back](refactor-workspace/../README.md)\n",
        )
        self.wiki.write("refactor-workspace/run/report.md", "# History\n")
        result = validate_wiki(self.root)
        self.assertEqual([item.code for item in result.errors], ["FEATURE_WORKSPACE_LINK"] * 2)

    def test_custom_nested_root_links_are_not_part_of_navigation(self) -> None:
        self.wiki.write("README.md", "# Home\n[History](process/maintenance/run.md)\n")
        self.wiki.write("process/maintenance/run.md", "# History\n[Old](missing.md)\n")
        cfg = {"workflow": {"process_workspaces": ["process/maintenance"]}}
        result = validate_wiki(self.root, cfg)
        self.assertEqual((result.files_scanned, result.files_excluded), (1, 1))
        self.assertEqual(self.codes(result), {"FEATURE_WORKSPACE_LINK", "FEATURE_WORKSPACE_DISCOVERY"})

    def test_similar_names_and_nested_unregistered_roots_remain_canonical(self) -> None:
        self.wiki.write(
            "README.md", "# Home\n[Concept](concepts/feature-workspace/topic.md)\n"
            "[Guide](workspace-guide.md)\n",
        )
        self.wiki.write("concepts/feature-workspace/topic.md", "# Concept\n")
        self.wiki.write("workspace-guide.md", "# Guide\n[Broken](missing.md)\n")
        self.wiki.write("product-workspace/orphan.md", "# Still canonical\n")
        result = validate_wiki(self.root)
        self.assertEqual((result.files_scanned, result.files_excluded), (4, 0))
        self.assertEqual(self.codes(result), {"BROKEN_LOCAL_LINK", "ORPHAN_MARKDOWN"})

    def test_cli_discovers_configured_process_roots_for_custom_wiki_path(self) -> None:
        self.wiki.write(
            "repo/.factory/factory.yaml",
            "repo:\n  wiki_path: docs/current\nworkflow:\n  process_workspaces: [temporary/audit]\n",
        )
        self.wiki.write("repo/docs/current/README.md", "# Home\n")
        self.wiki.write("repo/docs/current/temporary/audit/report.md", "# History\n[Bad](missing.md)\n")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "validate_llm_wiki.py"), "--wiki-root",
             str(self.root / "repo/docs/current"), "--format", "json"],
            capture_output=True, text=True, check=False,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertEqual((payload["files_scanned"], payload["files_excluded"]), (1, 1))
        self.assertIn("temporary/audit", payload["process_workspaces"])

    def test_invalid_process_registration_never_silently_widens_scan(self) -> None:
        self.wiki.write("README.md", "# Home\n")
        result = validate_wiki(self.root, {"workflow": {"process_workspaces": ["../"]}})
        self.assertEqual(self.codes(result), {"PROCESS_WORKSPACE_CONFIG"})

    def test_explicit_cli_process_root_is_additive(self) -> None:
        self.wiki.write("README.md", "# Home\n")
        self.wiki.write("temporary/audit/run.md", "# History\n")
        self.wiki.write("refactor-workspace/run/report.md", "# History\n")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "validate_llm_wiki.py"), "--wiki-root", str(self.root),
             "--process-workspace", "temporary/audit", "--format", "json"],
            capture_output=True, text=True, check=False,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertEqual(payload["files_excluded"], 2)

    def test_orphan_and_route_deeper_than_three_fail(self) -> None:
        self.wiki.write("README.md", "# Home\n[One](one/README.md)\n")
        self.wiki.write("one/README.md", "# One\n[Two](../two/index.md)\n")
        self.wiki.write("two/index.md", "# Two\n[Three](../three/_index.md)\n")
        self.wiki.write("three/_index.md", "# Three\n[Four](../four.md)\n")
        self.wiki.write("four.md", "# Four\n")
        self.wiki.write("orphan.md", "# Orphan\n")
        result = validate_wiki(self.root)
        paths = {(item.code, item.path) for item in result.errors}
        self.assertIn(("MOC_ROUTE_DEPTH", "four.md"), paths)
        self.assertIn(("ORPHAN_MARKDOWN", "orphan.md"), paths)

    def test_competing_home_and_broken_ascii_anchor_fail(self) -> None:
        self.wiki.write(
            "README.md", "# Home\n[Topic](topic.md#missing)\n[Other](HOME.md)\n"
        )
        self.wiki.write("topic.md", "# Present\n")
        self.wiki.write("HOME.md", "# Other\n")
        result = validate_wiki(self.root)
        self.assertTrue(
            {"COMPETING_HOME", "BROKEN_LOCAL_ANCHOR"} <= self.codes(result)
        )

    def test_non_ascii_anchor_is_warning_only(self) -> None:
        self.wiki.write("README.md", "# Home\n[Topic](topic.md#中文标题)\n")
        self.wiki.write("topic.md", "# 中文标题\n")
        result = validate_wiki(self.root)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual([item.code for item in result.warnings], ["NON_ASCII_ANCHOR"])

    def test_inline_code_feature_workspace_explanation_is_allowed(self) -> None:
        tick = chr(96)
        self.wiki.write("README.md", "# Home\n[Features](features/README.md)\n")
        self.wiki.write(
            "features/README.md",
            "# Features\nManual role: "
            + tick + "feature-workspace/README.md" + tick + "\n",
        )
        result = validate_wiki(self.root)
        self.assertTrue(result.ok, result.errors)

    def test_existing_repository_root_link_passes_without_joining_graph(self) -> None:
        repository = self.root / "repository"
        wiki_root = repository / "wiki"
        wiki = Fixture(wiki_root)
        wiki.write("README.md", "# Home\n[Startup](../.agents/start.md)\n")
        wiki.asset("../.agents/start.md")
        result = validate_wiki(wiki_root)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.files_scanned, 1)

    def test_existing_link_beyond_repository_root_fails(self) -> None:
        repository = self.root / "repository"
        wiki_root = repository / "wiki"
        wiki = Fixture(wiki_root)
        wiki.write("README.md", "# Home\n[Escape](../../outside.md)\n")
        self.wiki.asset("outside.md")
        result = validate_wiki(wiki_root)
        self.assertIn("OUTSIDE_WIKI_LINK", self.codes(result))

    def test_leaf_to_leaf_link_does_not_create_moc_reachability(self) -> None:
        self.wiki.write("README.md", "# Home\n[Leaf A](leaf-a.md)\n")
        self.wiki.write("leaf-a.md", "# Leaf A\n[Leaf B](leaf-b.md)\n")
        self.wiki.write("leaf-b.md", "# Leaf B\n")
        result = validate_wiki(self.root)
        paths = {(item.code, item.path) for item in result.errors}
        self.assertIn(("ORPHAN_MARKDOWN", "leaf-b.md"), paths)

    def test_uppercase_markdown_is_scanned_and_root_directory_link_resolves(self) -> None:
        self.wiki.write("README.md", "# Home\n[Self](./)\n[Topic](TOPIC.MD)\n")
        self.wiki.write("TOPIC.MD", "# Topic\n")
        result = validate_wiki(self.root)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.files_scanned, 2)

    def test_cli_json_receipt_is_ascii_and_keeps_unicode_diagnostics(self) -> None:
        self.wiki.write("README.md", "# Home\n[Missing](missing.md)\n[Topic](topic.md#中文标题)\n")
        self.wiki.write("topic.md", "# 中文标题\n")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "validate_llm_wiki.py"),
             "--wiki-root", str(self.root), "--format", "json"],
            check=False, capture_output=True, text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["files_scanned"], 2)
        self.assertEqual(payload["error_count"], 1)
        self.assertEqual(payload["warning_count"], 1)
        self.assertEqual(payload["warnings"][0]["message"], "non-ASCII anchor is warning-only: #中文标题")
        self.assertNotIn("中文", completed.stdout)

    def test_cli_returns_nonzero_and_prints_summary(self) -> None:
        self.wiki.write("README.md", "# Home\n[Missing](missing.md)\n")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "validate_llm_wiki.py"),
             "--wiki-root", str(self.root)],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("BROKEN_LOCAL_LINK", completed.stdout)
        self.assertIn("Summary:", completed.stdout)
        self.assertTrue(completed.stdout.rstrip().endswith("INVALID"))


    def test_cli_requires_explicit_wiki_root(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "validate_llm_wiki.py")],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("--wiki-root", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)


if __name__ == "__main__":
    unittest.main()
