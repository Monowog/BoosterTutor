# ADR 0012 — Color fit is a commitment tax, not a conditioned win rate

**Status:** Proposed · **Date:** 2026-09-21 · **Supersedes:** ADR 0003 §1.2, ADR 0007 §1 and ADR 0011 **in full**; amends ADR 0005 §3 (option value is deleted) · **Relates to:** ADR 0006 (tag synergy, now the only card-specific fit signal), ADR 0008 (classification), ADR 0013 (`tax_value` is format-level)

---

## Context

`color_fit` has been reworked more than any other term and was still the
least settled. It was a residual — `base(card, pool, t) − overall` — computed
by a three-way branch on a predicted archetype, with a presence taper, a
minimum penalty, a replacement floor and an archetype-strength correction
layered on over four ADRs.

Measuring it across the three reference drafts (882 scored card-instances;
HOB packs are 14 cards, so a draft is **42 picks, not 45**) showed it was not
doing the job its name claims.

**The off-color penalty is near-inert, and gets weaker late.** Median
off-color `color_fit` is **−1.25pp**. Only 15 of 307 off-color cards ever
lose 3pp or more; 112 lose under 1pp. Against `solid_gap` 2.0 that is barely
a signal at all. Worse, it decays through the back half of the draft:

| pick band | n | mean color_fit | mean λ | mean taper |
|---|---|---|---|---|
| 5–10 | 50 | −0.36 | 0.19 | 0.87 |
| 11–21 | 91 | −1.52 | 0.73 | 0.75 |
| 22–33 | 115 | −1.68 | 1.00 | 0.62 |
| 34–42 | 51 | **−1.30** | 1.00 | **0.55** |

λ pins at 1.0 from pick 22, but `off_color_discount` keeps sliding, so the
realized penalty falls exactly where the drafter should be most committed.
The mechanism is self-reinforcing by construction: the taper divides by the
archetype's weaker color share, and every off-color card you take raises
your off-colors' presence, so **each stray pick makes the next one cheaper**.

**The on-color branch is not a reward.** After ADR 0011's normalization it
is centered almost exactly on zero — mean +0.075, median 0.00, 131 negative
against 127 positive, range −5.01 to +9.69. It is card-specific fit plus
noise, not a signal that the pool likes the card.

**The predicted archetype is wrong for long stretches, not merely volatile.**
Top-two-by-count with `None` on any tie produced, by global pick index:

- **WR** `f1daa925`: `—[1-5] WR[6-42]`
- **BR** `d9ac6765`: `—[1-5] BR[6-10] — RG[12-23] — RG[25] — RG[27-32] — BR[34-42]`
- **UG** `dba56c2c`: `—[1-4] UG[5-8] — UG[10-13] —[14-18] WG[19-23] —[24-28] UG[29-42]`

The BR draft is scored against **RG for 21 of its 42 picks**. The UG draft
spends picks 19–23 as WG, whose archetype offset is −8.63pp, the largest in
the set. Every single-pick `—` dropout is a momentary second/third tie that
silently zeroes color fit for a whole pack.

## Decision

Replace the whole term with a **commitment tax** over a continuous archetype
signal. No scoped win rates, no belief distribution, no branches.

### 1. Archetype floats

For each of the ten pairs `P`:

```
f_P = |{x in pool : playable_in(x, P)}| / |pool|
```

over **colored pool cards only** — colorless cards and basic lands are
excluded from both numerator and denominator. `playable_in` is unchanged and
already encodes the intended rule exactly: a gold `{W}{R}` card counts toward
WR alone, a hybrid `{W/R}` card counts as a full card toward every pair
holding W *or* R, and a mono-white card counts toward all four W pairs.

The floats are **overlap measures, not a distribution**: they do not sum to
1. For a pool of 4 W, 4 U, 1 R and 1 WR they are WU 0.8, WR 0.6, WB 0.4,
WG 0.4, UB 0.4, UR 0.5, UG 0.4, BR 0.1, RG 0.1, BG 0.0.

### 2. The tax

```
color_fit = −λ(t) · tax_value · ( max_P f_P  −  max_{P : playable_in(card, P)} f_P )
```

`tax_value` is format-level (ADR 0013), **12.0 for HOB**. λ is the existing
commitment ramp, unchanged. The bracketed difference is the **color tax
fraction**, a 0–1 number that replaces the binary `off_color` flag.

For the example pool, a green card pays `12 × (0.8 − 0.4) = 4.8pp` at λ = 1;
a red card `12 × (0.8 − 0.6) = 2.4pp`; a white or blue card nothing.

**Edge cases.** An empty colored pool gives every float 0 and a tax of 0
(λ = 0 through pick 4 covers this anyway, but the division must not be left
there). A three-or-more-color card is playable in no pair, so the inner max
is over the empty set — **defined as 0**, giving the full `λ · tax_value ·
max_P f_P`. Both want tests.

