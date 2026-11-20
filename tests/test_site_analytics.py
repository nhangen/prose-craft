import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SITE_DIR = TESTS_DIR.parent / "site"


def scrub(href, replace_state="ok"):
    out = subprocess.run(
        ["node", str(TESTS_DIR / "scrubber_harness.js"), str(SITE_DIR / "index.html"),
         json.dumps({"href": href, "replaceState": replace_state})],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


class TestSiteAnalytics(unittest.TestCase):
    def setUp(self):
        self.html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        self.js = (SITE_DIR / "app.js").read_text(encoding="utf-8")

    def test_query_scrubber_runs_before_google_tag_load(self):
        scrub = self.html.index("history.replaceState")
        tag = self.html.index("googletagmanager.com/gtag/js")
        self.assertLess(scrub, tag)
        for key in ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"]:
            self.assertLess(self.html.index(key), scrub)
        self.assertIn("new URL(window.location.href)", self.html)
        self.assertIn("url.search = clean.toString()", self.html)
        self.assertIn("window.history.replaceState(window.history.state, '', url.href)", self.html)
        self.assertIn("window['ga-disable-G-TC0R2KF0H9'] = true", self.html)

    def test_referrer_is_set_to_origin_for_subsequent_events(self):
        self.assertIn('<meta name="referrer" content="origin">', self.html)
        referrer = self.html.index("page_referrer: document.referrer")
        config = self.html.index("gtag('config', 'G-TC0R2KF0H9')")
        self.assertLess(referrer, config)

    def test_config_uses_automatic_page_view(self):
        config = re.search(r"gtag\('config',[^;]*?\);", self.html, re.S)
        self.assertIsNotNone(config, "gtag config call missing")
        self.assertNotIn("send_page_view: false", config.group(0))

    def test_manual_page_view_is_not_sent(self):
        self.assertNotIn("gtag('event', 'page_view'", self.html)

    def test_click_handler_ignores_non_primary_click(self):
        self.assertIn('event.type === "click" && event.button !== 0', self.js)

    def test_destination_limited_to_http_schemes(self):
        self.assertIn('url.protocol === "http:" || url.protocol === "https:"', self.js)


@unittest.skipUnless(shutil.which("node"), "node is required to run the inline scrubber")
class TestQueryScrubber(unittest.TestCase):
    def test_drops_private_params_and_keeps_utm_and_hash(self):
        result = scrub("https://prosecraft.dev/?x=secret&q=private&gclid=abc&utm_source=test&utm_medium=cpc#rules")
        self.assertEqual(result["href"], "https://prosecraft.dev/?utm_source=test&utm_medium=cpc#rules")
        self.assertEqual(len(result["calls"]), 1)
        self.assertTrue(result["calls"][0]["sameState"])
        self.assertFalse(result["disabled"])

    def test_double_slash_path_is_scrubbed(self):
        result = scrub("https://prosecraft.dev//?x=secret&utm_source=test")
        self.assertEqual(result["href"], "https://prosecraft.dev//?utm_source=test")
        self.assertFalse(result["disabled"])

    def test_query_with_only_private_params_leaves_no_question_mark(self):
        self.assertEqual(scrub("https://prosecraft.dev/?x=secret#demo")["href"], "https://prosecraft.dev/#demo")

    def test_clean_url_is_left_alone(self):
        for href in ["https://prosecraft.dev/", "https://prosecraft.dev/#rules", "https://prosecraft.dev/?utm_source=test"]:
            result = scrub(href)
            self.assertEqual(result["href"], href)
            self.assertEqual(result["calls"], [])
            self.assertFalse(result["disabled"])

    def test_throwing_replace_state_disables_analytics(self):
        self.assertTrue(scrub("https://prosecraft.dev/?x=secret", replace_state="throw")["disabled"])


if __name__ == "__main__":
    unittest.main()
