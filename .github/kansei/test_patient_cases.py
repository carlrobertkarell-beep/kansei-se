"""Check the complete patient journey and catalogue without a browser."""
from pathlib import Path
import re
import unittest

from unify_case_stories import Tree

ROOT = Path(__file__).resolve().parents[2]


class PatientCases(unittest.TestCase):
    def test_complete_patient_journey_and_links(self):
        cases = []
        for file in (ROOT / 'ultraljud').rglob('index.html'):
            source = file.read_text()
            if not re.search(r'<body\b[^>]*class="[^"]*\bultrasound-case\b', source):
                continue
            cases.append(file)
            with self.subTest(page=str(file.relative_to(ROOT))):
                tree = Tree(source)
                nodes = list(tree.root.walk())
                ids = [n.attrs['id'] for n in nodes if n.attrs.get('id')]
                self.assertEqual(len(ids), len(set(ids)), 'Duplicate HTML/SVG IDs')
                self.assertEqual(sum(n.tag == 'h1' for n in nodes), 1)
                story = next(n for n in nodes if n.has_class('case-story'))
                viewer = next(n for n in nodes if n.attrs.get('id') == 'bilder')
                self.assertLess(story.start, viewer.start)
                self.assertEqual(sum('data-case-education' in n.attrs for n in nodes), 1)
                self.assertTrue(any('data-case-followup' in n.attrs or n.has_class('case-story-follow') for n in nodes))
                self.assertIn('nasta-steg', ids)
                self.assertEqual(sum(n.has_class('case-seo-byline') for n in nodes), 1)
                self.assertEqual(sum(n.has_class('case-library-back') for n in nodes), 1)
                self.assertTrue(any(n.has_class('atlas-case-bottom') for n in nodes))
                nav = next(n for n in nodes if n.has_class('case-page-nav'))
                self.assertIn('#bilder', [n.attrs.get('href') for n in nav.walk()])
                self.assertIn('#nasta-steg', [n.attrs.get('href') for n in nav.walk()])
                for link in (n for n in nodes if n.tag == 'a' and n.attrs.get('href', '').startswith('#')):
                    self.assertIn(link.attrs['href'][1:], ids, 'Broken local link')
        self.assertGreaterEqual(len(cases), 15)
        catalogue = Tree((ROOT / 'ultraljud/bilder/index.html').read_text())
        entries = [n for n in catalogue.root.walk() if n.has_class('atlas-entry')]
        paths = [n.attrs.get('href') for entry in entries for n in entry.walk() if n.tag == 'a' and 'data-atlas-case' in n.attrs]
        self.assertEqual(len(paths), len(set(paths)))
        expected = {'/' + str(file.parent.relative_to(ROOT)) + '/' for file in cases}
        self.assertEqual(set(paths), expected)


if __name__ == '__main__':
    unittest.main()
