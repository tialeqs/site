#!/usr/bin/env python3
"""Gera dist/ableton-express.html: um arquivo único, com os prints dos alunos
embutidos em base64, pronto pra colar no bloco de HTML personalizado do WordPress.

O arquivo sai 100% ASCII. Bancos do WordPress em utf8 (não utf8mb4) recusam
emoji e dão "Não foi possível atualizar o post no banco de dados". Por isso
acentos e emojis viram escapes que o navegador mostra igual:
  - no HTML:        &#N;
  - dentro de <style>:  \\HEX (escape de CSS)
  - dentro de <script>: \\uXXXX (escape de JavaScript)
"""
import base64, pathlib, re, sys

root = pathlib.Path(__file__).parent


def inline_images(html: str, base: pathlib.Path) -> str:
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}

    def sub(m):
        path = base / m.group(1)
        b64 = base64.b64encode(path.read_bytes()).decode()
        return f'src="data:{mime[path.suffix.lower()]};base64,{b64}"'

    return re.sub(r'src="(assets/[^"]+\.(?:jpe?g|png))"', sub, html)


def _html(ch):
    return ch if ord(ch) < 128 else f"&#{ord(ch)};"


def _css(ch):
    return ch if ord(ch) < 128 else f"\\{ord(ch):x} "


def _js(ch):
    o = ord(ch)
    if o < 128:
        return ch
    if o <= 0xFFFF:
        return f"\\u{o:04x}"
    o -= 0x10000  # par substituto pra emoji
    return f"\\u{0xD800 + (o >> 10):04x}\\u{0xDC00 + (o & 0x3FF):04x}"


def to_ascii(html: str) -> str:
    out, pos = [], 0
    for m in re.finditer(r"(<style[^>]*>)(.*?)(</style>)|(<script[^>]*>)(.*?)(</script>)", html, re.S):
        out.append("".join(map(_html, html[pos:m.start()])))
        if m.group(1):
            out.append(m.group(1) + "".join(map(_css, m.group(2))) + m.group(3))
        else:
            out.append(m.group(4) + "".join(map(_js, m.group(5))) + m.group(6))
        pos = m.end()
    out.append("".join(map(_html, html[pos:])))
    res = "".join(out)
    assert res.isascii()
    return res


def build(src: pathlib.Path, dest: pathlib.Path):
    html = src.read_text(encoding="utf-8")
    html = to_ascii(inline_images(html, src.parent))
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(html, encoding="ascii")
    print(f"{dest.relative_to(root)}  {len(html)/1024:.0f} KB  (ASCII puro)")


if __name__ == "__main__":
    build(root / "index.html", root / "dist" / "ableton-express.html")
    lk = root / "lite-keys" / "index.html"
    if lk.exists():
        build(lk, root / "dist" / "lite-keys.html")
