# ADR 0007 — Predicted archetype, class floors and the removal tag

**Status:** Proposed · **Date:** 2026-09-18 · **Supersedes:** ADR 0003 §1.2 (the belief distribution), parts of ADR 0003 §1.4 (role counting) and ADR 0005 §1–2 (class and unimportant rules) · **Relates to:** ADR 0006 (synergy), the BIG_FIX_#1 design note

---

## Context

The fitness function shipped in DraftDouble (BoosterTutor #20) implemented
ADR 0003 literally. Reviewing its output on a real draft, Jackson found the
belief distribution hard to reason about — ten pairs, a softmax temperature,
a card-conditioned prior whose "exactly the unconditioned rate at λ = 0"
promise turned out to be false with real scoped data (#31) — and the
class rules too generous: a flat pack of filler produced `solid` picks, and
a pack with a clearly good card could still come out `unimportant`.

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
and whenever the pool has not chosen a lane. `tau` is removed from the
tunables. **Off-colour** has one definition everywhere: not playable in the
predicted archetype (never off-colour when there is none; colourless cards
never are). It drives the `speculative` flag, option value, and the
unimportant veto below.

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

### 4. `unimportant` is vetoed by anything worth having

A pick is never `unimportant` when the pack holds a `solid` card, or an
on-colour card at or above replacement fitness. The single-card last-pick
rule stands: one card is always `unimportant`, solid or not. The remaining
ADR 0005 §2 conditions apply only after those vetoes.

### 5. Admin mode

Every scored card carries its full decomposition (`CardView.breakdown`:
total, GIH WR, colour fit, curve, role, openness, synergy, option value,
top-2 synergy firings). The review shows it in a popup on right-click. In
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
