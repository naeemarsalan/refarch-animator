#!/usr/bin/env python3
"""Embed open-source Google Fonts into a page as data-URI @font-face CSS —
without the base64 ever passing through the model context.

Usage:
  python3 scripts/embed_fonts.py --inject page.html "Family:400,700" ["Family2:400"] ...
  python3 scripts/embed_fonts.py --out fonts.css "Family:400,700" ...

--inject splices the CSS directly into the page: it replaces the block between
`/* fonts:begin */` and `/* fonts:end */` markers if present (idempotent), else
inserts right after the first <style> tag. --out writes a CSS file you can
splice with shell tools. stdout prints only family names and sizes — never CSS.

Only the latin subset is embedded to keep pages small. Variable-font families
(one file covering several weights) are emitted once with a weight range.
"""
import base64
import re
import sys
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BEGIN, END = "/* fonts:begin */", "/* fonts:end */"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req).read()


def build_css(specs) -> str:
    fams = []
    for spec in specs:
        name, _, weights = spec.partition(":")
        weights = weights or "400"
        fams.append("family=" + urllib.parse.quote(name)
                    + ":wght@" + weights.replace(",", ";"))
    css = fetch("https://fonts.googleapis.com/css2?"
                + "&".join(fams) + "&display=swap").decode()

    groups: dict = {}   # (family, file url) -> [weights]
    for subset, body in re.findall(r"/\* ([\w-]+) \*/\s*@font-face \{(.*?)\}", css, re.S):
        if subset != "latin":
            continue
        fam = re.search(r"font-family: '([^']+)'", body).group(1)
        weight = int(re.search(r"font-weight: (\d+)", body).group(1))
        url = re.search(r"url\((\S+?)\)", body).group(1)
        groups.setdefault((fam, url), []).append(weight)

    out = []
    for (fam, url), weights in groups.items():
        b64 = base64.b64encode(fetch(url)).decode()
        w = (str(weights[0]) if len(set(weights)) == 1
             else f"{min(weights)} {max(weights)}")
        out.append(f"@font-face {{ font-family:'{fam}'; font-style:normal; "
                   f"font-weight:{w}; font-display:swap; "
                   f"src:url(data:font/woff2;base64,{b64}) format('woff2'); }}")
        print(f"embedded: {fam} ({w}) — {len(b64) // 1024} KB")
    return "\n".join(out)


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 3 or args[0] not in ("--inject", "--out"):
        print(__doc__)
        return 1
    mode, target, specs = args[0], args[1], args[2:]
    css = build_css(specs)

    if mode == "--out":
        with open(target, "w", encoding="utf-8") as f:
            f.write(BEGIN + "\n" + css + "\n" + END + "\n")
        print(f"wrote {target}")
        return 0

    src = open(target, encoding="utf-8").read()
    block = BEGIN + "\n" + css + "\n" + END
    if BEGIN in src and END in src:
        src = src[: src.index(BEGIN)] + block + src[src.index(END) + len(END):]
        action = "replaced fonts block in"
    else:
        m = re.search(r"<style\b[^>]*>", src)
        if not m:
            print("error: no <style> tag found to inject into")
            return 1
        src = src[: m.end()] + "\n" + block + src[m.end():]
        action = "injected fonts block into"
    with open(target, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"{action} {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
