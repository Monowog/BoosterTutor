# ADR 0007 — Predicted archetype, class floors and the removal tag

**Status:** Proposed · **Date:** 2026-09-18 · **Supersedes:** ADR 0003 §1.2 (the belief distribution), parts of ADR 0003 §1.4 (role counting) and ADR 0005 §1–2 (class and indifferent rules) · **Relates to:** ADR 0006 (synergy), the BIG_FIX_#1 design note

---

## Context

The fitness function shipped in DraftDouble (BoosterTutor #20) implemented
ADR 0003 literally. Reviewing its output on a real draft, Jackson found the
belief distribution hard to reason about — ten pairs, a softmax temperature,
a card-conditioned prior whose "exactly the unconditioned rate at λ = 0"
promise turned out to be false with real scoped data (#31) — and the
class rules too generous: a flat pack of filler produced `solid` picks, and
a pack with a clearly good card could still come out `indifferent`.

## Decision

### 1. One predicted archetype, or none

The pool predicts **one** two-colour archetype, read off pick counts per
colour: each pool card counts once for each of its colours (a gold card
for both; colourless cards and basic lands for none). The archetype is the
top two colours **only when both are unambiguous**. A three-or-more-way tie
at the top is no archetype; a clear leader with a tie for second is no
archetype either; a mono-colour lead is no archetype.

Archetype-scoped GIH WR is used **only** once λ > 0 *and* an archetype is
predicted, and then only that pair's data. No other pair is consulted, and
nothing is averaged across pairs.

```python
base = (1 − λ) · overall
     + λ · (scoped rate in the predicted archetype   if playable there
            else replacement level)                   # format avg − 3
# before λ > 0, or with no predicted archetype: base = overall
```

`colour_fit = base − overall` is therefore exactly 0 at the start of a draft
and whenever the pool has not chosen a lane. **While λ = 0 there is no
predicted archetype anywhere** — not in the UI, not for off-colour, not for
the speculative flag.

**The off-colour discount tapers with presence.** Replacement is not a
cliff: the discount an off-colour card takes is scaled by
`max(0, 1 − share(missing colour) / share(second archetype colour))`, where
a colour's share is its fraction of the pool's coloured picks (gold cards
count once per colour; colourless cards and basics are out of the
denominator). With 3 U, 5 B, 5 R in a BR pool, a blue card takes 40% of the
discount, a white card all of it, and a colour as present as the second
colour takes none. A gold card missing two colours uses the weaker share,
since both would have to be splashed. Off-colour status itself stays binary.

**And it never reaches zero.** The discount scales
`max(off_colour_min_penalty, overall − replacement)`, not just the part of
a card's rate above replacement, so a card that is *already* below
replacement still pays for being unplayable instead of escaping the colour
term for being bad. The two branches meet at `replacement +
off_colour_min_penalty`, so the curve is continuous, monotonic, and never
raises a card toward replacement. `off_colour_min_penalty` is a placeholder
at 2.0pp. Note this is a fitness penalty only: classes stay pack-relative,
so in a pack where everything is weak such a card can still class
`reasonable`. `tau` is removed from the
tunables. **Off-colour** has one definition everywhere: not playable in the
predicted archetype (never off-colour when there is none; colourless cards
never are). It drives the `speculative` flag, option value, and the
indifferent veto below.

### 2. Role counts on-colour copies; removal is a tag

Creature and removal deficits count only pool cards playable in the
predicted archetype (every card while there is none), and copies of the
same card count as that many. **Removal is the hand-authored `_removal_`
tag and nothing else**, so that non-traditional but real removal can be
declared as such by a person; no oracle-text heuristic. Creatures still
come from the type line.

### 3. `solid` has an absolute floor

A card is `solid` only if its gap to the pack's best is within the noise
floor **and** its fitness is at or above the format average. Gaps stay
pack-relative; the floor is not. A flat pack of 54s has no solid card.

### 4. `indifferent` (was `unimportant`): same class, nothing off-colour

The verdict formerly called `unimportant` is renamed **`indifferent`**
everywhere. A pick is `indifferent` when the pack holds one card (a last
pick, solid or not), or nothing scorable. Otherwise it is never
`indifferent` when the pack holds a `solid` card, or an on-colour card at
or above replacement fitness; failing those vetoes, it is `indifferent`
exactly when every scored card shares one fitness class and none of them
is off-colour. ADR 0005 §2's thin-data and splash-worthy conditions are
dropped. Basic lands, never scored, are ignored by the test.

### 5. Hybrid cards are dual-monocoloured

Scryfall marks a `{B/R}` card as gold, but for playability it is a black
card *or* a red card. Each card carries its **colour options** — the
alternative colour sets that can pay its front face: `{B/R}` → `B` or `R`,
`{B}{R}` → `BR`, `{1}{B}{B/R}` → `B`, `{2/W}` → generic, `{B/P}` → `B`. A
card is playable in a pair when any option fits inside it; off-colour and
the taper read the same options (a hybrid tapers by its better-represented
colour). Pool colour counts still use Scryfall's colours, so a hybrid votes
for both colours, like a gold card. HOB has eleven hybrid cards.

### 6. Openness only for playable cards

The openness term (ADR 0003 §1.5 as amended) applies only to cards whose
overall GIH WR is at or above replacement. A below-replacement card
wheeling late is not a signal worth pp.

### 7. Admin mode

Every scored card carries its full decomposition (`CardView.breakdown`:
total, GIH WR, colour fit, curve, role, openness, synergy, option value,
top-2 synergy firings). The review shows it in a popup on right-click. In the expanded pool view,
basic lands always sit under "Likely Unplayed". In
DraftDouble anyone may see it; in BoosterTutor the API omits `breakdown`
for non-admin users and the UI gates the popup on an admin claim (#32).

## Consequences

**Good.** The archetype is one readable fact ("you are RG") that the UI,
the role term, the off-colour rules and the brief all share, and it is
exactly what the pool summary already showed. Classes stop flattering
weak packs. The removal tag makes "what counts as removal" a taxonomy
decision rather than a regex.

**Costs.** A pick-count prediction is **volatile**: on the real test draft
it flips between RG, BR and none from pick to pick as ties come and go, so
the same black-red card was off-colour at P3P4 and on-colour at P3P6.
Speculative picks all but vanish early, because the pool rarely has an
unambiguous pair before P1P5. Both are consequences to watch in the ADR
0003 §3 backtest; a hysteresis rule (keep the last archetype until it is
clearly overtaken) is the obvious first remedy if they bite. Until
`_removal_` is authored across a set, the removal deficit is always at its
maximum.

**Glossary.** *Predicted Archetype* should be added to `CONTEXT.md`.
