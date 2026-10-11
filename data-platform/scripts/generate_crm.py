"""Web アプリのエクスポート（jaffle_shop）をもとに、CRM のエクスポートファイルを生成する。

    python scripts/generate_crm.py

生成するファイル（sources/crm/）
- contacts.csv: 顧客（会員の大半と、会員登録していない見込み客）
- inquiries.csv: 問い合わせ
- campaigns.csv: キャンペーン（GA の utm_campaign と対応する）
"""

import random
from collections import defaultdict
from datetime import date, datetime, timedelta

from common import JST, SEED, SOURCES_DIR, read_csv, write_csv

EXPORT_AT = datetime(2018, 4, 10, 3, 0, tzinfo=JST)

CAMPAIGNS = [
    ("CMP-001", "新春セール 2018", "new_year_sale_2018", "email", date(2018, 1, 1), date(2018, 1, 14), 300000),
    ("CMP-002", "バレンタイン特集 2018", "valentine_2018", "social", date(2018, 2, 1), date(2018, 2, 14), 200000),
    ("CMP-003", "春の新生活セール 2018", "spring_sale_2018", "cpc", date(2018, 3, 15), date(2018, 3, 31), 500000),
    ("CMP-004", "会員限定クーポン 2018 春", "member_coupon_2018_spring", "email", date(2018, 4, 1), date(2018, 4, 9), 100000),
]

# CRM にのみ存在する見込み客（会員登録していない）
LEADS = [
    ("Emily", "R."), ("Daniel", "K."), ("Olivia", "T."), ("James", "W."), ("Sophia", "N."),
    ("Henry", "B."), ("Grace", "L."), ("Lucas", "F."), ("Chloe", "S."), ("Ethan", "H."),
]


def generate_contacts(rng, customers, orders_by_customer):
    # 一部の会員は CRM に登録されていない
    unregistered = set(rng.sample([c["id"] for c in customers], 8))
    registered = [c for c in customers if c["id"] not in unregistered]
    leads = [{"id": "", "first_name": fn, "last_name": ln} for fn, ln in LEADS]

    contacts = []
    for i, c in enumerate(registered + leads, start=1):
        customer_orders = orders_by_customer.get(c["id"], [])
        first_order = min((date.fromisoformat(o["order_date"]) for o in customer_orders), default=date(2018, 4, 9))
        created_at = datetime.combine(first_order - timedelta(days=rng.randint(1, 60)), datetime.min.time(), JST) + timedelta(
            minutes=rng.randint(0, 1439)
        )
        updated_at = min(created_at + timedelta(days=rng.randint(0, 90)), EXPORT_AT)
        rank = "gold" if len(customer_orders) >= 4 else "silver" if len(customer_orders) >= 2 else "bronze"
        contacts.append(
            {
                "contact_id": f"CRM-{i:04d}",
                "external_customer_id": c["id"],
                "first_name": c["first_name"],
                "last_name": c["last_name"],
                "email": f"{c['first_name'].lower()}.{c['last_name'].rstrip('.').lower()}{i}@example.com",
                "phone": f"090-{rng.randint(0, 9999):04d}-{rng.randint(0, 9999):04d}",
                "birth_date": (date(1960, 1, 1) + timedelta(days=rng.randint(0, 365 * 40))).isoformat(),
                "membership_rank": rank if c["id"] else "",
                "email_opt_in": str(rng.random() < 0.7).lower(),
                "created_at": created_at.isoformat(),
                "updated_at": updated_at.isoformat(),
            }
        )
    return contacts


def generate_inquiries(rng, contacts, orders):
    contact_by_customer = {c["external_customer_id"]: c["contact_id"] for c in contacts if c["external_customer_id"]}
    inquiries = []

    def add_inquiry(contact_id, order_id, category, day):
        created_at = datetime.combine(day, datetime.min.time(), JST) + timedelta(hours=rng.randint(9, 20), minutes=rng.randint(0, 59))
        closed_at = created_at + timedelta(days=rng.randint(0, 5), hours=rng.randint(1, 8))
        status = "closed" if closed_at < EXPORT_AT - timedelta(days=2) else rng.choice(["open", "in_progress"])
        inquiries.append(
            {
                "inquiry_id": "",
                "contact_id": contact_id,
                "order_id": order_id,
                "category": category,
                "channel": rng.choice(["email", "phone", "chat"]),
                "status": status,
                "created_at": created_at.isoformat(),
                "closed_at": closed_at.isoformat() if status == "closed" else "",
            }
        )

    for o in sorted(orders, key=lambda o: o["order_date"]):
        contact_id = contact_by_customer.get(o["user_id"])
        if contact_id is None:
            continue
        order_day = date.fromisoformat(o["order_date"])
        if o["status"] in ("returned", "return_pending"):
            add_inquiry(contact_id, o["id"], "return", order_day + timedelta(days=rng.randint(2, 7)))
        elif o["status"] in ("placed", "shipped") and rng.random() < 0.4:
            add_inquiry(contact_id, o["id"], "delivery", order_day + timedelta(days=rng.randint(1, 3)))
        elif rng.random() < 0.1:
            add_inquiry(contact_id, o["id"], rng.choice(["payment", "product"]), order_day + timedelta(days=rng.randint(0, 3)))
    # 注文に紐づかない問い合わせ
    for _ in range(8):
        contact = rng.choice(contacts)
        add_inquiry(contact["contact_id"], "", rng.choice(["account", "product"]), date(2018, 1, 1) + timedelta(days=rng.randint(0, 98)))

    inquiries.sort(key=lambda r: r["created_at"])
    for i, r in enumerate(inquiries, start=1):
        r["inquiry_id"] = f"INQ-{i:05d}"
    return inquiries


def main():
    rng = random.Random(SEED)
    customers = read_csv(SOURCES_DIR / "webapp" / "customers.csv")
    orders = read_csv(SOURCES_DIR / "webapp" / "orders.csv")
    orders_by_customer = defaultdict(list)
    for o in orders:
        orders_by_customer[o["user_id"]].append(o)

    contacts = generate_contacts(rng, customers, orders_by_customer)
    write_csv(SOURCES_DIR / "crm" / "contacts.csv", list(contacts[0].keys()), contacts)

    inquiries = generate_inquiries(rng, contacts, orders)
    write_csv(SOURCES_DIR / "crm" / "inquiries.csv", list(inquiries[0].keys()), inquiries)

    fieldnames = ["campaign_id", "campaign_name", "utm_campaign", "channel", "start_date", "end_date", "budget"]
    write_csv(SOURCES_DIR / "crm" / "campaigns.csv", fieldnames, [dict(zip(fieldnames, c)) for c in CAMPAIGNS])


if __name__ == "__main__":
    main()
