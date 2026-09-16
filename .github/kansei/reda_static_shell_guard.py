from pathlib import Path
s=Path('reda/index.html').read_text()
required=['<body class="reda-portal-shell">','class="reda-portal-top"','class="reda-portal-footer"','id="kodform"','/assets/reda-portal-shell.css?v=20260916-2']
missing=[x for x in required if x not in s]
if missing: raise SystemExit('Missing Reda static portal shell markers: '+repr(missing))
if s.count('class="reda-portal-top"') != 1: raise SystemExit('Expected one Reda portal header')
if s.count('class="reda-portal-footer"') != 1: raise SystemExit('Expected one Reda portal footer')
css=Path('assets/reda-portal-shell.css').read_text()
if 'footer:not(.reda-portal-footer)' not in css: raise SystemExit('Legacy footer selector would hide new Reda footer')
print('Reda static portal shell guard: PASS')
