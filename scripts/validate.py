#!/usr/bin/env python3
"""Structural validator for pages built with the refarch-animator skill.

Usage: python3 scripts/validate.py <page.html>

Checks:
  - HTML tag balance (SVG shape elements and HTML voids excluded)
  - every id referenced from the script ($('...') / getElementById('...')) exists
  - every internal anchor href="#..." resolves to an element id
  - duplicate ids
  - JS syntax via `node --check` when node is available

Exit code 0 = clean, 1 = findings.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

VOID = {"br", "img", "hr", "input", "meta", "link", "source", "wbr",
        "path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "use", "stop"}


class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errs = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errs.append(f"tag mismatch: </{tag}> at {self.getpos()}")
        if self.stack:
            self.stack.pop()


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    src = open(sys.argv[1], encoding="utf-8").read()
    findings = []

    p = Balance()
    p.feed(src)
    findings += p.errs
    findings += [f"unclosed tag: <{t}>" for t in p.stack]

    ids = re.findall(r'\bid="([^"]+)"', src)
    dupes = {i for i in ids if ids.count(i) > 1}
    findings += [f"duplicate id: {d}" for d in sorted(dupes)]
    idset = set(ids)

    scripts = re.findall(r"<script[^>]*>(.*?)</script>", src, re.S)
    js = "\n".join(scripts)
    refs = set(re.findall(r"\$\('([A-Za-z][\w-]*)'\)", js))
    refs |= set(re.findall(r"getElementById\('([A-Za-z][\w-]*)'\)", js))
    findings += [f"script references missing id: {r}" for r in sorted(refs - idset)]

    for href in re.findall(r'href="#([^"]+)"', src):
        if href not in idset:
            findings += [f"anchor target missing: #{href}"]

    if js.strip():
        node = shutil.which("node")
        if node:
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                f.write(js)
            r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
            if r.returncode != 0:
                findings += ["JS syntax: " + r.stderr.strip().splitlines()[-1]]
        else:
            print("note: node not found — JS syntax not checked")

    if findings:
        print("\n".join(findings))
        print(f"\n{len(findings)} finding(s)")
        return 1
    print("clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
