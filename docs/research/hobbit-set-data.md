# Research: "The Hobbit" set code + 17Lands data availability

**Ticket:** [Monowog/BoosterTutor#14](https://github.com/Monowog/BoosterTutor/issues/14)
**Date checked:** 2026-09-14 · **Corrected:** 2026-09-15 (§3 data-availability findings were wrong — see the note there)
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

## 3. Sample size / freshness — **CORRECTED 2026-09-15: not thin**

> **This section originally concluded that HOB was a data-thin set and that Traditional
> Draft had no card-level GIH WR at all. Both conclusions were wrong**, and the
> Premier Draft format decision rested on the second one. Corrected below; see
> [#14](https://github.com/Monowog/BoosterTutor/issues/14) and
> `docs/data-sources.md` in [Monowog/DraftDouble](https://github.com/Monowog/DraftDouble).

**Cause of the error.** The figures came from
`https://www.17lands.com/card_ratings/data?expansion=HOB&format=<...>`. That URL still
returns HTTP 200, but it is a **legacy shim**: it silently ignores its filter parameters
(requests with `colors=WU`, `colors=BR`, `colors=GW`, `deck_colors=`, `color_filter=` and
with date bounds all return *byte-identical* 122,132-byte payloads) and it reports only a
small slice of the data. The endpoint the site actually calls today is
`https://www.17lands.com/api/card_data?expansion=HOB&event_type=<Format>&time_period=ALL_TIME`
— note `/api/`, `event_type` rather than `format`, a required `time_period`, and a
`{copyright, notes, data}` envelope rather than a bare array.

**Corrected figures**, measured against the current endpoint on 2026-09-15:

| | legacy shim (original finding) | current endpoint |
|---|---|---|
| **Premier Draft** — total game count | 111,355 | **12,070,970** |
| **Premier Draft** — cards with GIH WR | 32–33 / 188 (17%) | **184 / 188 (98%)** |
| **Premier Draft** — median games/card | 366 | **39,705** |
| **Traditional Draft** — cards with GIH WR | **0 / 188** | **168 / 188 (89%)** |
| **Traditional Draft** — median games/card | 77 | **5,909** |

**HOB is a well-covered set.** Independently confirmed by computing the rates ourselves
from the public datasets: 184 of 193 cards clear a 500-game floor, averaging ~15,000 games
each, and the format average lands at 56.3% across 227,258 two-colour games — which matches
the "format average 56.0" that ADR 0003's worked example assumes.

**Consequences for the two conclusions that depended on this:**

- **ADR 0003's bands will operate normally.** The original "expect most HOB picks to land in
  `insufficient_data`" warning does not hold and should be disregarded.
- **Traditional Draft is viable.** It was ruled out here *because* it reportedly had 0%
  card-level GIH WR coverage. It has 89%. Premier Draft remains the chosen format — it still
  has roughly 6× the data and is already ingested and validated — but that is now a
  preference, not a forced move.

**Still true from the original measurement:** Premier Draft has meaningfully more data than
Traditional Draft, and the ~10× public-dump size gap (56.6 MB vs 5.6 MB, both
`Last-Modified: 2026-09-03`) reflects a real difference in volume. Only the absolute
magnitudes and the "no TradDraft data" claim were wrong.

**A further finding that supersedes this section's premise:** the aggregate endpoints are
not ours to use at all. Their response body states the data is "only for use on
17Lands.com" and that the only data permitted for outside use is
[the public datasets](https://www.17lands.com/public_datasets) (CC BY 4.0); the
[usage guidelines](https://www.17lands.com/usage_guidelines) discourage automated scraping,
require a visible top-level citation, and ask third-party tools to hold off on a new set
until its 12th day on Arena. So `development_plan.md` §2.3's "Path A" is off the table for
BoosterTutor as well as the prototype, and Path B is the route for both.

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
3. **Freshness: not thin** (corrected 2026-09-15 — see §3). Premier Draft: median **39,705** games/card, GIH WR for **184/188**. Traditional Draft: median **5,909**, GIH WR for **168/188**. ADR 0003's bands will operate normally. The original figures came from a legacy endpoint returning a small slice.
4. **Endpoint shape:** `card_ratings/data?expansion=HOB&format=<Format>` and `color_ratings/data?expansion=HOB&event_type=<Format>&start_date=&end_date=` both confirmed live; exact default-window behavior of the latter not fully pinned down and should be re-verified via a real Network-tab capture before ingestion code depends on it.
