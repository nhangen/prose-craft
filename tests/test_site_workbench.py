import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SITE_DIR = TESTS_DIR.parent / "site"
LIVE_URL = "https://claude.ai/artifact/U14dzUR4TaszeSjP27NnUV"


def run_app(initial=None, inputs=(), clipboard="ok"):
    spec = {"inputs": list(inputs), "clipboard": clipboard}
    if initial is not None:
        spec["initial"] = initial
    out = subprocess.run(
        ["node", str(TESTS_DIR / "workbench_harness.js"), str(SITE_DIR / "app.js"), json.dumps(spec)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


GO = "go:" + LIVE_URL


class TestLiveButton(unittest.TestCase):
    def test_button_has_id_and_base_url(self):
        html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        tag = re.search(r'<a\b[^>]*\bid="chk-live"[^>]*>', html)
        self.assertIsNotNone(tag, 'Prose Craft Live button must carry id="chk-live"')
        self.assertIn(f'href="{LIVE_URL}"', tag.group(0))

    def test_button_and_copy_name_prose_craft_live(self):
        html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        self.assertIn("Copy to Prose Craft Live &rarr;", html)
        self.assertNotIn("workbench", html.lower())


@unittest.skipUnless(shutil.which("node"), "node is required to run site/app.js")
class TestLiveHandoff(unittest.TestCase):
    def test_example_copy_navigates_without_copying(self):
        result = run_app()
        self.assertEqual(result["setupClick"], LIVE_URL)

    def test_restored_draft_is_copied_then_navigates(self):
        result = run_app(initial="My draft.")
        self.assertEqual(result["afterSetup"], LIVE_URL)
        self.assertEqual(result["events"], [["copy:My draft.", GO]])

    def test_copy_finishes_before_navigation(self):
        # Leaving the page while writeText is pending can drop the write.
        text = "Ship it & see — 100% #done\nline two, naïve"
        result = run_app(initial="My draft.", inputs=[text])
        self.assertEqual(result["events"], [["copy:My draft.", GO], [f"copy:{text}", GO]])
        self.assertEqual(result["navigates"], [LIVE_URL, LIVE_URL])

    def test_anchor_href_never_carries_the_draft(self):
        text = "Ship it & see — 100% #done\nline two, naïve"
        result = run_app(initial="My draft.", inputs=[text])
        for href in [result["afterSetup"], *result["afterInput"]]:
            self.assertEqual(href, LIVE_URL, "the anchor href must stay at the bare URL")

    def test_example_or_blank_copy_skips_the_clipboard(self):
        example = run_app()["example"]
        result = run_app(inputs=["My draft.", "", "   \n", example])
        self.assertEqual(result["events"], [["copy:My draft.", GO], [GO], [GO], [GO]])

    def test_click_cancels_the_default_navigation(self):
        # Without preventDefault the browser leaves before the copy settles.
        result = run_app(initial="My draft.", inputs=["Another draft."])
        self.assertEqual(result["prevented"], [True, True])

    def test_modified_and_middle_clicks_copy_and_leave_navigation_to_the_browser(self):
        # These open a new tab on the bare href, and this page stays open.
        result = run_app(initial="My draft.")
        for gesture, outcome in result["modified"].items():
            self.assertIsNone(outcome["navigated"], gesture)
            self.assertFalse(outcome["prevented"], gesture)
            self.assertEqual(outcome["events"], ["copy:My draft."], gesture)

    def test_copy_is_trimmed(self):
        self.assertEqual(run_app(inputs=["  My draft.\n"])["events"], [["copy:My draft.", GO]])

    def test_blocked_clipboard_falls_back_to_selection_copy(self):
        for mode in ("reject", "missing"):
            result = run_app(initial="My draft.", clipboard=mode)
            self.assertEqual(result["events"], [["exec:copy:My draft.", GO]], mode)

    def test_app_never_writes_to_the_anchor(self):
        # GA4 reads the link's attributes, so a draft written by any route
        # (href, hash, setAttribute, setAttributeNS) would reach it.
        result = run_app(initial="My draft.", inputs=["Another draft.", ""])
        self.assertEqual(result["linkWrites"], [])


if __name__ == "__main__":
    unittest.main()
