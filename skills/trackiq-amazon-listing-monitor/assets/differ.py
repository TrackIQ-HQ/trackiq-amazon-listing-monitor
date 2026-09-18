#!/usr/bin/env python3
"""Diff two listing snapshots and classify what changed.

An accelerant, not a dependency: the same rules are written out in
assets/fields.md, and the skill works by following those by hand when this
cannot run.

    python differ.py            # runs the self-check
    python differ.py a.json b.json
"""
from __future__ import annotations

import json
import sys

# --- ALERT: content and state a human changed, or Amazon changed for them ---
ALERT_SCALAR = {
    "title": "Title",
    "brand": "Brand",
    "description": "Description / A+",
    "bullet_points": "Bullet points",
}
# --- WATCH: real but noisy; only report past a threshold ---
PRICE_MOVE_PCT = 5.0      # report a price move only past this
RATING_DROP = 0.2         # report a rating fall only past this

# --- IGNORE: changes on its own between any two scrapes ---
IGNORE = {
    "delivery", "delivery_raw", "buybox_raw", "url", "credits_consumed_this_call",
    "credits_consumed_this_process", "_from_cache", "answered_questions_count",
    "reviews_count",            # monotonic; use velocity, never a diff
    "bsr_primary", "sales_rank_ladder",   # moves hourly; context only
}
IGNORE_BONUS = {"buy_it_with", "frequently_bought_together", "rating_stars_distribution"}


def _images(s):
    return [i for i in (s.get("images") or [])]


def _cats(s):
    cat = s.get("category") or []
    if not cat:
        return []
    return [c.get("name") for c in (cat[0].get("ladder") or [])]


def _seller(s):
    bb = s.get("buybox") or {}
    fm = (s.get("_oxylabs_bonus") or {}).get("featured_merchant") or {}
    return fm.get("seller_id") or bb.get("seller")


def is_unbuyable(s) -> bool:
    """No price and no buy box = not purchasable. Distinct from a failed scrape,
    which has no title either and must never be read as a suppression."""
    if not s.get("title"):
        return False
    bb = s.get("buybox") or {}
    stock = (bb.get("stock") or "").lower()
    if "unavailable" in stock or "out of stock" in stock:
        return True
    return s.get("price") in (None, 0) and not bb.get("price")


def diff(old: dict, new: dict) -> list[dict]:
    """Return findings, most severe first. severity: alert | watch."""
    out = []

    def add(sev, field, label, was, now, note=""):
        out.append(dict(severity=sev, field=field, label=label,
                        was=was, now=now, note=note))

    # availability first — it outranks everything else on the page
    if is_unbuyable(new) and not is_unbuyable(old):
        add("alert", "availability", "Listing not purchasable",
            "buyable", "no price / no buy box",
            "suppression, out of stock, or buy box suppressed")
    elif is_unbuyable(old) and not is_unbuyable(new):
        add("alert", "availability", "Listing purchasable again",
            "no price / no buy box", "buyable")

    for key, label in ALERT_SCALAR.items():
        a, b = old.get(key), new.get(key)
        if a != b:
            add("alert", key, label, a, b)

    ia, ib = _images(old), _images(new)
    if len(ia) != len(ib):
        add("alert", "images", "Image count",
            f"{len(ia)} images", f"{len(ib)} images",
            "image loss is the most common silent listing regression")
    elif ia != ib:
        add("alert", "images", "Images replaced",
            f"{len(ia)} images", f"{len(ib)} images",
            "same count, different files")

    ca, cb = _cats(old), _cats(new)
    if ca != cb:
        add("alert", "category", "Category ladder",
            " > ".join(ca), " > ".join(cb), "re-categorisation moves BSR and browse traffic")

    sa, sb = _seller(old), _seller(new)
    if sa != sb:
        add("alert", "buybox_seller", "Buy box seller", sa, sb)

    pa, pb = old.get("price"), new.get("price")
    if isinstance(pa, (int, float)) and isinstance(pb, (int, float)) and pa:
        move = 100.0 * (pb - pa) / pa
        if abs(move) >= PRICE_MOVE_PCT:
            add("watch", "price", "Price", f"${pa:,.2f}", f"${pb:,.2f}", f"{move:+.1f}%")

    ra, rb = old.get("rating"), new.get("rating")
    if isinstance(ra, (int, float)) and isinstance(rb, (int, float)):
        if ra - rb >= RATING_DROP:
            add("watch", "rating", "Star rating", ra, rb, f"{rb - ra:+.1f}")

    for key, label in (("coupon", "Coupon"), ("deal_type", "Deal")):
        a, b = old.get(key), new.get(key)
        if a != b:
            add("watch", key, label, a, b)

    order = {"alert": 0, "watch": 1}
    out.sort(key=lambda f: order[f["severity"]])
    return out


