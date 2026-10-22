import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "trace_feature_history.py"


class TraceFeatureHistoryTests(unittest.TestCase):
    def run_tool(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def fixture(self, root: Path) -> tuple[Path, Path]:
        retained = root / "initiatives" / "i007" / "features" / "feat-i007-f02-example"
        retained.mkdir(parents=True)
        (retained / "discussion").mkdir()
        (retained / "discussion" / "workbench.md").write_text("# Q-004\nBecause hashes are deterministic.\n", encoding="utf-8")
        (retained / "RETAINED_HISTORY.md").write_text("Non-authoritative history.\n", encoding="utf-8")
        (retained / "history-route.yaml").write_text(
            "schema_version: '1.0'\nstatus: retained-history\nauthority: non-authoritative\n"
            "feature_id: I007-F02\ncanonical_targets:\n  - implementation/backend/example.md\n"
            "routes:\n  - topic: deterministic revision identity\n"
            "    question_terms:\n      - content hash\n      - deterministic revision\n"
            "    canonical_targets:\n      - implementation/backend/example.md\n"
            "    source_refs:\n      - path: discussion/workbench.md\n        headings: [Q-004]\n",
            encoding="utf-8",
        )
        initiative = root / "initiatives" / "i007" / "initiative.yaml"
        initiative.write_text(
            "id: I007\ntitle: Example\nstate: completed\nfeatures:\n"
            "  - id: I007-F02\n    title: Example Feature\n    leaf: true\n"
            "    phase: merged\n    state: completed\n"
            "    canonical_docs:\n      - implementation/backend/example.md\n"
            "    merge_evidence:\n      - evidence/merge.md\n"
            "    retained_source:\n      path: features/feat-i007-f02-example\n"
            "      marker: RETAINED_HISTORY.md\n      route: history-route.yaml\n"
            "      checksum_manifest: history-checksums.sha256\n",
            encoding="utf-8",
        )
        registry = root / "registry.yaml"
        registry.write_text(
            "schema_version: '1.0'\ninitiatives:\n  - id: I007\n    manifest: initiatives/i007/initiative.yaml\n",
            encoding="utf-8",
        )
        return registry, retained

    def test_locate_then_route_from_authority_question(self):
        with tempfile.TemporaryDirectory() as temp:
            registry, retained = self.fixture(Path(temp))
            authority_doc = Path("implementation/backend/example.md")
            located = self.run_tool(
                "locate", "--registry", str(registry),
                "--authority-doc", str(authority_doc),
                "--question", "Why does revision use a content hash?",
            )
            self.assertEqual(located.returncode, 0, located.stderr)
            candidate = json.loads(located.stdout)["candidates"][0]
            self.assertEqual(candidate["feature_id"], "I007-F02")
            self.assertEqual(Path(candidate["retained_root"]), retained.resolve())

            routed = self.run_tool(
                "route", "--route-file", candidate["route_file"],
                "--question", "Why does revision use a content hash?",
            )
            self.assertEqual(routed.returncode, 0, routed.stderr)
            payload = json.loads(routed.stdout)
            self.assertTrue(payload["matched"])
            self.assertEqual(payload["routes"][0]["source_refs"][0]["path"], "discussion/workbench.md")

    def test_unmapped_authority_does_not_scan_all_history(self):
        with tempfile.TemporaryDirectory() as temp:
            registry, _ = self.fixture(Path(temp))
            result = self.run_tool(
                "locate", "--registry", str(registry),
                "--authority-doc", "implementation/frontend/unrelated.md",
                "--question", "Why?",
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["candidates"], [])

    def test_checksum_and_verify_detect_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            _, retained = self.fixture(Path(temp))
            manifest = retained / "history-checksums.sha256"
            generated = self.run_tool(
                "checksum", "--root", str(retained), "--output", str(manifest)
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)
            verified = self.run_tool(
                "verify", "--root", str(retained), "--manifest", str(manifest)
            )
            self.assertEqual(verified.returncode, 0, verified.stderr)
            self.assertTrue(json.loads(verified.stdout)["passed"])

            (retained / "discussion" / "workbench.md").write_text("changed\n", encoding="utf-8")
            failed = self.run_tool(
                "verify", "--root", str(retained), "--manifest", str(manifest)
            )
            self.assertEqual(failed.returncode, 1)
            self.assertFalse(json.loads(failed.stdout)["passed"])


if __name__ == "__main__":
    unittest.main()
