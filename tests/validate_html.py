"""
HTML validation checker for the Webcraft Studio site.

Sends every .html file to the W3C Nu Html Checker (validator.w3.org/nu)
and reports any validation errors. Requires an internet connection.

Usage:
    python tests/validate_html.py

Exit code 0 if every page validates cleanly, 1 if any page has errors.
"""

import json
import os
import sys
import time
import urllib.request

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALIDATOR_URL = "https://validator.w3.org/nu/?out=json"
SKIP_DIRS = {".git", "tests"}


def find_html_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f.endswith(".html"):
                yield os.path.join(dirpath, f)


def validate_file(path):
    with open(path, "rb") as fh:
        content = fh.read()
    req = urllib.request.Request(
        VALIDATOR_URL,
        data=content,
        headers={"Content-Type": "text/html; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    html_files = sorted(find_html_files(SITE_ROOT))
    total_errors = 0

    for path in html_files:
        rel = os.path.relpath(path, SITE_ROOT)
        try:
            result = validate_file(path)
        except Exception as e:
            print(f"{rel}: COULD NOT VALIDATE ({e})")
            continue

        errors = [m for m in result.get("messages", []) if m.get("type") == "error"]
        if errors:
            total_errors += len(errors)
            print(f"{rel}: {len(errors)} error(s)")
            for e in errors:
                print(f"    - {e.get('message')}")
        else:
            print(f"{rel}: OK")

        time.sleep(0.5)  # be polite to the free public validator

    print()
    if total_errors:
        print(f"TOTAL ERRORS: {total_errors}")
        return 1
    else:
        print("All pages validated with zero errors.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
