import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SITE_DIR = TESTS_DIR.parent / "site"
WORKBENCH_URL = "https://claude.ai/artifact/U14dzUR4TaszeSjP27NnUV"


def run_app(initial=None, inputs=(), test_paste=None):
    spec = {"inputs": list(inputs)}
    if initial is not None:
        spec["initial"] = initial
    if test_paste is not None:
        spec["testPaste"] = test_paste
    out = subprocess.run(
        ["node", str(TESTS_DIR / "workbench_harness.js"), str(SITE_DIR / "app.js"), json.dumps(spec)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


class TestWorkbenchButton(unittest.TestCase):
    def test_button_has_id_and_base_url(self):
        html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        tag = re.search(r'<a\b[^>]*\bid="chk-workbench"[^>]*>', html)
        self.assertIsNotNone(tag, 'workbench button must carry id="chk-workbench"')
        self.assertIn(f'href="{WORKBENCH_URL}"', tag.group(0))

    def test_button_says_copy_to_prose_craft_live(self):
        html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        tag = re.search(r'<a\b[^>]*\bid="chk-workbench"[^>]*>([\s\S]*?)</a>', html)
        self.assertIsNotNone(tag)
        self.assertIn("Copy to Prose Craft Live", tag.group(1))

    def test_section_does_not_mention_workbench(self):
        html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        check_section = re.search(r'<section id="check"[^>]*>([\s\S]*?)</section>', html)
        self.assertIsNotNone(check_section)
        # Verify user-visible text (excluding id/class attributes) does not say "workbench"
        text_only = re.sub(r'<[^>]+>', ' ', check_section.group(1))
        self.assertNotIn("workbench", text_only.lower())

    def test_paste_button_exists(self):
        html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        self.assertRegex(html, r'<button\b[^>]*\bid="chk-paste"[^>]*>\s*Paste copy\s*</button>')


@unittest.skipUnless(shutil.which("node"), "node is required to run site/app.js")
class TestWorkbenchLink(unittest.TestCase):
    def test_example_copy_keeps_base_url_at_setup(self):
        res = run_app()
        self.assertEqual(res["setupClick"], WORKBENCH_URL)
        self.assertEqual(res["setupClipboardWrites"], [])

    def test_restored_draft_is_copied_at_setup(self):
        result = run_app(initial="My draft.")
        self.assertEqual(result["afterSetup"], WORKBENCH_URL)
        self.assertEqual(result["setupClipboardWrites"], ["My draft."])
        self.assertEqual(result["navigates"], [WORKBENCH_URL])
        self.assertEqual(result["clipboardWrites"], ["My draft."])

    def test_anchor_href_never_carries_the_draft(self):
        text = "Ship it & see — 100% #done\nline two, naïve"
        result = run_app(initial="My draft.", inputs=[text])
        for href in [result["afterSetup"], *result["afterInput"]]:
            self.assertEqual(href, WORKBENCH_URL,
                             "the anchor href must stay at the bare workbench URL")

    def test_click_navigates_to_base_url_and_copies_to_clipboard(self):
        text = "Ship it & see — 100% #done\nline two, naïve"
        result = run_app(initial="My draft.", inputs=[text])
        self.assertEqual(result["navigates"], [WORKBENCH_URL, WORKBENCH_URL])
        self.assertEqual(result["clipboardWrites"], ["My draft.", text])

    def test_click_on_example_or_blank_copy_does_not_write_clipboard(self):
        example = run_app()["example"]
        result = run_app(inputs=["My draft.", "", "   \n", example])
        self.assertEqual(
            result["navigates"],
            [WORKBENCH_URL, WORKBENCH_URL, WORKBENCH_URL, WORKBENCH_URL],
        )
        self.assertEqual(result["clipboardWrites"], ["My draft."])

    def test_click_cancels_the_default_navigation(self):
        result = run_app(initial="My draft.", inputs=["Another draft."])
        self.assertEqual(result["prevented"], [True, True])

    def test_modified_and_middle_clicks_are_left_to_the_browser(self):
        result = run_app(initial="My draft.")
        for gesture, outcome in result["modified"].items():
            self.assertEqual(outcome, {"navigated": None, "prevented": False}, gesture)

    def test_copy_is_trimmed_before_clipboard_write(self):
        self.assertEqual(run_app(inputs=["  My draft.\n"])["clipboardWrites"], ["My draft."])

    def test_app_never_writes_to_the_anchor(self):
        result = run_app(initial="My draft.", inputs=["Another draft.", ""])
        self.assertEqual(result["linkWrites"], [])

    def test_paste_button_reads_clipboard_and_updates_textarea(self):
        result = run_app(test_paste="Pasted content from clipboard")
        self.assertEqual(result.get("pastedValue"), "Pasted content from clipboard")


if __name__ == "__main__":
    unittest.main()
