import re
import unittest
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent / "site"


class TestSiteAnalytics(unittest.TestCase):
    def setUp(self):
        self.html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        self.js = (SITE_DIR / "app.js").read_text(encoding="utf-8")

    def test_config_carries_sanitized_url_params(self):
        config = re.search(r"gtag\('config',[^;]*?\}\);", self.html, re.S)
        self.assertIsNotNone(config, "gtag config call missing")
        self.assertIn("page_location", config.group(0))
        self.assertIn("page_referrer", config.group(0))
        self.assertIn("send_page_view: false", config.group(0))

    def test_sanitized_url_set_only_on_config(self):
        self.assertNotIn("page_location", self.js)
        self.assertEqual(self.html.count("page_location"), 1)

    def test_page_view_sent_once(self):
        self.assertEqual(self.html.count("gtag('event', 'page_view'"), 1)

    def test_click_handler_ignores_non_primary_click(self):
        self.assertIn('event.type === "click" && event.button !== 0', self.js)

    def test_destination_limited_to_http_schemes(self):
        self.assertIn('url.protocol === "http:" || url.protocol === "https:"', self.js)


if __name__ == "__main__":
    unittest.main()
