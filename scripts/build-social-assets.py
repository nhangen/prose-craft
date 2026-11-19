#!/usr/bin/env python3
"""
Generate social images, Open Graph cards, and favicons for prosecraft.dev.
Uses Google Chrome headless to render pixel-perfect HTML/CSS templates with
Newsreader, Inter, and JetBrains Mono fonts embedded as base64.
"""

import os
import re
import base64
import urllib.request
import subprocess
from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_ROOT / "site"
TMP_DIR = Path("/tmp/prosecraft-assets")
TMP_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def fetch_embedded_fonts() -> str:
    """Fetch required Google Fonts and inline them as base64 WOFF2."""
    css_url = (
        "https://fonts.googleapis.com/css2?"
        "family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400;1,6..72,600&"
        "family=Inter:wght@400;500;600&"
        "family=JetBrains+Mono:wght@400;500;600&display=swap"
    )
    req = urllib.request.Request(
        css_url,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    )
    css_text = urllib.request.urlopen(req).read().decode("utf-8")

    cache = {}
    def replace_url(match):
        url = match.group(1)
        if url not in cache:
            font_data = urllib.request.urlopen(url).read()
            b64 = base64.b64encode(font_data).decode("ascii")
            cache[url] = f"data:font/woff2;base64,{b64}"
        return f"url({cache[url]})"

    return re.sub(r"url\((https://[^)]+)\)", replace_url, css_text)


def render_og_image(fonts_css: str, output_path: Path):
    """Render 1200x630 Open Graph card with safe margins and mobile-legible typography."""
    html_content = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
{fonts_css}

* {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

body {{
  width: 1200px;
  height: 630px;
  overflow: hidden;
  background: #F5F1E8;
  color: #1A1916;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
  padding: 50px 60px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
}}

.outer-border {{
  position: absolute;
  top: 18px;
  left: 18px;
  right: 18px;
  bottom: 18px;
  border: 1px solid #D9D2C0;
  border-radius: 12px;
  pointer-events: none;
}}

.serif {{
  font-family: 'Newsreader', Georgia, serif;
}}

.mono {{
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}}

.eyebrow {{
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 13px;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: #5C574D;
  font-weight: 500;
}}

.header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #D9D2C0;
  padding-bottom: 18px;
}}

.brand {{
  display: flex;
  align-items: center;
  gap: 16px;
}}

.brand-title {{
  font-size: 34px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: #1A1916;
}}

.brand-subtitle {{
  font-size: 13px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #6E685C;
}}

.pill {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  background: #EDE7D8;
  border: 1px solid #D9D2C0;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 500;
  color: #1A1916;
}}

.dot {{
  display: inline-block;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #B3261E;
}}

.dot-green {{
  background: #1B6B4F;
}}

.main {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 48px;
  margin-top: 6px;
  margin-bottom: 6px;
}}

.left {{
  flex: 1 1 480px;
}}

.headline {{
  font-size: 60px;
  line-height: 1.04;
  letter-spacing: -0.025em;
  font-weight: 400;
  color: #1A1916;
}}

.headline em {{
  font-weight: 600;
  font-style: italic;
}}

.subtitle {{
  margin-top: 20px;
  font-size: 20px;
  line-height: 1.5;
  color: #3D3A33;
  max-width: 460px;
}}

.rules-row {{
  display: flex;
  gap: 12px;
  margin-top: 24px;
}}

.rule-badge {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid #D9D2C0;
  background: #FFFDF7;
  font-size: 13.5px;
  color: #1A1916;
}}

.rule-badge b {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  color: #B3261E;
  letter-spacing: 0.06em;
}}

.right {{
  flex: 0 0 530px;
}}

.card {{
  background: #FFFDF7;
  border: 1px solid #D9D2C0;
  border-radius: 14px;
  padding: 24px 28px;
  box-shadow: 0 1px 0 #D9D2C0, 0 18px 40px -20px rgba(26,25,22,0.22);
}}

.card-sample {{
  margin-top: 10px;
  font-size: 22px;
  line-height: 1.35;
  color: #1A1916;
}}

.seg-bad {{
  background: #F6D9D4;
  color: #7A1710;
  text-decoration: underline wavy #B3261E;
  text-underline-offset: 4px;
  border-radius: 3px;
  padding: 1px 5px;
}}

.seg-fixed {{
  background: #D5EBDD;
  color: #0F4A35;
  border-radius: 3px;
  padding: 1px 5px;
}}

.terminal-box {{
  margin-top: 20px;
  background: #1A1916;
  color: #EAE4D4;
  border-radius: 8px;
  padding: 12px 18px;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  white-space: nowrap;
}}

.status-dot-green {{
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6FCF9F;
}}

/* Footer: right-aligned to keep bottom-left clear of Twitter domain pill */
.footer {{
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 32px;
  border-top: 1px solid #D9D2C0;
  padding-top: 16px;
  font-size: 13px;
  color: #5C574D;
}}
</style>
</head>
<body>
<div class="outer-border"></div>

<!-- Top header -->
<div class="header">
  <div class="brand">
    <span class="serif brand-title">Prose Craft</span>
    <span class="eyebrow brand-subtitle">&middot; Claude Code Plugin &amp; Skill</span>
  </div>
  <div class="pill mono">
    <span>prosecraft.dev</span>
  </div>
</div>

