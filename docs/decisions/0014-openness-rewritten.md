# ADR 0014 — Openness pays for wheeling *good* cards, and only while there is draft left to guide

**Status:** Proposed · **Date:** 2026-09-21 · **Supersedes:** ADR 0003 §1.5 in full, together with its two amendments — BoosterTutor #29 (the one-sided clamp) and ADR 0007 §6 (the replacement gate), both of which are carried forward below · **Relates to:** ADR 0012 (color fit), ADR 0013 (format-level constants)

---

## Context

ADR 0003 §1.5 paid `openness_weight` (0.25pp) per pick a card was still in
the pack past its ALSA, capped at 1.5pp and scaled by `(1 − λ)`.

That rewards **any** card for being late, at the same rate. A filler common
with an ALSA of 10 sitting in front of you at pick 14 earned 1.0pp on the
same terms as a bomb with an ALSA of 1.4 wheeling to pick 8. But those two
facts are not the same fact. A bad card being late is not information —
it is late because it is bad, and everyone at the table agrees. A *good*
card being late is the only version of this that says anything about the
table, and it is the whole reason the term exists: it tells you a color is
under-drafted, so speculating there will be repaid in future packs.

The flat rate had no way to express that difference.

## Decision

### 1. The rate depends on how early the card usually goes

```
slope = openness_best_rate / (openness_dead_alsa − 1)
rate(alsa) = max(0, openness_best_rate − slope × (alsa − 1))
```

With `openness_best_rate = 0.5` and `openness_dead_alsa = 6.0` the slope is
0.1pp per point of ALSA: a card with the best possible ALSA of 1.0 pays
0.5pp per pick late, one at 2.0 pays 0.4, one at 5.0 pays 0.1, and anything
at 6.0 or beyond pays nothing at all.

The curve is **parameterised by the two numbers that were actually reasoned
about** — the rate at the best ALSA, and the ALSA at which the signal dies —
with the slope derived. The alternative, storing the intercept and slope
directly, makes the cutoff implicit: the first draft of this proposal
specified a slope of 0.1 and a cutoff of 7.0, which are inconsistent (that
slope reaches zero at 6.0). Deriving the slope makes that state
unrepresentable.

6.0 is the right cutoff on the data as well as the argument: HOB cards with
ALSA ≥ 6.0 average **53.8** GIH WR, which is below the 53.3 replacement
level, against 55.62 for the rest.

### 2. The weight is how much draft is left to guide

```
pack_weight = (packs_per_draft − pack_no) / (packs_per_draft − 1)
```

1.0 in pack 1, 0.5 in pack 2, **0.0 in pack 3**. Openness exists to steer
the rest of the draft; in pack 3 there is no rest of the draft, so there is
nothing for it to steer and it is not a fitness consideration at all.

A second derivation lands on the same numbers and is probably the truer
causal story: packs pass left, right, left, so in pack 1 you are reading the
neighbours who will also feed you pack 3 — pack 1's signal reaches the rest
of pack 1 *and* all of pack 3, pack 2's reaches only the rest of pack 2, and
pack 3's reaches nothing. It is recorded here as corroboration rather than
as the rule, because it would break in a format that passed in a different
order, and "packs remaining" generalises to any pack count without thought.

**This replaces the `(1 − λ)` scaling, which is removed.** The two were
competing answers to one question, and the commitment ramp is the wrong one:
λ measures how committed the *pool* is, where openness is about how much
*draft* remains. Keeping both would have decayed the term twice and zeroed
it early in pack 2, before the halving could be observed. Openness is
therefore now wholly independent of the commitment ramp.

### 3. Both carried-forward amendments stay

