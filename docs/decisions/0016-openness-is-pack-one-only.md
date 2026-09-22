# ADR 0016 — Openness applies to pack 1 only

**Status:** Proposed · **Date:** 2026-09-22 · **Supersedes:** ADR 0014 §2 (the pack weight) **only**. ADR 0014 §1 (the ALSA rate curve), §3 (the one-sided clamp and the replacement gate), §4 (no cap) and §5 (the signature) all stand. · **Relates to:** ADR 0003 §1.1 (the commitment ramp)

---

## Context

ADR 0014 §2 weighted openness by how much draft was left to guide:
`(packs − pack_no) / (packs − 1)`, giving 1.0, 0.5 and 0.0 across the three
packs. The derivation was "packs remaining after this one, over two", with
the passing order (left, right, left — so pack 1 reads the neighbours who
also feed pack 3) recorded as corroboration.

That derivation has since stopped holding. `ramp_span` moved from 18 to 10,
so **λ now pins at pick 14, the last pick of pack 1**. From pack 2 onward
the pool fully constrains what is playable, and a signal about which colors
are flowing cannot help a drafter who is already committed. Openness exists
to steer speculation; by pack 2 there is none left to steer.

## Decision

```
pack_weight(pack_no) = 1.0 if pack_no == 1 else 0.0
```

Openness is paid in pack 1 and nowhere else. `packs_per_draft` is deleted:
it existed solely to parameterize the old formula, and a tunable with no
reader is worse than none.

The term keeps everything else from ADR 0014 — the ALSA-derived rate, the
one-sided lateness clamp, the replacement gate, and the absence of a cap.

## Consequences

**Good.** The term is now tied to the same boundary the commitment ramp
uses, so "the pool has decided" and "openness stops paying" are one fact
rather than two that happen to sit near each other. It also removes the
half-weight case, which was the hardest part of the rule to explain and the
least motivated once the ramp moved.

**Observed.** Over the three reference drafts, openness fires on **18
card-instances rather than 44**, paying **4.1pp rather than 7.5pp** in
total. More than half its firings were in pack 2. **No verdict changed on
any of the three drafts**, so those firings were real but individually too
small to matter — consistent with ADR 0014's finding that the largest
openness anywhere in these drafts is 0.78pp.

**Costs.** Openness now affects at most 14 of a draft's 42 picks, which
narrows an already scarce term: half the set can never earn it (ALSA ≥ 6 or
below replacement), and nothing is late at pick 1. Whether enough signal
survives to be worth the term at all is a fair question, and one the
reference drafts cannot answer for the same reason they cannot calibrate
`tax_value` — these drafters barely speculated.

**Revisit when:** the ramp moves again, since the two are now coupled by
argument rather than by coincidence; or if the backtest shows pack 2 reads
carry predictive weight after all.
