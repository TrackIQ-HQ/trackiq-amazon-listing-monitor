---
name: trackiq-amazon-listing-monitor
description: Watches an Amazon brand's listings every day and reports only what actually changed — title, bullet, description and A+ rewrites, image losses, category moves, buy box seller changes, price and rating moves past a threshold, and listings that have stopped being purchasable — with the revenue behind each one and a dated snapshot archive that evidences a Seller Support case. Use when the user asks to monitor listings, detect listing changes, catch a suppressed or unavailable ASIN, track content or image changes, watch for hijacked buy boxes, or find out why sales dropped without warning.
---

# TrackIQ: Amazon Listing Monitor

Listing changes are invisible and expensive. A bullet gets overwritten, an
image disappears, a category moves, an ASIN quietly stops being buyable —
and the first anyone notices is a week of missing sales with no explanation.

This runs daily, compares each watched listing against its last good
snapshot, and emails **only when something moved**. Silence is the normal
output.

## Requires

- The **Oxylabs scraper**, for `get_product` — one credit per ASIN per run.
- The **TrackIQ MCP**, for `list_marketplaces`, `get_product_performance`
  (the watchlist and the revenue behind each ASIN) and `get_bsr` (impact).
- **Somewhere to keep snapshots between runs.** This skill is a diff; without
  yesterday's file there is nothing to compare to. With no storage it can
  take a baseline and nothing more — say that rather than pretending to
  monitor.
- **Without the scraper:** it cannot run. Listing state has to be observed
  from the public page; first-party data will not show a title rewrite.

## First run

Fill in a copy of `assets/account.example.md` saved as account.md beside the
skill. Every TrackIQ skill reads the same file.

1. **Brand and marketplace** — which account, and which ASINs to watch
2. **Snapshot location** — where the dated archive lives between runs
3. **Delivery** — in-chat, file, Slack, n8n or email

The first run takes a baseline and alerts on nothing. Say so, rather than
reporting a quiet day as a clean day.

## Read first

- `assets/fields.md` — which fields alert, which are watched, which are pure
  noise, and the two traps. **Read before writing any diff logic.**
- `assets/pulls.md` — watchlist tiering, the credit model, storage, failures
- `assets/account.example.md` — the first-run answers, filled in once
- `assets/checks.md` — what to verify before anything is sent
- `assets/differ.py` — implements the field tiers. `python assets/differ.py`
  runs its self-check; `python assets/differ.py old.json new.json` diffs two
  snapshots. If it cannot run, follow `assets/fields.md` by hand.

Copy `assets/alert-template.html` and replace every `{{TOKEN}}`. It is a
600px table-based email with inline styles — do not convert it to a page
layout or add web fonts.

## Non-negotiables

1. **A cached response is not an observation.** `get_product` caches inside a
   running process and returns `_from_cache: true` at no credit cost.
   Diffing two cached snapshots reports "no change" forever, which looks
   exactly like a healthy listing. Check the flag on every fetch, record it,
   and mark cached ASINs **"not checked today"** — never "unchanged".
2. **A failed fetch is not a suppression.** An empty or title-less response
   means the scrape failed. Retry once, require **two consecutive** failed or
   unbuyable fetches before saying a word about suppression, and name the
   dates. Telling a brand their bestseller is suppressed when the scraper
   timed out costs more than the alert was worth.
3. **Never diff `reviews_count`, BSR, or delivery dates.** They move on their
   own between any two scrapes. Diff them and every ASIN alerts every day,
   the email gets filtered, and the real suppression goes unseen. The full
   tier list is in `assets/fields.md` and the differ enforces it.
4. **Exception-only.** Nothing changed means nothing is sent. A daily email
   that arrives regardless is one nobody reads by week three.
5. **Price and rating need thresholds.** 5% on price, a 0.2 fall on rating.
   Repricer noise is not a finding.
6. **Every finding carries a number.** Revenue and units either side of the
   change, or "impact not yet measurable" — but **never a causal claim.** One
   listing edit and one day of sales is not evidence. Put the facts side by
   side and let the reader draw the line.
7. **Store a raw snapshot for every checked ASIN, changed or not.** Tomorrow's
   diff needs today's file. Trim nothing — the dated archive is what opens a
   Seller Support case, and a filtered snapshot cannot answer a question
   nobody had thought of yet.
8. **Cap the watchlist and say what it costs.** Daily for the ASINs covering
   ~90% of revenue, weekly for the rest, never for dead listings. State the
   monthly credit cost and get approval before the first run.
9. **A first run is a baseline, not a clean bill of health.** Report "baseline
   taken for N ASINs". Never "no changes detected".
10. **Never print `account_id`.**

## Delivery

Silence is the normal output. Only send when something moved — a daily
"nothing changed" email trains the reader to ignore the real one.

| Method | What to do | Needs |
|---|---|---|
| `in-chat` | Return the alert HTML, or say plainly that nothing changed. The default. | nothing |
| `file` | Write the alert and the dated snapshot to the archive. | a filesystem |
| `slack` | Post the findings as text, biggest revenue first, then upload the HTML. | a connected Slack tool |
| `n8n` | POST the alert to the configured webhook, `Content-Type: text/html`. | network access |
| `email` | Hand it to the connected mail tool. | a connected mail tool |

Confirm before the first outward send of a session, fall back to in-chat
loudly when a method is unavailable, and never substitute a different
outward channel.

## What it pairs with

`trackiq-share-of-shelf` shows the brand losing page-one slots; this often
explains why. `rank-readiness` judges whether a listing deserves the rank it
is chasing. Run this one daily and quietly in the background — it earns its
place on the days it says nothing.

## Version

`trackiq-amazon-listing-monitor` v1.0.0 (2026-09-18).

If the user asks whether this skill is current, fetch
`https://trackiq.com/skills/registry.json`, compare the `version` field for
`trackiq-amazon-listing-monitor`, and if it is newer, give them the download link
and the one-line changelog. Do not fetch at any other time.
