#!/usr/bin/env python3
"""
Logo Fetcher — downloads company logos from multiple CDN sources.
Cross-platform (Windows + macOS + Linux). Uses requests → curl → PowerShell fallback chain.

Usage (standalone):
    python fetch_logo.py "The Trade Desk" thetradedesk.com
    python fetch_logo.py "FanDuel" --url "https://cdn.example.com/fanduel.png"

Imported usage:
    from scripts.fetch_logo import fetch_logo, get_optimove_logo_png
    logo_path = fetch_logo("Mixpanel", domain="mixpanel.com")
    logo_path = fetch_logo("FanDuel", direct_url="https://...")
"""

import sys
import re
import os
import tempfile
import subprocess
from pathlib import Path

# ── Cross-platform cache dir ───────────────────────────────────────────────────
CACHE_DIR = Path(tempfile.gettempdir()) / "optimove_logos"



def make_styled_text_logo(name: str, out_path: Path,
                           width: int = 320, height: int = 80) -> bool:
    """
    Generate a clean styled brand-name image as a logo fallback.
    Transparent background, dark text, Signal Mist accent underline.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)

        font = None
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    font = ImageFont.truetype(fp, 22)
                    break
                except Exception:
                    pass
        if font is None:
            font = ImageFont.load_default()

        text = name.upper()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (width - tw) / 2
        y = (height - th) / 2 - 4
        draw.text((x, y), text, fill=(17, 17, 17, 240), font=font)

        img.save(str(out_path), "PNG")
        return True
    except Exception as e:
        print(f"  ⚠️  Styled fallback failed: {e}")
        return False

# ── Known domain overrides ─────────────────────────────────────────────────────
DOMAIN_MAP = {
    "the trade desk":    "thetradedesk.com",
    "trade desk":        "thetradedesk.com",
    "tradedesk":         "thetradedesk.com",
    "mixpanel":          "mixpanel.com",
    "klaviyo":           "klaviyo.com",
    "amplitude":         "amplitude.com",
    "segment":           "segment.com",
    "salesforce":        "salesforce.com",
    "braze":             "braze.com",
    "twilio":            "twilio.com",
    "sendgrid":          "sendgrid.com",
    "google":            "google.com",
    "facebook":          "facebook.com",
    "meta":              "meta.com",
    "tiktok":            "tiktok.com",
    "snapchat":          "snapchat.com",
    "twitter":           "twitter.com",
    "x (twitter)":       "twitter.com",
    "appsflyer":         "appsflyer.com",
    "adjust":            "adjust.com",
    "airship":           "airship.com",
    "iterable":          "iterable.com",
    "attentive":         "attentivemobile.com",
    "postscript":        "postscript.io",
    "cordial":           "cordial.com",
    "insider":           "useinsider.com",
    "moengage":          "moengage.com",
    "clevertap":         "clevertap.com",
    "bloomreach":        "bloomreach.com",
    "emarsys":           "emarsys.com",
    "cheetah digital":   "cheetahdigital.com",
    "jabra gn":          "jabra.com",
    "jabra":             "jabra.com",
    "tesco bank":        "tesco.com",
    "tesco":             "tesco.com",
    "fanduel":           "fanduel.com",
    "sephora":           "sephora.com",
    "sodastream":        "sodastream.com",
    "staples":           "staples.com",
    "hubspot":           "hubspot.com",
    "marketo":           "marketo.com",
    "adobe":             "adobe.com",
    "tableau":           "tableau.com",
    "looker":            "looker.com",
    "databricks":        "databricks.com",
    "snowflake":         "snowflake.com",
    "aws":               "aws.amazon.com",
    "azure":             "microsoft.com",
    "google cloud":      "cloud.google.com",
}


def infer_domain(partner_name: str) -> str:
    key = partner_name.lower().strip()
    if key in DOMAIN_MAP:
        return DOMAIN_MAP[key]
    cleaned = re.sub(r'[^a-z0-9]', '', key)
    return f"{cleaned}.com"


def _download(url: str, out_path: Path) -> bool:
    """
    Download a URL to out_path.
    Tries: requests → curl → wget → PowerShell (Windows).
    Returns True if a valid image file was saved.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; OptimoveSkill/1.0)"}

    # 1. Python requests
    try:
        import requests
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if r.status_code == 200 and len(r.content) > 300:
            out_path.write_bytes(r.content)
            if _looks_like_image(out_path):
                return True
    except Exception:
        pass

    # 2. curl
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "12",
             "-A", headers["User-Agent"],
             "-o", str(out_path), url],
            capture_output=True, timeout=15,
        )
        if result.returncode == 0 and out_path.exists() and _looks_like_image(out_path):
            return True
    except Exception:
        pass

    # 3. wget
    try:
        result = subprocess.run(
            ["wget", "-q", "--timeout=12", f"--user-agent={headers['User-Agent']}",
             "-O", str(out_path), url],
            capture_output=True, timeout=15,
        )
        if result.returncode == 0 and out_path.exists() and _looks_like_image(out_path):
            return True
    except Exception:
        pass

    # 4. PowerShell (Windows fallback)
    try:
        ps_cmd = (
            f"Invoke-WebRequest -Uri '{url}' "
            f"-OutFile '{out_path}' "
            f"-UserAgent '{headers['User-Agent']}' -UseBasicParsing"
        )
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True, timeout=15,
        )
        if result.returncode == 0 and out_path.exists() and _looks_like_image(out_path):
            return True
    except Exception:
        pass

    return False


