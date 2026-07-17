# refarch-animator

A [Claude Code](https://claude.com/claude-code) skill that generates **animated
reference-architecture pages**: layered diagram views (logical + schematic) plus
a **step-by-step animated storyboard** showing how a workload, request, scale
event, or failover moves through a system — all in **one self-contained HTML
file** you can host anywhere (static server, wiki, artifact platform).

The storyboard is the centerpiece: an SVG stage of the whole topology, a player
(Prev / Next / autoplay / step dots / arrow keys), traveling dots along the
active flows, live counters (queue depth, replica counts), and deep-linkable
steps (`page.html#step-7`) with a copy-link button.

## What you get

- **Single file, zero external requests** — CSS, JS, and (optionally) fonts
  inlined; safe behind strict CSPs and on air-gapped hosts.
- **Light + dark themes** via tokens, honoring both the OS preference and a
  host page's `data-theme` toggle.
- **A disciplined visual grammar** (flat zones, orthogonal plane-colored
  connectors, status conventions) distilled from Red Hat's public Portfolio
  Architecture methodology — swap in your own brand tokens if you have them.
- **Accessible by construction** — real buttons, `aria-live` captions, full
  keyboard support, and a `prefers-reduced-motion` mode where every step still
  works without animation.

## Install

Clone into your Claude Code skills directory — user-wide:

```bash
git clone https://github.com/naeemarsalan/refarch-animator ~/.claude/skills/refarch-animator
```

or per-project:

```bash
git clone https://github.com/naeemarsalan/refarch-animator .claude/skills/refarch-animator
```

Claude Code picks it up automatically; invoke it by asking naturally or with
`/refarch-animator`.

## Use

Ask Claude Code things like:

> Create an animated reference architecture for this repo — show how a request
> flows from the CDN to the database, slide by slide.

> Make a step-by-step animated diagram of our autoscaling path: queue depth →
> metrics → autoscaler → new pods.

The skill walks Claude through gathering the real components/flows/numbers
first, applying the visual grammar, building the storyboard state machine, and
validating the result (`scripts/validate.py`) before shipping.

## Repo layout

```
SKILL.md                        the skill: process, geometry rules, QA loop
references/style-guide.md       visual grammar + validated light/dark palette
references/storyboard-pattern.md  the player: steps state machine, dots, deep links
references/template.html        small complete working example (open it in a browser)
scripts/validate.py             tag/id/anchor/JS structural checks
scripts/embed_fonts.py          inline Google Fonts as data-URI @font-face CSS
```

Open `references/template.html` in a browser to see the pattern running — a
generic autoscaling scenario in 9 steps.

## License

MIT — see [LICENSE](LICENSE).