<!-- Main hero content -->
<div class="main">
  <div class="left">
    <div class="eyebrow" style="margin-bottom: 12px;">Two hard rules &middot; Measured habits &middot; Automated filter</div>
    <h1 class="serif headline">Convert AI text into <em>human-friendly prose</em></h1>
    <p class="subtitle">A writing skill and a filter that checks every sentence and sends violations back to your agent until clean.</p>
    <div class="rules-row mono">
      <div class="rule-badge"><b>RULE 1</b> Subject first</div>
      <div class="rule-badge"><b>RULE 2</b> No em dashes</div>
    </div>
  </div>

  <div class="right">
    <div class="card">
      <div class="eyebrow" style="display:flex;align-items:center;gap:8px;">
        <span class="dot"></span>Typical AI draft
      </div>
      <p class="serif card-sample">
        Setup takes one command<br><span class="seg-bad">&mdash; no daemon, no account.</span>
      </p>

      <div style="height:1px;background:#D9D2C0;margin:18px 0;"></div>

      <div class="eyebrow" style="display:flex;align-items:center;gap:8px;color:#1B6B4F;">
        <span class="dot dot-green"></span>Crafted with Prose Craft
      </div>
      <p class="serif card-sample">
        Setup takes one command,<br><span class="seg-fixed">with no daemon and no account.</span>
      </p>

      <div class="terminal-box mono">
        <span style="color:#A8A08C;">$ python3 prose-filter.py check</span>
        <span style="display:flex;align-items:center;gap:8px;color:#6FCF9F;">
          <span class="status-dot-green"></span> 0 violations (exit 0)
        </span>
      </div>
    </div>
  </div>
</div>

<!-- Footer: safe margin from bottom-left corner -->
<div class="footer mono">
  <div>Open source &middot; Zero dependencies &middot; MIT License</div>
  <div>github.com/nhangen/prose-craft</div>
</div>

</body>
</html>
"""
    tmp_html = TMP_DIR / "og-card.html"
    tmp_html.write_text(html_content, encoding="utf-8")

    cmd = [
        CHROME_PATH,
        "--headless",
        "--disable-gpu",
        f"--screenshot={output_path}",
        "--window-size=1200,630",
        "--hide-scrollbars",
        f"file://{tmp_html.resolve()}"
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def render_apple_touch_icon(fonts_css: str, output_path: Path):
    """Render 180x180 Apple Touch Icon (100% opaque RGB, no alpha)."""
    html_content = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
{fonts_css}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  width: 180px;
  height: 180px;
  overflow: hidden;
  background: #1A1916;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}}
.monogram {{
  font-family: 'Newsreader', Georgia, serif;
  font-size: 96px;
  font-weight: 600;
  color: #F5F1E8;
  line-height: 1;
  letter-spacing: -0.04em;
  margin-top: -6px;
}}
.dot {{
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6FCF9F;
  margin-top: 4px;
}}
</style>
</head>
<body>
  <div class="monogram">PC</div>
  <div class="dot"></div>
</body>
</html>
"""
    tmp_html = TMP_DIR / "touch-icon.html"
    tmp_html.write_text(html_content, encoding="utf-8")

    cmd = [
        CHROME_PATH,
        "--headless",
        "--disable-gpu",
        f"--screenshot={output_path}",
        "--window-size=180,180",
        "--hide-scrollbars",
        f"file://{tmp_html.resolve()}"
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Ensure strictly opaque RGB mode for iOS
    im = Image.open(output_path).convert("RGB")
    im.save(output_path)


def generate_favicons(apple_touch_path: Path):
    """Generate favicon-32x32.png, favicon.ico, and favicon.svg."""
    im = Image.open(apple_touch_path).convert("RGB")

    # 32x32 PNG
    fav_32 = im.resize((32, 32), Image.Resampling.LANCZOS)
    fav_32.save(SITE_DIR / "favicon-32x32.png")

    # Multi-size ICO (16, 32, 48)
    im.save(SITE_DIR / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])

    # SVG Favicon
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="7" fill="#1A1916"/>
  <text x="16" y="21.5" font-family="'Newsreader', Georgia, 'Times New Roman', serif" font-size="16" font-weight="600" fill="#F5F1E8" text-anchor="middle" letter-spacing="-0.04em">PC</text>
  <circle cx="16" cy="26" r="1.5" fill="#6FCF9F"/>
</svg>
"""
    (SITE_DIR / "favicon.svg").write_text(svg_content, encoding="utf-8")


def main():
    print("Embedding fonts...")
    fonts_css = fetch_embedded_fonts()

    print("Rendering site/og-image.png (1200x630)...")
    og_path = SITE_DIR / "og-image.png"
    render_og_image(fonts_css, og_path)
    print(f"  OG Image size: {og_path.stat().st_size // 1024} KB")

    print("Rendering site/apple-touch-icon.png (180x180, opaque)...")
    touch_path = SITE_DIR / "apple-touch-icon.png"
    render_apple_touch_icon(fonts_css, touch_path)
    print(f"  Touch Icon size: {touch_path.stat().st_size // 1024} KB")

    print("Generating favicons...")
    generate_favicons(touch_path)

    print("Creating site/.nojekyll...")
    (SITE_DIR / ".nojekyll").touch()

    print("All social assets generated successfully.")


if __name__ == "__main__":
    main()