def _looks_like_image(path: Path) -> bool:
    """Check if a file has a valid image magic bytes header."""
    if not path.exists() or path.stat().st_size < 300:
        return False
    try:
        header = path.read_bytes()[:16]
        # PNG, JPEG, GIF, WebP, SVG, ICO
        return (
            header[:4] == b'\x89PNG' or
            header[:3] == b'\xff\xd8\xff' or
            header[:6] in (b'GIF87a', b'GIF89a') or
            header[4:8] == b'ftyp' or
            header[:4] == b'RIFF' or
            header[:5] == b'<?xml' or
            header[:4] == b'<svg' or
            b'<svg' in header[:200] or
            header[:2] == b'\x00\x00'  # ICO
        )
    except Exception:
        return False


def fetch_logo(
    partner_name: str,
    domain: str = None,
    direct_url: str = None,
    size: int = 128,
    force: bool = False,
) -> str | None:
    """
    Fetch a company logo. Priority:
      1. direct_url (if Claude pre-found a URL via web search)
      2. logo.dev CDN
      3. Clearbit CDN
      4. Brandfetch CDN
      5. SeekLogo (requires HTML scrape — skipped; Claude handles this)

    Returns the local file path (PNG), or None if nothing worked.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if not domain:
        domain = infer_domain(partner_name)

    safe_name = re.sub(r'[^\w]', '_', partner_name.lower())
    cache_path = CACHE_DIR / f"{safe_name}.png"

    if cache_path.exists() and not force:
        if _looks_like_image(cache_path):
            print(f"  ✅ Logo cached: {cache_path.name}")
            return str(cache_path)

    # ── 1. Direct URL (Claude pre-fetched this via web search) ────────────────
    if direct_url:
        print(f"  Trying direct URL: {direct_url}")
        tmp = CACHE_DIR / f"{safe_name}_direct.png"
        if _download(direct_url, tmp):
            tmp.rename(cache_path)
            print(f"  ✅ Logo from direct URL: {cache_path.name}")
            return str(cache_path)

    # ── 2. logo.dev (most reliable free CDN) ─────────────────────────────────
    logo_dev_url = f"https://img.logo.dev/{domain}?token=pk_X0Rgq0eAQiOHzOGEE5KZjg=="
    print(f"  Trying logo.dev: {domain}")
    if _download(logo_dev_url, cache_path):
        print(f"  ✅ Logo via logo.dev: {cache_path.name}")
        return str(cache_path)

    # ── 3. Clearbit ───────────────────────────────────────────────────────────
    for url in [
        f"https://logo.clearbit.com/{domain}?size={size}",
        f"https://logo.clearbit.com/{domain}",
    ]:
        print(f"  Trying Clearbit: {domain}")
        if _download(url, cache_path):
            print(f"  ✅ Logo via Clearbit: {cache_path.name}")
            return str(cache_path)

    # ── 4. Brandfetch CDN ────────────────────────────────────────────────────
    for url in [
        f"https://cdn.brandfetch.io/{domain}/w/400/h/400",
        f"https://cdn.brandfetch.io/{domain}/w/200/h/200",
    ]:
        print(f"  Trying Brandfetch: {domain}")
        if _download(url, cache_path):
            print(f"  ✅ Logo via Brandfetch: {cache_path.name}")
            return str(cache_path)

    # All CDNs failed — generate a styled text logo as fallback
    if make_styled_text_logo(partner_name, cache_path):
        print(f"  ℹ️  Using styled text logo for '{partner_name}' (CDN unavailable in sandbox)")
        return str(cache_path)
    print(f"  ⚠️  Could not fetch or generate logo for '{partner_name}'")
    return None


def get_optimove_logo_png(height_px: int = 60) -> str | None:
    """Convert the Optimove SVG logo to PNG. Returns the PNG path or None."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CACHE_DIR / f"optimove_logo_{height_px}.png"

    if out_path.exists() and _looks_like_image(out_path):
        return str(out_path)

    skill_dir = Path(__file__).parent.parent
    svg_candidates = [
        skill_dir / "assets" / "logos" / "optimove-blue-logo.svg",
        skill_dir.parent / "optimove-brand-bible" / "references" / "blue-logo.svg",
    ]
    # Also search installed skills path
    for p in Path(tempfile.gettempdir()).parent.glob("**/optimove-brand-bible/references/blue-logo.svg"):
        svg_candidates.append(p)

    svg_path = next((p for p in svg_candidates if p.exists()), None)
    if not svg_path:
        print("  ⚠️  Optimove SVG not found")
        return None

    # Try cairosvg
    try:
        import cairosvg
        cairosvg.svg2png(url=str(svg_path), write_to=str(out_path), output_height=height_px)
        if _looks_like_image(out_path):
            print(f"  ✅ Optimove logo rendered via cairosvg")
            return str(out_path)
    except Exception as e:
        print(f"  ⚠️  cairosvg: {e}")

    # Try svglib
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
        drawing = svg2rlg(str(svg_path))
        if drawing:
            scale = height_px / drawing.height
            drawing.width *= scale
            drawing.height *= scale
            drawing.transform = (scale, 0, 0, scale, 0, 0)
            renderPM.drawToFile(drawing, str(out_path), fmt="PNG")
            if _looks_like_image(out_path):
                print(f"  ✅ Optimove logo rendered via svglib")
                return str(out_path)
    except Exception as e:
        print(f"  ⚠️  svglib: {e}")

    # Last resort: Pillow SVG via CairoSVG binary
    try:
        result = subprocess.run(
            ["cairosvg", str(svg_path), "-o", str(out_path),
             "--output-height", str(height_px)],
            capture_output=True, timeout=10,
        )
        if result.returncode == 0 and _looks_like_image(out_path):
            print(f"  ✅ Optimove logo via cairosvg CLI")
            return str(out_path)
    except Exception:
        pass

    return None
