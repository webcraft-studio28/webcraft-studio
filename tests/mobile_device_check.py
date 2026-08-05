"""
Real-device-emulation mobile check.

Unlike a plain viewport resize (which only changes pixel dimensions),
Playwright's built-in device profiles also set the real device pixel
ratio, user agent, and touch capability of an actual phone — closer to
what a visitor's real phone renders than a manual --width flag.

Checks every real page on the site (skips concept-project demos and
the private outreach one-pager, same convention as the other test
scripts) for horizontal overflow and console/JS errors, and saves a
full-page screenshot of each for manual visual review.

Usage:
    python tests/mobile_device_check.py [base_url]
    (base_url defaults to the live production site)

Screenshots are written to tests/mobile-screenshots/<device>/<page>.png
(gitignored-friendly location — these are for eyeballing, not committed).

Exit code 0 if no overflow/console errors found, 1 otherwise.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "https://webcraft-studio28.github.io/webcraft-studio"

PAGES = [
    "index.html", "about.html", "services.html", "portfolio.html",
    "contact.html", "blog.html", "404.html", "privacy.html", "terms.html",
    "blog/hiring-a-freelance-web-designer/index.html",
    "blog/seo-mistakes-small-business-websites/index.html",
    "blog/website-speed-core-web-vitals/index.html",
    "blog/how-much-should-a-small-business-website-cost/index.html",
]

DEVICES = ["iPhone 14", "Pixel 7"]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "mobile-screenshots")

issues = []

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    for device_name in DEVICES:
        device = p.devices[device_name]
        context = browser.new_context(**device)
        page = context.new_page()
        errors = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        device_dir = os.path.join(OUT_DIR, device_name.replace(" ", "_"))
        os.makedirs(device_dir, exist_ok=True)

        for path in PAGES:
            errors.clear()
            resp = page.goto(f"{BASE_URL}/{path}", wait_until="networkidle")
            page.wait_for_timeout(300)

            # scroll through to trigger scroll-reveal animations before
            # screenshotting, otherwise below-fold content shows as blank
            height = page.evaluate("document.body.scrollHeight")
            y = 0
            while y < height:
                page.evaluate(f"window.scrollTo(0, {y})")
                page.wait_for_timeout(80)
                y += 500
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(200)

            sw = page.evaluate("document.documentElement.scrollWidth")
            cw = page.evaluate("document.documentElement.clientWidth")
            overflow = sw - cw

            status = resp.status if resp else None
            fname = path.replace("/", "_")
            page.screenshot(path=os.path.join(device_dir, fname + ".png"), full_page=True)

            flags = []
            if overflow > 2:
                flags.append(f"OVERFLOW {overflow}px")
            if status and status >= 400:
                flags.append(f"HTTP {status}")
            if errors:
                flags.append(f"{len(errors)} console error(s)")

            marker = "FAIL" if flags else "OK"
            print(f"[{marker}] {device_name} - {path}" + (f"  ({', '.join(flags)})" if flags else ""))
            if flags:
                issues.append((device_name, path, flags))

        context.close()
    browser.close()

print(f"\nScreenshots saved to: {OUT_DIR}")
print(f"\n{'='*60}")
if issues:
    print(f"{len(issues)} issue(s) found across {len(DEVICES)} devices x {len(PAGES)} pages.")
    sys.exit(1)
else:
    print(f"No overflow, HTTP, or console errors across {len(DEVICES)} devices x {len(PAGES)} pages.")
    sys.exit(0)
