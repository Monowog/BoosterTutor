# Research: "The Hobbit" set code + 17Lands data availability

**Ticket:** [Monowog/BoosterTutor#14](https://github.com/Monowog/BoosterTutor/issues/14)
**Date checked:** 2026-09-14
**Context:** `docs/decisions/0003-pick-grading.md` (fitness function + backtest), `docs/development_plan.md` §2.3 (17Lands access etiquette)

---

## 1. Scryfall set code

Queried live against `https://api.scryfall.com/sets` and `https://api.scryfall.com/sets/<code>`.

The set the repo owner calls "The Hobbit" is a single expansion:

| Code | Name | `set_type` | Released | Card count | Notes |
|---|---|---|---|---|---|
| **`hob`** | **The Hobbit** | `expansion` | 2026-08-14 | 321 (193 unique via card search) | **The draftable set. `arena_code`/`mtgo_code` also `hob`.** |
| `hoc` | The Hobbit Eternal | `eternal` | 2026-08-14 | 158 | `parent_set_code: hob`, but a separate eternal/singleton-format companion product, not a draft-booster bonus sheet. |
| `thob` | The Hobbit Tokens | `token` | 2026-08-14 | 15 | Token set, not a card pool. |

**Answer: one Scryfall code, `hob`.** This confirms the owner's claim of no bonus sheet — `hoc` exists but is a distinct parent-linked *eternal-format* product (comparable to a standalone Commander-style release), not a sheet mixed into `hob` draft boosters the way e.g. a "Special Guests" sheet would be. Sources:
- `https://api.scryfall.com/sets/hob` (checked 2026-09-14)
- `https://api.scryfall.com/sets/hoc` (checked 2026-09-14)
- `https://api.scryfall.com/cards/search?q=e%3Ahob` → `total_cards: 193`

Sanity check on "most recent set": Scryfall's `/sets` list (sorted by `released_at`) shows one entry technically newer by date — `slz` "The Zeta Set", released 2026-09-02, `set_type: box`. That's a non-draftable box product (`nonfoil_only: true`, not present at all in 17Lands' expansion list — see §2). So `hob` is correctly the most recent *draftable* set, matching the owner's framing.

## 2. 17Lands data availability

Checked `17lands.com`'s public aggregate JSON endpoints directly (no browser network-tab needed — they responded to plain `curl` with the URL shape from `docs/development_plan.md` §2.3):

- `https://www.17lands.com/data/expansions` → returns a JSON array of expansion codes with **`"HOB"` first** (list appears newest-first), confirming 17Lands has HOB on-boarded as a tracked expansion. Checked 2026-09-14.
- `https://www.17lands.com/card_ratings/data?expansion=HOB&format=PremierDraft` → **HTTP 200**, 188 card rows returned, each with `seen_count`/`avg_seen` (ALSA), `pick_count`/`avg_pick` (ATA), `game_count`, `win_rate` (GP WR), `opening_hand_win_rate`, `drawn_win_rate`, `ever_drawn_win_rate` (**GIH WR**), `never_drawn_win_rate` (GND WR), `drawn_improvement_win_rate` (IWD). Field names match the vocabulary in ADR 0003 / development plan §2.3.
- `https://www.17lands.com/card_ratings/data?expansion=HOB&format=TradDraft` → **HTTP 200**, also 188 rows, same schema.
- `https://www.17lands.com/card_ratings/data?expansion=HOB&format=QuickDraft` → **HTTP 200** (data exists, though QuickDraft is a bot format the app doesn't need).
- `https://www.17lands.com/color_ratings/data?expansion=HOB&event_type=PremierDraft&start_date=2026-08-14&end_date=2026-09-14` → **HTTP 200**, full archetype/color-pair win-rate table (mono-color, two-color pairs, splashes). Note: this endpoint requires `event_type` (not `format`) plus `start_date`/`end_date` — calling it with only `expansion`+`format` returns a 400 `"event_type": "Field required"` validation error. This is the one concrete deviation from the URL shape guessed in §2.3 worth recording for whoever wires up ingestion.

**Answer: yes, 17Lands publishes data for HOB in both Traditional Draft and Premier Draft**, at both the card-rating and color/archetype-rating granularity. QuickDraft also has data but isn't relevant per the dev plan's scope.

## 3. Sample size / freshness — thin, as expected for a 1-month-old set

HOB released 2026-08-14; today is 2026-09-14 — the set is exactly one month old. Data is present but visibly thin, especially for the win-rate fields the fitness function needs most:

**Premier Draft** (`/card_ratings/data?expansion=HOB&format=PremierDraft`, 188 cards):
- `game_count` per card: min 0, median **366**, max 2,673.
- Only **32 of 188 cards (17%)** have a non-null `ever_drawn_win_rate` (GIH WR) — 17Lands itself withholds the stat below its own minimum-sample threshold for the rest.
- Only 77/188 have a non-null `win_rate` (GP WR).

**Traditional Draft** (same endpoint, `format=TradDraft`, 188 cards):
- `game_count` per card: min 0, median **77**, max 759 — roughly 5× thinner than Premier.
- **0 of 188 cards have a non-null `ever_drawn_win_rate`.** 17Lands has not published GIH WR for *any* card in Traditional Draft for this set yet.

**Color/archetype ratings** look much healthier in aggregate — the Premier Draft two-color-pair table alone sums to hundreds of thousands of games (e.g. one query returned 282,358 "two-color" games combined) — because archetype rates aggregate across all cards and all drafts, whereas a single card's GIH WR needs that specific card drawn in a game.

**Path B (public bulk CSVs)** — also live, confirming Path A and giving a size signal:
- `https://17lands-public.s3.amazonaws.com/analysis_data/draft_data/draft_data_public.HOB.PremierDraft.csv.gz` → HTTP 200, **56.6 MB**, `Last-Modified: 2026-09-03`.
- `https://17lands-public.s3.amazonaws.com/analysis_data/draft_data/draft_data_public.HOB.TradDraft.csv.gz` → HTTP 200, **5.6 MB**, `Last-Modified: 2026-09-03`.
- The ~10× size gap between formats matches the card-level `game_count` gap above — Traditional Draft has meaningfully less data than Premier Draft for this set.

**Implication for ADR 0003 §2.2's bands:** with card-level `game_count` medians in the hundreds (Premier) or tens (Traditional), and most `min_games` (start: 1,000) thresholds unmet, expect most HOB picks today to land in `insufficient_data` or the widened `optimal`/`defensible` bands per the σ-scaling table — this is "correct behaviour, not a bug" per the ADR, but worth knowing before building/demoing against this set specifically. Traditional Draft in particular currently has **no usable GIH WR at all** at the card level; anything built against HOB TradDraft archetype-scoped stats right now would be working from color-pair aggregates only, not card-level signal.

## 4. Aggregate-endpoint URL/parameters (confirmed by direct request, not network-tab inspection)

No browser was available for a literal Network-tab capture, so these were confirmed by requesting the URL shapes described in `docs/development_plan.md` §2.3 directly and reading the response codes/bodies — the same information the Network tab would show, just obtained without a browser session.

- **Card ratings:**
  `GET https://www.17lands.com/card_ratings/data?expansion=HOB&format=<PremierDraft|TradDraft|QuickDraft>`
  Returns a JSON array of per-card objects (schema in §2 above). No auth/cookie required for a plain GET.

- **Color ratings:**
  `GET https://www.17lands.com/color_ratings/data?expansion=HOB&event_type=<PremierDraft|TradDraft>&start_date=<YYYY-MM-DD>&end_date=<YYYY-MM-DD>&combine_splash=<true|false>`
  `expansion` + `event_type` are required (`format` alone is rejected with a 400); `start_date`/`end_date` bound the window — using the set's release date through today returned data cleanly. Not fully verified: whether omitting `start_date`/`end_date` defaults to all-time (a second test call without `format` but with the other params still returned 200, but that wasn't a controlled A/B, so don't treat the exact default behavior as confirmed — re-check via a real Network tab before depending on it in ingestion code).

- **Expansion list (useful for ingest validation):**
  `GET https://www.17lands.com/data/expansions` → flat JSON array of expansion codes, `HOB` first.

Not confirmed: rate limits, required headers beyond `User-Agent`, and whether these endpoints are stable long-term — per dev plan §2.3, treat this as the current observed shape only, re-verify before shipping ingestion code against it, and keep Path B (public S3 CSVs, confirmed live above) as the authoritative fallback.

## Summary

1. **Scryfall code:** `hob` only (single code, no bonus sheet — `hoc`/`thob` are separate non-bonus-sheet companion products).
2. **17Lands availability:** yes, for both Premier Draft and Traditional Draft, at card-rating and color-rating granularity; public S3 CSVs also live for both formats.
3. **Freshness:** thin. Premier Draft: median ~366 games/card, GIH WR published for only 17% of cards. Traditional Draft: median ~77 games/card, **GIH WR published for 0% of cards**. Expect most picks to fall in `insufficient_data`/`optimal`/`defensible` bands per ADR 0003 §2.2.
4. **Endpoint shape:** `card_ratings/data?expansion=HOB&format=<Format>` and `color_ratings/data?expansion=HOB&event_type=<Format>&start_date=&end_date=` both confirmed live; exact default-window behavior of the latter not fully pinned down and should be re-verified via a real Network-tab capture before ingestion code depends on it.
