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
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}

    def sub(m):
        path = base / m.group(1)
        b64 = base64.b64encode(path.read_bytes()).decode()
        return f'src="data:{mime[path.suffix.lower()]};base64,{b64}"'

    return re.sub(r'src="(assets/[^"]+\.(?:jpe?g|png|webp))"', sub, html)


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


SCOPE = "#pg"


def _split_top(sel: str):
    parts, depth, cur = [], 0, ""
    for ch in sel:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur); cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def _scope_selector(sel: str) -> str:
    out = []
    for s in _split_top(sel):
        if s in (":root", "html", "::selection") or s.startswith("::"):
            out.append(s)
        elif s == "body":
            out += ["body", SCOPE]
        elif s == "*":
            out += [SCOPE, f"{SCOPE} *"]
        elif re.match(r"^(html|:root|body)[.\[:]", s) or s.startswith(("html ", ":root ", "body ")):
            head, _, rest = s.partition(" ")
            out.append(f"{head} {SCOPE} {rest}" if rest else f"{head} {SCOPE}")
        else:
            out.append(f"{SCOPE} {s}")
    return ",".join(out)


def scope_css(css: str) -> str:
    """Prefixa todo seletor com #pg. Com um id na frente, o CSS da página sempre
    ganha do CSS do tema do WordPress (Hello Elementor deixa botão com hover
    rosa e white-space:nowrap, põe margem em título etc.)."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            out.append(css[i:]); break
        head = css[i:j].strip()
        # acha o fim do bloco, respeitando chaves aninhadas
        depth, k = 1, j + 1
        while depth and k < n:
            if css[k] == "{": depth += 1
            elif css[k] == "}": depth -= 1
            k += 1
        body = css[j + 1:k - 1]
        if head.startswith("@media") or head.startswith("@supports"):
            out.append(f"{head}{{{scope_css(body)}}}")
        elif head.startswith("@"):
            out.append(f"{head}{{{body}}}")
        else:
            out.append(f"{_scope_selector(head)}{{{body}}}")
        i = k
    return "\n".join(out)


def scope_page(html: str) -> str:
    html = re.sub(r"(<style[^>]*>)(.*?)(</style>)", lambda m: m.group(1) + scope_css(m.group(2)) + m.group(3), html, flags=re.S)
    html = html.replace("<body>", f'<body>\n<div id="{SCOPE[1:]}">', 1)
    i = html.rfind("</body>")
    return html[:i] + "</div>\n" + html[i:]


def wp_safe_scripts(html: str) -> str:
    """O WordPress troca '&' por '&#038;' dentro de <script> colado no bloco de
    HTML (quebra todo '&&' do JavaScript). Aqui cada script inline vira
    <script src="data:...base64">: base64 não tem & < > pro WordPress mexer."""
    def sub(m):
        b64 = base64.b64encode(m.group(1).encode("ascii")).decode()
        return f'<script src="data:text/javascript;base64,{b64}"></script>'
    out = re.sub(r"<script>(.*?)</script>", sub, html, flags=re.S)
    return out


def build(src: pathlib.Path, name: str):
    html = src.read_text(encoding="utf-8")
    html = to_ascii(scope_page(inline_images(html, src.parent)))
    # 1) versão pro WordPress (é essa que vai no bloco de HTML personalizado)
    wp = wp_safe_scripts(html)
    assert "&&" not in re.sub(r"<style.*?</style>", "", wp, flags=re.S)
    dest = root / "dist" / f"{name}.html"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(wp, encoding="ascii")
    print(f"{dest.relative_to(root)}  {len(wp)/1024:.0f} KB  (WordPress)")
    # 2) versão de preview (script legível; usada no artifact do Claude)
    prev = root / "dist" / "preview" / f"{name}.html"
    prev.parent.mkdir(exist_ok=True)
    prev.write_text(html, encoding="ascii")
    print(f"{prev.relative_to(root)}  {len(html)/1024:.0f} KB  (preview)")


if __name__ == "__main__":
    build(root / "index.html", "ableton-express")
    lk = root / "lite-keys" / "index.html"
    if lk.exists():
        build(lk, "lite-keys")
