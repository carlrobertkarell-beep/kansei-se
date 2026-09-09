"""Deterministic metadata editor. No shell, tools, arbitrary files or model code."""
from __future__ import annotations
import hashlib
import html
import re
from html.parser import HTMLParser

ALLOWED_PATHS = ("index.html", "naprapati/index.html", "ultraljud/index.html")
FORBIDDEN = re.compile(r"garanter|botar|smärtfri|riskfri|100\s*%|bäst|billigast|rabatt|erbjudande|gratis|\d+\s*(kr|sek)", re.I)

class Refused(ValueError):
    pass

class Snapshot(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.titles, self.descriptions, self.headings = [], [], []
        self._capture = None
        self._parts = []
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("title", "h1"):
            self._capture, self._parts = tag, []
        if tag == "meta" and (attrs.get("name") or "").lower() == "description":
            self.descriptions.append(attrs.get("content") or "")
    def handle_data(self, data):
        if self._capture:
            self._parts.append(data)
    def handle_endtag(self, tag):
        if tag == self._capture:
            value = " ".join("".join(self._parts).split())
            (self.titles if tag == "title" else self.headings).append(value)
            self._capture = None

def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def page_facts(source: str) -> dict:
    s = Snapshot(source)
    if len(s.titles) != 1 or len(s.descriptions) != 1:
        raise Refused("Expected one title and one meta description")
    return {"title": s.titles[0], "description": s.descriptions[0], "h1": s.headings, "sha256": digest(source)}

def meta_spans(source: str, kind: str, key: str) -> list[tuple[int, int]]:
    spans = []
    # Match real attribute boundaries, not words embedded in a content value.
    for tag in re.finditer(r"<meta\b(?:\"[^\"]*\"|'[^']*'|[^'\">])*>", source, re.I):
        attrs = list(re.finditer(r"([\w:-]+)\s*=\s*([\"'])(.*?)\2", tag.group(), re.S))
        data = {a.group(1).lower(): html.unescape(a.group(3)) for a in attrs}
        if data.get(kind, "").lower() == key.lower():
            content = [a for a in attrs if a.group(1).lower() == "content"]
            if len(content) != 1:
                raise Refused("Ambiguous metadata attributes")
            m = content[0]
            spans.append((tag.start() + m.start(3), tag.start() + m.end(3)))
    return spans

def editable_spans(source: str) -> list[tuple[int, int]]:
    spans = [(m.start(1), m.end(1)) for m in re.finditer(r"<title\b[^>]*>(.*?)</title\s*>", source, re.I | re.S)]
    for kind, key in (("name", "description"), ("property", "og:title"), ("property", "og:description"), ("name", "twitter:title"), ("name", "twitter:description")):
        spans += meta_spans(source, kind, key)
    return sorted(spans)

def protected_content(source: str) -> str:
    for start, end in sorted(editable_spans(source), reverse=True):
        source = source[:start] + "[PROTECTED_METADATA_SLOT]" + source[end:]
    return source

def validate_text(value: str, minimum: int, maximum: int):
    if not isinstance(value, str) or not minimum <= len(value) <= maximum:
        raise Refused("Metadata length outside pilot limits")
    if any(ord(c) < 32 for c in value) or any(c in value for c in '<>'):
        raise Refused("Markup or control characters refused")
    if FORBIDDEN.search(value):
        raise Refused("Claim, price or promotional wording requires manual work")
    # This is deliberately NOT a medical-accuracy validator. Every proposal still needs review.

def apply_edit(path: str, source: str, edit: dict) -> str:
    if path not in ALLOWED_PATHS or edit.get("path") != path:
        raise Refused("Path outside allowlist")
    if set(edit) != {"path", "source_sha256", "title", "description"}:
        raise Refused("Unexpected edit fields")
    if digest(source) != edit["source_sha256"]:
        raise Refused("Stale source; nothing overwritten")
    page_facts(source)
    validate_text(edit["title"], 20, 100)
    validate_text(edit["description"], 60, 220)
    replacements = []
    title_matches = list(re.finditer(r"<title\b[^>]*>(.*?)</title\s*>\s*", source, re.I | re.S))
    if len(title_matches) != 1:
        raise Refused("Ambiguous title")
    m = title_matches[0]
    replacements.append((m.start(1), m.end(1), edit["title"]))
    for kind, key, field, required in (
        ("name", "description", "description", True),
        ("property", "og:title", "title", False),
        ("property", "og:description", "description", False),
        ("name", "twitter:title", "title", False),
        ("name", "twitter:description", "description", False),
    ):
        spans = meta_spans(source, kind, key)
        if len(spans) > 1 or (required and len(spans) != 1):
            raise Refused("Ambiguous or absent metadata")
        replacements += [(a, b, edit[field]) for a, b in spans]
    result = source
    for start, end, value in sorted(replacements, reverse=True):
        result = result[:start] + html.escape(value, quote=True) + result[end:]
    if protected_content(source) != protected_content(result):
        raise Refused("Protected page content changed")
    return result

def validate_proposal(proposal: dict, sources: dict[str, str]) -> dict[str, str]:
    if not isinstance(proposal, dict) or set(proposal) != {"summary_sv", "hypothesis_sv", "follow_up_sv", "edits"}:
        raise Refused("Invalid proposal object")
    for name in ("summary_sv", "hypothesis_sv", "follow_up_sv"):
        if not isinstance(proposal[name], str) or len(proposal[name]) > 2000:
            raise Refused("Invalid report field")
    edits = proposal["edits"]
    if not isinstance(edits, list) or len(edits) > 2:
        raise Refused("At most two pages per proposal")
    result = {}
    for edit in edits:
        if not isinstance(edit, dict):
            raise Refused("Invalid edit")
        path = edit.get("path")
        if not isinstance(path, str) or path not in sources or path in result:
            raise Refused("Unknown or duplicate path")
        updated = apply_edit(path, sources[path], edit)
        if updated != sources[path]:
            result[path] = updated
    return result
