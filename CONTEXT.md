# BoosterTutor

An LLM-based Magic: the Gathering Limited coach. Python computes every fact and
every verdict; Claude only explains them in prose.

## Language

### Draft structure

**Pool**:
Everything a drafter has already taken at a given point in a draft.
_Avoid_: deck, collection

**Pack**:
The cards available to choose from for a single pick.
_Avoid_: booster

**Pick**:
One decision: a pack, the pool before it, and the card taken.

**Archetype**:
A two-colour pair a deck can be built toward, named in sorted WUBRG form (`BR`,
`WU`). The ten pairs are the hypotheses the fitness function scores against.
_Avoid_: colour pair, deck type, lane

### Grading

**Fitness**:
A card's value to a specific pool at a specific point in a draft, measured in
percentage points of win rate.
_Avoid_: score, rating, grade

**Verdict**:
The band a pick falls into once its fitness gap is compared against the noise in
the underlying data.
_Avoid_: grade, judgement

### Tags

Tags are authored per set, not shared between sets. Name a tag after the set's
own mechanic where one exists (`storied`, `ferocious`), and generically where
none does (`go_wide`, `graveyard_payoff`).

Tags are assigned directly and exhaustively, with no hierarchy between them: a
card that makes Treasure is tagged `artifact` outright, rather than tagged
`treasure` and inferred to be an artifact. The tags on a card are the whole
truth about it.

**Tag**:
A named property attached to a card by hand, describing what it supplies to a
deck or what it rewards.
_Avoid_: label, trait, keyword

**Enabler**:
A card that supplies a resource or condition that other cards reward.
_Avoid_: provides, provider, source

**Payoff**:
A card that rewards a resource or condition being present in the deck.
_Avoid_: wants, wanter, needs

**Self-Payoff**:
A tag that synergises only with itself, for a card that rewards having more
copies of that same card in the deck. Normally a vocabulary of one card and
named after it (`seven_dwarves`). Its coefficient sits on the diagonal of the
tag pair grid — the pairing of the tag with itself — and prices what each
further copy is worth to the copies already there. See ADR 0004.
_Avoid_: self-synergy, stacking tag, multiples tag

**Tag Pair**:
One enabler tag coupled to one payoff tag, carrying the importance coefficient
that prices that synergy. A card may carry many tags of both kinds. A
self-payoff is the one case where the two halves are the same tag.
_Avoid_: synergy pair, combo

**Importance Coefficient**:
The weight given to a single tag pair, expressing how much an enabler is
actually worth to its payoff in this set.
_Avoid_: weight, multiplier, synergy score

**Threshold Synergy**:
A tag pair whose payoff needs a fixed count of enablers and gains nothing
beyond it, as opposed to one that rewards each additional enabler. Independent
of [Self-Payoff](#tags), which rewards every additional copy by definition.
_Avoid_: capped synergy, binary synergy
