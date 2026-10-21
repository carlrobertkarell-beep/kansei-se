"""Re-export the reviewed whole bursa paintings with their recorded global fits."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json


ART = Path(__file__).resolve().parent
ROOT = next(p for p in ART.parents
            if (p / '.github/kansei/paint_registration.py').is_file())
MANIFEST = ART / 'registration.20261021f.json'


def rebuild(qa_dir):
    spec = importlib.util.spec_from_file_location(
        'paint_registration', ROOT / '.github/kansei/paint_registration.py')
    registration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(registration)
    manifest = json.loads(MANIFEST.read_text())
    for view in manifest['views']:
        original = ROOT / 'bilder/ultraljud/bursit-axel' / (view['key'] + '.original.jpg')
        if hashlib.sha256(original.read_bytes()).hexdigest() != view['original_sha256']:
            raise ValueError('Clinical original changed: ' + view['key'])
        result = registration.register(
            ROOT / view['archived_source'], ROOT / view['asset'],
            qa_dir / ('rebuild-source-' + Path(view['archive']).name),
            view['canvas'], view['source_bounds'],
            view['target_bounds'], qa_dir)
        view['asset_sha256'] = result['asset_sha256']
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qa-dir', required=True, type=Path)
    rebuild(parser.parse_args().qa_dir)
