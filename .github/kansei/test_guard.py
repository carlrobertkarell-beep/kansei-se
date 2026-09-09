import subprocess
from pathlib import Path
import tempfile
import unittest
from guard_ai import guard
from safety import Refused

SOURCE = '<html><head><title>Naprapat Odenplan | Kansei Rehabcenter</title><meta name="description" content="Legitimerad naprapat vid Odenplan. Undersökning och rehabilitering på Kansei Rehabcenter."></head><body><h1>Naprapati</h1><p>890 kr</p><a href="https://www.bokadirekt.se/places/kansei-rehabcenter-48847">Boka</a></body></html>'

class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.before = Path(self.temp.name) / 'before'
        self.after = Path(self.temp.name) / 'after'
        for root in (self.before,self.after):
            root.mkdir()
            subprocess.run(['git','init','-q',str(root)],check=True)
            (root/'index.html').write_text(SOURCE)
            subprocess.run(['git','-C',str(root),'add','.'],check=True)
    def modify(self,text):
        (self.after/'index.html').write_text(text)
    def test_metadata_passes(self):
        self.modify(SOURCE.replace('Naprapat Odenplan |','Naprapat vid Odenplan |'))
        guard(self.before,self.after)
    def test_untracked_pycache_does_not_block(self):
        (self.before/'__pycache__').mkdir()
        (self.before/'__pycache__/safety.pyc').write_bytes(b'cache')
        self.test_metadata_passes()
    def test_price_change_blocked(self):
        self.modify(SOURCE.replace('890 kr','790 kr'))
        with self.assertRaises(Refused):guard(self.before,self.after)
    def test_booking_change_blocked(self):
        self.modify(SOURCE.replace('www.bokadirekt.se','example.com'))
        with self.assertRaises(Refused):guard(self.before,self.after)
    def test_workflow_change_blocked(self):
        (self.after/'bad.yml').write_text('new workflow')
        subprocess.run(['git','-C',str(self.after),'add','.'],check=True)
        with self.assertRaises(Refused):guard(self.before,self.after)
    def test_symlink_blocked(self):
        (self.after/'link').symlink_to('index.html')
        subprocess.run(['git','-C',str(self.after),'add','.'],check=True)
        with self.assertRaises(Refused):guard(self.before,self.after)

if __name__=='__main__':unittest.main()
