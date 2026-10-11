#!/usr/bin/env python3
"""Regenerate the example preview screenshots.

Usage:
    python3 scripts/screenshots.py

Requires Playwright with Chromium installed:
    pip install playwright && playwright install chromium

Writes examples/before-after/preview-{before,after,index}[-mobile].png
and exits non-zero if any page scrolls horizontally at any tested width.
"""

from __future__ import annotations

import pathlib
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    print("playwright is not installed — run: pip install playwright && playwright install chromium")
    sys.exit(1)

ROOT = pathlib.Path(__file__).resolve().parent.parent
EX = ROOT / "examples" / "before-after"

DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}
WIDTHS = (1440, 1024, 768, 390)


def main() -> int:
    failures: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for page_name in ("before", "after", "index"):
            src = EX / f"{page_name}.html"
            if not src.is_file():
                failures.append(f"{src.name}: missing")
                continue

            for label, viewport in (("", DESKTOP), ("-mobile", MOBILE)):
                page = browser.new_page(viewport=viewport, device_scale_factor=1)
                errors: list[str] = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(src.as_uri())
                page.wait_for_timeout(900)

                out = EX / f"preview-{page_name}{label}.png"
                page.screenshot(path=str(out))
                print(f"wrote {out.relative_to(ROOT)}  {viewport['width']}x{viewport['height']}")

                if errors:
                    failures.append(f"{src.name}: page errors {errors}")

                for w in WIDTHS:
                    page.set_viewport_size({"width": w, "height": 900})
                    page.wait_for_timeout(200)
                    overflow = page.evaluate(
                        "() => document.documentElement.scrollWidth"
                        " - document.documentElement.clientWidth"
                    )
                    if overflow > 0:
                        failures.append(
                            f"{src.name}: horizontal overflow {overflow}px at {w}px"
                        )
                page.close()

        browser.close()

    if failures:
        print("\nFAILURES")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("\nall pages render with no horizontal overflow at " + ", ".join(f"{w}px" for w in WIDTHS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
