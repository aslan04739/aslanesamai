"""Record the pixel size of every image used in the content (for width/height attributes, no layout shift).
Needs Pillow:  python _build/measure_images.py   -> _build/imgsize.json (cached; only new images are fetched)."""
import io, json, re, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_build/imgsize.json"
sizes = json.loads(OUT.read_text()) if OUT.exists() else {}
site = json.loads((ROOT / "_build/site.json").read_text())
srcs = set()
for f in (ROOT / "_build/content").rglob("*.html"):
    srcs.update(re.findall(r'<img[^>]*\bsrc="([^"]+)"', f.read_text()))
srcs.update(p["cover"] for p in site["pages"].values() if p.get("cover"))
todo = [s for s in srcs if s not in sizes]

def measure(src):
    try:
        if src.startswith("/"):
            data = (ROOT / urllib.parse.unquote(src.lstrip("/"))).read_bytes()
        else:
            req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0 aslanesamai.com build"})
            data = urllib.request.urlopen(req, timeout=30).read()
        return src, list(Image.open(io.BytesIO(data)).size)
    except Exception as ex:
        print("could not measure", src, ex)
        return src, None

with ThreadPoolExecutor(8) as ex:
    for src, size in ex.map(measure, todo):
        if size:
            sizes[src] = size
OUT.write_text(json.dumps(dict(sorted(sizes.items())), indent=1))
print(f"{len(sizes)} images measured ({len(todo)} new)")
