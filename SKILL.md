---
name: refarch-animator
description: Generate an animated reference-architecture page — layered diagram views (logical, schematic) plus a step-by-step animated storyboard of one scenario — as a single self-contained HTML file. Use when the user asks for an architecture diagram with animation, a "slide by slide" walkthrough of how a workload/request/failover moves through a system, or a polished reference-architecture deliverable they can host anywhere.
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

Read `references/style-guide.md` for the full visual grammar and a validated
default palette (zone borders by domain, flow-plane colors, neutrals for both
themes). The grammar in one breath: flat square-cornered zones on a quiet gray
canvas, white component nodes with thin borders, ALL-CAPS zone labels /
sentence-case component names, orthogonal 3px connectors color-coded by plane,
dashed borders for planned or torn-down elements, a footer legend band. Fonts:
system stack by default; `scripts/embed_fonts.py` can inline open-source faces
as data URIs when brand typography matters.

## Step 2 — build the views

- **Logical**: HTML rows (`display:grid`), one band per tier, service cards
  inside. No SVG needed.
- **Schematic**: SVG with `viewBox`, wrapped in a container with
  `overflow-x:auto` and a `min-width` so phones scroll instead of squishing.
  Zones are `<rect>`s with labels top-left; components are white `<rect>`s with
  2–5 `<text>` lines; connectors are `<path>` with only `H`/`V` segments.
- **Detail/storyboard**: a second, simpler SVG laid out left-to-right in
  scenario order, plus the player. Implement the player from
  `references/storyboard-pattern.md` — it specifies the steps data shape, the
  dot animator, counter tweens, ghost elements, `#step-N` deep links, a
  copy-link button, autoplay, ARIA, and `prefers-reduced-motion` behavior.
  `references/template.html` is a small complete working example — read it
  before writing your own player rather than reinventing it.

## Step 3 — geometry discipline (where these pages actually fail)

SVG has no layout engine; you are the layout engine. Budget before drawing:

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

## Step 4 — validate, then adversarially review

1. Run `python3 scripts/validate.py <page.html>` — checks tag balance, that
   every id referenced from the script exists, anchor targets resolve, and JS
   syntax (if `node` is available).
2. Re-check the geometry rules above against your actual coordinates —
   arithmetic, not vibes. The five recurring bugs: text overflowing a box, a
   path cutting through a box, a label sitting on a box, a path endpoint
   floating short of its box, and a storyboard step whose caption promises a
   state change the stage data doesn't show.
3. If the architecture came from a real codebase or document, verify every
   number and name in the page against the source before shipping — wrong
   figures in a polished page are worse than no figures.
4. Walk every storyboard step: highlighted boxes match the caption's actors,
   active flows match the movement described, counters end where the next step
   expects them.

## Hard rules

- Single file, zero external requests. Inline everything; assets as data URIs.
- Both themes get equal care — check connector colors and node fills on dark.
- Respect `prefers-reduced-motion`: traveling dots off, state changes instant,
  stepping still fully functional.
- Never put real secrets, tokens, or private hostnames into a page that may be
  hosted publicly.
- Real content only: real component names, real ports, real measured numbers —
  or clearly illustrative ones. No lorem, no invented metrics presented as fact.
