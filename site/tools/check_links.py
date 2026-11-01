"""Check internal links, anchors and local asset references across the built pages."""
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
pages = sorted(SITE.glob("*.html"))
ids = {p.name: set(re.findall(r'\sid="([^"]+)"', p.read_text(encoding="utf-8"))) for p in pages}
problems, external = [], set()
for p in pages:
    t = p.read_text(encoding="utf-8")
    for ref in re.findall(r'(?:href|src|data-full)="([^"]+)"', t) + [u.split()[0] for s in re.findall(r'srcset="([^"]+)"', t) for u in s.split(",")]:
        if ref.startswith(("http", "mailto:", "tel:", "data:")):
            if ref.startswith("http"):
                external.add(ref)
            continue
        path, _, frag = ref.partition("#")
        path = path.split("?")[0]  # cache-busting ?v= on css/js
        target = p.name if not path else path
        if path and not (SITE / path).exists():
            problems.append(f"{p.name}: missing file {path}")
        elif frag and target.endswith(".html") and frag not in ids.get(target, set()):
            problems.append(f"{p.name}: missing anchor #{frag} in {target}")
print("\n".join(problems) or "all internal links, anchors and assets resolve")
print("external:", *sorted(external), sep="\n  ")
