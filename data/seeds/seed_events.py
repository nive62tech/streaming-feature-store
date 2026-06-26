import csv
import random
import uuid
from datetime import datetime, timedelta
import os

USERS = [f"user_{i:04d}" for i in range(1, 201)]
ITEMS = [f"item_{i:04d}" for i in range(1, 501)]
CATEGORIES = ["electronics", "clothing", "books", "sports", "home", "beauty", "food"]
PLATFORMS = ["web", "mobile", "tablet"]
REGIONS = ["us-east", "us-west", "eu-west", "ap-south"]
EVENT_TYPES = ["click", "purchase", "view", "search", "add_to_cart"]
EVENT_WEIGHTS = [0.35, 0.10, 0.30, 0.15, 0.10]

def generate_seed_events(n: int = 50000) -> list[dict]:
    events = []
    base_time = datetime.utcnow() - timedelta(days=30)

    for i in range(n):
        event_type = random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS, k=1)[0]
        price = None
        quantity = None
        if event_type in ["purchase", "add_to_cart"]:
            price = round(random.uniform(5.0, 500.0), 2)
            quantity = random.randint(1, 5)
        timestamp = base_time + timedelta(seconds=random.randint(0, 30 * 24 * 3600))
        events.append({
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "user_id": random.choice(USERS),
            "item_id": random.choice(ITEMS),
            "category": random.choice(CATEGORIES),
            "price": price,
            "quantity": quantity,
            "session_id": f"sess_{random.randint(10000, 99999)}",
            "timestamp": timestamp.isoformat(),
            "platform": random.choice(PLATFORMS),
            "region": random.choice(REGIONS),
        })

    events.sort(key=lambda x: x["timestamp"])
    return events

def save_to_csv(events: list[dict], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=events[0].keys())
        writer.writeheader()
        writer.writerows(events)
    print(f"Saved {len(events)} events to {path}")

if __name__ == "__main__":
    print("Generating 50,000 seed events...")
    events = generate_seed_events(n=50000)
    save_to_csv(events, "data/raw/events.csv")
    print("Seed complete.")
    print(f"Sample event: {events[0]}")
