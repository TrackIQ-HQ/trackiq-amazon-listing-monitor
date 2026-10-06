# Before you send it

## 1. Is this an observation at all?

- **No ASIN in the email returned `_from_cache: true`.** A cached snapshot
  compared against itself reports "no change" forever. Cached ASINs are
  listed as "not checked today", never as clean.
- **Every alerting ASIN had a successful fetch** — a title came back.
- **No availability finding rests on a title-less snapshot.** That is a
  failed fetch, and calling it a suppression is the most damaging mistake
  this skill can make.
- **A suppression claim has two consecutive failed or unbuyable fetches
  behind it**, and the email says which dates.

## 2. Is it the first run?

If there is no prior snapshot, the output says **"baseline taken"** and the
ASIN count. It does not say "no changes detected" — those are opposite
statements and only one of them is true.

## 3. Is it worth sending?

- Nothing alerted, and the user has not asked for a heartbeat → **send
  nothing.** That is the skill working, not failing.
- Every finding is in the ALERT tier, or is a WATCH past its threshold. No
  raw `reviews_count`, `bsr`, or delivery-date rows anywhere in the email.
- No ASIN appears twice for the same underlying change.

## 4. Do the findings carry a cost?

- Every alerting ASIN shows revenue and units either side of the change, or
  says **"impact not yet measurable"** where the sales data has not landed.
- No sentence claims the listing change *caused* the sales move. The two
  facts sit next to each other; the reader draws the line.
- ASINs are ordered by revenue at risk, not alphabetically and not by how
  many fields changed.

## 5. The diff renders honestly

- Old text is struck through, new text highlighted, and **both are shown in
  full** for title and bullets. A truncated diff hides the edit that matters.
- Image changes state the counts on both sides.
- Long fields are shown as the changed portion with enough surrounding text
  to locate it — never a bare "description changed".

## 6. Render check

Open the HTML and run:

```js
({ width: document.body.scrollWidth,
   imgs: [...document.images].map(i => i.naturalWidth > 0),
   alerts: document.querySelectorAll('[data-sev="alert"]').length,
   watches: document.querySelectorAll('[data-sev="watch"]').length })
```

- `width` at or under 600 for the email build.
- `imgs` all true.
- `alerts` and `watches` match the counts in the summary line.

Then look at it. If the page will not paint, say the check was structural
rather than visual.

## 7. Housekeeping

- Snapshot written for **every** checked ASIN, including unchanged ones —
  tomorrow's diff needs today's file whether or not anything moved.
- Snapshot stored raw and unfiltered.
- The run states ASINs checked, cached, failed, and credits consumed.
- `python assets/differ.py` still passes its self-check after any edit to
  the field tiers.
