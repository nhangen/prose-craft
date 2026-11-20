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
    return f"{WORKBENCH_URL}#text={quote(text, safe='')}"


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

    def test_input_carries_copy_in_hash_fragment(self):
        text = "Ship it & see — 100% #done\nline two, naïve"
        self.assertEqual(run_app(inputs=[text])["afterInput"], [carried(text)])

    def test_copy_is_trimmed_before_encoding(self):
        self.assertEqual(run_app(inputs=["  My draft.\n"])["afterInput"], [carried("My draft.")])

    def test_empty_whitespace_and_example_revert_to_base_url(self):
        example = run_app()["example"]
        result = run_app(inputs=["My draft.", "", "My draft.", "   \n", "My draft.", example])
        self.assertEqual(
            result["afterInput"],
            [carried("My draft."), WORKBENCH_URL, carried("My draft."), WORKBENCH_URL,
             carried("My draft."), WORKBENCH_URL],
        )


if __name__ == "__main__":
    unittest.main()
