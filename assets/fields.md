# What counts as a change

The whole skill lives or dies here. A snapshot has around forty fields and
most of them move on their own. Diff everything and the first email has
sixty rows, the second is deleted unread, and a real suppression three weeks
later goes unnoticed.

Three tiers. `assets/differ.py` implements exactly this list; if it cannot
run, follow the tiers by hand.

## ALERT — somebody changed the listing, or Amazon changed it for them

Report every one of these, every time.

| Field | Why it matters |
|---|---|
| `title` | rewrites happen without the brand's knowledge and move rank |
| `bullet_points` | the most commonly overwritten field on a shared catalogue |
| `description` | carries A+ content; its disappearance is a real regression |
| `brand` | a brand-field change breaks brand-store and Brand Analytics links |
| `images` | **count first.** Image loss is the most common silent regression |
| `category` ladder | re-categorisation moves BSR, browse traffic and the badge |
| buy box seller | `_oxylabs_bonus.featured_merchant.seller_id`, else `buybox.seller` |
| availability | no price **and** no buy box — see below |

## WATCH — real, but noisy; report only past a threshold

| Field | Threshold |
|---|---|
| `price` | move of **5% or more**. Below that it is repricer noise |
| `rating` | a **fall of 0.2 or more**. Rises are not alerts |
| `coupon`, `deal_type` | any change — these are usually intentional, so report as context |

## IGNORE — changes between any two scrapes on its own

`delivery`, `delivery_raw`, `buybox_raw`, `offer_listing_id`, `url`,
`answered_questions_count`, `_from_cache`, the credit counters, and:

- **`reviews_count`** — monotonic. A diff on it fires daily and says nothing.
  Track velocity separately if anyone wants it; never diff it.
- **`bsr_primary` / `sales_rank_ladder`** — moves hourly. Useful as *impact*
  context next to a change, never as the change itself.
- **`buy_it_with`, `frequently_bought_together`, `rating_stars_distribution`**
  — Amazon-curated and rotating.

## Availability, and the failure that looks like it

A listing is **not purchasable** when:

- `buybox.stock` says unavailable or out of stock, **or**
- `price` is null/zero **and** `buybox.price` is absent.

**A failed scrape looks identical to a suppression and is not one.** If the
response has no `title`, the fetch failed — it is not evidence about the
listing. The differ refuses to raise an availability finding on a
title-less snapshot, and the skill requires **two consecutive failed
fetches** before it will say a word about suppression. Telling a brand their
bestseller is suppressed when the scraper merely timed out costs more trust
than the alert was ever worth.

This monitor sees the public page. It cannot see *why* something is
suppressed — that lives in Seller Central. It reports the symptom with a
timestamped snapshot attached, which is what opens the case.

## Impact — give the change a cost

A change with no number beside it gets ignored. For every alerting ASIN,
pull from the TrackIQ MCP:

- `get_product_performance` (`asin=`, the days either side) — revenue, units,
  sessions, conversion
- `get_bsr` — rank around the change date

Then state the before and after plainly. **Never claim the change caused the
move** — one listing edit and one day of sales is not evidence. Put the two
facts next to each other and let the reader judge; where the sales data is
not in yet, say "impact not yet measurable" rather than leaving it blank.

## The cache trap

`get_product` responses are cached inside a running process. A cached
response carries **`_from_cache: true`** and consumes no credit.

A cached snapshot is **not an observation**. Diffing two cached responses
compares a snapshot with itself and reports "no change" forever, which is
indistinguishable from a healthy listing and is the worst failure this skill
has. Check the flag on every fetch, record it in the snapshot, and if a run
returns cached data for an ASIN, mark that ASIN "not checked today" rather
than "unchanged".
