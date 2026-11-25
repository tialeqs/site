#!/usr/bin/env python3
"""Gera dist/ableton-express.html: um arquivo único, com os prints dos alunos
embutidos em base64, pronto pra colar/subir no WordPress (igual ao original)."""
import base64, pathlib, re

root = pathlib.Path(__file__).parent
html = (root / "index.html").read_text(encoding="utf-8")

def inline(m):
    path = root / m.group(1)
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f'src="data:image/jpeg;base64,{b64}"'

out = re.sub(r'src="(assets/[^"]+\.jpe?g)"', inline, html)
dist = root / "dist"
dist.mkdir(exist_ok=True)
(dist / "ableton-express.html").write_text(out, encoding="utf-8")
print(f"dist/ableton-express.html  {len(out)/1024:.0f} KB")
