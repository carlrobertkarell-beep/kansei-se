"""Export five upper-limb anatomy layers in unchanged ultrasound coordinates."""
from pathlib import Path
import hashlib
import json
from paint_registration import register

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / '.github/kansei/artwork/layer-audit-20261021/upper-limb'
QA = Path('/tmp/kansei-upper-limb-final')
SPECS = [
    ('biceps-transverse', 'bicepssena/tvarsnitt-helbild.20261009.jpg',
     'bicepssena/tvarsnitt-anatomi.20261021f.webp',
     [114, 110, 1334, 977], [108, 110, 1172, 890],
     'Regenerated from original; small tendon and fascial branches retained.'),
    ('biceps-longitudinal', 'bicepssena/langdsnitt-helbild.20261009.jpg',
     'bicepssena/langdsnitt-anatomi.20261021f.webp',
     [84, 121, 1363, 1008], [76, 110, 1204, 890],
     'Regenerated from original; genuine two-acquisition split retained without headings.'),
    ('pectoralis-longitudinal', 'pectoralis/langdsnitt-helbild.20261009.jpg',
     'pectoralis/langdsnitt-anatomi.20261021f.webp',
     [235, 144, 1212, 922], [228, 142, 1050, 830],
     'Regenerated from original; local tear geometry replaces enlarged displaced painting.'),
    ('pectoralis-transverse', 'pectoralis/tvarsnitt-helbild.20261009.jpg',
     'pectoralis/tvarsnitt-anatomi.20261021f.webp',
     [231, 141, 1216, 946], [228, 142, 1050, 830],
     'Regenerated from original; narrow tear branches and preserved central tissue retained.'),
    ('medianus', 'karpaltunnel/medianus-helbild.20261009.jpg',
     'karpaltunnel/medianus-anatomi.20261021f.webp',
     [103, 78, 1448, 1086], [74, 112, 1206, 891],
     'Existing geometry retained with text-only cleanup; one global registration corrects scale/depth mismatch.'),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    records = []
    for name, original_name, output_name, source_bounds, target_bounds, reason in SPECS:
        source = ARCHIVE / (name + '.source.webp')
        original = ROOT / 'bilder/ultraljud' / original_name
        output = ROOT / 'bilder/ultraljud' / output_name
        record = register(source, output, QA / name / (name + '.archive.webp'),
                          [1280, 960], source_bounds, target_bounds, QA / name)
        record.update({
            'name': name, 'source_image': str(source.relative_to(ROOT)),
            'original': str(original.relative_to(ROOT)),
            'original_sha256': digest(original),
            'archive': str(source.relative_to(ROOT)),
            'archive_sha256': digest(source),
            'asset': str(output.relative_to(ROOT)),
            'reason': reason,
            'findings': 'Original scan coordinates retained in both modes.',
        })
        records.append(record)
    (ARCHIVE / 'manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps([{'name': r['name'], 'asset': r['asset']} for r in records], indent=2))


if __name__ == '__main__':
    build()
