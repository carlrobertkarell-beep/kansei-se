"""One-off preparation of review scripts; never deployed as an active workflow on main."""
from pathlib import Path
p=Path('.github/kansei/visibility-update.py');t=p.read_text()
t=t.replace("text,'p','vår egen'", "text,'p','Fysioterapeutens kärna'")
t=t.replace("hashlib.sha256(text[a:b].encode()).hexdigest()==case_hashes[rel]", "hashlib.sha256(re.sub(r' data-measure=\"[^\"]*\"', '', text[a:b]).encode()).hexdigest()==case_hashes[rel]")
p.write_text(t)
p=Path('assets/analytics.20261016.js');t=p.read_text()
t=t.replace("</span></a></div>';", "</span></a></div></div>';")
t=t.replace("panel, opener, source = 'unknown';", "panel, opener, source = 'unknown', sourceAt = 0;")
t=t.replace("    if (!granted) return;\n    try { sessionStorage.setItem", "    if (!granted) return;\n    if (sourceAt && Date.now() - sourceAt >= sourceMaxAge) source = 'unknown';\n    sourceAt = Date.now();\n    try { sessionStorage.setItem")
t=t.replace("    rememberSource();\n  };\n  const payload", "    sourceAt = Date.now();\n    rememberSource();\n  };\n  const payload")
p.write_text(t)
for name in ['docs/analytics-installation.md','docs/booking-measurement.md']:
 p=Path(name)
 if p.exists():
  p.write_text(p.read_text()+'\n\n## Visibility measurement update — 16 October 2026\n\nSee `visibility-measurement-2026-10-16.md` for the newer bridge, version 20261016, strict referral groups and explicit exclusion of review/profile links from booking_click. The same GA4 property and consent choice are reused; do not add another tag. Browser tests use stubbed third parties and do not by themselves verify actual GA4 collection.\n')
