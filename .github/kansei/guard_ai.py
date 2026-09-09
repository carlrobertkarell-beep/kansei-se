#!/usr/bin/env python3
"""Run this copy from the trusted base revision, not from the proposed branch."""
import argparse
import subprocess
from pathlib import Path
from safety import ALLOWED_PATHS, Refused, protected_content, page_facts, validate_text


def files(root):
    names = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'], check=True, capture_output=True).stdout.decode().split('\0')
    result = {name: root / name for name in names if name}
    if any(p.is_symlink() or not p.is_file() for p in result.values()):
        raise Refused('Unexpected symlink or missing tracked file')
    return result


def guard(before, after):
    a, b = files(before), files(after)
    changed = [p for p in a.keys() | b.keys() if p not in a or p not in b or a[p].read_bytes() != b[p].read_bytes()]
    if not changed or len(changed) > 2 or not set(changed) <= set(ALLOWED_PATHS):
        raise Refused('AI pilot may change only metadata on at most two approved pages')
    for p in changed:
        old, new = a[p].read_text(), b[p].read_text()
        if protected_content(old) != protected_content(new):
            raise Refused('AI changed protected content')
        facts = page_facts(new)
        validate_text(facts['title'],20,100)
        validate_text(facts['description'],60,220)
    print('PASS: AI diff contains metadata only. Human review is still required.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('before',type=Path);p.add_argument('after',type=Path)
    args=p.parse_args();guard(args.before,args.after)
