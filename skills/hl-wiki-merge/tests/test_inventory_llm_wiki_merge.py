#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "inventory_llm_wiki_merge.py"


class InventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_json(self, source: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--source", str(source), "--format", "json"],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_json_inventory_excludes_profiles_and_retained_markers(self) -> None:
        eligible = self.write("docs/current.md", "# Current\n")
        excluded = self.write("code-ai/profile.md", "# Profile\n")
        marker = self.write("RETAINED_HISTORY.md", "# History\n")
        self.write("notes.txt", "ignored")
        completed = self.run_json(self.root)
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(payload["eligible"], [str(eligible)])
        self.assertIn(str(excluded), payload["skipped"])
        self.assertIn(str(marker), payload["skipped"])
        self.assertEqual(len(payload["source_sha256"]), 64)
        self.assertEqual(payload["source_kind"], "directory")
        self.assertEqual(len(payload["ignored"]), 1)

    def test_merged_feature_is_history_and_cannot_be_reimported(self) -> None:
        feature = self.root / "feature"
        feature.mkdir()
        (feature / "feature.yaml").write_text("phase: merged\nstate: completed\n", encoding="utf-8")
        source = feature / "docs" / "contract.md"
        source.parent.mkdir()
        source.write_text("# Retained contract\n", encoding="utf-8")
        marker = feature / "RETAINED_HISTORY.md"
        marker.write_text("# Historical\n", encoding="utf-8")
        completed = self.run_json(feature)
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 2)
        self.assertTrue(payload["source_is_merged_feature"])
        self.assertEqual(payload["eligible"], [])
        self.assertIn(str(source), payload["merged_history"])
        self.assertIn(str(marker), payload["skipped"])

    def test_current_wiki_excludes_registered_roots_without_hashing_history(self) -> None:
        self.write(
            ".factory/factory.yaml",
            "repo:\n  wiki_path: docs/current\nworkflow:\n  process_workspaces: [temporary/audit]\n",
        )
        home = self.write("docs/current/README.md", "# Current\n")
        guide = self.write("docs/current/product-workspace/guide.md", "# Current workspace concept\n")
        profile = self.write("docs/current/code-ai/profile.md", "# Current agent contract\n")
        extra = self.write("docs/current/temporary/audit/history.md", "# Old decision\n")
        history = self.write("docs/current/refactor-workspace/run/report.md", "# Process\n")
        # Invalid text in process history must never become current scan input.
        history.write_bytes(b"\xff historical bytes")
        command = [sys.executable, str(SCRIPT), "--wiki-root", str(self.root / "docs/current"), "--format", "json"]
        first = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        payload = json.loads(first.stdout)
        self.assertEqual(set(payload["eligible"]), {str(home), str(guide), str(profile)})
        self.assertEqual(set(payload["skipped"]), {str(history), str(extra)})
        self.assertEqual(payload["source_kind"], "canonical-wiki")
        self.assertIn("temporary/audit", payload["process_workspaces"])
        history.write_bytes(b"\xfe different history")
        second = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(payload["source_sha256"], json.loads(second.stdout)["source_sha256"])

    def test_explicit_staged_process_source_remains_mergeable(self) -> None:
        source = self.write("quick-workspace/completed/change.md", "# Approved staged documentation\n")
        completed = self.run_json(source)
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(payload["eligible"], [str(source)])

    def test_process_option_cannot_silently_change_staged_merge_rules(self) -> None:
        source = self.write("staged.md", "# Staged\n")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--source", str(source), "--process-workspace", "temporary"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("--process-workspace requires --wiki-root", completed.stderr)


if __name__ == "__main__":
    unittest.main()
