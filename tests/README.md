# Tests

Lightweight checks for this static site. No dependencies beyond Python 3's standard library — nothing to install.

## Automated checks

Run from the project root (or from anywhere — both scripts locate the site root automatically):

```bash
python tests/check_links.py
```
Walks every `.html` file and confirms every local `href`/`src`/`action` reference resolves to a real file. Catches typos in links, images pointing at moved/renamed files, etc. External links, `mailto:`, `tel:`, and anchor-only links are skipped (not local files to check). No internet connection required.

```bash
python tests/validate_html.py
```
Sends every page to the [W3C Nu Html Checker](https://validator.w3.org/nu/) and reports real HTML errors (invalid attributes, heading-hierarchy skips, malformed markup, etc.). Requires an internet connection, and is polite to the free public validator (small delay between requests) — expect it to take a minute or two for the whole site.

Run both before committing anything that touches HTML.

```bash
python tests/test_interactive.py
```
Real automated functional tests for the interactive behaviors — mobile nav toggle, the currency converter, scroll-reveal/count-up animations, and the contact form's JS wiring. Uses [Playwright](https://playwright.dev) driving your **already-installed Chrome** (no separate browser download — see setup below). Produces genuine pass/fail results with real assertions, not something you have to eyeball in a screenshot.

The contact form check intercepts the network request instead of letting it reach Formspree, so running this repeatedly won't spam your inbox with test submissions.

**One-time setup:**
```bash
pip install playwright
```
That's it — no `playwright install` step needed, since the script uses `channel="chrome"` to drive your existing Chrome rather than downloading its own browser.

**Requires a local server running first**, e.g. from the project root:
```bash
python -m http.server 8765
```

```bash
python tests/mobile_device_check.py [base_url]
```
Real-device-emulation mobile check — uses Playwright's built-in device profiles (currently iPhone 14 and Pixel 7), which set real device pixel ratio, user agent, and touch capability, not just a resized viewport. Checks every real page for horizontal overflow, HTTP errors, and console/JS errors, and saves a full-page screenshot of each to `tests/mobile-screenshots/<device>/` for manual visual review — **always look at the screenshots yourself, not just the pass/fail line**, since the automated checks (overflow width, console errors) can't catch everything a human eye would (e.g. the fixed mobile CTA bar genuinely overlapping content mid-scroll was only caught by looking at a screenshot and then confirming with real per-element bounding-box math, not by the overflow check). Defaults to the live production site; pass `http://localhost:8765` to test local changes before pushing.

## Manual QA checklist

See `manual-qa-checklist.md` in this folder — things that need a real look (visual layout, animations, actually submitting the contact form) rather than an automated script.
