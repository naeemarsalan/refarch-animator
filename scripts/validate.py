#!/usr/bin/env python3
"""Structural + geometry validator for pages built with the refarch-animator skill.

Usage: python3 scripts/validate.py [--strict] <page.html>

Structural checks (errors -> exit 1):
  - HTML tag balance; duplicate ids; script id references; anchor targets
  - JS syntax via `node --check` when node is available

Geometry checks per <svg> (warnings; errors with --strict) — the recurring
diagram bugs, checked by arithmetic so no review pass has to re-read the file:
  - <text> estimated width (~0.62em/char) overflowing its containing box
  - free-floating labels overlapping a solid box
  - H/V path segments cutting through a solid box's interior
  - path endpoints not landing on any box/zone edge
  - elements extending outside the viewBox

Width estimates are heuristics: treat warnings as pointers and confirm with
arithmetic before changing a coordinate. Rotated (transform=) text is skipped.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

VOID = {"br", "img", "hr", "input", "meta", "link", "source", "wbr",
        "path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "use", "stop"}

# solid component boxes: interior must stay clear of paths and stray labels
NODE_CLASSES = {"node", "chip", "vm"}
# containers: legitimate to enter/label, but their edges count for path endpoints
CONTAINER_CLASSES = {"zone", "subz", "frame"}
SKIP_RECT_CLASSES = {"meter-fill", "meter-track"}

FONT_SIZES = {"ntitle": 12.5, "nsub": 10.8, "nport": 10.3, "zlabel": 11.5,
              "zsub": 10.5, "flabel": 10.6, "counter": 12.5, "chiplabel": 9.8,
              "vmlabel": 9.6, "dg-title": 22.0}
CHAR_W = 0.62   # estimated advance per character, in em
EDGE_TOL = 3.0


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


def attrs_of(tag_src: str) -> dict:
    return dict(re.findall(r'([\w-]+)="([^"]*)"', tag_src))


def classes_of(a: dict) -> set:
    return set(a.get("class", "").split())


def parse_path(d: str):
    """Absolute M/H/V/L only (the skill's grammar). Returns point list or None."""
    pts, x, y = [], 0.0, 0.0
    for cmd, val in re.findall(r"([A-Za-z])\s*([-\d.,\s]*)", d):
        nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", val)]
        if cmd == "M" and len(nums) >= 2:
            x, y = nums[0], nums[1]
            pts.append((x, y))
            for i in range(2, len(nums) - 1, 2):
                x, y = nums[i], nums[i + 1]
                pts.append((x, y))
        elif cmd == "H":
            for n in nums:
                x = n
                pts.append((x, y))
        elif cmd == "V":
            for n in nums:
                y = n
                pts.append((x, y))
        elif cmd == "L":
            for i in range(0, len(nums) - 1, 2):
                x, y = nums[i], nums[i + 1]
                pts.append((x, y))
        else:
            return None  # relative/curve commands: out of grammar, skip checks
    return pts if len(pts) >= 2 else None


def on_edge(px, py, r, tol=EDGE_TOL):
    rx, ry, rw, rh = r
    on_v = (abs(px - rx) <= tol or abs(px - (rx + rw)) <= tol) and ry - tol <= py <= ry + rh + tol
    on_h = (abs(py - ry) <= tol or abs(py - (ry + rh)) <= tol) and rx - tol <= px <= rx + rw + tol
    return on_v or on_h


def font_size(a: dict) -> float:
    m = re.search(r"font-size:\s*([\d.]+)", a.get("style", ""))
    if m:
        return float(m.group(1))
    for c in classes_of(a):
        if c in FONT_SIZES:
            return FONT_SIZES[c]
    return 12.0


def check_svg(svg_src: str, label: str, warn):
    head = svg_src[: svg_src.index(">") + 1]
    vb = re.search(r'viewBox="([\d.\s-]+)"', head)
    vbw = vbh = None
    if vb:
        parts = [float(v) for v in vb.group(1).split()]
        vbw, vbh = parts[2], parts[3]

    nodes, containers = [], []
    for m in re.finditer(r"<rect\b[^>]*>", svg_src):
        a = attrs_of(m.group(0))
        cls = classes_of(a)
        if cls & SKIP_RECT_CLASSES or "width" not in a:
            continue
        r = (float(a.get("x", 0)), float(a.get("y", 0)),
             float(a["width"]), float(a.get("height", 0)))
        if cls & NODE_CLASSES:
            nodes.append(r)
        elif cls & CONTAINER_CLASSES:
            containers.append(r)
        if vbw and (r[0] + r[2] > vbw + 2 or r[1] + r[3] > vbh + 2 or r[0] < -2 or r[1] < -2):
            warn(f"{label}: rect at {r[0]},{r[1]} extends outside the viewBox")
    attachable = nodes + containers

    for m in re.finditer(r"<text\b([^>]*)>(.*?)</text>", svg_src, re.S):
        a = attrs_of(m.group(1))
        if "transform" in a:
            continue
        content = re.sub(r"<[^>]*>", "", m.group(2)).strip()
        if not content:
            continue
        tx, ty = float(a.get("x", 0)), float(a.get("y", 0))
        fs = font_size(a)
        est_w = len(content) * fs * CHAR_W
        snippet = content[:34]
        if vbw and tx + est_w > vbw + 4:
            warn(f'{label}: text "{snippet}" ≈{tx + est_w - vbw:.0f}px past the viewBox right edge')
        inside = [r for r in nodes if r[0] <= tx <= r[0] + r[2] and r[1] <= ty <= r[1] + r[3]]
        if inside:
            r = min(inside, key=lambda r: r[2] * r[3])
            over = tx + est_w - (r[0] + r[2] - 1)
            if over > EDGE_TOL:
                warn(f'{label}: text "{snippet}" ≈{over:.0f}px past its box right edge')
        else:
            x1, x2, y1, y2 = tx, tx + est_w, ty - fs * 0.75, ty + 2
            for r in nodes:
                rx, ry, rw, rh = r
                if x1 < rx + rw - 2 and x2 > rx + 2 and y1 < ry + rh - 2 and y2 > ry + 2:
                    warn(f'{label}: label "{snippet}" overlaps the box at {rx},{ry}')
                    break

    for m in re.finditer(r"<path\b[^>]*>", svg_src):
        a = attrs_of(m.group(0))
        pts = parse_path(a.get("d", ""))
        if not pts:
            continue
        pid = a.get("id") or a.get("d", "")[:24]
        for px, py in (pts[0], pts[-1]):
            if not any(on_edge(px, py, r) for r in attachable):
                warn(f"path {pid}: endpoint {px:g},{py:g} floats — not on any box edge")
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            for r in nodes:
                rx, ry, rw, rh = r
                if on_edge(pts[0][0], pts[0][1], r) or on_edge(pts[-1][0], pts[-1][1], r):
                    continue
                if y1 == y2 and ry + 2 < y1 < ry + rh - 2:
                    if min(max(x1, x2), rx + rw - 2) - max(min(x1, x2), rx + 2) > 4:
                        warn(f"path {pid}: horizontal segment at y={y1:g} cuts through the box at {rx},{ry}")
                elif x1 == x2 and rx + 2 < x1 < rx + rw - 2:
                    if min(max(y1, y2), ry + rh - 2) - max(min(y1, y2), ry + 2) > 4:
                        warn(f"path {pid}: vertical segment at x={x1:g} cuts through the box at {rx},{ry}")


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--strict"]
    strict = "--strict" in sys.argv
    if len(args) != 1:
        print(__doc__)
        return 1
    src = open(args[0], encoding="utf-8").read()
    errors, warnings = [], []

    p = Balance()
    p.feed(src)
    errors += p.errs
    errors += [f"unclosed tag: <{t}>" for t in p.stack]

    ids = re.findall(r'\bid="([^"]+)"', src)
    errors += [f"duplicate id: {d}" for d in sorted({i for i in ids if ids.count(i) > 1})]
    idset = set(ids)

    js = "\n".join(re.findall(r"<script[^>]*>(.*?)</script>", src, re.S))
    refs = set(re.findall(r"\$\('([A-Za-z][\w-]*)'\)", js))
    refs |= set(re.findall(r"getElementById\('([A-Za-z][\w-]*)'\)", js))
    errors += [f"script references missing id: {r}" for r in sorted(refs - idset)]
    for href in re.findall(r'href="#([^"]+)"', src):
        if href not in idset:
            errors.append(f"anchor target missing: #{href}")

    if js.strip():
        node = shutil.which("node")
        if node:
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                f.write(js)
            r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
            if r.returncode != 0:
                errors.append("JS syntax: " + r.stderr.strip().splitlines()[-1])
        else:
            print("note: node not found — JS syntax not checked")

    for i, m in enumerate(re.finditer(r"<svg\b[^>]*>.*?</svg>", src, re.S), 1):
        head = attrs_of(m.group(0)[: m.group(0).index(">") + 1])
        check_svg(m.group(0), head.get("id", f"svg#{i}"), warnings.append)

    for e in errors:
        print("ERROR:", e)
    for w in warnings:
        print("warn: ", w)
    fail = bool(errors) or (strict and bool(warnings))
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)" if (errors or warnings) else "clean")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
