---
name: refarch-animator
description: Generate an animated reference-architecture page — layered diagram views plus a step-by-step animated storyboard — as one self-contained HTML file. Use for architecture diagrams with animation, "slide by slide" system walkthroughs, or polished reference-architecture deliverables.
---

# Animated reference-architecture pages

You produce **one self-contained HTML file**: no external requests (no CDNs, no
webfonts by URL, no remote images), theme-aware (light + dark), responsive, and
hostable anywhere — a static file server, an artifact platform, an internal wiki.

The page has up to four parts, in this order:

1. **Masthead** — title, one-line thesis, metadata row (version, date, source ref).
2. **Logical view** — 2–4 broad tiers, no networking detail. HTML/CSS tier bands.
3. **Schematic view** — deployment topology as an SVG: zones, components,
   connectors color-coded by flow plane. Optional: legend buttons that isolate
   one plane by dimming the others.
4. **Detail view — the storyboard** — one concrete scenario animated slide by
   slide: an SVG stage plus a player (Prev/Next/autoplay/step dots/keyboard/deep
   links), where each step highlights the acting components, runs traveling dots
   along the active flows, and updates live counters (queue depth, replica
   counts). This is the centerpiece; spend most of your effort here.

Scale to the ask: a quick request may need only the schematic + storyboard; a
full reference-architecture deliverable gets all sections plus tables the domain
calls for (ports, sizing, decisions).

## Step 0 — gather real inputs first

Never invent an architecture. Before writing HTML, collect from the user, the
repo, or documents:

- **Zones/sites** (regions, clusters, networks) and each one's status:
  live / planned / decommissioned.
- **Components** with a name and a one-line role, placed in a zone.
- **Flows** between components, each labeled with protocol/port and classified
  into a **plane** (pick 2–4): e.g. data, control/scale, management/observability.
- **One scenario** for the storyboard as numbered steps: *who acts, what
  happens, what visually moves from where to where*. Harvest **real numbers**
  (queue depths, scale timings, thresholds, durations) — real figures are what
  make a storyboard credible. If a claim can't be confirmed, leave it out or
  mark it as illustrative.

## Step 1 — design tokens

Define the palette as CSS custom properties on `:root`, redefine only tokens
under `@media (prefers-color-scheme: dark)`, then again under
`:root[data-theme="dark"]` and `:root[data-theme="light"]` so a host page's
theme toggle wins in both directions. Style components only through tokens.

The grammar in one breath: flat square-cornered zones on a quiet gray canvas,
white component nodes with thin borders, ALL-CAPS zone labels / sentence-case
component names, orthogonal 3px connectors color-coded by plane, dashed borders
for planned or torn-down elements, a footer legend band. The template you copy
in step 2 already carries the full validated palette as CSS tokens — that plus
this summary is enough for most pages. Open `references/style-guide.md` only
when you need the reasoning behind the grammar or are adapting the palette to a
user's brand.

Fonts: system stack by default. When brand typography matters, run
`scripts/embed_fonts.py --inject <page> "Family:400,700"` — it downloads
open-source faces and splices the data-URI `@font-face` CSS directly into the
file. Base64 must never pass through your context: don't cat the CSS, don't
paste blobs into Write/Edit.

## Step 2 — build the views

- **Logical**: HTML rows (`display:grid`), one band per tier, service cards
  inside. No SVG needed.
- **Schematic**: SVG with `viewBox`, wrapped in a container with
  `overflow-x:auto` and a `min-width` so phones scroll instead of squishing.
  Zones are `<rect>`s with labels top-left; components are white `<rect>`s with
  2–5 `<text>` lines; connectors are `<path>` with only `H`/`V` segments.
- **Detail/storyboard**: **start by copying the working example — do not write
  the player from scratch.** `cp references/template.html <output>.html`, then
  edit in place: replace the demo stage SVG (topology, counters, ghosts) and
  the `steps` array, adjust the masthead/legend copy, and add the other
  sections around the player. The CSS tokens and everything below the
  `KEEP: player machinery` comment in the script stay as they are — they're
  boilerplate that is identical in every page. You don't need to read the whole
  template into context; the `EDIT`/`KEEP` comments mark what changes. Consult
  `references/storyboard-pattern.md` (a short adaptation checklist) only when
  your scenario needs mechanics the template lacks.

## Step 3 — geometry discipline (where these pages actually fail)

SVG has no layout engine; you are the layout engine. `scripts/validate.py`
re-checks all of this mechanically afterwards, but budgeting while you draw is
cheaper than fixing warnings later:

- **Text width**: estimate ~0.60em per character (≈6.2 px at font-size 10.5–12.5).
  Every `<text>` must fit `box_width − 2×padding`. Shorten the string or widen
  the box — never let labels overrun into a neighbor.
- **Connector routing**: paths must never pass **through** a box. Leave 20–40 px
  gutters between box columns and route `H`/`V` segments through gutters and the
  empty bands above/below box rows. Two parallel segments on the same axis need
  ≥6 px separation. Perpendicular **crossings** of two flows are fine; collinear
  **overlaps** are not.
- **Endpoints**: every path must start and end exactly on the edge of the boxes
  it connects (compare the path's first/last coordinate to the rect's
  x/y/width/height — don't eyeball it).
- **Flow labels** live in whitespace beside their line, never on top of a box or
  another label. If there's no room, shorten the label or drop it (the caption
  panel can carry detail the diagram can't).
- Everything must stay inside the `viewBox`, and children inside their parent zone.

## Step 4 — validate, then review (inline, bounded)

1. Run `python3 scripts/validate.py <page.html>`. It checks structure (tag
   balance, script id references, anchors, JS syntax) **and geometry** — text
   overflowing boxes, labels sitting on boxes, paths cutting through boxes,
   endpoints floating off box edges, viewBox escapes. Fix errors; treat
   warnings as pointers and confirm each with arithmetic (widths are
   estimates) before moving a coordinate. Two fix-and-rerun cycles is
   normally enough — if warnings persist past that, they're probably
   tolerable near-edge estimates; say so and stop.
2. Walk every storyboard step **from the steps array you just wrote — do not
   re-Read the finished file**: highlighted boxes match the caption's actors,
   active flows match the movement described, counters and ghosts show every
   state change the caption claims, and each step's end state is where the
   next step starts.
3. If the architecture came from a real codebase or document, verify the
   numbers and names you put in the page against the source before shipping —
   wrong figures in a polished page are worse than no figures. Keep this
   proportionate to the claim's weight.

This whole step is a single inline pass by you — it does not need subagents or
a separate review round unless the user explicitly asks for deep verification.

## Hard rules

- Single file, zero external requests. Inline everything; assets as data URIs.
- Both themes get equal care — check connector colors and node fills on dark.
- Respect `prefers-reduced-motion`: traveling dots off, state changes instant,
  stepping still fully functional.
- Never put real secrets, tokens, or private hostnames into a page that may be
  hosted publicly.
- Real content only: real component names, real ports, real measured numbers —
  or clearly illustrative ones. No lorem, no invented metrics presented as fact.
