# Visual grammar & default palette

Conventions distilled from Red Hat's publicly documented Portfolio Architecture
methodology (the logical / schematic / detail diagram taxonomy and its draw.io
toolkit), generalized for any stack. Use them as the default; a user's own
brand/design system always wins.

## The grammar

**Zones** (sites, regions, clusters, networks)
- Flat rectangles, **square corners**, light-gray fill on a slightly darker
  quiet canvas.
- Border color encodes the *domain*, not decoration: one color for
  infrastructure/site zones, a second for the management/operations zone.
- Label: ALL CAPS, bold, small (10–12 px), top-left **inside** the zone; an
  optional second line in lighter weight for CIDRs/regions/status.
- Solid border = live. Dashed border = planned, inert, or torn down — say which
  in the label or a status chip.

**Components**
- White (surface-token) rectangles, thin neutral border, square corners.
- Line 1: bold sentence-case name (12–13 px). Lines 2–4: role, then
  ports/identifiers in the mono face at ~10.5 px.
- Dashed component border = not currently deployed.
- Multiplicity as plain text: `×3`, `0→2`, `1..n`.

**Connectors**
- Orthogonal only (`H`/`V` path segments), `stroke-width: 3`, no arrowheads —
  small filled-dot terminators or bare ends; direction is carried by the
  storyboard animation and labels, not chevrons.
- Color encodes the **flow plane** (2–4 planes max), consistent across every
  diagram on the page and restated in a legend band.
- Dashed stroke = planned path.
- Labels: 10–11 px, in whitespace beside the line, colored like their plane.

**Legend** — a full-width band under the diagram (band token background):
color swatch + plane name for each plane, plus any status conventions used.

**Typography roles**
- Display face: page title + section headings only.
- Text face: everything else.
- Mono face: ports, CIDRs, object names, code, and any lined-up digits
  (`font-variant-numeric: tabular-nums` where digits form columns).
- System stacks are fine; `scripts/embed_fonts.py` inlines open-source faces as
  data URIs when brand typography matters (never link a webfont URL — the page
  must be self-contained).

## Default palette (validated on both themes)

| Token          | Light     | Dark      | Use                              |
| -------------- | --------- | --------- | -------------------------------- |
| `--bg`         | `#F1F1F1` | `#1B1B1B` | page canvas                      |
| `--surface`    | `#FFFFFF` | `#292929` | component nodes, panels          |
| `--band`       | `#E6E6E6` | `#141414` | legend/footer bands              |
| `--zone`       | `#EBEBEB` | `#232323` | zone fill                        |
| `--subzone`    | `#F7F7F7` | `#1F1F1F` | nested zone fill                 |
| `--ink`        | `#151515` | `#F2F2F2` | primary text                     |
| `--ink2`       | `#4C4C4C` | `#C7C7C7` | secondary text                   |
| `--ink3`       | `#595959` | `#A3A3A3` | captions, metadata               |
| `--line`       | `#C7C7C7` | `#4D4D4D` | node borders                     |
| `--zone-a`     | `#1D4174` | `#6B93CB` | site/infrastructure zone borders |
| `--zone-b`     | `#4CB6D6` | `#4CB6D6` | management zone borders          |
| `--flow-1`     | `#D97E13` | `#FAAA4F` | plane 1 (e.g. data)              |
| `--flow-2`     | `#5E40BE` | `#9B85E8` | plane 2 (e.g. control/scale)     |
| `--flow-3`     | `#2E93B8` | `#5BC0DE` | plane 3 (e.g. management)        |
| `--ok`         | `#63993D` | `#8CC152` | live/healthy accents             |
| `--warn`       | `#B8860B` | `#E0A83A` | degraded / torn-down chips       |
| `--plan`       | `#8C8C8C` | `#8C8C8C` | planned chips                    |

Theme wiring (token-level, so a host toggle beats the OS preference):

```css
:root { /* light values */ }
@media (prefers-color-scheme: dark) { :root { /* dark values */ } }
:root[data-theme="light"] { /* light values again */ }
:root[data-theme="dark"]  { /* dark values again */ }
```

## Don'ts

- No rounded-corner zones, no drop shadows, no gradients inside diagrams.
- No arrowhead clutter; no diagonal or curved connectors.
- Don't use a brand's primary red/logo color as a diagram accent — if you adopt
  a corporate style, reserve its hero color for the masthead only.
- Don't overlay every plane on one crowded canvas if it stops being readable —
  add per-plane isolation buttons, or split views, instead.
- No emoji as section markers; no decorative numbering that isn't a real sequence.
