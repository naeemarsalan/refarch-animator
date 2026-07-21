# Storyboard adaptation checklist

The canonical player implementation is `references/template.html` — copy it and
edit; don't re-derive it from prose. This file is the delta: the rules that
matter when adapting the copy to a new scenario, including the ones the code
can't show.

## Stage

- Lay components out **left-to-right in scenario order** (signal source →
  transforms → decision maker → effect). When that ordering happens to match
  the schematic's layout, reuse one diagram rather than drawing two.
- Id conventions the machinery expects: `b-*` component groups, `f-*` flow
  paths, `c-*` counters (`<tspan>`s), `g-*` ghosts. Update the `HOT` and
  `GHOSTS` arrays to match your stage.
- Flow paths are drawn once and dimmed; steps light them. Elements that appear
  mid-story start as `.ghost`.

## Steps array

- **Steps are absolute, not incremental**: every step lists the complete
  visible state — all counters, all ghosts. Rendering step N must never depend
  on step N−1 having rendered; that's what makes deep links work.
- Captions carry the story: 1–3 sentences, real numbers. If a caption claims a
  state change ("scales back to 0"), the step's data must show it. Auditing
  caption-vs-data across all steps catches most storyboard bugs — do it from
  the array you wrote, not by re-reading the file.
- Every id a step references must exist in the SVG (`scripts/validate.py`
  checks this).

## Wiring changes in `go()`

Counters and meters are scenario-specific: retarget the tween call(s) and the
plain-text counter assignments to your `c-*` ids; keep one cancellable tween
handle per animated counter or rapid stepping makes numbers flicker.

## Behavior contracts (already implemented — don't break them when editing)

- Deep links: `#step-N` honored on load and `hashchange`; navigation uses
  `history.replaceState` (never push) wrapped in try/catch, and skips the
  initial render so an incoming section hash isn't clobbered.
- Copy-link button falls back to `execCommand('copy')` because
  `navigator.clipboard` needs a secure context (plain-HTTP hosts don't have one).
- Arrow keys: ignored with modifiers, on interactive/scrollable targets, and
  when the player is off-screen; `preventDefault()` only when handled.
- Dots move at constant speed (~90 px/s), not constant duration.
- `prefers-reduced-motion`: no dots, instant tweens, stepping fully functional.
- Autoplay stops at the last step; any manual action cancels it.
- The caption panel keeps `aria-live="polite"`; the active dot uses
  `aria-current`.
