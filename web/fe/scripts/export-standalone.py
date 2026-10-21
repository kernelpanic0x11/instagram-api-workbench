"""Bundle the built Astro prototype into one HTML file for offline review."""
from pathlib import Path
import base64
import re

root = Path(__file__).resolve().parents[1]
dist = root / 'dist'
output = root.parent / 'outputs' / 'rea-prototype.html'
svg = 'data:image/svg+xml;base64,' + base64.b64encode((dist / 'rea.svg').read_bytes()).decode()
font = 'data:font/woff2;base64,' + base64.b64encode((dist / 'fonts/inter-latin.woff2').read_bytes()).decode()
html = (dist / 'index.html').read_text()

def stylesheet(match):
    css = (dist / match.group(1).lstrip('/')).read_text()
    return '<style>' + css.replace('/fonts/inter-latin.woff2', font) + '</style>'

def javascript(match):
    name = match.group(1)
    # Astro's network-prefetch helper is unnecessary in an offline document.
    if '/page.' in name:
        return ''
    js = (dist / name.lstrip('/')).read_text().replace('/rea.svg', svg)
    js = js.replace('</script', '<\\/script')
    return '<script type="module">' + js + '</script>'

html = re.sub(r'<link\b(?=[^>]*rel="stylesheet")[^>]*href="([^"]+)"[^>]*>', stylesheet, html)
html = re.sub(r'<script\b[^>]*src="([^"]+)"[^>]*>\s*</script>', javascript, html)
html = html.replace('/rea.svg', svg)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(html)
assert not re.search(r'(?:src|href)="/(?:_astro|fonts|rea)', html)
print(output)
