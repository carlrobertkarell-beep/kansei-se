#!/usr/bin/env python3
"""Read-only SEO regression checks. Standard library only; no credentials needed."""
from __future__ import annotations

import argparse
import json
import re
import time
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = "https://www.kansei.se"
REDIRECTS = {
    "/mot-vart-team/": "/om-oss/",
    "/team-kansei/": "/om-oss/",
    "/kontakt/contact-v1/": "/kontakt/",
    "/kliniken/odenplan/": "/kontakt/",
}


class Page(HTMLParser):
    def __init__(self, text: str) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []
        self.robots = ""
        self.refresh: str | None = None
        self.hrefs: list[str] = []
        self.jsonld: list[str] = []
        self.scripts: list[str] = []
        self.h1 = 0
        self._script: list[str] | None = None
        self._ld = False
        self.feed(text)
        self.close()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "meta":
            if (a.get("name") or "").lower() == "robots":
                self.robots += " " + (a.get("content") or "").lower()
            if (a.get("http-equiv") or "").lower() == "refresh":
                self.refresh = a.get("content") or ""
        if tag == "link" and "canonical" in (a.get("rel") or "").split():
            self.canonicals.append(a.get("href") or "")
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"] or "")
        if tag == "h1":
            self.h1 += 1
        if tag == "script":
            self._script = []
            self._ld = (a.get("type") or "").lower() == "application/ld+json"

    def handle_data(self, data: str) -> None:
        if self._script is not None:
            self._script.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._script is not None:
            text = "".join(self._script)
            self.scripts.append(text)
            if self._ld:
                self.jsonld.append(text)
            self._script = None


def local_path(url: str) -> Path:
    path = unquote(urlsplit(url).path).lstrip("/")
    result = ROOT / path
    if not result.suffix:
        result = result / "index.html"
    result = result.resolve()
    if not result.is_relative_to(ROOT):
        raise AssertionError(f"URL outside site root: {url}")
    return result


def check_404(page: Page) -> None:
    assert page.refresh is None, "404 must not automatically redirect"
    assert not page.canonicals, "404 must not canonicalize to a valid page"
    assert "noindex" in page.robots, "404 requires noindex"
    assert page.h1 == 1, "404 requires one clear heading"
    assert not any(re.search(r"location\s*[.=]", s) for s in page.scripts), "404 JS redirect"
    assert {"/", "/tjanster/", "/kontakt/"} <= set(page.hrefs), "404 navigation missing"


def check_redirect(page: Page, destination: str) -> None:
    assert page.refresh is not None, "Redirect missing"
    match = re.fullmatch(r"\s*0\s*;\s*url\s*=\s*(.+?)\s*", page.refresh, re.I)
    assert match and match.group(1).strip("\"'") == destination, "Incorrect redirect target"
    assert page.canonicals == [ORIGIN + destination], "Incorrect redirect canonical"
    assert "noindex" in page.robots, "Legacy alias requires noindex"


def check_static() -> None:
    files = sorted(ROOT.rglob("*.html"))
    pages: dict[Path, Page] = {}
    blocks = 0
    broken: list[str] = []
    for file in files:
        page = Page(file.read_text(encoding="utf-8"))
        pages[file] = page
        for block in page.jsonld:
            try:
                json.loads(block)
            except json.JSONDecodeError as exc:
                raise AssertionError(f"Invalid JSON-LD: {file.relative_to(ROOT)}: {exc}") from exc
            blocks += 1
        relative = file.relative_to(ROOT).as_posix()
        base = ORIGIN + "/" + (relative[:-10] if relative.endswith("index.html") else relative)
        for href in page.hrefs:
            resolved = urlsplit(urljoin(base, href))
            if resolved.scheme not in {"http", "https"} or resolved.netloc not in {"kansei.se", "www.kansei.se"}:
                continue
            if not local_path(resolved.geturl()).is_file():
                broken.append(f"{relative}: {href}")
    assert not broken, "Missing internal link targets:\n" + "\n".join(sorted(set(broken)))
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [node.text for node in ET.parse(ROOT / "sitemap.xml").findall("s:url/s:loc", namespace)]
    assert len(urls) == len(set(urls)), "Duplicate sitemap URLs"
    for url in urls:
        assert url and url.startswith(ORIGIN + "/"), f"Unexpected sitemap URL: {url}"
        file = local_path(url)
        assert file.is_file(), f"Missing sitemap target: {url}"
        page = pages[file]
        assert "noindex" not in page.robots, f"Noindex URL in sitemap: {url}"
        assert page.refresh is None, f"Redirect URL in sitemap: {url}"
        assert page.canonicals == [url], f"Sitemap/canonical mismatch: {url}"
    check_404(pages[ROOT / "404.html"])
    for source, destination in REDIRECTS.items():
        check_redirect(pages[local_path(source)], destination)
        assert pages[local_path(destination)].refresh is None, f"Redirect chain: {source}"
    print(f"PASS: {len(files)} HTML files; {blocks} JSON-LD blocks parse; {len(urls)} sitemap URLs.")
    print("PASS: internal HTML link targets exist; 404 and four legacy aliases pass regression checks.")
    print("Scope: JSON syntax and static targets only, not schema vocabulary, rankings or external links.")


def fetch_public(path: str) -> tuple[int, Page]:
    request = Request(ORIGIN + path, headers={"User-Agent": "Kansei-SEO-check/126"})
    try:
        with urlopen(request, timeout=20) as response:
            return response.status, Page(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, Page(exc.read().decode("utf-8"))


def check_live() -> None:
    for attempt in range(6):
        try:
            status, page = fetch_public("/__kansei-seo-check-v126-not-found__/")
            assert status == 404, f"Missing URL returned HTTP {status}, expected 404"
            check_404(page)
            for source, destination in REDIRECTS.items():
                status, page = fetch_public(source)
                assert status == 200, f"Legacy alias {source}: HTTP {status}"
                check_redirect(page, destination)
            print("PASS: live HTTP 404 and all four targeted HTML redirects verified.")
            return
        except (AssertionError, OSError, UnicodeError) as exc:
            if attempt == 5:
                raise
            print(f"Waiting for Pages/CDN propagation ({attempt + 1}/6): {exc}", flush=True)
            time.sleep(15)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Check public HTTP responses after deployment")
    args = parser.parse_args()
    check_static()
    if args.live:
        check_live()
