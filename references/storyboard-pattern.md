# The storyboard player pattern

One SVG stage + one steps array + ~150 lines of dependency-free JS. The stage
shows the whole topology at once; each step highlights actors, animates the
active flows, and updates counters. `references/template.html` implements all
of this — read it first; this file explains the moving parts so you can adapt
them.

## Stage SVG

- Lay components out **left-to-right in scenario order** (signal source →
  transforms → decision maker → effect), which usually differs from the
  schematic's geographic layout. Duplicate the topology here rather than
  reusing the schematic — the two views optimize for different things.
- Every element the steps reference gets an `id`: component groups (`b-*`),
  flow paths (`f-*`), counters (`c-*`), ghost elements that appear mid-story.
- Flow paths are drawn once, dimmed by default (`opacity:0.16`), and lit by the
  active step (`.on { opacity:1 }`).
- Elements that appear during the story (new replicas, new links) are `.ghost`
  (opacity 0) until a step adds `.shown`.
- Counters are `<tspan id>`s inside node labels; meters are a track `<rect>` +
  fill `<rect>` whose width the script sets.

## Steps data shape

Each step is one object; the whole scenario is an array:

```js
{
  t: 'Autoscaler reacts',                 // slide title
  b: 'Depth 480 exceeds 50/worker...',    // caption: 1–3 sentences, real numbers
  hot: ['b-scaler', 'b-pool'],            // component ids to highlight
  flows: [['f-scale', false]],            // [pathId, reverse?] to light + animate
  counters: { depth: 480, replicas: 6 },  // every counter, every step (no deltas)
  ghosts: ['g-w3', 'g-w4'],               // ghost ids visible from this step
}
```

Rules that keep the machine debuggable:
- **Steps are absolute, not incremental.** Every step lists the *complete*
  visible state (all counters, all ghosts). Rendering step N must not depend on
  having rendered N−1 — that's what makes deep links and the dot-jump work.
- Every id referenced must exist in the SVG (the validator checks this).
- If a caption claims a state change ("scales back to 0"), the step's data must
  show it (counters/ghosts actually at 0). Auditing caption-vs-data across all
  steps catches most storyboard bugs.

## The renderer: `go(i)`

Single function, idempotent: set title/caption text, toggle `aria-current` on
the step dots, clear all highlights then apply `hot`, clear all `.on` then
light `flows`, tween counters to their new values, sync ghosts, then start the
dot animator for the active flows. Wire Prev/Next buttons, clickable step dots,
ArrowLeft/ArrowRight, and autoplay (≈7 s/step, stops at the end, any manual
action cancels it) to `go()`.

## Traveling dots

`requestAnimationFrame` loop; per active path spawn 2–4 `<circle>`s (spaced by
initial offset) and advance each along `path.getPointAtLength((offset % 1) *
totalLength)` — reversed paths use `1 − offset`. Constant *speed* (≈90 px/s),
not constant duration, so long paths don't get comically fast dots. Kill the
loop and remove the circles on every step change. Color each dot from its
path's plane class.

## Counter tweens

~600 ms ease from current to target, `toLocaleString` for thousands, meter
width = `track × value / max`. Keep **one** cancellable handle per counter
family (`cancelAnimationFrame` before starting a new tween) or rapid stepping
spawns racing loops that make numbers flicker.

## Deep links

- On navigation: `history.replaceState(null, '', '#step-' + (i+1))` — replace,
  not push, so stepping doesn't pollute history. Wrap in try/catch (sandboxed
  iframes may throw). Skip it during the initial render so an incoming section
  hash like `#detail` isn't clobbered.
- On load and on `hashchange`: parse `/^#step-(\d+)$/`, clamp to range,
  `go(n-1)`, and `scrollIntoView()` the player (the browser won't scroll to a
  hash that has no element).
- A "Copy step link" button: `navigator.clipboard` needs a secure context, so
  on plain-HTTP hosts fall back to a hidden textarea + `document.execCommand
  ('copy')`; on failure show "Link in address bar" (replaceState already put it
  there). Button label states what it does; flip to "Copied" for ~1.5 s.

## Accessibility & motion

- Controls are real `<button>`s with `aria-label`s and visible focus states;
  the caption panel gets `aria-live="polite"`; the current step dot gets
  `aria-current="true"` (don't cargo-cult `role="tab"` without the full tabs
  contract).
- Global arrow-key handler: bail on modifier keys, on interactive/scrollable
  targets, and when the player is off-screen (`getBoundingClientRect` check);
  `preventDefault()` only when actually handling the key.
- `prefers-reduced-motion: reduce`: no traveling dots, tweens jump instantly —
  highlights, ghosts, and stepping still work. The storyboard must be fully
  usable with zero animation.
