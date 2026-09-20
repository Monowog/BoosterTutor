# ADR 0011 — An archetype's own strength is not color fit

**Status:** Proposed · **Date:** 2026-09-19 · **Supersedes:** ADR 0003 §1.2's use of the raw archetype-scoped rate, as carried into ADR 0007 §1 · **Relates to:** ADR 0007 (the predicted archetype), `CLAUDE.md`'s "advice blends format-level meta with card-specific synergy"

---

## Context

ADR 0003 §1.2 made archetype-scoped GIH WR the synergy layer: "a card at 53%
overall and 57% in Boros is telling us about synergy, measured over millions
of games". ADR 0007 kept that, scoring an on-color card at its rate inside
the one predicted archetype. `color_fit` is then `λ × (scoped − overall)`.

A bug report on a predominantly green draft showed what that actually
measures. Duskwatch Hunter, a `{2}{B/G}` hybrid correctly recognised as
playable in UG, was docked **6.10pp** of color fit. It is 55.74% overall and
49.64% in UG over 965 games, so the arithmetic was right.

The data was the problem. **UG is the second-worst archetype in HOB**, 52.17%
against a 56.3% format average. Every UG-scoped rate carries that 4.13pp
deficit before the card is considered, so `color_fit` — a term whose name and
purpose are "does this card suit your colors" — was largely reporting "are
your colors any good". About two thirds of that 6.10 was UG being weak.

Worse, it applied unevenly. Of 83 on-color cards scored while the pool read
UG, the 73 whose scoped sample cleared `min_games_scoped` averaged −2.11pp,
while the 10 with thin samples fell back to the overall rate and were docked
**exactly 0.00**. The function was penalising the cards it knew most about
and sparing the rest: a data-availability artifact, not a drafting signal.

## Decision

Normalize a scoped rate against its own archetype's win rate before using
it:

```
conditioned = scoped − (archetype_win_rate − format_avg_win_rate)
```

Duskwatch Hunter becomes `49.64 + 4.13 = 53.77`, so its color fit reads
−1.97: the card-specific part alone.

`Stats` gains `archetype_wr` (pair → that whole pair's win rate) and
`archetype_offset()`. The rates come from the `archetype_stats` table, which
the 17Lands ingest already populated and nothing had read. An archetype with
no recorded rate offsets by zero.

`Stats.scoped_wr()` is added alongside `gih_wr()` so `base` can tell whether
a scoped rate was actually used rather than silently falling back — the
distinction the old code could not express, and the reason the penalty
landed unevenly.

**Archetype strength therefore leaves the fitness function entirely.**
`CLAUDE.md` says advice should blend format-level meta with card-specific
synergy, and it still should: the view taken here is that the strength of
the archetype you are in is a fact the prompt brief should *state*, not one
that should be silently folded into every card's score. Whether your colors
are good is a sentence a coach says once per draft, not a tax applied 500
times.

## Consequences

**Good.** `color_fit` means what it says. Cards with deep and thin scoped
samples are treated comparably instead of arbitrarily differently. It also
repairs a second distortion that had not been reported: on-color cards in a
weak archetype used to drift down toward the fixed `replacement` level,
which made off-color cards look relatively better precisely when committing
harder was the right advice.

**Costs.** The function no longer expresses "you are in a bad lane" at all,
so if that signal is wanted it must be added deliberately, in the brief
(ticket #22). This ADR is also a second correction to ADR 0003 §1.2's claim
that scoped rates are cleanly "the synergy layer" — they are the synergy
layer plus the archetype's strength, and only the difference is synergy.

**Observed.** On the reported draft, color fit for Duskwatch Hunter went
from −6.10 to −1.97, mistakes fell from 7 to 3, and solid rose from 21 to
24. Cards genuinely off-color are unaffected, since their penalty never used
a scoped rate.

**Revisit when:** the brief carries archetype strength as its own stated
fact, at which point check that the two are not double-counting; or if the
backtest shows drafters really should be pushed out of weak lanes by the
pick scores themselves.
