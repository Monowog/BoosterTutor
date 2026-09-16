# ADR 0004 — Self-payoff tags: pricing extra copies of one card

**Status:** Proposed · **Date:** 2026-09-15 · **Relates to:** ADR 0003 §1.2 (synergy), the tag vocabulary in `CONTEXT.md`

---

## Context

The tag system prices synergy between *two different properties*: an enabler
supplies something, a payoff rewards it, and the importance coefficient on the
tag pair says how much. Every coefficient lives on an `(enabler, payoff)` row,
and the adjacency matrix in the tagging UI is that table drawn out.

A small class of cards does not fit that shape. Seven Dwarves (Throne of
Eldraine) gets better with every *other copy of Seven Dwarves* in the deck. The
thing being enabled and the thing being rewarded are the same card, so there is
no second property to pair it with. Modelled with the existing kinds, it would
need a fake partner tag carried on one card, which says nothing true.

The draft consequence is real and is the reason to model it at all: a card like
this should be taken *more* eagerly once you already have one, and the fitness
function has no way to express that without being told.

## Decision

Add a fourth tag kind, **`self_payoff`**: a tag that synergises only with
itself, for a card that rewards having more copies of that same card. It is
normally a vocabulary of one card and is named after that card
(`seven_dwarves`).

**Its coefficient lives on the diagonal of `tag_pairs`** — the row
`(seven_dwarves, seven_dwarves, 4.0)` — rather than in a new column on `tags`.

The diagonal was previously unused and blocked in the UI, so the rule becomes
symmetric and total:

- The diagonal is reserved for `self_payoff` tags.
- Every other kind is barred from the diagonal: a normal tag being its own
  synergy says nothing.
- A `self_payoff` tag is barred from every cell *except* its diagonal: it is
  about one card and nothing else.

This is enforced in the store (the seam), not only in the UI, and a kind change
clears any edge it strands — an edge that still prices a synergy but that
nothing can display or remove is worse than a deleted one.

## Consequences

**Why the diagonal and not a column on `tags`.** `schema.sql` states that
`tag_pairs` *is* the directed weighted graph and the grid is its adjacency
matrix. A `tags.self_coefficient` column would make that false: weights would
live in two tables, and everything reading them would have to know to look in
both. The diagonal keeps one place where a coefficient can be.

**The counting problem — the load-bearing caveat.** `card_tags` is keyed by
`oracle_id`. Four copies of Seven Dwarves in a pool are four picks but *one*
tagged card, so a self-payoff is one row no matter how many copies are held.
Anything consuming this must count **copies in the pool**, not tagged cards.
Ordinary tags do not have this problem, because their enabler count is a count
of distinct cards and that is what is wanted. This is the one place the tag
model depends on how the pool is represented, and it is not yet implemented —
DraftDouble has no fitness function at the time of writing.

**It stays hand-authored.** Nothing detects self-payoff cards. Like the rest of
the taxonomy, the kind and the coefficient are set by a person. There are
typically one or two such cards in a set, and missing one costs a small amount
of accuracy on a rare card, not a wrong verdict everywhere.

**Threshold synergy is unaffected.** A self-payoff rewards *each* additional
copy, which is the opposite of a threshold synergy's fixed count. The two are
independent and a tag could in principle be both; nothing models that yet, and
nothing needs to.

## Alternatives rejected

**Derive it from oracle text.** Regex for "other creatures you control named"
would find Seven Dwarves. Rejected for the same reason the rest of the taxonomy
is hand-authored: the vocabulary is deliberately a human judgement, and
pre-seeding it has been rejected as a direction.

**Reuse `both` with a self-referential edge.** Works mechanically — a `both`
tag can already be its own enabler and payoff if the diagonal is unblocked —
but loses the signal that this tag is *only* self-referential, which is what
tells the UI not to offer it as anyone else's edge and tells a reader what the
tag is for.
