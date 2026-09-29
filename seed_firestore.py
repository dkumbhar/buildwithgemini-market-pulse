# Copyright 2026 Google LLC
# Seed script for Firestore portfolio collection

import sys
from google.cloud import firestore

FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-f582106045c5"

SEED_DATA = [
    {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "asset_type": "Stock",
        "shares": 15.0,
        "avg_buy_price": 180.50,
        "current_price": 224.30,
        "category": "Technology",
    },
    {
        "ticker": "GOOGL",
        "name": "Alphabet Inc.",
        "asset_type": "Stock",
        "shares": 25.0,
        "avg_buy_price": 145.00,
        "current_price": 178.60,
        "category": "Technology",
    },
    {
        "ticker": "NVDA",
        "name": "NVIDIA Corporation",
        "asset_type": "Stock",
        "shares": 10.0,
        "avg_buy_price": 110.00,
        "current_price": 130.20,
        "category": "Semiconductors",
    },
    {
        "ticker": "BTC",
        "name": "Bitcoin",
        "asset_type": "Crypto",
        "shares": 0.35,
        "avg_buy_price": 58000.00,
        "current_price": 64500.00,
        "category": "Crypto",
    },
    {
        "ticker": "ETH",
        "name": "Ethereum",
        "asset_type": "Crypto",
        "shares": 2.5,
        "avg_buy_price": 2800.00,
        "current_price": 3450.00,
        "category": "Crypto",
    },
    {
        "ticker": "VOO",
        "name": "Vanguard S&P 500 ETF",
        "asset_type": "ETF",
        "shares": 8.0,
        "avg_buy_price": 450.00,
        "current_price": 512.80,
        "category": "Index ETF",
    },
]


def seed_database():
    print(f"Connecting to Firestore for project: {FIRESTORE_PROJECT_ID}...")
    db = firestore.Client(project=FIRESTORE_PROJECT_ID)
    collection_ref = db.collection("portfolio")

    for item in SEED_DATA:
        doc_id = item["ticker"].upper()
        collection_ref.document(doc_id).set(item)
        print(f"Seeded portfolio item: {doc_id} ({item['name']})")

    print("Firestore seeding completed successfully!")


if __name__ == "__main__":
    try:
        seed_database()
    except Exception as e:
        print(f"Error seeding Firestore: {e}", file=sys.stderr)
        sys.exit(1)
