import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path
from urllib.parse import quote

TESTS_DIR = Path(__file__).resolve().parent
SITE_DIR = TESTS_DIR.parent / "site"
WORKBENCH_URL = "https://claude.ai/artifact/U14dzUR4TaszeSjP27NnUV"


def run_app(initial=None, inputs=()):
    spec = {"inputs": list(inputs)}
    if initial is not None:
        spec["initial"] = initial
    out = subprocess.run(
        ["node", str(TESTS_DIR / "workbench_harness.js"), str(SITE_DIR / "app.js"), json.dumps(spec)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def carried(text):
    return WORKBENCH_URL + "#text=" + quote(text, safe="!*'()")


class TestWorkbenchButton(unittest.TestCase):
    def test_button_has_id_and_base_url(self):
        html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        tag = re.search(r'<a\b[^>]*\bid="chk-workbench"[^>]*>', html)
        self.assertIsNotNone(tag, 'workbench button must carry id="chk-workbench"')
        self.assertIn(f'href="{WORKBENCH_URL}"', tag.group(0))


@unittest.skipUnless(shutil.which("node"), "node is required to run site/app.js")
class TestWorkbenchLink(unittest.TestCase):
    def test_example_copy_keeps_base_url_at_setup(self):
        self.assertEqual(run_app()["afterSetup"], WORKBENCH_URL)

    def test_restored_draft_is_carried_at_setup(self):
        # The anchor href stays at the bare URL, but a click at setup time
        # navigates with the restored draft in the hash fragment.
        result = run_app(initial="My draft.")
        self.assertEqual(result["afterSetup"], WORKBENCH_URL)
        self.assertEqual(result["navigates"], [carried("My draft.")])

    def test_anchor_href_never_carries_the_draft(self):
        text = "Ship it & see — 100% #done\nline two, naïve"
        result = run_app(initial="My draft.", inputs=[text])
        for href in [result["afterSetup"], *result["afterInput"]]:
            self.assertEqual(href, WORKBENCH_URL,
                             "the anchor href must stay at the bare workbench URL")

    def test_click_navigates_with_copy_in_hash_fragment(self):
        text = "Ship it & see — 100% #done\nline two, naïve"
        result = run_app(initial="My draft.", inputs=[text])
        self.assertEqual(result["navigates"], [carried("My draft."), carried(text)])

    def test_click_on_example_or_blank_copy_uses_base_url(self):
        example = run_app()["example"]
        result = run_app(inputs=["My draft.", "", "   \n", example])
        self.assertEqual(
            result["navigates"],
            [carried("My draft."), WORKBENCH_URL, WORKBENCH_URL, WORKBENCH_URL],
        )

    def test_click_cancels_the_default_navigation(self):
        # Without preventDefault the anchor's bare href replaces the
        # location.assign navigation and the draft is lost.
        result = run_app(initial="My draft.", inputs=["Another draft."])
        self.assertEqual(result["prevented"], [True, True])

    def test_modified_and_middle_clicks_are_left_to_the_browser(self):
        # These open a new tab on the bare href. Issue #6 accepted that the
        # draft does not travel with them.
        result = run_app(initial="My draft.")
        for gesture, outcome in result["modified"].items():
            self.assertEqual(outcome, {"navigated": None, "prevented": False}, gesture)

    def test_copy_is_trimmed_before_encoding(self):
        self.assertEqual(run_app(inputs=["  My draft.\n"])["navigates"], [carried("My draft.")])

    def test_app_never_writes_the_anchor_href(self):
        # GA4 reads the href attribute, so a write through setAttribute leaks
        # the draft as surely as one through the href property.
        result = run_app(initial="My draft.", inputs=["Another draft.", ""])
        self.assertEqual(result["hrefWrites"], [])


if __name__ == "__main__":
    unittest.main()