**The clamp stays one-sided** (BoosterTutor #29): a card seen *earlier* than
its ALSA earns nothing rather than a penalty. At pick 1 every card is
"early", least so the cards usually taken first, and a symmetric clamp turned
that into a second helping of card quality.

**The replacement gate stays** (ADR 0007 §6): a card below
`format_avg − replacement_offset` earns nothing however late it is. The rate
curve does *not* subsume this. ALSA says what the table believes; GIH WR says
what is true, and the two disagree often enough to matter — 35 of 193 HOB
cards have an ALSA under 6.0 while sitting below replacement, led by Orcrist,
Goblin-cleaver (ALSA 1.81, GIH WR 50.7), My Precious (2.20, 50.4) and Inside
Information (2.74, 50.5). Rares and mythics get taken early for collection
and gem value regardless of whether they are any good, so a low ALSA is
evidence about drafters' incentives as much as about card quality. Without
the gate, Orcrist wheeling to pick 8 would earn 2.6pp for being bad in a way
other drafters have not noticed.

96 of 193 HOB cards (50%) clear both filters and can ever earn openness.

### 4. There is no cap

`openness_cap` is deleted. A bomb that wheels is the strongest read on a
table there is, and clipping it at 1.5pp discarded exactly the case the term
was rewritten to capture.

Uncapped is not unbounded: the rate maxes at `openness_best_rate` and
lateness cannot exceed `picks_per_pack − alsa`, so the term is structurally
capped at 0.5 × 13 = **6.5pp**, and at 6.25pp given HOB's actual minimum
ALSA of 1.14. That is larger than `synergy_cap` (5.0) and `mistake_gap`
(4.0), which is intended: a wheeling bomb should be able to spike a pick.

### 5. Signature

`openness(card, pick, pack_no, stats, cfg)`. With `(1 − λ)` gone the term no
longer reads the global pick index at all, and `score_pack` gains `pack_no`,
which `draft_link` already parses from the 17Lands payload.

`openness_weight` and `openness_cap` are deleted; `openness_best_rate`,
`openness_dead_alsa` and `packs_per_draft` are added.

## Consequences

**Good.** The term now says what its name means. The rate curve weights the
low-ALSA end hardest, which is exactly where ALSA is a trustworthy signal —
the six lowest-ALSA cards in HOB run 58.9 to 64.0 GIH WR — and flattens to
nothing through the middle, where it is not. Half the set can never earn it,
which is the point.

**Costs.** Two new tunables, neither validated, replacing two that were not
either. The term can now move a pick by up to 6.25pp on an inference drawn
from a single table's behaviour in a single pack, which is by some distance
the noisiest input in the function — `synergy`, measured over millions of
games, is capped at 5.0. This is a knowing trade.

`openness_dead_alsa` is **measured in picks and therefore scales with pack
size**: a 15-card-pack format's ALSAs all sit about 7% higher, so 6.0 would
want to be roughly 6.4. It is kept global rather than added to ADR 0013's
`format_constants`, consistent with the calls made there for `solid_gap`,
`mistake_gap` and the ramp, and for the same reason — there is no second
format to calibrate against. **Revisit when there is.**

**Observed.** Implemented and re-scored. Across all three reference drafts,
counting every scored card in every pack:

| | fires on | total pp paid | largest single |
|---|---|---|---|
| old term | 97 | 25.7 | 0.78 |
| new term | **44** | **7.5** | **0.78** |

The term is now about twice as selective and pays under a third as much in
total, which is the intended effect: half the set can no longer earn it at
all, and pack 3 pays nothing.

**But the case this was rewritten for never occurs in these drafts.** The
largest openness in all three is 0.78pp — unchanged from the old term, and
a factor of eight below the 6.25pp ceiling. Nothing fires above 1pp. That is
not a flaw in the rule so much as a consequence of it: a card only earns a
large boost by having a low ALSA *and* wheeling, and a low ALSA is precisely
a statement that the card does not wheel. The spike is a rare event by
construction, and three drafts do not contain one.

So `openness_best_rate` and `openness_dead_alsa` have the same calibration
problem as ADR 0012's `tax_value`: the reference drafts confirm the shape is
doing what was asked and give no evidence at all about the magnitude. Both
stay at their proposed values, and this ADR stays **Proposed** on that basis.

Verdict splits moved barely, and only on the UG draft
(solid / questionable / mistake / indifferent): WR 28/7/1/6 unchanged, BR
35/0/2/5 to 35/1/1/5, UG 23/10/2/7 to 22/11/2/7.

**Glossary.** *Openness* and *ALSA* are added to `CONTEXT.md`; neither was
in it.