### 3. What this deletes

`Stats.scoped`, `scoped_wr`, `archetype_wr`, `archetype_offset`,
`min_games_scoped`, `off_color_discount`, `color_shares`,
`off_color_min_penalty`, `predicted_archetype` (top-two-by-count), the
three-branch `base()`, and — per ADR 0005 §3 — `option_value`,
`option_value_weight` and `splash_worthy_wr`. Option value existed to soften
a penalty that fired too hard too early; λ already does that, and a refund
on top risks a net *bonus* for straying. `replacement_offset` survives, but
its only remaining reader is the `openness` gate.

`CardFitness.off_color: bool` becomes `color_tax_fraction: float`, and
`CardFitness.option_value` is removed.

### 4. One definition of your archetype

The **argmax float pair** is the predicted archetype everywhere — fitness,
`on_color_pool()` for the role term, the UI and the brief. It never returns
`None`, so the tie dropouts disappear. `target_creatures` and
`target_removal` keep counting whole cards and are **not** re-derived.

### 6. Lands (amended 2026-09-22)

ADR 0012 as first written had nothing to say about lands, which left them in
an incoherent position: Scryfall gives a land no colour, so a dual land was
playable in every pair and paid **no tax in any pool**, while also being
excluded from the floats only by accident of that same empty `colors` field.

**A land's playable colours come from its colour identity, read as hybrid.**
One option per colour, so Goblin-town (BR) is playable in any pair holding
black or red. Hybrid rather than gold, because the two are genuinely
different: a `{B}{R}` spell in a BG deck is uncastable, whereas Goblin-town
in a BG deck taps for black and goes straight in. It generalises upward — a
WUB tri-land in a UB deck taps for two of your colours, so it suits more
decks than a dual, not fewer — and it keeps the magnitude sane, since gold
treatment would price an off-colour land at the full `tax_value`, three
times `mistake_gap`.

**Colour identity, not produced mana, is the definition** — deliberately,
not as a convenience. A land whose only relevant ability costs `{B}` is
black-exclusive in practice even though it taps for nothing coloured, and
identity is what captures that. `produced_mana` would be the wrong source
here, so there is nothing to revisit.

**Every land is excluded from the archetype floats, whatever its colours.** A
dual land is evidence that you are *open to* a pair, not that you are in it,
and lands get taken for fixing and for want of anything better. This was
already true incidentally, because the float filter keys on `colors` and
lands have none — but Magic prints coloured lands (Dryad Arbor is a green
Land Creature), so the exclusion now keys on the `land` tag and does not
depend on that accident.

The rule lives in `analysis/` as `playable_colors(card)`, which defers to
`color_options()` for anything that is not a land, so every playability rule
stays in the pure, exhaustively tested module.

**On HOB this affects six cards.** Five duals — Lake-town (WU), Goblin-town
(BR), Iron Hills (WR), Mirkwood (BG), Elvenking's Halls (UG), a half-cycle —
plus The Lonely Mountain, a mono-red nonbasic taken at ALSA 3.00 on a 58.1
GIH WR, the strongest land in the set and previously untaxed everywhere.
Elven Passage and Hobbit Hole have no colour identity and stay untaxed.
Basic lands are never scored at all.

## Consequences

**Good.** The tax is continuous in the pool: it reads float *values*, not the
argmax *identity*, so `color_fit` cannot jump when the leading pair changes --
a flip does not alter `max_P f_P`, which is the only thing the tax reads from
the leader. The `None`-on-tie dropouts are gone outright.

**But the leading pair still flips, and that claim was overstated when this
ADR was drafted.** On the BR reference draft the pair still reads
`WR[2-3] RG[4] BR[5-11] RG[12-23] BR[24] RG[25] BR[26] RG[27-32] BR[33-42]`
-- nine changes, the same count as the rule it replaces. The measured reason
is that the pool genuinely was contested: through picks 12-32 it held more
green than black (G 4-6 against B 2-5) and the BR and RG floats sat within
0.000 to 0.15 of each other, crossing repeatedly, until black pulled away at
pick 33. The old rule was not misreading the pool so much as the pool was
ambiguous, and calling it "wrong for 21 picks" in the Context above overstates
it: "BR" is the label of the finished deck, not of the pool at pick 20.

What changed is the *consequence* of a flip. It no longer moves `color_fit`
at all; it moves only `on_color_pool` (and so the role term, at weights 0.40
and 1.25) and the pair named in the UI. Hysteresis would now be a cosmetic
fix, not a scoring one.

The term is
roughly fifteen lines replacing eighty, with one tunable instead of four. It
distinguishes splash depth correctly — in a balanced 10W/10U pool every
single-off-color card (mono-B, mono-G, WB, UB) taxes at 6.0pp while a BG gold
card, needing two new colors, taxes at the full 12.0.

