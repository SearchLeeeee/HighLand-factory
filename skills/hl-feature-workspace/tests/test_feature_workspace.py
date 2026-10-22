import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "feature_workspace.py"


def load_module():
    spec = importlib.util.spec_from_file_location("feature_workspace", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def aligned_consistency_matrix():
    return {
        name: {
            "status": "aligned",
            "owner": name,
            "source_refs": ["discussion/workbench.md"],
            "promotion_targets": [f"implementation/{name}.md"],
        }
        for name in ("business", "architecture", "contract", "code", "testing")
    }


class FeatureWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.fw = load_module()

    def test_scope_gate_thresholds_and_hard_gate(self):
        self.assertEqual(self.fw.scope_verdict([1] * 8, []), "leaf")
        self.assertEqual(self.fw.scope_verdict([2, 2, 2, 1, 1, 1, 1, 1], []), "split-default")
        self.assertEqual(self.fw.scope_verdict([2] * 8, []), "must-split")
        self.assertEqual(self.fw.scope_verdict([0] * 8, ["multiple-business-loops"]), "must-split")

    def test_discussion_entry_rejects_must_split_feature(self):
        feature = {
            "id": "I007-F01",
            "leaf": True,
            "scope_gate": {
                "scores": [2] * 8,
                "hard_gates": [],
                "verdict": "must-split",
            },
        }
        self.assertIn(
            "scope_gate requires splitting before discussion",
            self.fw.discussion_entry_errors(feature),
        )

    def test_split_default_requires_indivisibility_reason(self):
        feature = {
            "id": "I007-F01",
            "leaf": True,
            "scope_gate": {
                "scores": [2, 1, 1, 1, 1, 1, 1, 1],
                "hard_gates": [],
                "verdict": "split-default",
            },
        }
        self.assertTrue(
            any(
                "indivisibility_reason" in error
                for error in self.fw.discussion_entry_errors(feature)
            )
        )
        feature["scope_gate"]["indivisibility_reason"] = "One atomic user-visible contract."
        self.assertEqual(self.fw.discussion_entry_errors(feature), [])

    def test_discussion_phase_requires_completed_initial_decomposition(self):
        feature = {
            "id": "I007-F01",
            "leaf": True,
            "phase": "discussion",
            "state": "in-progress",
            "scope_gate": {
                "scores": [1] * 8,
                "hard_gates": [],
                "verdict": "leaf",
            },
        }
        initiative = {"id": "I007", "features": [feature]}
        self.assertIn(
            "initial decomposition is not completed",
            self.fw.initial_decomposition_errors(initiative),
        )
        initiative["initial_decomposition"] = {
            "status": "completed",
            "feature_ids": ["I007-F01"],
        }
        self.assertEqual(self.fw.initial_decomposition_errors(initiative), [])

    def test_transition_into_discussion_requires_decomposition_and_leaf_gate(self):
        feature = {
            "id": "I007-F01",
            "leaf": True,
            "phase": "scope-gate",
            "state": "in-progress",
            "scope_gate": {
                "scores": [1] * 8,
                "hard_gates": [],
                "verdict": "leaf",
            },
        }
        with self.assertRaisesRegex(ValueError, "initial decomposition"):
            self.fw.transition_feature(
                feature,
                phase="discussion",
                state="in-progress",
                next_action={
                    "skill": "feature-discuss",
                    "instruction": "Discuss the first Leaf Feature",
                },
            )
        updated = self.fw.transition_feature(
            feature,
            phase="discussion",
            state="in-progress",
            next_action={
                "skill": "feature-discuss",
                "instruction": "Discuss the first Leaf Feature",
            },
            initial_decomposition_complete=True,
        )
        self.assertEqual(updated["phase"], "discussion")

    def test_cycle_is_rejected(self):
        initiative = {
            "features": [
                {"id": "I007-F01", "depends_on": ["I007-F02"]},
                {"id": "I007-F02", "depends_on": ["I007-F01"]},
            ]
        }
        errors = self.fw.validate_dependency_graph(initiative)
        self.assertTrue(any("cycle" in error.lower() for error in errors))

    def test_ready_features_respect_dependencies_and_wave(self):
        initiative = {
            "features": [
                {"id": "I007-F01", "state": "completed", "wave": 1, "depends_on": []},
                {"id": "I007-F02", "state": "ready", "wave": 2, "depends_on": ["I007-F01"]},
                {"id": "I007-F03", "state": "ready", "wave": 2, "depends_on": ["I007-F01"]},
                {"id": "I007-F04", "state": "ready", "wave": 3, "depends_on": ["I007-F02"]},
            ]
        }
        self.assertEqual(self.fw.ready_features(initiative), ["I007-F02", "I007-F03"])

    def test_ready_dependency_requires_qualified_merge_ready_closure(self):
        qualified = {
            "id": "I007-F01", "leaf": True, "phase": "ready-to-merge", "state": "ready",
            "wave": 1, "depends_on": [], "acceptance": {"passed": True},
            "consistency_matrix": aligned_consistency_matrix(),
            "closure": {"canonical_docs": ["implementation/example.md"], "validation_evidence": ["pytest -q"], "tombstone_target": "registry.yaml"},
        }
        dependent = {"id": "I007-F02", "leaf": True, "phase": "ready-to-merge", "state": "ready", "wave": 2, "depends_on": ["I007-F01"], "acceptance": {"passed": True}, "consistency_matrix": aligned_consistency_matrix(), "closure": qualified["closure"]}
        initiative = {"features": [qualified, dependent]}
        self.assertEqual(self.fw.ready_features(initiative), ["I007-F01"])
        self.assertEqual(self.fw.merge_readiness_errors(dependent, initiative), [])

        qualified["acceptance"]["passed"] = False
        self.assertEqual(self.fw.ready_features(initiative), ["I007-F01"])
        self.assertTrue(any("dependency I007-F01" in error for error in self.fw.merge_readiness_errors(dependent, initiative)))

    def test_initiative_merge_preflight_requires_passed_integration_testing(self):
        feature = {"id": "I007-F01", "leaf": True, "phase": "ready-to-merge", "state": "ready", "depends_on": [], "acceptance": {"passed": True}, "consistency_matrix": aligned_consistency_matrix(), "closure": {"canonical_docs": ["a"], "validation_evidence": ["b"], "tombstone_target": "c"}}
        initiative = {"id": "I007", "features": [feature]}
        self.assertIn("initiative integration testing handoff is missing", self.fw.initiative_merge_readiness_errors(initiative))
        initiative["integration_testing"] = {"handoff": "integration-testing/handoff.md", "passed": False, "evidence": []}
        self.assertIn("initiative integration testing has not passed", self.fw.initiative_merge_readiness_errors(initiative))
        initiative["integration_testing"]["passed"] = True
        initiative["integration_testing"]["evidence"] = ["integration-testing/evidence.md"]
        self.assertEqual(self.fw.initiative_merge_readiness_errors(initiative), [])

    def test_initiative_merge_preflight_requires_every_active_leaf_ready(self):
        ready = {
            "id": "I007-F01", "leaf": True, "phase": "ready-to-merge", "state": "ready",
            "wave": 1, "depends_on": [], "acceptance": {"passed": True},
            "consistency_matrix": aligned_consistency_matrix(),
            "closure": {"canonical_docs": ["implementation/example.md"], "validation_evidence": ["pytest -q"], "tombstone_target": "registry.yaml"},
        }
        not_ready = {"id": "I007-F02", "leaf": True, "phase": "acceptance", "state": "completed", "wave": 2, "depends_on": ["I007-F01"], "acceptance": {"passed": True}, "consistency_matrix": aligned_consistency_matrix(), "closure": ready["closure"]}
        initiative = {"features": [ready, not_ready, {"id": "I007-F03", "leaf": False, "state": "superseded"}]}
        errors = self.fw.initiative_merge_readiness_errors(initiative)
        self.assertTrue(any(error.startswith("I007-F02:") for error in errors))

        not_ready.update(phase="ready-to-merge", state="ready")
        initiative["integration_testing"] = {"handoff": "integration-testing/handoff.md", "passed": True, "evidence": ["integration-testing/evidence.md"]}
        self.assertEqual(self.fw.initiative_merge_readiness_errors(initiative), [])

    def test_merge_readiness_requires_acceptance_and_closure(self):
        feature = {
            "id": "I007-F01",
            "phase": "ready-to-merge",
            "state": "ready",
            "leaf": True,
            "depends_on": [],
            "blocking_children": [],
            "acceptance": {"passed": True},
            "consistency_matrix": aligned_consistency_matrix(),
            "closure": {
                "canonical_docs": ["implementation/example.md"],
                "validation_evidence": ["pytest -q"],
                "tombstone_target": "registry.yaml",
            },
        }
        self.assertEqual(self.fw.merge_readiness_errors(feature), [])
        feature["acceptance"]["passed"] = False
        self.assertIn("acceptance has not passed", self.fw.merge_readiness_errors(feature))

    def test_progress_report_is_read_only_and_has_next_action(self):
        registry = {
            "initiatives": [
                {
                    "id": "I007",
                    "title": "Example Initiative",
                    "state": "in-progress",
                    "features": [
                        {
                            "id": "I007-F01",
                            "title": "Single Symbol",
                            "phase": "discussion",
                            "state": "in-progress",
                            "next_action": {
                                "skill": "feature-discuss",
                                "instruction": "Continue the feature discussion",
                            },
                        }
                    ],
                }
            ]
        }
        before = repr(registry)
        report = self.fw.render_progress(registry)
        self.assertIn("I007-F01", report)
        self.assertIn("feature-discuss", report)
        self.assertEqual(repr(registry), before)


    def test_progress_reports_initial_decomposition_before_discussion(self):
        registry = {
            "initiatives": [
                {
                    "id": "I007",
                    "title": "New Initiative",
                    "state": "in-progress",
                    "features": [],
                }
            ]
        }
        report = self.fw.render_progress(registry)
        self.assertIn("finalize-decomposition", report)
        self.assertNotIn("feature-discuss", report)

    def test_allocate_ids_never_reuses_cancelled_entries(self):
        registry = {
            "next_initiative_number": 8,
            "initiatives": [{"id": "I007", "state": "cancelled"}],
        }
        self.assertEqual(self.fw.allocate_initiative_id(registry), "I008")
        initiative = {
            "id": "I008",
            "next_feature_number": 3,
            "features": [{"id": "I008-F02", "state": "cancelled"}],
        }
        self.assertEqual(self.fw.allocate_feature_id(initiative), "I008-F03")

    def test_transition_preserves_phase_when_blocked(self):
        feature = {
            "id": "I007-F01",
            "phase": "discussion",
            "state": "in-progress",
            "next_action": {"skill": "feature-discuss", "instruction": "Continue"},
        }
        updated = self.fw.transition_feature(
            feature,
            state="blocked",
            next_action={"skill": "feature-discuss", "instruction": "Resolve dependency"},
            blocked_by=["I007-F02"],
        )
        self.assertEqual(updated["phase"], "discussion")
        self.assertEqual(updated["state"], "blocked")
        self.assertEqual(updated["blocked_by"], ["I007-F02"])

    def test_cancelled_dependency_does_not_release_dependent(self):
        initiative = {
            "features": [
                {"id": "I007-F01", "phase": "discussion", "state": "cancelled", "wave": 1, "depends_on": []},
                {"id": "I007-F02", "phase": "discussion", "state": "ready", "wave": 2, "depends_on": ["I007-F01"]},
            ]
        }
        self.assertEqual(self.fw.ready_features(initiative), [])

    def test_registry_resolves_external_manifests(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "initiatives" / "i007" / "features" / "f01").mkdir(parents=True)
            (root / "registry.yaml").write_text(
                "schema_version: '1.0'\ninitiatives:\n  - id: I007\n    manifest: initiatives/i007/initiative.yaml\n",
                encoding="utf-8",
            )
            (root / "initiatives" / "i007" / "initiative.yaml").write_text(
                "id: I007\ntitle: Example\nstate: in-progress\nnext_feature_number: 2\n"
                "initial_decomposition:\n  status: completed\n  feature_ids: [I007-F01]\n"
                "features:\n  - id: I007-F01\n    manifest: features/f01/feature.yaml\n",
                encoding="utf-8",
            )
            (root / "initiatives" / "i007" / "features" / "f01" / "feature.yaml").write_text(
                "id: I007-F01\ntitle: Leaf\nleaf: true\nphase: discussion\nstate: in-progress\n"
                "wave: 1\ndepends_on: []\nblocking_children: []\n"
                "scope_gate:\n  scores: [1, 1, 1, 1, 1, 1, 1, 1]\n  hard_gates: []\n  verdict: leaf\n"
                "next_action:\n  skill: feature-discuss\n  instruction: Continue\n",
                encoding="utf-8",
            )
            registry = self.fw.load_registry(root / "registry.yaml")
            self.assertEqual(registry["initiatives"][0]["features"][0]["title"], "Leaf")
            self.assertEqual(self.fw.validate_registry(registry), [])

    def test_finalize_decomposition_records_all_active_leaf_features(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            feature_root = root / "initiatives" / "i007" / "features" / "f01"
            feature_root.mkdir(parents=True)
            (root / "registry.yaml").write_text(
                "schema_version: '1.0'\ninitiatives:\n"
                "  - id: I007\n    manifest: initiatives/i007/initiative.yaml\n",
                encoding="utf-8",
            )
            (root / "initiatives" / "i007" / "initiative.yaml").write_text(
                "id: I007\ntitle: Example\nstate: in-progress\n"
                "next_feature_number: 2\nfeatures:\n"
                "  - id: I007-F01\n    manifest: features/f01/feature.yaml\n",
                encoding="utf-8",
            )
            (feature_root / "feature.yaml").write_text(
                "id: I007-F01\ntitle: Leaf\nleaf: true\n"
                "phase: scope-gate\nstate: in-progress\nwave: 1\n"
                "depends_on: []\nblocking_children: []\n"
                "scope_gate:\n  scores: [1, 1, 1, 1, 1, 1, 1, 1]\n"
                "  hard_gates: []\n  verdict: leaf\n"
                "next_action:\n  skill: feature-workspace\n"
                "  instruction: Finalize initial decomposition\n",
                encoding="utf-8",
            )
            rc = self.fw.main(
                [
                    "finalize-decomposition",
                    "--registry",
                    str(root / "registry.yaml"),
                    "--initiative",
                    "I007",
                ]
            )
            self.assertEqual(rc, 0)
            initiative = self.fw.load_yaml(
                root / "initiatives" / "i007" / "initiative.yaml"
            )
            self.assertEqual(
                initiative["initial_decomposition"],
                {"status": "completed", "feature_ids": ["I007-F01"]},
            )

    def test_unreferenced_retained_merged_source_is_not_discovered(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            retained = root / "initiatives" / "i006" / "features" / "f01"
            retained.mkdir(parents=True)
            (retained / "feature.yaml").write_text(
                "id: I006-F01\ntitle: Historical\nleaf: true\nphase: merged\nstate: completed\n",
                encoding="utf-8",
            )
            (retained / "historical.md").write_text("old material", encoding="utf-8")
            (root / "registry.yaml").write_text(
                "schema_version: '1.0'\ninitiatives: []\n",
                encoding="utf-8",
            )

            registry = self.fw.load_registry(root / "registry.yaml")

            self.assertEqual(self.fw.validate_registry(registry), [])
            self.assertNotIn("I006-F01", self.fw.render_progress(registry))

    def test_merged_routing_record_requires_isolated_retained_history_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            initiative_root = root / "initiatives" / "i006"
            retained = initiative_root / "features" / "f01"
            retained.mkdir(parents=True)
            (retained / "feature.yaml").write_text(
                "id: I006-F01\ntitle: Historical\nleaf: true\nphase: merged\nstate: completed\n",
                encoding="utf-8",
            )
            (retained / "RETAINED_HISTORY.md").write_text("history", encoding="utf-8")
            (retained / "history-route.yaml").write_text("schema_version: '1.0'\n", encoding="utf-8")
            (retained / "history-checksums.sha256").write_text("", encoding="utf-8")
            (root / "registry.yaml").write_text(
                "schema_version: '1.0'\ninitiatives:\n  - id: I006\n    manifest: initiatives/i006/initiative.yaml\n",
                encoding="utf-8",
            )
            (initiative_root / "initiative.yaml").write_text(
                "id: I006\ntitle: Historical Initiative\nstate: completed\nfeatures:\n"
                "  - id: I006-F01\n    title: Historical\n    leaf: true\n"
                "    phase: merged\n    state: completed\n"
                "    canonical_docs: [implementation/example.md]\n"
                "    merge_evidence: [evidence/merge.md]\n"
                "    retained_source:\n      path: features/f01\n"
                "      marker: RETAINED_HISTORY.md\n      route: history-route.yaml\n"
                "      checksum_manifest: history-checksums.sha256\n",
                encoding="utf-8",
            )

            self.assertEqual(self.fw.validate_registry(self.fw.load_registry(root / "registry.yaml")), [])

    def test_merged_source_cannot_remain_an_active_manifest_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            retained = root / "initiatives" / "i006" / "features" / "f01"
            retained.mkdir(parents=True)
            (root / "registry.yaml").write_text(
                "schema_version: '1.0'\ninitiatives:\n  - id: I006\n    manifest: initiatives/i006/initiative.yaml\n",
                encoding="utf-8",
            )
            (root / "initiatives" / "i006" / "initiative.yaml").write_text(
                "id: I006\ntitle: Historical Initiative\nstate: completed\nfeatures:\n"
                "  - id: I006-F01\n    manifest: features/f01/feature.yaml\n",
                encoding="utf-8",
            )
            (retained / "feature.yaml").write_text(
                "id: I006-F01\ntitle: Historical\nleaf: true\nphase: merged\nstate: completed\n"
                "canonical_docs: [implementation/example.md]\n"
                "merge_evidence: [evidence/merge.md]\n"
                "retained_source:\n  path: .\n  marker: RETAINED_HISTORY.md\n"
                "  route: history-route.yaml\n  checksum_manifest: history-checksums.sha256\n",
                encoding="utf-8",
            )

            errors = self.fw.validate_registry(self.fw.load_registry(root / "registry.yaml"))

            self.assertTrue(any("remains actively referenced" in error for error in errors))

    def test_context_ref_into_retained_merged_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            current = root / "initiatives" / "i007" / "features" / "f01"
            retained = root / "initiatives" / "i006" / "features" / "f01"
            current.mkdir(parents=True)
            retained.mkdir(parents=True)
            (retained / "feature.yaml").write_text(
                "id: I006-F01\ntitle: Historical\nleaf: true\nphase: merged\nstate: completed\n",
                encoding="utf-8",
            )
            (retained / "historical.md").write_text("old material", encoding="utf-8")
            (root / "registry.yaml").write_text(
                "schema_version: '1.0'\ninitiatives:\n  - id: I007\n    manifest: initiatives/i007/initiative.yaml\n",
                encoding="utf-8",
            )
            (root / "initiatives" / "i007" / "initiative.yaml").write_text(
                "id: I007\ntitle: Current\nstate: in-progress\nfeatures:\n"
                "  - id: I007-F01\n    manifest: features/f01/feature.yaml\n",
                encoding="utf-8",
            )
            (current / "feature.yaml").write_text(
                "id: I007-F01\ntitle: Current Leaf\nleaf: true\nphase: intake\nstate: not-started\n"
                "wave: 1\ndepends_on: []\n"
                "context_refs:\n"
                "  - path: ../../../i006/features/f01/historical.md\n    required: true\n"
                "next_action:\n  skill: feasibility-grill\n  instruction: Continue\n",
                encoding="utf-8",
            )

            errors = self.fw.validate_registry(self.fw.load_registry(root / "registry.yaml"))

            self.assertTrue(any("retained merged Feature source" in error for error in errors))

    def test_merge_gate_rejects_nonleaf_blocked_or_unmet_dependency(self):
        feature = {
            "id": "I007-F02",
            "leaf": False,
            "phase": "ready-to-merge",
            "state": "ready",
            "depends_on": ["I007-F01"],
            "blocking_children": ["I007-F03"],
            "acceptance": {"passed": True},
            "closure": {
                "canonical_docs": ["implementation/example.md"],
                "validation_evidence": ["pytest -q"],
                "tombstone_target": "registry.yaml",
            },
        }
        initiative = {
            "features": [
                {"id": "I007-F01", "phase": "discussion", "state": "in-progress"},
                feature,
            ]
        }
        errors = self.fw.merge_readiness_errors(feature, initiative)
        self.assertTrue(any("leaf" in error for error in errors))
        self.assertTrue(any("blocking child" in error for error in errors))
        self.assertTrue(any("dependency" in error for error in errors))

    def test_registry_rejects_missing_required_context_ref(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "initiatives" / "i001" / "features" / "f01").mkdir(parents=True)
            (root / "registry.yaml").write_text(
                "schema_version: '1.0'\ninitiatives:\n  - id: I001\n    manifest: initiatives/i001/initiative.yaml\n",
                encoding="utf-8",
            )
            (root / "initiatives" / "i001" / "initiative.yaml").write_text(
                "id: I001\ntitle: Example\nstate: in-progress\n"
                "context_refs:\n  - path: feasibility/confirmed-constraints.md\n    required: true\n"
                "features:\n  - id: I001-F01\n    manifest: features/f01/feature.yaml\n",
                encoding="utf-8",
            )
            (root / "initiatives" / "i001" / "features" / "f01" / "feature.yaml").write_text(
                "id: I001-F01\ntitle: Leaf\nleaf: true\nphase: intake\nstate: not-started\n"
                "wave: 1\ndepends_on: []\n"
                "next_action:\n  skill: feasibility-grill\n  instruction: Continue\n",
                encoding="utf-8",
            )

            errors = self.fw.validate_registry(self.fw.load_registry(root / "registry.yaml"))

            self.assertTrue(any("context ref" in error.lower() and "missing" in error.lower() for error in errors))

    def test_registry_rejects_context_ref_outside_workspace(self):
        with tempfile.TemporaryDirectory() as temp:
            container = Path(temp)
            root = container / "workspace"
            (root / "initiatives" / "i001" / "features" / "f01").mkdir(parents=True)
            (container / "outside.md").write_text("outside", encoding="utf-8")
            (root / "registry.yaml").write_text(
                "schema_version: '1.0'\ninitiatives:\n  - id: I001\n    manifest: initiatives/i001/initiative.yaml\n",
                encoding="utf-8",
            )
            (root / "initiatives" / "i001" / "initiative.yaml").write_text(
                "id: I001\ntitle: Example\nstate: in-progress\n"
                "context_refs:\n  - path: ../../../outside.md\n    required: true\n"
                "features:\n  - id: I001-F01\n    manifest: features/f01/feature.yaml\n",
                encoding="utf-8",
            )
            (root / "initiatives" / "i001" / "features" / "f01" / "feature.yaml").write_text(
                "id: I001-F01\ntitle: Leaf\nleaf: true\nphase: intake\nstate: not-started\n"
                "wave: 1\ndepends_on: []\n"
                "next_action:\n  skill: feasibility-grill\n  instruction: Continue\n",
                encoding="utf-8",
            )

            errors = self.fw.validate_registry(self.fw.load_registry(root / "registry.yaml"))

            self.assertTrue(any("context ref" in error.lower() and "outside" in error.lower() for error in errors))


class TransitionCommandTests(unittest.TestCase):
    """The `transition` CLI command applies transition_feature, writes the
    feature manifest, and (optionally) validates the workspace -- the sanctioned
    state-change path that was previously missing."""

    def setUp(self):
        self.fw = load_module()

    def _write_feature(self, root: Path) -> Path:
        feature_path = root / "feature.yaml"
        feature_path.write_text(
            "id: I007-F01\n"
            "title: Leaf\n"
            "leaf: true\n"
            "phase: discussion\n"
            "state: in-progress\n"
            "wave: 1\n"
            "depends_on: []\n"
            "scope_gate:\n"
            "  scores: [1, 1, 1, 1, 1, 1, 1, 1]\n"
            "  hard_gates: []\n"
            "  verdict: leaf\n"
            "next_action:\n"
            "  skill: feature-discuss\n"
            "  instruction: Continue\n",
            encoding="utf-8",
        )
        return feature_path

    def test_apply_transition_writes_state_blocked_by_and_preserves_phase(self):
        with tempfile.TemporaryDirectory() as temp:
            feature_path = self._write_feature(Path(temp))
            updated = self.fw.apply_transition(
                feature_path,
                state="blocked",
                next_action={"skill": "feasibility-grill", "instruction": "Resolve X"},
                blocked_by=["I007-F02"],
            )
            self.assertEqual(updated["state"], "blocked")
            self.assertEqual(updated["phase"], "discussion")
            self.assertEqual(updated["blocked_by"], ["I007-F02"])
            # Persisted to disk.
            reloaded = self.fw.load_yaml(feature_path)
            self.assertEqual(reloaded["state"], "blocked")
            self.assertEqual(reloaded["blocked_by"], ["I007-F02"])

    def test_apply_transition_terminal_state_drops_next_action(self):
        with tempfile.TemporaryDirectory() as temp:
            feature_path = self._write_feature(Path(temp))
            updated = self.fw.apply_transition(feature_path, state="completed")
            self.assertEqual(updated["state"], "completed")
            self.assertNotIn("next_action", updated)
            self.assertNotIn("next_action", self.fw.load_yaml(feature_path))

    def test_apply_transition_invalid_state_leaves_file_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            feature_path = self._write_feature(Path(temp))
            before = feature_path.read_text(encoding="utf-8")
            with self.assertRaises(ValueError):
                self.fw.apply_transition(feature_path, state="frozen")
            self.assertEqual(feature_path.read_text(encoding="utf-8"), before)

    def test_main_transition_cli_updates_file_and_returns_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            feature_path = self._write_feature(Path(temp))
            rc = self.fw.main(
                [
                    "transition",
                    "--feature",
                    str(feature_path),
                    "--state",
                    "blocked",
                    "--phase",
                    "discussion",
                    "--next-skill",
                    "feasibility-grill",
                    "--next-instruction",
                    "Resolve dependency",
                    "--blocked-by",
                    "I007-F02",
                ]
            )
            self.assertEqual(rc, 0)
            reloaded = self.fw.load_yaml(feature_path)
            self.assertEqual(reloaded["state"], "blocked")
            self.assertEqual(reloaded["blocked_by"], ["I007-F02"])

    def test_main_transition_rejects_missing_next_action_for_nonterminal(self):
        with tempfile.TemporaryDirectory() as temp:
            feature_path = self._write_feature(Path(temp))
            before = feature_path.read_text(encoding="utf-8")
            rc = self.fw.main(
                ["transition", "--feature", str(feature_path), "--state", "in-progress"]
            )
            self.assertNotEqual(rc, 0)
            # File unchanged on governance failure.
            self.assertEqual(feature_path.read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()