import re
import unittest
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent / "site"


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

    def test_referrer_is_set_to_origin_before_config(self):
        referrer = self.html.index("page_referrer: document.referrer")
        config = self.html.index("gtag('config', 'G-TC0R2KF0H9')")
        self.assertLess(referrer, config)

    def test_config_uses_automatic_page_view(self):
        config = re.search(r"gtag\('config',[^;]*?\);", self.html, re.S)
        self.assertIsNotNone(config, "gtag config call missing")
        self.assertNotIn("send_page_view: false", config.group(0))

    def test_manual_page_view_is_not_sent(self):
        self.assertNotIn("page_location", self.js)
        self.assertNotIn("gtag('event', 'page_view'", self.html)

    def test_click_handler_ignores_non_primary_click(self):
        self.assertIn('event.type === "click" && event.button !== 0', self.js)

    def test_destination_limited_to_http_schemes(self):
        self.assertIn('url.protocol === "http:" || url.protocol === "https:"', self.js)


if __name__ == "__main__":
    unittest.main()
