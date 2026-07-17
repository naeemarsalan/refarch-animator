#!/usr/bin/env python3
"""Emit self-contained @font-face CSS (woff2 as base64 data URIs) for open-source
Google Fonts families, so a page needs no network access for typography.

Usage:
  python3 scripts/embed_fonts.py "Family Name:400,700" ["Second Family:400"] ...

Prints CSS to stdout; paste it at the top of your page's <style>. Only the
latin subset is embedded to keep pages small (add subsets if you need them).
Some families are served as variable fonts — one file covers several weights —
in which case a single @font-face with `font-weight: <min> <max>` is emitted.
"""
import base64
import re
import sys
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req).read()


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    fams = []
    for spec in sys.argv[1:]:
        name, _, weights = spec.partition(":")
        weights = weights or "400"
        fams.append("family=" + urllib.parse.quote(name)
                    + ":wght@" + weights.replace(",", ";"))
    css_url = ("https://fonts.googleapis.com/css2?"
               + "&".join(fams) + "&display=swap")
    css = fetch(css_url).decode()

    # group latin-subset blocks by (family, file url) — variable fonts reuse one url
    groups: dict[tuple[str, str], list[int]] = {}
    for subset, body in re.findall(r"/\* ([\w-]+) \*/\s*@font-face \{(.*?)\}", css, re.S):
        if subset != "latin":
            continue
        fam = re.search(r"font-family: '([^']+)'", body).group(1)
        weight = int(re.search(r"font-weight: (\d+)", body).group(1))
        url = re.search(r"url\((\S+?)\)", body).group(1)
        groups.setdefault((fam, url), []).append(weight)

    for (fam, url), weights in groups.items():
        b64 = base64.b64encode(fetch(url)).decode()
        w = (str(weights[0]) if len(set(weights)) == 1
             else f"{min(weights)} {max(weights)}")
        print(f"@font-face {{ font-family:'{fam}'; font-style:normal; "
              f"font-weight:{w}; font-display:swap; "
              f"src:url(data:font/woff2;base64,{b64}) format('woff2'); }}")
        print(f"/* {fam} ({w}): {len(b64) // 1024} KB embedded */", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
