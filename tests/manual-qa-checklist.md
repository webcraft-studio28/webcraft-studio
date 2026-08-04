# Manual QA Checklist

Things worth checking by eye/hand — not automatable, but repeatable. Run through this after any significant change, before pushing.

## Every page loads

- [ ] Home, About, Services, Portfolio, Contact, Blog, 404, Privacy, Terms
- [ ] All 3 blog posts
- [ ] Both concept projects (Amber & Oak, Pulse)

## Navigation

- [ ] Desktop nav links go to the right page, "active" state highlights the current page
- [ ] Mobile (narrow window, or resize browser < 720px): hamburger icon appears, tapping it opens the menu, tapping a link closes it and navigates
- [ ] Logo always links back to Home

## Contact form

- [ ] Fill out and submit a real test message — confirm the "Sending... / Thanks!" flow works and a submission actually lands in the Formspree inbox
- [ ] Try submitting with a required field empty — browser validation should block it
- [ ] "Trouble sending? Email directly" fallback link works

## Pricing / currency converter (Services page)

- [ ] Prices count up when scrolled into view
- [ ] Currency dropdown switches between USD/GBP/INR and prices update
- [ ] "Approximate — quotes and invoices are in USD" note is visible

## Responsive layout

- [ ] Resize the browser from wide to narrow on a few pages (Home, Services, Portfolio) — check nothing overlaps, text doesn't overflow its container, images/cards reflow to fewer columns
- [ ] Sticky mobile "Get in Touch" bar appears at the bottom on narrow widths and doesn't cover page content

## Animations

- [ ] Cards/sections fade in as you scroll (staggered, not all at once)
- [ ] Hovering icons/buttons/portfolio thumbnails shows a subtle motion response
- [ ] With OS "reduce motion" turned on, everything should just appear instantly with no animation (no broken/invisible content)

## Cross-page consistency

- [ ] Footer is identical on every page (links, email, copyright year)
- [ ] Favicon shows correctly in the browser tab
- [ ] Logo/wordmark looks correct in header and footer on every page

## Known non-issues (don't re-report these)

- Headless-browser screenshot testing tools can show native `<select>` dropdowns as solid black boxes, and can show CSS transitions/animations "frozen" mid-state (e.g. mobile nav opacity stuck at 0, count-up numbers stuck mid-count). These are testing-tool artifacts (specifically, Chrome's `--virtual-time-budget` flag not properly driving compositor-based animations), not real bugs — always verify with a real browser or computed-style inspection with the animation/transition temporarily removed before treating these as real issues.
- If `tests/test_interactive.py` ever shows several unrelated tests failing together (e.g. currency switch stops working, reveal animations stop firing, a button click hangs for 30s) — check whether the tests are sharing one Playwright `page`/context across multiple navigations first. This happened once during development: every feature worked perfectly in isolation, but failed when 4 tests shared one page object across sequential `page.goto()` calls and viewport changes. Giving each test its own fresh `browser.new_context()` fixed it immediately. It was a test-harness state leak, not a site bug — don't go looking for a site bug first if this pattern shows up again.
