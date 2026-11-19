import os
import unittest
from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_ROOT / "site"


class TestSiteSocialMeta(unittest.TestCase):
    def setUp(self):
        self.index_html_path = SITE_DIR / "index.html"
        self.assertTrue(self.index_html_path.exists(), "site/index.html must exist")
        self.html = self.index_html_path.read_text(encoding="utf-8")

    def test_open_graph_tags_present(self):
        required_og = [
            '<meta property="og:type" content="website">',
            '<meta property="og:url" content="https://prosecraft.dev/">',
            '<meta property="og:site_name" content="Prose Craft">',
            '<meta property="og:locale" content="en_US">',
            '<meta property="og:title" content="Prose Craft — Convert AI text into human-friendly prose">',
            '<meta property="og:image" content="https://prosecraft.dev/og-image.png">',
            '<meta property="og:image:type" content="image/png">',
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            'property="og:image:alt"',
        ]
        for tag in required_og:
            self.assertIn(tag, self.html, f"Missing required Open Graph tag or attribute: {tag}")

    def test_twitter_card_tags_present(self):
        required_twitter = [
            '<meta name="twitter:card" content="summary_large_image">',
            '<meta name="twitter:url" content="https://prosecraft.dev/">',
            '<meta name="twitter:title" content="Prose Craft — Convert AI text into human-friendly prose">',
            '<meta name="twitter:image" content="https://prosecraft.dev/og-image.png">',
            'name="twitter:image:alt"',
        ]
        for tag in required_twitter:
            self.assertIn(tag, self.html, f"Missing required Twitter tag: {tag}")

    def test_icons_and_theme_color_present(self):
        required_links = [
            '<link rel="canonical" href="https://prosecraft.dev/">',
            '<link rel="icon" href="/favicon.ico" sizes="32x32">',
            '<link rel="icon" type="image/svg+xml" href="/favicon.svg">',
            '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">',
            '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">',
            '<meta name="theme-color" content="#F5F1E8"',
            '<meta name="theme-color" content="#15140F"',
        ]
        for item in required_links:
            self.assertIn(item, self.html, f"Missing icon/theme tag: {item}")

    def test_og_image_dimensions_and_size(self):
        og_path = SITE_DIR / "og-image.png"
        self.assertTrue(og_path.exists(), "site/og-image.png must exist")

        # Must be strictly under 250KB for WhatsApp / iMessage unfurls
        size_kb = og_path.stat().st_size / 1024
        self.assertLess(size_kb, 250, f"OG image too large: {size_kb:.1f} KB (must be < 250 KB)")

        with Image.open(og_path) as im:
            self.assertEqual(im.size, (1200, 630), "OG image must be 1200x630")
            self.assertEqual(im.format, "PNG", "OG image must be PNG")

    def test_apple_touch_icon_opaque(self):
        touch_path = SITE_DIR / "apple-touch-icon.png"
        self.assertTrue(touch_path.exists(), "site/apple-touch-icon.png must exist")

        with Image.open(touch_path) as im:
            self.assertEqual(im.size, (180, 180), "Apple touch icon must be 180x180")
            self.assertEqual(im.mode, "RGB", "Apple touch icon must be opaque RGB (no alpha)")

    def test_favicon_files_exist(self):
        for filename in ["favicon.ico", "favicon.svg", "favicon-32x32.png", ".nojekyll"]:
            path = SITE_DIR / filename
            self.assertTrue(path.exists(), f"site/{filename} must exist")


if __name__ == "__main__":
    unittest.main()
