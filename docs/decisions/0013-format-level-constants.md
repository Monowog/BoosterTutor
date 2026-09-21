# ADR 0013 — Format-level constants get their own table

**Status:** Proposed · **Date:** 2026-09-21 · **Relates to:** ADR 0012 (`tax_value`), ADR 0010 (the measured deck-shape targets), ADR 0003 §1.3–§1.4 · **Affects:** BoosterTutor Phase 2 schema

---

## Context

ADR 0012 makes `tax_value` format-level: some formats punish three-color
soup hard and some barely at all, so one global number cannot serve. But
`tax_value` is not the first such constant, only the first whose
format-dependence was noticed at the time it was introduced.

Today these are scattered. `FORMAT_AVG_WR = 56.3` is a module constant in
`draft_link.py`. `PICKS_PER_PACK = 14` lives in the 17Lands ingest, with a
comment noting that BoosterTutor's own `CLAUDE.md` is wrong to say 45 picks.
`target_curve`, `target_creatures` and `target_removal` sit in
`FitnessConfig` alongside a dozen genuinely global weights, distinguishable
only by a comment saying which were measured.

DraftDouble's `config.py` states the prototype is "single-set by design" and
"does not generalize across sets", which is still a useful simplification —
it holds exactly one format's data, so a table there would have one row and
prove nothing.

## Decision

### 1. The table lives in BoosterTutor, not DraftDouble

A new `format_constants` table, created by an Alembic migration as part of
Phase 2's schema work. DraftDouble keeps plain constants and gains
`tax_value: float = 12.0` as an ordinary `FitnessConfig` field; its values
are gathered into one labelled block so the eventual port is mechanical.

### 2. Keyed by `(set_code, event_type)`

Premier and Traditional Draft are different formats with different match
structures and plausibly different soupiness. `card_archetype_stats` and
`archetype_stats` are already keyed this way, so anything else makes the
join awkward and invites a silent mismatch where format constants come from
one event type and card statistics from another.

### 3. Columns

```
set_code            text     not null
event_type          text     not null
format_avg_wr       numeric  not null   -- 56.3 for HOB/PremierDraft
tax_value           numeric  not null   -- ADR 0012; 12.0 for HOB
replacement_offset  numeric  not null   -- now read only by `openness`
picks_per_pack      int      not null   -- 14 for HOB, NOT 15
target_creatures    int      not null
target_removal      int      not null
target_curve_1 .. target_curve_6  int not null
source              text     not null   -- provenance, free text
updated_at          timestamptz not null
primary key (set_code, event_type)
```

`target_curve` is **six integer columns, not JSON and not a child table**.
The six buckets are structure, not data: `mv_bucket()` clamps to 1..6 and
`derive_target_curve.py` hardcodes `BUCKETS = (1,2,3,4,5,6)`, so a
variable-length representation would express a flexibility the code does not
have. If buckets ever become variable, JSONB is the migration.

### 4. Nothing writes to this table automatically

Scripts print; a human transcribes. This is already how it works —
`derive_target_curve.py` writes nothing, its findings go to
`docs/target-curve.md` and then by hand into `FitnessConfig` — and it is the
only arrangement with no clobber surface. The values change roughly once per
set; automating a three-times-a-year edit buys nothing and risks exactly the
failure mode `docs/data-sources.md` has already been bitten by.

`source` records how the row's values were arrived at. **It is one free-text
column for a row whose values have mixed provenance**, which is a known
compromise rather than a clean design: the curve targets are script-derived,
`format_avg_wr` is measured, `picks_per_pack` is structural and `tax_value`
is a judgment call. A row's `source` should say all of that explicitly, e.g.
`"curve/creatures/removal: derive_target_curve.py 2026-09-19; format_avg_wr:
measured, docs/data-sources.md; tax_value: hand-picked 2026-09-21"`. If this
becomes unwieldy, per-column provenance is the upgrade.

### 5. The split

**Format-level (this table):** `format_avg_wr`, `tax_value`,
`replacement_offset`, `picks_per_pack`, `target_curve_1..6`,
`target_creatures`, `target_removal`.

**Global (stays in `FitnessConfig`):** `curve_weight`, `removal_weight`,
`creature_weight`, `openness_weight`, `openness_cap`, `synergy_weight`,
`synergy_cap`, `synergy_firing_floor`, `ramp_start`, `ramp_span`,
`min_games`, `solid_gap`, `mistake_gap`.

Two of those global placements are judgment calls, recorded here so they are
known rather than assumed:

- **`ramp_start` / `ramp_span` are in picks**, and 18 picks is 43% of a
  42-pick draft but 40% of a 45-pick one — so they are weakly
  format-dependent. Kept absolute and global for now, because converting
  them to fractions is a behavior change disguised as a refactor.
- **`solid_gap` / `mistake_gap` are in pp** and compare against card-quality
  spreads that genuinely differ by format; a format with compressed card
  quality wants tighter gaps. Kept global until there is a second format to
  compare against.

### 6. Soupiness is not measured

`tax_value` was considered as a derived quantity: `_sorted_pair()` in the
17Lands ingest already reads `main_colors` on every game row and discards
everything that is not exactly two colors, so counting games and wins by
**number of colors** — and with it the win-rate deficit of 3+ color decks —
would cost a few lines inside a loop that already runs and nothing extra
from 17Lands.

**This was declined.** `tax_value` is hand-picked per format, informed by
looking at the data rather than by a stored measurement. This is a knowing
departure from the project's usual "derive targets from the cache before
coding a term" habit, and it means `tax_value` is **the only column in this
table with no measurable basis** — every other value is measured or
structural. Its only validation is how the three reference drafts score,
which lives in DraftDouble, not here. The `source` column should say so
plainly.

## Consequences

**Good.** "What varies by format" stops being tribal knowledge spread across
three modules and a comment. Adding a set becomes a row rather than a code
change. The `(set_code, event_type)` key makes the eventual Traditional
Draft support a data question instead of a migration.

**Costs.** The table lands with **no reader**: the fitness function has not
been ported to BoosterTutor, whose Phase 2 scope is schema and ingest. So
this ships as migration plus model plus a hand-written HOB row, and cannot
be validated end to end until the port. `FitnessConfig` also stops being
purely static once the port happens — some fields will come from the
database. `parsing/` and `analysis/` stay pure, since the values are passed
in as `Stats` already is, but the dataclass's "every tunable in one place"
comment stops being true and should be reworded at that point.

**Also.** `CLAUDE.md`'s description of Draft Review as "a short critique of
each of the 45 picks" is wrong for HOB and should be corrected to reference
`picks_per_pack` rather than a hardcoded number.

**Revisit when:** a second format is ingested, at which point check whether
`solid_gap` / `mistake_gap` and the ramp really are format-independent; or
if `tax_value` by feel starts going in circles, at which point §6's declined
measurement is the first thing to build.
