import json
import time
import random
import logging
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
from feature_store.config import settings
from feature_store.ingestion.schemas import RawEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USERS = [f"user_{i:04d}" for i in range(1, 201)]
ITEMS = [f"item_{i:04d}" for i in range(1, 501)]
CATEGORIES = ["electronics", "clothing", "books", "sports", "home", "beauty", "food"]
PLATFORMS = ["web", "mobile", "tablet"]
REGIONS = ["us-east", "us-west", "eu-west", "ap-south"]
EVENT_TYPES = ["click", "purchase", "view", "search", "add_to_cart"]
EVENT_WEIGHTS = [0.35, 0.10, 0.30, 0.15, 0.10]

def generate_event() -> RawEvent:
    event_type = random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS, k=1)[0]
    category = random.choice(CATEGORIES)
    price = None
    quantity = None
    if event_type in ["purchase", "add_to_cart"]:
        price = round(random.uniform(5.0, 500.0), 2)
        quantity = random.randint(1, 5)
    return RawEvent(
        event_type=event_type,
        user_id=random.choice(USERS),
        item_id=random.choice(ITEMS),
        category=category,
        price=price,
        quantity=quantity,
        session_id=f"sess_{random.randint(10000, 99999)}",
        platform=random.choice(PLATFORMS),
        region=random.choice(REGIONS),
    )

def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=settings.kafka.BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        acks="all",
        retries=3,
        max_in_flight_requests_per_connection=1,
    )

def on_send_success(record_metadata):
    logger.debug(
        f"Sent to {record_metadata.topic} "
        f"partition={record_metadata.partition} "
        f"offset={record_metadata.offset}"
    )

def on_send_error(exc):
    logger.error(f"Failed to send event: {exc}")

def run_producer(events_per_second: float = 2.0, max_events: int = None):
    logger.info(f"Starting producer — {events_per_second} events/sec")
    producer = create_producer()
    count = 0
    interval = 1.0 / events_per_second

    try:
        while True:
            event = generate_event()
            event_dict = event.to_dict()
            producer.send(
                settings.kafka.TOPIC_RAW_EVENTS,
                key=event.user_id,
                value=event_dict,
            ).add_callback(on_send_success).add_errback(on_send_error)
            count += 1
            if count % 10 == 0:
                logger.info(f"Produced {count} events — latest: {event.event_type} by {event.user_id}")
            if max_events and count >= max_events:
                logger.info(f"Reached max_events={max_events}. Stopping.")
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info(f"Producer stopped by user after {count} events.")
    finally:
        producer.flush()
        producer.close()
        logger.info("Producer closed cleanly.")

if __name__ == "__main__":
    run_producer(events_per_second=2.0)
