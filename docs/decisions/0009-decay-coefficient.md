# ADR 0009 — The decay coefficient: pricing the second enabler

**Status:** Proposed · **Date:** 2026-09-19 · **Supersedes:** ADR 0006 §4 (the per-edge `cap`) and its `cap` column · **Relates to:** ADR 0006 (the synergy term), ADR 0004 (self-payoff)

---

## Context

ADR 0006 §4 gave each tag pair an optional `cap`, saturating the effective
count as `cap · n / (n + cap)`. It was meant to stop a fourth sacrifice
outlet being worth as much as the first. In practice it had three problems:

1. **It taxed the first copy.** At `cap = 2` a single complementary card was
   worth 0.67 of the edge's coefficient. The first enabler for a payoff is
   the one that matters most, and pricing it below the authored weight makes
   the weight itself hard to reason about.
2. **It could not say "no decay".** Linear behaviour required `cap` to be
   `NULL`, so the column mixed a number with a mode.
3. **Nobody ever set one.** It was never surfaced in the tagger, and every
   authored HOB edge left it `NULL`, so the mechanism was dead code.

## Decision

Replace `cap` with **`decay`**, a per-edge coefficient in `[0, 1]` that says
how much of the previous copy's value each further copy of the complementary
tag is worth. The effective count is the geometric series:

```
n_eff = 1 + d + d² + … + d^(n-1) = (1 − d^n) / (1 − d)
```

so the synergy an edge contributes is `coefficient × n_eff`, and the first
complementary card always pays the coefficient in full.

| copies | d = 0 | d = 0.5 | d = 0.8 | d = 1 |
|---|---|---|---|---|
| 1 | 1.00 | 1.00 | 1.00 | 1 |
| 2 | 1.00 | 1.50 | 1.80 | 2 |
| 3 | 1.00 | 1.75 | 2.44 | 3 |
| 4 | 1.00 | 1.88 | 2.95 | 4 |
| limit | 1.00 | 2.00 | 5.00 | unbounded |

The three ends of the range are all meaningful, which is what makes one
number enough: **1 is no decay at all**, every copy worth the same, the
behaviour an uncapped ADR 0006 edge had; **0 means only the first copy ever
counts**, for a payoff that needs one enabler and no more; and anything
between converges on `coefficient / (1 − d)`.

**The default is 0.5**, on both new edges and every edge migrated from
before this ADR. Diminishing returns are the common case, so they are what
you get without thinking about it; linear is the opt-in.

### Schema and migration

`decay REAL NOT NULL DEFAULT 0.5 CHECK (decay BETWEEN 0 AND 1)`, and the
`cap` column is dropped. SQLite refuses to `ALTER TABLE ADD COLUMN` anything
that is both `NOT NULL` and `CHECK`ed, so an older database is migrated by
rebuilding `tag_pairs`: rename it aside, let `schema.sql` recreate it, copy
the rows back. That keeps the canonical DDL in one file and leaves migrated
and fresh databases with identical shapes, which matters because
`tag_pairs` is hand-authored and its only other copy is the JSON mirror.

The taxonomy export **always writes `decay`**, unlike `cap`, which was
omitted when unset. It is a real column with a real default, and a reader
pricing an edge from the file should not have to know what that default is.
The importer tolerates a file written before this ADR: a pair with no
`decay` takes 0.5 rather than failing the restore.

### Authoring

The coefficient grid carries two numbers in every filled cell, the
coefficient above and the decay below. The decay input is disabled until the
pair has a coefficient, because an unpriced edge has nothing to decay.

The two fields are written separately, and **`setDecay` never creates or
deletes an edge**, because 0 means opposite things for each: a coefficient
of 0 deletes the edge, since a blank cell and "no synergy" are the same
statement, while a decay of 0 is a real setting. The bound is enforced three
times over: the schema `CHECK`, the store, and the endpoint.

## Consequences

**Good.** Runaway synergy is bounded by construction. On the real test draft
`storied ← historic` fires with six enablers in the pool: linear would pay
0.60pp and keep climbing, while the default decay holds it at 0.20pp,
converging on twice the 0.1 coefficient. The first enabler is priced at
exactly what was authored, so the coefficient means what it says. One number
covers the whole range from "every copy counts" to "only the first does".

**Costs.** A third number per edge to tune, on top of the coefficient and
the tag assignments themselves, and it is a per-edge judgement no backtest
currently sets. Every existing edge changes behaviour, from linear to
converging on twice its coefficient. And `d = 1` is deliberately unbounded,
so a mis-set edge can still run away; `synergy_cap` (ADR 0006 §5, 5pp)
remains the global backstop for that.

**Observed since (2026-09-22).** The worked example above describes the
0.5 default, which is still what a new edge gets. It is no longer what that
edge carries: `historic → storied` was hand-tuned to **0.9**, and nine of
HOB's sixteen edges have moved off the default, eight of them upward.

So the example now reads differently. At coefficient 0.1:

| enablers in pool | d = 0.5 | d = 0.9 |
|---|---|---|
| 1 | 0.100pp | 0.100pp |
| 2 | 0.150pp | 0.190pp |
| 3 | 0.175pp | 0.271pp |
| 6 | 0.197pp | **0.469pp** |
| 15 | 0.200pp | **0.794pp** |
| limit | 0.20pp | **1.00pp** |

The six-enabler case the ADR quotes at 0.20pp is 0.469pp today, and the edge
converges on ten times its coefficient rather than twice. A real firing
observed on the WR reference draft — Óin the Brave, `storied ← historic`
with fifteen enablers in the pool — pays 0.794pp.

This does not change the decision: one number still spans "every copy
counts" to "only the first does", and the default is still 0.5. But it does
weaken the ADR's "runaway synergy is bounded by construction" claim in
practice. The bound at d = 0.9 is ten coefficients, and `synergy_cap`
(ADR 0006 §5, 5pp) is doing more of the work than this ADR assumed. Worth
watching as more edges are tuned upward.

**Revisit when:** the backtest can fit per-edge decays from data, or if a
set needs a payoff that is genuinely inert below some count, which this
design still does not express (ADR 0006's rejected hard knee).

**Glossary:** **Decay Coefficient** is added to `CONTEXT.md`, replacing
**Threshold Synergy**, whose retirement ADR 0006 called for and which this
mechanism supersedes outright.
