#!/usr/bin/env python3
"""Read-only browser smoke checks. Never clicks booking links or submits forms."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

PATHS = ("/", "/naprapati/", "/ultraljud/", "/kontakt/", "/priser/", "/om-oss/", "/reda/", "/reda-rehab/")
SIZES = (("mobile", 390, 844), ("desktop", 1440, 1000))


def check(base, output):
    parsed = urlsplit(base)
    if base not in ("https://www.kansei.se", "http://127.0.0.1:4173", "http://127.0.0.1:4174"):
        raise ValueError("Unapproved test origin")
    baseline_only = base == "http://127.0.0.1:4174"
    output.mkdir(parents=True, exist_ok=True)
    records, errors = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for label, width, height in SIZES:
            context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce", locale="sv-SE")
            def route(req):
                host = urlsplit(req.request.url).hostname or ""
                if host == parsed.hostname or host in ("fonts.googleapis.com", "fonts.gstatic.com"):
                    req.continue_()
                else:
                    req.abort()
            context.route("**/*", route)
            for path in PATHS:
                page = context.new_page()
                js_errors = []
                page.on("pageerror", lambda err: js_errors.append(str(err)[:180]))
                row = {"path": path, "viewport": label, "errors": []}
                try:
                    response = page.goto(base + path, wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(800)
                    page.add_style_tag(content="*,*::before,*::after{animation-duration:0s!important;transition-duration:0s!important;scroll-behavior:auto!important}")
                    if response is None or response.status != 200:
                        row["errors"].append("Page does not return HTTP 200")
                    if page.locator("h1").count() != 1:
                        row["errors"].append("Expected one H1")
                    if not page.title().strip():
                        row["errors"].append("Title missing")
                    dimensions = page.evaluate("({width:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})")
                    row["overflow_px"] = max(0, dimensions["scroll"] - dimensions["width"])
                    if row["overflow_px"] > 3:
                        row["errors"].append("Horizontal overflow")
                    bookings = page.locator('a[href*="bokadirekt.se/"]')
                    row["booking_links"] = bookings.count()
                    if path not in ("/reda/", "/reda-rehab/") and not bookings.count():
                        row["errors"].append("No booking link found")
                    for link in bookings.all():
                        target = urlsplit(link.get_attribute("href") or "")
                        if target.scheme != "https" or target.hostname not in ("www.bokadirekt.se", "bokadirekt.se"):
                            row["errors"].append("Unexpected booking origin")
                    row["broken_visible_images"] = page.locator("img").evaluate_all("els=>els.filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.top<innerHeight&&r.bottom>0&&e.complete&&e.naturalWidth===0}).map(e=>new URL(e.src).pathname)")
                    if row["broken_visible_images"]:
                        row["errors"].append("Broken visible image")

                    if not baseline_only and path == "/reda/":
                        if not page.locator(".reda-portal-top").is_visible():
                            row["errors"].append("Reda portal header missing")
                        if page.locator('body > nav[aria-label="Huvudmeny"]').is_visible():
                            row["errors"].append("Legacy Kansei navigation still visible")
                        if not page.locator("#kodform").is_visible():
                            row["errors"].append("Reda code form missing")
                        if not page.locator(".reda-portal-title").is_visible():
                            row["errors"].append("Current Reda portal title missing")
                        if page.locator(".reda-lockup").count():
                            row["errors"].append("Legacy mixed Reda hero branding still present")
                        if not page.locator('a[href="/reda-rehab/"]').count():
                            row["errors"].append("Reda product link missing")
                        if not page.locator('.reda-portal-links a[href="/"]').count():
                            row["errors"].append("Return-to-Kansei link missing")
                    elif not baseline_only and path == "/reda-rehab/":
                        if not page.locator('header .identity img[src*="/bilder/reda/nav.svg"]').is_visible():
                            row["errors"].append("Current Reda product brand missing")
                        for portal in page.locator('a[href="/reda/"]').all():
                            if portal.get_attribute("target") == "_blank":
                                row["errors"].append("Reda product page opens patient portal in a new tab")
                    elif not baseline_only:
                        bad_internal = page.locator('a[href^="https://www.kansei.se/"],a[href^="https://kansei.se/"]').count()
                        if bad_internal:
                            row["errors"].append("Absolute internal Kansei link found")
                        rehab = page.get_by_role("link", name="Min rehabplan", exact=True)
                        if rehab.count():
                            if rehab.first.get_attribute("href") != "/reda/":
                                row["errors"].append("Min rehabplan has wrong destination")
                            if rehab.first.get_attribute("target") == "_blank":
                                row["errors"].append("Min rehabplan opens a new tab")
                        if page.locator('a.menu-reda[href="/reda-rehab/"]').count() == 0:
                            row["errors"].append("Reda product logo has wrong destination")

                    slug = path.strip("/").replace("/", "-") or "home"
                    page.screenshot(path=str(output / f"{slug}-{label}.png"), full_page=False, animations="disabled")
                    if label == "mobile" and path not in ("/reda/", "/reda-rehab/") and page.locator("button.burger").count() == 1:
                        menu = page.locator("button.burger")
                        if menu.is_visible():
                            menu.click(timeout=5000)
                            page.wait_for_timeout(100)
                            if menu.get_attribute("aria-expanded") != "true":
                                row["errors"].append("Mobile menu does not expose expanded state")
                            page.screenshot(path=str(output / f"{slug}-mobile-menu.png"), animations="disabled")
                    if js_errors:
                        row["errors"].append("JavaScript runtime error")
                        row["js_errors"] = js_errors[:5]
                except Exception as exc:
                    row["errors"].append(type(exc).__name__)
                finally:
                    page.close()
                records.append(row)
                errors.extend(f"{path} {label}: {e}" for e in row["errors"])
            context.close()
        browser.close()
    (output / "report.json").write_text(json.dumps(records, ensure_ascii=False, indent=2))
    print(json.dumps({"checks": len(records), "errors": errors}, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="https://www.kansei.se")
    ap.add_argument("--output", type=Path, default=Path("browser-report"))
    args = ap.parse_args()
    check(args.base, args.output)
