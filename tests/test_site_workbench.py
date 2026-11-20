import re
import unittest
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent / "site"
WORKBENCH_URL = "https://claude.ai/artifact/U14dzUR4TaszeSjP27NnUV"


class TestSiteWorkbench(unittest.TestCase):
    def setUp(self):
        self.html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        self.js = (SITE_DIR / "app.js").read_text(encoding="utf-8")

    def test_workbench_button_has_id(self):
        self.assertRegex(
            self.html,
            r'<a class="btn" id="chk-workbench" href="https://claude\.ai/artifact/U14dzUR4TaszeSjP27NnUV">',
            'workbench button must carry id="chk-workbench" and the base URL',
        )

    def test_link_uses_hash_fragment_with_encoded_text(self):
        self.assertIn('encodeURIComponent(text)', self.js)
        self.assertRegex(self.js, r"\$\(\"chk-workbench\"\)\.href = ")
        self.assertIn("WORKBENCH_URL", self.js)
        self.assertIn(WORKBENCH_URL, self.js)

    def test_link_updates_on_input(self):
        self.assertRegex(
            self.js,
            r'\$\("chk-src"\)\.addEventListener\("input",[^"]*?drawWorkbenchLink\(\)',
            "the #chk-src input listener must refresh the workbench link",
        )

    def test_link_updates_on_initial_setup(self):
        self.assertIn("drawWorkbenchLink();", self.js)
        self.assertRegex(
            self.js,
            r"drawCheck\(\);\s*drawWorkbenchLink\(\);",
            "drawWorkbenchLink must run during initial setup",
        )

    def test_example_text_keeps_base_url(self):
        self.assertRegex(
            self.js,
            r"text && text !== CHK_EXAMPLE",
            "example/empty copy must fall back to the clean base URL",
        )


if __name__ == "__main__":
    unittest.main()
