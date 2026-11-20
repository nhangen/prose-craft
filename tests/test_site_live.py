import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SITE_DIR = TESTS_DIR.parent / "site"
LIVE_URL = "https://claude.ai/artifact/U14dzUR4TaszeSjP27NnUV"


def run_app(initial=None, inputs=(), clipboard="ok", exec_ok=True):
    spec = {"inputs": list(inputs), "clipboard": clipboard, "exec": "ok" if exec_ok else "fail"}
    if initial is not None:
        spec["initial"] = initial
    out = subprocess.run(
        ["node", str(TESTS_DIR / "live_harness.js"), str(SITE_DIR / "app.js"), json.dumps(spec)],
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
        for name in ("index.html", "app.js"):
            text = (SITE_DIR / name).read_text(encoding="utf-8")
            self.assertNotIn("workbench", text.lower(), name)


@unittest.skipUnless(shutil.which("node"), "node is required to run site/app.js")
class TestLiveHandoff(unittest.TestCase):
    def test_example_copy_navigates_without_copying(self):
        result = run_app()
        self.assertEqual(result["setupClick"], LIVE_URL)

    def test_restored_draft_is_copied_then_navigates(self):
        result = run_app(initial="My draft.")
        self.assertEqual(result["afterSetup"], LIVE_URL)
        self.assertEqual(result["events"], [["copied:My draft.", GO]])

    def test_copy_finishes_before_navigation(self):
        # Leaving the page while writeText is pending can drop the write. The
        # harness's writeText settles a few ticks late, so a handler that does
        # not wait logs "go:" before "copied:".
        text = "Ship it & see — 100% #done\nline two, naïve"
        result = run_app(initial="My draft.", inputs=[text])
        self.assertEqual(result["events"], [["copied:My draft.", GO], [f"copied:{text}", GO]])
        self.assertEqual(result["navigates"], [LIVE_URL, LIVE_URL])

    def test_anchor_href_never_carries_the_draft(self):
        text = "Ship it & see — 100% #done\nline two, naïve"
        result = run_app(initial="My draft.", inputs=[text])
        for href in [result["afterSetup"], *result["afterInput"]]:
            self.assertEqual(href, LIVE_URL, "the anchor href must stay at the bare URL")

    def test_example_or_blank_copy_skips_the_clipboard(self):
        example = run_app()["example"]
        result = run_app(inputs=["My draft.", "", "   \n", example])
        self.assertEqual(result["events"], [["copied:My draft.", GO], [GO], [GO], [GO]])

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
            self.assertEqual(outcome["events"], ["copied:My draft."], gesture)

    def test_right_and_side_button_auxclicks_leave_the_clipboard_alone(self):
        # "Copy link address" or a mouse back button must not replace the
        # visitor's clipboard with the draft.
        result = run_app(initial="My draft.")
        for gesture, outcome in result["ignored"].items():
            self.assertEqual(outcome["events"], [], gesture)
            self.assertFalse(outcome["prevented"], gesture)

    def test_copy_is_trimmed(self):
        self.assertEqual(run_app(inputs=["  My draft.\n"])["events"], [["copied:My draft.", GO]])

    def test_blocked_clipboard_falls_back_to_selection_copy(self):
        for mode in ("reject", "missing"):
            result = run_app(initial="My draft.", clipboard=mode)
            self.assertEqual(result["events"], [["exec:copy:My draft.", GO]], mode)

    def test_hung_clipboard_times_out_to_the_fallback(self):
        result = run_app(initial="My draft.", clipboard="hang")
        self.assertEqual(result["events"], [["exec:copy:My draft.", GO]])

    def test_failed_copy_stays_and_explains(self):
        # Paste in Prose Craft Live would otherwise pick up older clipboard
        # contents and send them to Claude.
        for mode in ("reject", "missing", "hang"):
            result = run_app(initial="My draft.", clipboard=mode, exec_ok=False)
            self.assertEqual(result["events"], [["msg"]], mode)
            self.assertEqual(result["navigates"], [None], mode)
            self.assertEqual(result["prevented"], [True], mode)

    def test_app_never_writes_to_the_anchor(self):
        # GA4 reads the link's attributes, so a draft written by any route
        # (href, hash, setAttribute, setAttributeNS) would reach it.
        result = run_app(initial="My draft.", inputs=["Another draft.", ""])
        self.assertEqual(result["linkWrites"], [])


if __name__ == "__main__":
    unittest.main()
