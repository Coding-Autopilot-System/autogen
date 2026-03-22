from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = REPO_ROOT / "autogen_dashboard" / "static" / "index.html"
APP_JS = REPO_ROOT / "autogen_dashboard" / "static" / "app.js"
STYLES_CSS = REPO_ROOT / "autogen_dashboard" / "static" / "styles.css"


class Phase5UiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index_html = INDEX_HTML.read_text(encoding="utf-8")
        cls.app_js = APP_JS.read_text(encoding="utf-8")
        cls.styles_css = STYLES_CSS.read_text(encoding="utf-8")

    def test_index_html_exposes_wave1_operator_shell_landmarks(self) -> None:
        self.assertIn('id="operator-tab-timeline"', self.index_html)
        self.assertIn('id="active-route-strip"', self.index_html)
        self.assertIn('id="active-stage-strip"', self.index_html)

    def test_app_js_operator_tabs_include_timeline(self) -> None:
        operator_tabs_match = re.search(
            r"const\s+OPERATOR_TABS\s*=\s*\[(?P<body>.*?)\];",
            self.app_js,
            re.DOTALL,
        )
        self.assertIsNotNone(operator_tabs_match, "Expected OPERATOR_TABS declaration in app.js.")
        operator_tabs_body = operator_tabs_match.group("body")
        self.assertRegex(operator_tabs_body, r'["\']timeline["\']')

    def test_app_js_declares_wave1_transcript_render_helpers(self) -> None:
        self.assertIn("function messageFamilyForRole", self.app_js)
        self.assertIn("function renderMessageMetaStrip", self.app_js)
        self.assertIn("function renderMessageCard", self.app_js)

    def test_normalize_message_preserves_source_and_metadata(self) -> None:
        normalize_message_match = re.search(
            r"function\s+normalizeMessage\s*\([^)]*\)\s*\{(?P<body>.*?)\n  \}",
            self.app_js,
            re.DOTALL,
        )
        self.assertIsNotNone(normalize_message_match, "Expected normalizeMessage function in app.js.")
        normalize_message_body = normalize_message_match.group("body")
        self.assertRegex(normalize_message_body, r"\bsource\s*:")
        self.assertRegex(normalize_message_body, r"\bmetadata\s*:")

    def test_normalize_session_detail_preserves_events(self) -> None:
        normalize_detail_match = re.search(
            r"function\s+normalizeSessionDetail\s*\([^)]*\)\s*\{(?P<body>.*?)\n  \}",
            self.app_js,
            re.DOTALL,
        )
        self.assertIsNotNone(
            normalize_detail_match,
            "Expected normalizeSessionDetail function in app.js.",
        )
        normalize_detail_body = normalize_detail_match.group("body")
        self.assertRegex(normalize_detail_body, r"\bevents\s*:")

    def test_styles_css_declares_message_family_cards_and_meta_strip(self) -> None:
        self.assertIn(".message-card.manager", self.styles_css)
        self.assertIn(".message-card.specialist", self.styles_css)
        self.assertIn(".message-card.approval", self.styles_css)
        self.assertIn(".message-card.event", self.styles_css)
        self.assertIn(".message-meta-strip", self.styles_css)


if __name__ == "__main__":
    unittest.main()
