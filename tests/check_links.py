"""
Broken-link / broken-asset checker for the Webcraft Studio site.

Walks every .html file in the project and checks that every local
href/src/action reference (relative links, images, stylesheets, scripts,
form actions) resolves to a real file on disk. External links (http/https),
mailto:, tel:, data:, and pure anchor links (#section) are skipped, since
those aren't local files to check.

Usage:
    python tests/check_links.py

Exit code 0 if everything resolves, 1 if anything is broken (so this can
be used as a pass/fail check, e.g. before committing).
"""

import os
import re
import sys
from urllib.parse import urlsplit, unquote

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ATTR_PATTERN = re.compile(r'(?:href|src|action)\s*=\s*"([^"]+)"', re.IGNORECASE)

# Folders that intentionally have their own independent asset references
# (concept projects are self-contained demo sites, not part of the main
# site's link graph) and folders that shouldn't be scanned at all.
SKIP_DIRS = {".git"}


def is_external(url):
    return (
        url.startswith("http://") or url.startswith("https://") or
        url.startswith("mailto:") or url.startswith("tel:") or
        url.startswith("data:") or url.startswith("#") or
        url.startswith("//")
    )


def find_html_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f.endswith(".html"):
                yield os.path.join(dirpath, f)


def main():
    broken = []
    checked = 0
    external_skipped = 0

    html_files = list(find_html_files(SITE_ROOT))

    for html_path in html_files:
        with open(html_path, encoding="utf-8") as fh:
            content = fh.read()
        base_dir = os.path.dirname(html_path)
        for match in ATTR_PATTERN.finditer(content):
            raw_url = match.group(1)
            url = urlsplit(raw_url).path  # strip query/fragment
            if is_external(raw_url):
                external_skipped += 1
                continue
            if not url:
                continue  # pure fragment link like "#main"
            checked += 1
            resolved = os.path.normpath(os.path.join(base_dir, unquote(url)))
            if not os.path.exists(resolved):
                rel_html = os.path.relpath(html_path, SITE_ROOT)
                broken.append((rel_html, raw_url, resolved))

    print(f"HTML files scanned: {len(html_files)}")
    print(f"Local references checked: {checked}")
    print(f"External/mailto/anchor references skipped: {external_skipped}")
    print()
    if broken:
        print(f"BROKEN REFERENCES FOUND: {len(broken)}")
        for rel_html, raw_url, resolved in broken:
            print(f"  {rel_html}  ->  {raw_url}   (resolved: {resolved})")
        return 1
    else:
        print("No broken local references found.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
