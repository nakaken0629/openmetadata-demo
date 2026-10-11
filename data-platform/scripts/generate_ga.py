"""Web アプリのエクスポート（jaffle_shop）をもとに、Google Analytics のエクスポートファイルを生成する。

流入元のキャンペーンに CRM のキャンペーン（sources/crm/campaigns.csv）を使うため、
先に generate_crm.py を実行しておくこと。

    python scripts/generate_ga.py

生成するファイル（sources/ga/）
- events_YYYYMMDD.csv: 1 日分のイベント（GA4 のイベントエクスポートを平坦化した形式）
"""

import random
from collections import defaultdict
from datetime import date, datetime, timedelta

from common import JST, SEED, SOURCES_DIR, read_csv, write_csv

SITE_URL = "https://shop.example.com"
CAMPAIGN_SOURCE = {"email": ("newsletter", "email"), "social": ("instagram", "social"), "cpc": ("google", "cpc")}
ORGANIC_SOURCES = [("google", "organic"), ("yahoo", "organic"), ("(direct)", "(none)"), ("twitter.com", "referral")]
DEVICES = ["desktop", "mobile", "mobile", "tablet"]
ANONYMOUS_VISITORS = 120


def pseudo_id(rng):
    return f"{rng.randint(10**9, 10**10 - 1)}.{rng.randint(10**9, 10**10 - 1)}"


def traffic_source(rng, day, campaigns):
    active = [c for c in campaigns if date.fromisoformat(c["start_date"]) <= day <= date.fromisoformat(c["end_date"])]
    if active and rng.random() < 0.4:
        campaign = rng.choice(active)
        source, medium = CAMPAIGN_SOURCE[campaign["channel"]]
        return source, medium, campaign["utm_campaign"]
    source, medium = rng.choice(ORGANIC_SOURCES)
    return source, medium, ""


def build_session(rng, campaigns, day, user_pseudo_id, session_number, user_id="", order=None, revenue=None):
    """1 セッション分の GA イベントを生成する。order を渡すと購入セッションになる。"""
    start = datetime.combine(day, datetime.min.time(), JST) + timedelta(
        hours=rng.randint(8, 23), minutes=rng.randint(0, 59), seconds=rng.randint(0, 59)
    )
    session_id = int(start.timestamp())
    source, medium, campaign = traffic_source(rng, day, campaigns)
    device = rng.choice(DEVICES)

    pages = [("session_start", "/"), ("page_view", "/")]
    for _ in range(rng.randint(1, 4)):
        item = rng.randint(1, 20)
        pages += [("page_view", f"/products/{item}"), ("view_item", f"/products/{item}")]
    if order is not None:
        pages += [
            ("add_to_cart", pages[-1][1]),
            ("page_view", "/cart"),
            ("begin_checkout", "/checkout"),
            ("login", "/login"),
            ("purchase", "/checkout/complete"),
        ]

    events = []
    ts = start
    for event_name, path in pages:
        ts += timedelta(seconds=rng.randint(5, 90))
        is_purchase = event_name == "purchase"
        events.append(
            {
                "event_date": day.strftime("%Y%m%d"),
                "event_timestamp": int(ts.timestamp() * 1_000_000),
                "event_name": event_name,
                "user_pseudo_id": user_pseudo_id,
                "user_id": user_id,
                "ga_session_id": session_id,
                "ga_session_number": session_number,
                "page_location": SITE_URL + path,
                "traffic_source": source,
                "traffic_medium": medium,
                "traffic_campaign": campaign,
                "device_category": device,
                "transaction_id": order["id"] if is_purchase else "",
                "purchase_revenue": f"{revenue:.2f}" if is_purchase else "",
            }
        )
    return events


def main():
    rng = random.Random(SEED)
    customers = read_csv(SOURCES_DIR / "webapp" / "customers.csv")
    orders = read_csv(SOURCES_DIR / "webapp" / "orders.csv")
    payments = read_csv(SOURCES_DIR / "webapp" / "payments.csv")
    campaigns = read_csv(SOURCES_DIR / "crm" / "campaigns.csv")

    revenue_by_order = defaultdict(int)
    for p in payments:
        revenue_by_order[p["order_id"]] += int(p["amount"])

    days = sorted({date.fromisoformat(o["order_date"]) for o in orders})
    first_day, last_day = days[0], days[-1]
    period = (last_day - first_day).days

    # (日付, user_pseudo_id, user_id, 注文) のセッション計画を作る
    plans = []
    customer_pseudo = {c["id"]: pseudo_id(rng) for c in customers}
    # 購入セッション（購入時にログインするため user_id あり）
    for o in orders:
        plans.append((date.fromisoformat(o["order_date"]), customer_pseudo[o["user_id"]], o["user_id"], o))
    # 会員の閲覧のみのセッション（ログインしていないため user_id なし）
    for c in customers:
        for _ in range(rng.randint(0, 3)):
            plans.append((first_day + timedelta(days=rng.randint(0, period)), customer_pseudo[c["id"]], "", None))
    # 非会員の訪問
    for _ in range(ANONYMOUS_VISITORS):
        visitor = pseudo_id(rng)
        for _ in range(rng.randint(1, 2)):
            plans.append((first_day + timedelta(days=rng.randint(0, period)), visitor, "", None))

    plans.sort(key=lambda p: (p[0], p[1]))
    session_numbers = defaultdict(int)
    events_by_day = defaultdict(list)
    for day, visitor, user_id, order in plans:
        session_numbers[visitor] += 1
        revenue = revenue_by_order[order["id"]] / 100 if order else None
        events_by_day[day] += build_session(rng, campaigns, day, visitor, session_numbers[visitor], user_id, order, revenue)

    fieldnames = list(next(iter(events_by_day.values()))[0].keys())
    for offset in range(period + 1):
        day = first_day + timedelta(days=offset)
        rows = sorted(events_by_day[day], key=lambda e: e["event_timestamp"])
        write_csv(SOURCES_DIR / "ga" / f"events_{day:%Y%m%d}.csv", fieldnames, rows)


if __name__ == "__main__":
    main()
