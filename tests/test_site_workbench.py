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

    def test_copy_is_trimmed_before_encoding(self):
        self.assertEqual(run_app(inputs=["  My draft.\n"])["navigates"], [carried("My draft.")])

    def test_draft_text_never_reaches_an_anchor_attribute(self):
        html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        js = (SITE_DIR / "app.js").read_text(encoding="utf-8")
        self.assertNotIn(".href =", js,
                         "app.js must never write the draft into the anchor's href")


if __name__ == "__main__":
    unittest.main()
