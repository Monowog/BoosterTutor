# ADR 0010 — Deck-shape terms: what counts, and what the targets are

**Status:** Proposed · **Date:** 2026-09-19 · **Supersedes:** ADR 0003 §1.3 (what the curve term counts) and §1.4 (the role term's single weight and its placeholder targets) · **Relates to:** ADR 0007 §2 (role counts on-color copies and reads the `_removal_` tag)

---

## Context

`curve` and `role` are the two terms that score a card for the shape of the
deck rather than its own quality. Three things about them were still
inherited guesses after the function shipped:

1. **The curve counted lands.** `mv_bucket` clamps a mana value of 0 up to 1,
   because `target_curve` starts at one drop. Every land in the pool
   therefore counted as a one-drop, and a land being scored was paid for
   filling a one-drop slot. This also silently contradicted how
   `target_curve` was measured, which counted non-land cards only.
2. **`target_removal` had never been measured.** `target_creatures` came out
   of the winning-deck data, but removal had no marker in the 17Lands
   dataset, so 4 was conventional Limited wisdom standing in.
3. **One weight served both branches.** A missing removal spell and a
   missing creature were each worth `role_weight`, 0.75pp, which does not
   match how Limited actually plays.

## Decision

### 1. A land is not a spell

Lands are excluded from the curve term **on both sides**: a land neither
fills a curve slot nor has a curve of its own. They carry a derived `land`
tag, assigned from the type line by the caller in the same way `creature`
is, so the pure analysis module never inspects a type line.

This aligns the count with the target's own definition. It does not change
`role` or `synergy`, where a nonbasic land is a real card and can carry
authored tags.

### 2. Both role targets are measured

From the same winning-deck pass that produced `target_curve`:

| | All decks | ≥ 6 wins | 7 wins | Strong users |
|---|---|---|---|---|
| Creatures | 14.37 | 14.30 | 14.32 | 14.33 |
| Removal | 4.22 | 4.24 | 4.23 | 4.20 |

So `target_creatures = 14` and `target_removal = 4`. The removal figure
lands exactly where the placeholder had been guessed, so the value does not
move — but it is now measured rather than asserted, and it will move as the
taxonomy grows.

**Removal is the `_removal_` tag and nothing else**, so this number is only
as complete as the taxonomy: 14 of HOB's 193 cards carried it when measured,
and a fully tagged set would measure higher. That is less dangerous than it
sounds, because the role term counts the same tag on both sides. An untagged
removal spell is missing from the target *and* from the pool count, so
partial tagging shrinks both together rather than skewing the deficit.
Re-derive as the set gets tagged.

### 3. One weight per branch

`role_weight` splits into **`removal_weight` 1.25pp** and
**`creature_weight` 0.40pp**. Removal is the scarcer and more decisive
resource in Limited, so a missing removal spell is worth roughly three times
a missing body. The saturating deficits are unchanged: two removal spells
short, or three creatures short, already pays that branch in full.

Putting removal above 1pp is a **knowing departure** from ADR 0003 §1.4,
which sized `role_weight` so the term could not outrank a two-point
card-quality difference. ADR 0005 already recorded that this cap would
likely have to lift; this is that lift.

## Consequences

**Good.** The curve term now measures what its targets were derived from.
Both role targets are evidence rather than folklore, and reproducible from
one script. The two branches can be tuned independently, which they could
not be while sharing a weight.

**Costs.** Three tunables where there were two, all still awaiting the ADR
0003 §3 backtest. `target_removal` is now coupled to taxonomy completeness
and needs re-deriving as tagging proceeds, which is a maintenance obligation
the creature target does not carry.

**Observed.** The role change is muted on a well-drafted pool, for an
instructive reason: on the test draft the term fired 98 times but only 8 of
those were on removal cards, and the largest role bonus any removal card
received was 0.38pp against a 1.25pp ceiling. The drafter took removal
early, so the deficit closed before λ grew. The term is shaped to shout when
you are short *late*, which is correct, but it means the weight change will
show its effect mainly on drafts that neglect removal into pack three.

**Revisit when:** the backtest can fit the two weights, or when `_removal_`
covers the set and the measured target moves off 4.
