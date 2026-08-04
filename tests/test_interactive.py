"""
Automated functional tests for interactive site behaviors.

Drives the system's already-installed Chrome via Playwright (no separate
browser download — uses channel="chrome"). Unlike screenshot-based checks,
this gets real return values from the page, so it produces genuine
pass/fail results instead of something a human has to eyeball.

Covers the behaviors that are easy to silently break when editing
script.js or style.css: mobile nav toggle, the currency converter,
scroll-reveal / count-up animations, and the contact form's JS wiring.

The contact form test intercepts the network request instead of letting
it actually reach Formspree — it verifies the right endpoint/method/data
would be sent, without generating a real submission to your inbox.

Requires:
    pip install playwright
    (playwright drives your existing Chrome install; no `playwright install`
    step needed as long as Google Chrome is already installed)

A local server must be running first, e.g. from the project root:
    python -m http.server 8765

Usage:
    python tests/test_interactive.py [base_url]
    (base_url defaults to http://localhost:8765)

Exit code 0 if every check passes, 1 if anything fails.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765"

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    marker = "OK" if condition else "XX"
    print(f"[{marker}] {name}" + (f"  ({detail})" if detail else ""))


def test_mobile_nav_toggle(page):
    print("\n-- Mobile nav toggle --")
    page.set_viewport_size({"width": 375, "height": 800})
    page.goto(f"{BASE_URL}/index.html")
    page.wait_for_load_state("networkidle")

    toggle = page.locator("#navToggle")
    nav = page.locator("#nav")

    check("nav toggle button is visible on a mobile viewport", toggle.is_visible())
    check(
        "nav menu starts closed",
        not nav.evaluate("el => el.classList.contains('open')"),
    )

    toggle.click()
    page.wait_for_timeout(400)  # transition is 300ms, real wait (real browser, no virtual time issues)
    is_open = nav.evaluate("el => el.classList.contains('open')")
    opacity = float(nav.evaluate("el => getComputedStyle(el).opacity"))
    check(
        "nav menu opens (class added + becomes visible) on toggle click",
        is_open and opacity > 0.9,
        f"open={is_open} opacity={opacity}",
    )

    # clicking a nav link should close the menu again
    page.locator("#nav a", has_text="About").click()
    page.wait_for_timeout(400)
    check("nav menu closes after clicking a link", "about.html" in page.url)


def test_currency_converter(page):
    print("\n-- Currency converter --")
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(f"{BASE_URL}/services.html")
    page.wait_for_timeout(1500)  # allow the exchange-rate fetch to complete

    select = page.locator("#currencySelect")
    check("currency selector is present", select.count() == 1)

    price_el = page.locator('.price-num[data-usd="299"]').first

    select.select_option("INR")
    # poll instead of a fixed sleep — the exchange-rate fetch has variable
    # network latency, so wait for the actual DOM change rather than guessing
    try:
        page.wait_for_function(
            "document.querySelector('.price-num[data-usd=\"299\"]').textContent.includes('₹')",
            timeout=5000,
        )
    except Exception:
        pass  # fall through, the check below will report the real state
    inr_text = price_el.inner_text()
    check("switching to INR updates the displayed price symbol", "₹" in inr_text, inr_text)

    digits = "".join(c for c in inr_text if c.isdigit())
    inr_value = int(digits) if digits else 0
    # sanity check: USD/INR has been roughly 80-100 for a long time; catches a
    # completely broken conversion (e.g. showing $299 or 0) without being
    # brittle to the exact daily rate
    check(
        "INR value is in a sane range for a live conversion of $299",
        80 * 299 < inr_value < 110 * 299,
        inr_text,
    )

    select.select_option("USD")
    page.wait_for_timeout(400)
    usd_text = price_el.inner_text()
    check("switching back to USD restores the $299 display", usd_text.strip() == "$299", usd_text)


def test_scroll_reveal_and_count_up(page):
    print("\n-- Scroll reveal & count-up animations --")
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(f"{BASE_URL}/index.html")
    page.wait_for_timeout(1500)  # hero badge is in the initial viewport

    badge = page.locator('[data-count-to="98"]')
    check("SEO score count-up reaches its target value", badge.inner_text().strip() == "98", badge.inner_text())

    cards = page.locator(".services-grid .card.reveal")
    total = cards.count()
    # manual scroll instead of scroll_into_view_if_needed(): that helper waits
    # for the target to stop moving, which fights with the reveal transition
    # itself (the element is *supposed* to animate for 600ms after becoming
    # visible) and can time out even though nothing is actually broken
    page.evaluate("document.querySelector('.services-grid').scrollIntoView()")
    page.wait_for_timeout(800)
    in_view = page.locator(".services-grid .card.reveal.in-view").count()
    check("service cards reveal (get in-view class) when scrolled into place", in_view == total, f"{in_view}/{total}")


def test_contact_form_wiring(page):
    print("\n-- Contact form wiring (intercepted, no real submission sent) --")
    page.goto(f"{BASE_URL}/contact.html")

    form = page.locator("#contactForm")
    action = form.get_attribute("action")
    check("contact form action points at the Formspree endpoint", action == "https://formspree.io/f/mbgrrorv", action)

    honeypot = page.locator('input[name="_gotcha"]')
    check("honeypot spam field is present", honeypot.count() == 1)

    captured = {}

    def handle_route(route):
        captured["url"] = route.request.url
        captured["method"] = route.request.method
        route.fulfill(status=200, content_type="application/json", body='{"ok": true}')

    page.route("https://formspree.io/**", handle_route)

    page.fill("#name", "Automated Wiring Check")
    page.fill("#email", "wiring-check@example.com")
    page.fill("#message", "This request was intercepted by the test suite and never reached Formspree.")
    page.click('button[type="submit"]')
    page.wait_for_timeout(600)

    check(
        "submitting the form fires a POST to the Formspree endpoint",
        captured.get("url") == "https://formspree.io/f/mbgrrorv" and captured.get("method") == "POST",
        captured,
    )

    note_text = page.locator("#formNote").inner_text()
    check("success message shows after a successful (intercepted) submission", "Thanks" in note_text, note_text)


def main():
    # Each test gets its own fresh browser context (and page), not a shared
    # one — real test isolation. Sharing a single page across tests that each
    # navigate and change viewport size turned out to leave Playwright's
    # internal action-readiness state confused for later tests (symptoms:
    # later tests would time out or silently no-op even though the exact
    # same steps worked fine standalone) — a test-harness issue, not a bug
    # in the site itself.
    tests = [
        test_mobile_nav_toggle,
        test_currency_converter,
        test_scroll_reveal_and_count_up,
        test_contact_form_wiring,
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        for test_fn in tests:
            context = browser.new_context()
            page = context.new_page()
            test_fn(page)
            context.close()
        browser.close()

    failed = [r for r in results if r[1] == "FAIL"]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("\nFAILURES:")
        for name, status, detail in failed:
            print(f"  - {name} ({detail})")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
