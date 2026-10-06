# The run

## 0. Account and watchlist

`list_marketplaces` to identify the account, then `get_product_performance`
(`group_by='product'`, trailing 30 days, `limit=200`) for the catalogue with
revenue.

**Rank the watchlist by revenue and cap it.** Every ASIN is a credit a day.
A 60-ASIN catalogue monitored daily is ~1,800 credits a month, and most of
those ASINs earn nothing. The default split:

| Tier | Which ASINs | Cadence |
|---|---|---|
| **Daily** | the ASINs covering ~90% of trailing revenue — usually 10–20 | every day |
| **Weekly** | everything else with revenue above zero | one day a week |
| **Never** | zero-revenue and dead listings | on request only |

State the resulting monthly credit cost before the first run and let the
user approve the tiering. Never monitor a whole catalogue daily by default.

## 1. Snapshot

One call per watched ASIN:

```
get_product(asin=<asin>, country='us')
```

**One credit per ASIN, per run** — but only when it is a live fetch. A
response carrying `_from_cache: true` cost nothing and is **not an
observation**: see the cache trap in `assets/fields.md`. Record the flag in
every snapshot you store.

Store each snapshot as `listing-history/<asin>/<YYYY-MM-DD>.json` with the
raw response plus `fetched_at` and `from_cache`. Keep the raw response —
the archive is half the value of this skill, because a dated snapshot is the
evidence that opens a Seller Support case.

Trim nothing on write. `buybox_raw` is bulky and ignored by the differ, but
a stored snapshot that has been filtered cannot answer a question you have
not thought of yet.

## 2. Diff

Compare today's snapshot to the most recent *live* snapshot for that ASIN —
not necessarily yesterday's, since a cached or failed day has no
observation in it.

`python assets/differ.py old.json new.json` returns the findings as JSON.
Run `python assets/differ.py` with no arguments for its self-check. Where
the script cannot run, apply the tiers in `assets/fields.md` by hand.

**First run has nothing to diff against.** Store the baseline, report that a
baseline was taken and for how many ASINs, and send nothing else. Never
present a first run as "no changes detected".

## 3. Impact

Only for ASINs that alerted. From the TrackIQ MCP:

- `get_product_performance` with `asin=` across the days either side
- `get_bsr` for the same window

Put before and after next to the change. Do not assert causation.

## 4. Send

**Exception-only.** If nothing alerted, send nothing — or, at most, a
one-line "N ASINs checked, no changes" if the user has asked for a daily
heartbeat. A monitor that emails every day regardless is a monitor nobody
reads by week three.

Always state in the output: ASINs checked, ASINs that returned cached data,
ASINs whose fetch failed, and the credits consumed.

## 5. Failures

- An empty or error response is a **failed fetch**, not a finding. Retry once.
- Two consecutive failed fetches for one ASIN: report it as "could not be
  checked", with the dates — not as a suppression.
- If more than about a quarter of the watchlist fails in one run, stop and
  report a scraper problem. Do not send a partial alert email that implies
  the rest were checked and clean.
