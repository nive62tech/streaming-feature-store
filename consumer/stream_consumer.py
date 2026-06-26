import json
import logging
import signal
import sys
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from feature_store.config import settings
from feature_store.computation.feature_pipeline import pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

class StreamConsumer:
    """
    Kafka consumer that reads raw events and runs them
    through the feature computation pipeline.
    """

    def __init__(self):
        self.consumer = KafkaConsumer(
            settings.kafka.TOPIC_RAW_EVENTS,
            bootstrap_servers=settings.kafka.BOOTSTRAP_SERVERS,
            group_id=settings.kafka.CONSUMER_GROUP,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            auto_offset_reset="latest",
            enable_auto_commit=True,
            max_poll_records=10,
        )
        self.running = False
        self.processed_count = 0
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        logger.info(f"Shutdown signal received. Processed {self.processed_count} events total.")
        self.running = False

    def process_message(self, event: dict) -> dict:
        features = pipeline.process(event)
        return features

    def run(self):
        logger.info(f"Consumer started — listening on topic: {settings.kafka.TOPIC_RAW_EVENTS}")
        self.running = True

        try:
            for message in self.consumer:
                if not self.running:
                    break

                event = message.value
                try:
                    features = self.process_message(event)
                    self.processed_count += 1

                    if self.processed_count % 5 == 0:
                        logger.info(
                            f"Processed {self.processed_count} events | "
                            f"Latest user: {features['entity_id']} | "
                            f"event_count_1min: {features.get('event_count_1min', 0)} | "
                            f"event_count_5min: {features.get('event_count_5min', 0)}"
                        )

                except Exception as e:
                    logger.error(f"Failed to process event {event.get('event_id')}: {e}")
                    continue

        except KafkaError as e:
            logger.error(f"Kafka error: {e}")
        finally:
            self.consumer.close()
            logger.info("Consumer closed cleanly.")


if __name__ == "__main__":
    consumer = StreamConsumer()
    consumer.run()