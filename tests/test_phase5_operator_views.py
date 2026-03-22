from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_JS = REPO_ROOT / "autogen_dashboard" / "static" / "app.js"
STYLES_CSS = REPO_ROOT / "autogen_dashboard" / "static" / "styles.css"
PHASE3_API_TEST = REPO_ROOT / "tests" / "test_phase3_api.py"


class Phase5OperatorViewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app_js = APP_JS.read_text(encoding="utf-8")
        cls.styles_css = STYLES_CSS.read_text(encoding="utf-8")
        cls.phase3_api_test = PHASE3_API_TEST.read_text(encoding="utf-8")

    def test_app_js_declares_operator_view_model_helpers(self) -> None:
        self.assertIn("function buildTimelineEntries", self.app_js)
        self.assertIn("function buildOperatorArtifactSections", self.app_js)
        self.assertIn("function buildRoutingSummary", self.app_js)

    def test_app_js_declares_timeline_and_artifact_renderers(self) -> None:
        self.assertIn("function renderTimelineTab", self.app_js)
        self.assertIn("function renderArtifactsTab", self.app_js)
        self.assertIn("timeline:", self.app_js)

    def test_normalize_session_detail_keeps_operator_payload_dependencies(self) -> None:
        normalize_detail_match = re.search(
            r"function\s+normalizeSessionDetail\s*\([^)]*\)\s*\{(?P<body>.*?)\n  \}",
            self.app_js,
            re.DOTALL,
        )
        self.assertIsNotNone(
            normalize_detail_match,
            "Expected normalizeSessionDetail function in app.js.",
        )
        body = normalize_detail_match.group("body")
        self.assertRegex(body, r"\bevents\s*:")
        self.assertRegex(body, r"\bpendingApproval\b")
        self.assertRegex(body, r"\bvalidationResults\b")
        self.assertRegex(body, r"\brouteAttempts\b")

    def test_timeline_builder_uses_structured_events_and_validation_results(self) -> None:
        timeline_match = re.search(
            r"function\s+buildTimelineEntries\s*\([^)]*\)\s*\{(?P<body>.*?)\n  \}",
            self.app_js,
            re.DOTALL,
        )
        self.assertIsNotNone(
            timeline_match,
            "Expected buildTimelineEntries function in app.js.",
        )
        body = timeline_match.group("body")
        self.assertIn("session.events", body)
        self.assertIn("session.pendingApproval", body)
        self.assertIn("output.validationResults", body)
        self.assertIn("session.routeAttempts", body)

    def test_artifact_section_builder_groups_diffs_validation_and_artifacts(self) -> None:
        artifact_match = re.search(
            r"function\s+buildOperatorArtifactSections\s*\([^)]*\)\s*\{(?P<body>.*?)\n  \}",
            self.app_js,
            re.DOTALL,
        )
        self.assertIsNotNone(
            artifact_match,
            "Expected buildOperatorArtifactSections function in app.js.",
        )
        body = artifact_match.group("body")
        self.assertIn("diffArtifacts", body)
        self.assertIn("validationResults", body)
        self.assertIn("artifacts", body)
        self.assertIn("changedFiles", body)

    def test_styles_declare_timeline_routing_agent_and_artifact_cards(self) -> None:
        self.assertIn(".timeline-card", self.styles_css)
        self.assertIn(".route-summary-card", self.styles_css)
        self.assertIn(".artifact-detail-card", self.styles_css)
        self.assertIn(".agent-activity-card", self.styles_css)

    def test_phase3_api_contract_exposes_fields_required_by_operator_views(self) -> None:
        self.assertIn("route_attempts", self.phase3_api_test)
        self.assertIn("events", self.phase3_api_test)
        self.assertIn("validation_results", self.phase3_api_test)
        self.assertIn("diff_artifacts", self.phase3_api_test)

    def test_routing_tab_uses_routing_summary_cards(self) -> None:
        routing_match = re.search(
            r"function\s+renderRoutingTab\s*\([^)]*\)\s*\{(?P<body>.*?)\n  \}",
            self.app_js,
            re.DOTALL,
        )
        self.assertIsNotNone(
            routing_match,
            "Expected renderRoutingTab function in app.js.",
        )
        body = routing_match.group("body")
        self.assertIn("route-summary-card", body)
        self.assertIn("buildRoutingSummary", body)

    def test_agents_tab_uses_agent_activity_cards(self) -> None:
        agents_match = re.search(
            r"function\s+renderAgentsTab\s*\([^)]*\)\s*\{(?P<body>.*?)\n  \}",
            self.app_js,
            re.DOTALL,
        )
        self.assertIsNotNone(
            agents_match,
            "Expected renderAgentsTab function in app.js.",
        )
        body = agents_match.group("body")
        self.assertIn("agent-activity-card", body)
        self.assertIn("specialist-grid", body)
        self.assertIn("handoff-list", body)

    def test_artifacts_tab_uses_artifact_detail_cards(self) -> None:
        artifacts_match = re.search(
            r"function\s+renderArtifactsTab\s*\([^)]*\)\s*\{(?P<body>.*?)\n  \}",
            self.app_js,
            re.DOTALL,
        )
        self.assertIsNotNone(
            artifacts_match,
            "Expected renderArtifactsTab function in app.js.",
        )
        body = artifacts_match.group("body")
        self.assertIn("artifact-detail-card", body)
        self.assertIn("buildOperatorArtifactSections", body)
        self.assertIn("validationResults", body)


if __name__ == "__main__":
    unittest.main()
