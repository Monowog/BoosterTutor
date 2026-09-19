# ADR 0008 — Classification: pure gap bands, and what earns a note

**Status:** Proposed · **Date:** 2026-09-19 · **Supersedes:** ADR 0005 §1 (fitness classes), §2 (the verdict and its `unimportant` conditions), §3's `speculative` flag and §4 (relevant picks); ADR 0007 §3–4 (the `solid` floor and the indifferent vetoes) · **Relates to:** the *Classification Overhaul* design note

---

## Context

The class and verdict rules had been patched three times (ADR 0005, then
BIG_FIX_#1 and #2 via ADR 0007) while the fitness function was still being
built. With fitness now roughly accurate, grading two real 42-pick drafts
showed the rules were measuring the wrong things:

- **Taking the best card in the pack often read `reasonable`.** Ten picks on
  one draft and six on the other had a gap under 0.5pp, several exactly
  0.00, and still missed `solid`, because the σ-aware noise floor
  `max(0.5pp, 1σ)` demanded a gap smaller than the data's own error bars.
- **`questionable` mixed blunders with near-misses.** One draft's four
  questionable gaps were 16.06, 3.84, 3.44 and 3.08pp. All four got the same
  label and the same written note.
- **One label carried two questions.** The pack-relative gap asked "what did
  this pick cost", and ADR 0007's format-average floor asked "is this card
  any good". Mixing them is what produced the first symptom.
- **Half of every draft is a coin flip.** The median gap to the best card is
  0.16pp and 0.09pp on the two drafts. Grading those is grading noise.

## Decision

**A class answers one question: how conducive was this pick to drafting a
winning deck?** The highest-fitness card in the pack is the gold standard,
and every other card is classed by how far short of it it falls.

### 1. Three bands, fixed thresholds

| Class | Gap to the pack's best scored card |
|---|---|
| `solid` | ≤ `solid_gap`, 2.0pp |
| `questionable` | ≤ `mistake_gap`, 4.0pp |
| `mistake` | beyond |

Nothing else enters. **Retired:** the σ-aware noise floor, the `max(0.5pp,
1σ)` band, ADR 0007's format-average floor for `solid`, and every
thin-data adjustment. A card with 200 games is banded exactly like one with
20,000, and the best card in a weak pack is `solid`, because taking it is
the most conducive thing on offer.

Two tunables replace four. Both are placeholders for the ADR 0003 §3
backtest, but 2.0pp is where dropped equity starts to cost a winning list,
and 4.0pp is where a pick is worth interrupting the drafter about.

**Basic lands** keep their ADR 0007 treatment and are always `mistake`:
never scored, never the pack's best, ignored by the spread test below.

### 2. The verdict, and `indifferent`

The verdict is the fitness class of the card taken, with one exception.

A pick is **`indifferent`** when the pack held one card, held nothing
scorable, or **every card in it was `solid`** — the spread from best to
worst is within `solid_gap`, which is precisely "no available choice cost
the deck anything". Every veto ADR 0007 had added is dropped, so two equal
bombs at P1P1 are now `indifferent` rather than several solid picks,
reversing that decision.

**Taking a card that was never scored is a `mistake`, checked before the
indifferent test.** Otherwise a pack of one playable and a Swamp would read
`indifferent` on a spread of zero and taking the Swamp would come out free.

### 3. Only a `mistake` earns a note

Written notes and LLM calls go to `mistake` picks alone. Scarcity is the
point: a handful of notes per draft land harder than forty, it cuts the API
bill, and **a flawless draft with no notes at all is a valid outcome**. The
`speculative` flag, its chip, the `PickFlag` type and the
`speculative_until` tunable are removed: the flag was unreliable, and a
speculative pick is obvious from the fact that it does not match the pool.

### 4. Nothing that does not affect win rate is considered

No allowance is made for rare-drafting or any other motive the draft log
cannot see. Such a pick did cost equity and is graded as such; the written
note can acknowledge the possibility in prose, because the brief already
receives the card's rarity and its gap.

### 5. How this is validated

By eye, on known drafts, until the fitness function's own weights are
tuned. A labelled pick set and the ADR 0003 §3 backtest are deliberately
deferred: tuning classification against a moving fitness function would
fit the thresholds to today's noise.

## Consequences

**Good.** The two questions are separated, so "you took the best card" can
never read as an error. Bands are legible: the drafter can be told a pick
cost 3pp and see why it is called questionable. Two tunables instead of
four, and the vocabulary finally matches the meaning.

**Costs.** In a set's first week the tool will call picks mistakes on thin
evidence, where the σ-aware bands stayed quiet; `insufficient_data` remains
only as a UI annotation, so the interface must carry that warning. Notes
become rare, one and two on the two test drafts, which is intended but
leaves little for a reader on a well-drafted deck. And `solid` becomes much
more common, 25 and 31 picks against 13 and 20 before.

**Revisit when:** the fitness weights are tuned, at which point the
thresholds should be set against a labelled pick set rather than by eye.

**Glossary:** Fitness Class, Verdict, Indifferent and Relevant Pick are
updated in `CONTEXT.md`. Speculative is retired.
