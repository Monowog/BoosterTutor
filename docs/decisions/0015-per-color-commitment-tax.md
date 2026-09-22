# ADR 0015 — The commitment tax is summed per off-color, not read off a pair gap

**Status:** Proposed · **Date:** 2026-09-22 · **Supersedes:** ADR 0012 §2 (the tax formula) **only**. ADR 0012 §1 (archetype floats), §3–§5 and §6 (lands) all stand and still do real work. · **Relates to:** ADR 0007 §5 (hybrid cards), ADR 0013 (`tax_value` is format-level)

---

## Context

ADR 0012 §2 priced commitment as the gap between the leading archetype float
and the best float of any archetype the card could be played in. Testing it
found it does not punish off-color mono cards hard enough, and the reason is
structural rather than a matter of the constant.

**A lopsided pool collapses the gap.** With 8 white and 2 blue cards, `WG`
floats 0.80 against `WU`'s 1.00, so a green card pays `12 × 0.20 = 2.4pp`.
The float measure is saying "you are basically mono-white, so green is
nearly as good a second color as blue" — true as far as it goes, and useless
as advice. What the drafter needs to hear is measured against how committed
the *second color* actually is, which is two cards.

This was foreseen. The first grilling on ADR 0012 recorded that "a heavily
mono pool taxes all off-colors lightly", and the point was deferred; it is
what testing surfaced.

## Decision

```
color_fit = −λ × tax_value × color_tax_units(card, pool)
```

where, with A the predicted archetype (**still ADR 0012 §1's argmax float
pair** — there remains exactly one definition of your archetype), `counts`
the number of pool cards containing each color, and `second` the count of
A's weaker color:

```
units(option) = Σ  clamp(0, 1, (second − counts[c]) / second)   for c in option not in A
color_tax_units = min over the card's color options of units(option)
```

`tax_value` moves from **12.0 to 6.0**, because the unit is now one whole
off-color rather than a pair-overlap fraction.

**Each off-color is charged separately and they add.** A mono card in a
color with no pool presence pays one full `tax_value`; Thranduil, the
Elvenking (`{2}{B}{G}{U}`, HOB's only three-color card) with none of its
colors present pays three, 18pp.

### Four rules the formula needs

**The minimum is over color options, not a sum over `colors`.** A `{2}{B/G}`
card needs black *or* green, so it pays whichever is cheaper — exactly the
card ADR 0007 §5 exists to protect, and exactly what `playable_in` already
means by playable. Summing naively over `colors` would have charged
Duskwatch Hunter for both: **−9.75pp instead of −4.50pp**, on a set where
**12 of 26 multicolor cards are hybrid**. Dual lands fall out of the same
rule, since ADR 0012 §6 already gives them per-color options.

**Each color's term is clamped to [0, 1].** It cannot go negative, which
matters because the archetype comes from floats while the counts do not, so
a color outside A can out-count A's weaker color.

**A second color count of zero yields no tax.** With fewer than two colors
in the pool there is no commitment to be off. This happens on 8 of 126 picks
across the reference drafts, all within picks 1–4, where λ is zero anyway.

**Lands are excluded from the counts**, for the reason ADR 0012 §6 excludes
them from the floats: a dual land says you are open to a pair, not in it.

## Consequences

**Good.** The tax is now measured against how committed you actually are,
not against how much overlap two pairs happen to share. Over the three
reference drafts, cards taxed by either scheme move from a mean of −1.61 and
a floor of −6.60 to **−2.76 and −8.80**.

Note precisely what changed, because the formulae obscure it: the *ceiling*
for a mono-color card is 6pp under both schemes — `tax_value / 2` before,
`tax_value × 1.0` now. What changed is how often it is reached. Before, only
when your two colors were exactly balanced; now, whenever the card's color
is simply absent from the pool. ADR 0012's "structural halving" is gone as a
*constraint*, not as a number.

**Costs.** `color_tax_fraction` is deleted rather than renamed: with a
per-color sum it can exceed 1.0 (it reaches 2.40 on these drafts, and
Thranduil could reach 3.0), and a field named "fraction" reading 2.40 is
worse than no field at all. `color_fit` in pp carries what the popup needs.

**The self-reinforcement survives**, in the form ADR 0012 adopted
deliberately: taking more of an off-color raises its count and lowers its own
tax, reaching zero when it ties your second color. The argument there is
unchanged — a pool that really is three colors is three colors.

`tax_value` is still hand-picked with no measurable basis, and the reference
drafts still cannot calibrate it: those drafters barely strayed, so the
evidence is a handful of picks. ADR 0003 §3's backtest remains the thing that
would settle it.

**Revisit when:** the backtest exists; or if the thin-denominator case bites
— `second` is 1 or 2 on 21% of picks, and at 1 a single card swings the term
by a whole `tax_value`. A floor on the denominator was considered and
deliberately not added, on the grounds that those picks are concentrated
early where λ is small. That should be measured before it is assumed.
