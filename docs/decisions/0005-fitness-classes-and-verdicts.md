# ADR 0005 — Fitness classes and verdicts

**Status:** Proposed · **Date:** 2026-09-17 · **Supersedes:** ADR 0003 §2.2 (bands) and §2.3 (speculation override). ADR 0003 §1 (the fitness function) and §3 (backtest) stand.

> **Amended by ADR 0007 (2026-09-18):** `unimportant` is renamed `indifferent`; §1 gains a format-average floor for `solid`; §2's conditions are replaced by vetoes plus a same-class rule. The text below is kept as written.

---

## Context

ADR 0003 turned a fitness gap into one of five verdicts (`insufficient_data`,
`optimal`, `reasonable`, `questionable`, `mistake`) and then applied a
post-hoc "downgrade" when an early off-colour bomb was taken. Designing the
Draft Review UI against it surfaced four problems:

1. **The names were wrong for the product.** "Optimal" over-claims for a gap
   that is merely within noise, "mistake" is the scolding tone the prompt rules
   forbid, and the product notes had used Solid / Reasonable / Questionable
   for a year.
2. **Only the pick had a band.** The UI needs a band for *every* card in the
   pack, so a drafter can see which alternatives were also fine. The verdict is
   then just the band of the card taken.
3. **The override was a patch.** Speculation was handled by softening a
   computed verdict one band after the fact, which made the verdict a
   two-step function and the fitness number a lie about the card's value.
4. **`insufficient_data` was the wrong level.** A card with thin data is a
   property of the card; a pick where *nothing* was worth taking is a
   different thing, and there was no way to say it.

## Decision

### 1. Every card in a pack gets a fitness class

```
gap(card) = max_fitness(pack) - fitness(card)     # pp, always >= 0
```

| Fitness class | Condition |
|---|---|
| `solid` | `gap` within the noise floor (ADR 0003 §2.1, unchanged) |
| `reasonable` | `gap < X` |
| `questionable` | `gap >= X` |

`X` is a set-level tunable, not yet chosen; it is one of the numbers the
ADR 0003 §3 backtest exists to find. The gap is measured against the best card
in *this* pack, so classes are pack-relative by construction: a flat pack has
no `questionable` card, whatever its absolute power.

Cards under `min_games` are **still scored** from the data they have and
classed like any other card. They carry an `insufficient_data` flag for the UI
and the brief, but there is no separate class for them.

### 2. The verdict is the class of the card taken, or `unimportant`

`verdict = fitness_class(card_taken)`, except when the pick is **unimportant**,
which requires one of:

1. only one card in the pack; or
2. no card in the drafter's colours is above replacement fitness, and no
   off-colour card is above the splash-worthy GIH WR threshold; or
3. every card in the pack is individually either `insufficient_data` or below
   replacement fitness.

Condition 2 can only fire once the commitment ramp λ is above zero; before
that the drafter has no colours and every card is "in colour". In practice
no pick should come out `unimportant` before roughly pick 11 of a pack.

A pack that is flat *and* strong (two equal bombs at P1P1) is **not**
unimportant. It is several `solid` picks. Unimportant means nothing worth
choosing between *and* nothing worth having.

### 3. Speculation is a fitness term, not an override

Option value — keeping colours open by taking a strong off-colour card early —
is added to the fitness function as a term in pp, scaled by `(1 − λ)` like
openness, so that the gap shrinks on its own and no second classing step is
needed. The `speculative` flag is set only when a card is off-colour, taken in
the first half of the draft, and above a GIH WR threshold; a weak off-colour
card never earns it. Such picks are expected to land `reasonable` at worst.
That is an expectation to check in the backtest, **not** a rule in the
classer: class stays a pure function of the gap.

The exact form and weight of the term belong to the fitness-function ticket.

### 4. Relevant picks

A pick is **relevant** when its verdict is `questionable`, or when it carries
the `speculative` flag. Only relevant picks get a brief and an LLM blurb.
This is where the teaching is, and it turns ~42 API calls per draft into a
handful.

## Consequences

**Good.** One class per card makes the UI honest about alternatives. Verdicts
are a single pure function. The product vocabulary and the code vocabulary
finally agree. LLM cost per review drops by an order of magnitude.

**Costs.** `X`, the splash-worthy GIH WR threshold, and the option-value
weight are three new tunables on top of ADR 0003's eight. The role term will
likely need to be allowed above 1pp when removal or creature counts are badly
short, which ADR 0003 §1.4 capped; revisit during tuning.

**Glossary:** Fitness Class, Verdict, Relevant Pick and Speculative are
defined in `CONTEXT.md`.