**Costs, accepted knowingly:**

- **`color_fit` is non-positive by construction.** No card can be rewarded
  for suiting your deck, only taxed for not. The only remaining
  card-specific fit signal in the function is ADR 0006's authored tag
  synergy, which fires on **16 authored pairs across 193 HOB cards**. That
  coverage gap is now load-bearing, and growing the taxonomy is the debt
  this ADR creates.
- **252 of 328 on-color cards lose their scoped adjustment**, which ranged
  −5.01 to +9.69 with deciles −1.93 / −1.11 / −0.58 / −0.19 / −0.02 / +0.18
  / +0.61 / +1.16 / +2.19. About a fifth move by more than 2pp. Verdicts
  will shift on all three reference drafts, probably more than the tax
  redesign itself causes.
- **The self-reinforcement is not fixed — it is adopted.** Adding green
  cards to a committed 10W/10U pool, the tax on a *further* green card:

  | green in pool | WU float | WG float | tax |
  |---|---|---|---|
  | 0 | 1.000 | 0.500 | **6.00** |
  | 2 | 0.909 | 0.545 | 4.36 |
  | 4 | 0.833 | 0.583 | 3.00 |
  | 6 | 0.769 | 0.615 | 1.85 |
  | 8 | 0.714 | 0.643 | 0.86 |
  | 10 | 0.667 | 0.667 | **0.00** |

  A drafter who took one green card is told it cost 6pp; one who took eight
  is told the ninth is free. The position taken here is that a genuinely
  three-color pool *is* three colors and the tax should describe reality —
  the complaint belongs in the brief as "you are three colors", not in every
  pick's score. Rejected alternatives: weighting pool cards by pick recency
  or by their own fitness; computing floats only over cards that were
  on-color when picked (makes floats path-dependent, throwing away the main
  advantage); and measuring the gap against a fixed reference rather than
  `max_float`, which bounds the decay at 2.67pp instead of 0 but is less
  honest about the pool.
- **The tax structurally halves for mono-colored cards.** Any pair holding
  the card's color also holds one of yours and inherits those pool cards, so
  `best_float ≥ max(share of your first color, share of your second) ≥ 0.5`
  in a two-color pool. A mono off-color card therefore tops out at
  `tax_value / 2` = 6pp, maximized when your two colors are *evenly split*
  and falling as you commit harder to one. Only double-off-color gold cards
  ever see 12.
- **Archetype strength now has no carrier at all.** ADR 0011 removed it from
  fitness on the promise the brief would state it; this ADR makes that
  removal permanent and renders `archetype_offset` dead. Ticket #22 is now
  the only home for "you are in a weak lane". `card_archetype_stats` and
  `archetype_stats` stay in the schema — the ingest already populates them
  and the brief will need `archetype_stats` — but nothing in the fitness
  path reads either.

**Observed.** Implemented and re-scored. Verdict splits
(solid / questionable / mistake / indifferent), before and at `tax_value` 12:

| draft | before | after |
|---|---|---|
| WR `f1daa925` | 27 / 6 / 1 / 8 | 28 / 7 / 1 / 6 |
| BR `d9ac6765` | 32 / 1 / 2 / 7 | 35 / 0 / 2 / 5 |
| UG `dba56c2c` | 24 / 9 / 3 / 6 | 23 / 10 / 2 / 7 |

**`tax_value` cannot be calibrated from these three drafts.** Swept from 0 to
24, the splits barely move and mistakes are not even monotone in it (10 across
all three drafts at 0, 5 at 12, 6 at 24); what the tax mostly does is convert
`indifferent` into `solid` by widening pack spreads past `solid_gap`.

The reason is that verdicts are pack-relative and **these drafters almost
never strayed**. Of roughly 40 scored picks per draft, the card actually taken
carried any tax at all on 5 (WR), 9 (BR) and 6 (UG) picks, and a tax fraction
above 0.25 on 2, 2 and 1 -- about five picks across all three drafts where the
term has real weight. Raising the tax mostly pushes down cards nobody took.

So the tax is doing what it was designed to do and there is no evidence here
for what its value should be. Calibrating it needs either a draft that
actually goes off-color or ADR 0003 s3's backtest. `tax_value` stays at 12 as
a placeholder, and this ADR stays **Proposed** on that basis.

**Revisit when:** the taxonomy covers enough of a set that tag synergy is a
real signal rather than a sparse one; or the self-reinforcement above turns
out to flatter three-color drafts in practice; or a second format shows
`tax_value` needs a shape rather than a scalar.

**Glossary.** *Archetype Float* and *Color Tax* should be added to
`CONTEXT.md`; *Predicted Archetype* needs rewording to the argmax float pair.