def _selfcheck():
    base = {
        "title": "Outdoor String Lights 48ft Weatherproof, 15 Sockets",
        "brand": "Example Brand",
        "description": "Certified. Guaranteed. Raw.",
        "bullet_points": "A\nB\nC",
        "images": [f"img{i}.jpg" for i in range(7)],
        "category": [{"ladder": [{"name": "Patio, Lawn & Garden"}, {"name": "String Lights"}]}],
        "price": 39.29, "rating": 4.5, "reviews_count": 1200,
        "buybox": {"price": 39.29, "seller": "Example Brand", "stock": "In Stock"},
        "_oxylabs_bonus": {"featured_merchant": {"seller_id": "AAA"}},
        "bsr_primary": {"rank": 3638},
        "delivery": {"delivery_date": {"by": "Wednesday, September 23"}},
    }
    import copy

    # 1. identical snapshots produce nothing
    assert diff(base, copy.deepcopy(base)) == [], "identical snapshots must not alert"

    # 2. pure noise produces nothing
    noisy = copy.deepcopy(base)
    noisy["delivery"] = {"delivery_date": {"by": "Friday, September 25"}}
    noisy["reviews_count"] = 1207
    noisy["bsr_primary"] = {"rank": 4102}
    assert diff(base, noisy) == [], "delivery / reviews / BSR drift must not alert"

    # 3. an image dropping is an alert
    lost = copy.deepcopy(base); lost["images"] = lost["images"][:6]
    f = diff(base, lost)
    assert any(x["field"] == "images" and x["severity"] == "alert" for x in f), f

    # 4. title rewrite is an alert
    ret = copy.deepcopy(base); ret["title"] = "String Lights 48ft"
    assert any(x["field"] == "title" for x in diff(base, ret))

    # 5. small price move is ignored, large one is a watch
    small = copy.deepcopy(base); small["price"] = 40.00
    assert diff(base, small) == [], "sub-threshold price move must not report"
    big = copy.deepcopy(base); big["price"] = 31.00
    assert any(x["field"] == "price" and x["severity"] == "watch" for x in diff(base, big))

    # 6. losing the buy box to another seller is an alert
    hij = copy.deepcopy(base)
    hij["_oxylabs_bonus"]["featured_merchant"]["seller_id"] = "BBB"
    assert any(x["field"] == "buybox_seller" for x in diff(base, hij))

    # 7. going unbuyable is an alert; a FAILED SCRAPE is not
    sup = copy.deepcopy(base); sup["price"] = None; sup["buybox"] = {}
    assert any(x["field"] == "availability" for x in diff(base, sup))
    failed = {"asin": base.get("asin")}          # no title -> scrape failure
    assert not any(x["field"] == "availability" for x in diff(base, failed)), \
        "an empty scrape must never be reported as a suppression"

    # 8. severity ordering
    both = copy.deepcopy(base); both["title"] = "x"; both["price"] = 20.0
    assert [x["severity"] for x in diff(base, both)] == ["alert", "watch"]

    print("differ self-check: 8/8 passed")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        a = json.load(open(sys.argv[1], encoding="utf-8"))
        b = json.load(open(sys.argv[2], encoding="utf-8"))
        print(json.dumps(diff(a, b), indent=2))
    else:
        _selfcheck()
