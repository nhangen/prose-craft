import re
import unittest
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent / "site"


class TestSiteAnalytics(unittest.TestCase):
    def setUp(self):
        self.html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        self.js = (SITE_DIR / "app.js").read_text(encoding="utf-8")

    def test_config_carries_sanitized_url_params_and_uses_automatic_page_view(self):
        config = re.search(r"gtag\('config',[^;]*?\}\);", self.html, re.S)
        self.assertIsNotNone(config, "gtag config call missing")
        self.assertIn("page_location", config.group(0))
        self.assertIn("page_referrer", config.group(0))
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
