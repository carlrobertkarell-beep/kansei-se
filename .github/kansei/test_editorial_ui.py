"""Catch the site-wide navigation and prose patterns removed at the owner's request."""
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
ARROWS = re.compile(r'[←→↑↓↗↘↙↖⇐⇒⇑⇓↔↕➜➝➞➔⟶⟵]')
PROSE = re.compile(r'\s[–—-]\s|,\s+och\b|;\s+[A-Za-zÅÄÖåäö]')


class Reader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.text = []
        self.labels = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        if not self.skip:
            for key, value in attrs:
                if key in ('aria-label', 'title', 'alt') and value:
                    self.labels.append(value)

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.text.append(data)


class EditorialUI(unittest.TestCase):
    def test_navigation_assets(self):
        result = subprocess.run([sys.executable, str(ROOT / '.github/kansei/navigation_check.py')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_public_copy_and_navigation(self):
        problems = []
        checked = 0
        for path in sorted(ROOT.rglob('*.html')):
            relative = path.relative_to(ROOT)
            if any(part.startswith('.') for part in relative.parts):
                continue
            reader = Reader()
            reader.feed(path.read_text())
            checked += 1
            for text in reader.text + reader.labels:
                if ARROWS.search(text) or PROSE.search(text):
                    problems.append(f'{relative}: {text.strip()[:160]}')
        self.assertGreater(checked, 200, 'Expected the full public website')
        self.assertFalse(problems, '\n' + '\n'.join(problems[:35]))


if __name__ == '__main__':
    unittest.main()
